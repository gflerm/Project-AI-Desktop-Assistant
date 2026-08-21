from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
import re
import time
from typing import Any, Literal
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from . import __version__
from .config import Settings
from .protocol import (
    BYTES_PER_FRAME,
    CHANNELS,
    FRAMES_PER_CHUNK,
    KIND_MICROPHONE,
    KIND_TTS,
    PCM_BYTES_PER_CHUNK,
    PROTOCOL_VERSION,
    SAMPLE_BITS,
    SAMPLE_RATE_HZ,
    ProtocolError,
    decode_audio_chunk,
    encode_audio_chunk,
)
from .services import ConversationMemory, PiServices, pcm_to_wav
from .personality import PersonalityStore, personality_prompt
from .speech_adaptation import SpeechAdaptation
from .local_learning import LocalLearning
from .telemetry import TelemetryRecorder
from .system_status import PiSystemStatus, system_status_requested
from .weather import WeatherClient, WeatherUnavailable, current_weather_place
from .persistent_memory import PersistentMemory
from .network_status import NetworkStatus
from .intents import TIME_QUERY, ToolIntent, plan_intents
from .capabilities import capability_snapshot, describe_capabilities


settings = Settings.from_environment()
personality_store = PersonalityStore(settings.personality_path)
speech_adaptation = SpeechAdaptation(settings.speech_adaptation_path)
local_learning = LocalLearning(settings.local_learning_path)
persistent_memory = PersistentMemory(settings.persistent_memory_path)
memory = ConversationMemory(settings.session_max_turns, settings.session_idle_seconds)
services = PiServices(
    settings.whisper_url,
    settings.piper_url,
    settings.ollama_url,
    settings.ollama_model,
    settings.ollama_think,
    settings.llm_provider,
    settings.llm_fallback_to_ollama,
    settings.gemini_url,
    settings.gemini_model,
    settings.gemini_api_key,
    settings.gemini_google_search,
    settings.tts_length_scale,
    settings.tts_noise_scale,
    settings.tts_noise_w_scale,
    personality_prompt(personality_store.values),
    memory,
    local_learning,
    persistent_memory,
)
pi_status = PiSystemStatus()
network_status = NetworkStatus()
weather = WeatherClient(
    settings.weather_latitude,
    settings.weather_longitude,
    settings.weather_place,
)
telemetry = TelemetryRecorder(
    settings.telemetry_path,
    enabled=settings.telemetry_enabled,
    include_text=settings.telemetry_include_text,
    max_bytes=settings.telemetry_max_bytes,
)
app = FastAPI(title="Project James Pi Gateway", version=__version__)


@app.middleware("http")
async def record_http_errors(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        telemetry.record(
            "http_error",
            method=request.method,
            path=request.url.path,
            status_code=500,
            status="error",
            server_ms=round((time.perf_counter() - started) * 1000),
        )
        raise
    if response.status_code >= 400:
        telemetry.record(
            "http_error",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            status="error",
            server_ms=round((time.perf_counter() - started) * 1000),
        )
    return response


@app.on_event("startup")
async def warm_local_fallback() -> None:
    warm = getattr(services, "warm_ollama", None)
    if warm:
        try:
            await warm()
        except httpx.HTTPError:
            # Health and telemetry expose the degraded state; cloud service can still start.
            pass


@app.on_event("shutdown")
async def close_clients() -> None:
    close_services = getattr(services, "close", None)
    if close_services:
        await close_services()
    close_weather = getattr(weather, "close", None)
    if close_weather:
        await close_weather()


class TestChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    device_id: str = Field(default="windows-test", min_length=1, max_length=80)
    provider: Literal["auto", "gemini", "ollama"] = "auto"
    turn_id: str | None = Field(default=None, max_length=80)


class TestSpeechRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    turn_id: str | None = Field(default=None, max_length=80)


class ClientTelemetryRequest(BaseModel):
    turn_id: str = Field(min_length=1, max_length=80)
    route: str = Field(min_length=1, max_length=80)
    capture_ms: float | None = Field(default=None, ge=0)
    stt_wall_ms: float | None = Field(default=None, ge=0)
    llm_wall_ms: float | None = Field(default=None, ge=0)
    tts_wall_ms: float | None = Field(default=None, ge=0)
    total_ms: float = Field(ge=0)
    audio_bytes: int | None = Field(default=None, ge=0)
    audio_duration_ms: float | None = Field(default=None, ge=0)
    status: Literal["ok", "error"] = "ok"


class PersonalityRequest(BaseModel):
    values: dict[str, int]


class SpeechHintsRequest(BaseModel):
    hints: str = Field(max_length=1000)


class SpeechCorrectionRequest(BaseModel):
    turn_id: str = Field(min_length=1, max_length=80)
    observed: str = Field(min_length=1, max_length=4000)
    corrected: str = Field(min_length=1, max_length=4000)
    audio_verified: bool = False


class LocalLessonRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)
    response: str = Field(default="", max_length=4000)
    guidance: str = Field(min_length=1, max_length=4000)


class MemoryRequest(BaseModel):
    fact: str = Field(min_length=1, max_length=1000)
    cloud_allowed: bool = False


class ForgetMemoryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)


def require_token(x_james_token: str = Header(default="")) -> None:
    if x_james_token != settings.token:
        raise HTTPException(status_code=401, detail="Invalid Project James token")


def choose_expression(reply: str) -> str:
    lower = reply.lower()
    if any(word in lower for word in ("sorry", "cannot", "can't", "failed")):
        return "concerned"
    if "?" in reply:
        return "curious"
    if any(word in lower for word in ("great", "glad", "done", "ready")):
        return "happy"
    return "neutral"


def word_count(text: str) -> int:
    return len(text.split())


def current_inference_status() -> dict[str, object]:
    status = getattr(services, "inference_status", None)
    return status() if status else {"active": 0, "waiting": 0, "maximum_parallel": 1}


def south_africa_time_reply(text: str) -> str | None:
    if not TIME_QUERY.search(text):
        return None
    now = datetime.now(ZoneInfo("Africa/Johannesburg"))
    hour = now.strftime("%I").lstrip("0")
    return (
        f"It is {hour}:{now:%M} {now:%p} on {now:%A}, {now.day} {now:%B %Y} "
        "in South Africa, South African Standard Time."
    )


@dataclass
class Utterance:
    utterance_id: int
    next_sequence: int = 0
    frame_count: int = 0
    pcm: bytearray = field(default_factory=bytearray)


@dataclass
class ConnectionState:
    session_id: str = ""
    device_id: str = ""
    last_client_message_id: int = -1
    next_server_message_id: int = 1
    active: Utterance | None = None

    def response(self, message_type: str, **fields: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "v": PROTOCOL_VERSION,
            "type": message_type,
            "session_id": self.session_id,
            "message_id": self.next_server_message_id,
        }
        self.next_server_message_id += 1
        payload.update(fields)
        return payload


def websocket_authorized(websocket: WebSocket) -> bool:
    direct = websocket.headers.get("x-james-token", "")
    authorization = websocket.headers.get("authorization", "")
    bearer = authorization[7:].strip() if authorization.lower().startswith("bearer ") else ""
    return direct == settings.token or bearer == settings.token


def validate_control(state: ConnectionState, payload: Any) -> tuple[str, int]:
    if not isinstance(payload, dict):
        raise ProtocolError("control_shape", "Control message must be a JSON object")
    if payload.get("v") != PROTOCOL_VERSION:
        raise ProtocolError("control_version", "Only protocol version 1 is supported")
    message_type = payload.get("type")
    session_id = payload.get("session_id")
    message_id = payload.get("message_id")
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("control_type", "Control message type is required")
    if not isinstance(session_id, str) or not session_id:
        raise ProtocolError("control_session", "session_id is required")
    if not isinstance(message_id, int) or message_id < 0:
        raise ProtocolError("control_message_id", "message_id must be a non-negative integer")
    if message_id <= state.last_client_message_id:
        raise ProtocolError("stale_message", "message_id must increase monotonically")
    if state.session_id and session_id != state.session_id:
        raise ProtocolError("stale_session", "Message belongs to a stale session")
    state.last_client_message_id = message_id
    return message_type, message_id


async def send_error(
    websocket: WebSocket,
    state: ConnectionState,
    error: ProtocolError,
    *,
    related_message_id: int | None = None,
    utterance_id: int | None = None,
) -> None:
    telemetry.record(
        "websocket_error",
        session_id=state.session_id or None,
        utterance_id=utterance_id,
        code=error.code,
        retryable=error.retryable,
        status="error",
    )
    fields: dict[str, Any] = {
        "code": error.code,
        "detail": error.detail,
        "retryable": error.retryable,
    }
    if related_message_id is not None:
        fields["related_message_id"] = related_message_id
    if utterance_id is not None:
        fields["utterance_id"] = utterance_id
    await websocket.send_json(state.response("error", **fields))


@app.get("/health")
async def health(x_james_token: str = Header(default="")) -> dict[str, Any]:
    require_token(x_james_token)
    components = await services.health()
    ok = (
        components.get("whisper", False)
        and components.get("piper", False)
        and components.get("llm", components.get("ollama", False))
    )
    return {"ok": ok, "components": components, "version": __version__}


@app.get("/capabilities")
async def capabilities(x_james_token: str = Header(default="")) -> dict[str, Any]:
    require_token(x_james_token)
    components = await services.health()
    runtime = capability_snapshot(
        settings,
        components,
        persistent_memory.status(),
        current_inference_status(),
    )
    return {
        "protocol_versions": [PROTOCOL_VERSION],
        "transport": "websocket",
        "websocket_path": "/ws/v1",
        "audio": {
            "encoding": "pcm_s16le",
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "sample_bits": SAMPLE_BITS,
            "channels": CHANNELS,
            "frame_ms": 20,
            "preferred_frames_per_chunk": FRAMES_PER_CHUNK,
        },
        "features": ["stt.final", "assistant.text", "tts.binary", "ack", "ping"],
        "conversation": {
            "primary_provider": settings.llm_provider,
            "gemini_model": (
                settings.gemini_model
                if settings.llm_provider in {"auto", "gemini"}
                else None
            ),
            "ollama_fallback": settings.llm_fallback_to_ollama,
            "ollama_model": settings.ollama_model,
            "ollama_thinking": settings.ollama_think,
            "google_search_grounding": settings.gemini_google_search,
            "private_local_learning": local_learning.status(),
            "persistent_memory": persistent_memory.status(),
            "automatic_routing": "tools-first, local-routine, cloud-current-complex, same-turn-recovery",
        },
        "tools": [item["id"] for item in runtime["tools"] if item.get("available")],
        "runtime": runtime,
        "telemetry": {
            "enabled": settings.telemetry_enabled,
            "include_text": settings.telemetry_include_text,
            "summary_path": "/v1/telemetry/summary",
        },
    }


@app.get("/v1/telemetry/summary")
async def telemetry_summary(x_james_token: str = Header(default="")) -> dict[str, Any]:
    require_token(x_james_token)
    return telemetry.summary()


@app.get("/v1/system/status")
async def system_status(x_james_token: str = Header(default="")) -> dict[str, Any]:
    """Return the gateway's fixed, read-only operating metrics."""
    require_token(x_james_token)
    snapshot = pi_status.snapshot()
    return {"metrics": snapshot.as_dict(), "components": await services.health()}


@app.post("/v1/telemetry/client")
async def client_telemetry(
    request: ClientTelemetryRequest, x_james_token: str = Header(default="")
) -> dict[str, bool]:
    require_token(x_james_token)
    telemetry.record("client_turn", **request.model_dump())
    return {"recorded": settings.telemetry_enabled}


@app.get("/v1/settings/personality")
async def get_personality(x_james_token: str = Header(default="")) -> dict[str, Any]:
    require_token(x_james_token)
    return {"values": dict(personality_store.values), "applies": "immediately"}


@app.put("/v1/settings/personality")
async def set_personality(
    request: PersonalityRequest, x_james_token: str = Header(default="")
) -> dict[str, Any]:
    require_token(x_james_token)
    try:
        values = personality_store.update(request.values)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    services.personality = personality_prompt(values)
    telemetry.record("personality_update", changed_controls=sorted(request.values))
    return {"values": values, "applies": "immediately"}


@app.get("/v1/settings/speech")
async def get_speech_settings(x_james_token: str = Header(default="")) -> dict[str, object]:
    require_token(x_james_token)
    return speech_adaptation.status()


@app.put("/v1/settings/speech/hints")
async def set_speech_hints(
    request: SpeechHintsRequest, x_james_token: str = Header(default="")
) -> dict[str, object]:
    require_token(x_james_token)
    speech_adaptation.set_hints(request.hints)
    telemetry.record("speech_hints_update", hint_chars=len(request.hints))
    return speech_adaptation.status()


@app.post("/v1/settings/speech/corrections")
async def teach_speech_correction(
    request: SpeechCorrectionRequest, x_james_token: str = Header(default="")
) -> dict[str, object]:
    require_token(x_james_token)
    if not request.audio_verified:
        raise HTTPException(
            status_code=422,
            detail="Speech corrections require confirmation against the recorded turn audio",
        )
    try:
        speech_adaptation.teach(request.observed, request.corrected)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    telemetry.record(
        "speech_correction",
        turn_id=request.turn_id,
        audio_verified=True,
        observed_chars=len(request.observed),
        corrected_chars=len(request.corrected),
    )
    return speech_adaptation.status()


@app.get("/v1/settings/local-learning")
async def get_local_learning(x_james_token: str = Header(default="")) -> dict[str, object]:
    require_token(x_james_token)
    return local_learning.status()


@app.get("/v1/memory")
async def get_memory(x_james_token: str = Header(default="")) -> dict[str, object]:
    require_token(x_james_token)
    return {"status": persistent_memory.status(), "entries": persistent_memory.active()}


@app.post("/v1/memory")
async def remember_memory(
    request: MemoryRequest, x_james_token: str = Header(default="")
) -> dict[str, object]:
    require_token(x_james_token)
    try:
        entry = persistent_memory.remember(
            request.fact, cloud_allowed=request.cloud_allowed
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    telemetry.record("memory_remember", fact_chars=len(request.fact), cloud_allowed=request.cloud_allowed)
    return {"entry": entry, "status": persistent_memory.status()}


@app.post("/v1/memory/forget")
async def forget_memory(
    request: ForgetMemoryRequest, x_james_token: str = Header(default="")
) -> dict[str, object]:
    require_token(x_james_token)
    try:
        forgotten = persistent_memory.forget(request.query)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    telemetry.record("memory_forget", query_chars=len(request.query), forgotten_count=len(forgotten))
    return {"forgotten": forgotten, "status": persistent_memory.status()}


@app.get("/v1/system/inference")
async def inference_status(x_james_token: str = Header(default="")) -> dict[str, object]:
    require_token(x_james_token)
    return current_inference_status()


@app.get("/v1/system/network")
async def network_health(x_james_token: str = Header(default="")) -> dict[str, object]:
    require_token(x_james_token)
    snapshot = await asyncio.to_thread(network_status.snapshot)
    return {"metrics": snapshot.as_dict(), "summary": snapshot.describe()}


@app.post("/v1/settings/local-learning/lessons")
async def teach_local_lesson(
    request: LocalLessonRequest, x_james_token: str = Header(default="")
) -> dict[str, object]:
    require_token(x_james_token)
    try:
        local_learning.add(request.prompt, request.response, request.guidance)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    telemetry.record(
        "local_lesson",
        prompt_chars=len(request.prompt),
        response_chars=len(request.response),
        guidance_chars=len(request.guidance),
    )
    return local_learning.status()


async def execute_tool_intent(intent: ToolIntent, device_id: str) -> tuple[str, str, str]:
    if intent.kind == "system.identity":
        return (
            "My name is James. I am your desktop AI assistant. I answer questions, "
            "use approved local and live-information tools, remember preferences you "
            "explicitly give me, and speak through the desktop companion.",
            "system:identity",
            "identity-registry",
        )
    if intent.kind == "system.status.readonly":
        reply = pi_status.snapshot().describe(await services.health())
        return reply, "system:pi-status", "system-status"
    if intent.kind == "time.system-clock":
        return south_africa_time_reply(intent.text) or "The system clock query was not understood.", "time:system-clock", "system-clock"
    if intent.kind == "weather.current":
        try:
            reply = (await weather.current(intent.argument if isinstance(intent.argument, str) else None)).describe()
        except httpx.HTTPError:
            reply = "The live weather service is temporarily unavailable."
        except WeatherUnavailable as error:
            reply = str(error)
        return reply, "weather:open-meteo", "open-meteo"
    if intent.kind == "system.network.readonly":
        snapshot = await asyncio.to_thread(network_status.snapshot)
        return snapshot.describe(), "system:network-status", "system-network"
    if intent.kind == "system.capabilities":
        snapshot = capability_snapshot(
            settings,
            await services.health(),
            persistent_memory.status(),
            current_inference_status(),
        )
        return describe_capabilities(snapshot, intent.text), "system:capabilities", "capability-registry"
    if intent.kind == "memory.remember":
        entry = persistent_memory.remember(str(intent.argument))
        return f"Remembered locally: {entry['fact']}.", "memory:remember", "persistent-memory"
    if intent.kind == "memory.list":
        entries = persistent_memory.active()
        if not entries:
            reply = "I have no explicit persistent memories yet."
        else:
            reply = "I remember: " + "; ".join(str(entry["fact"]) for entry in entries) + "."
        return reply, "memory:list", "persistent-memory"
    if intent.kind == "memory.forget":
        forgotten = persistent_memory.forget(str(intent.argument))
        reply = (
            f"Forgot {len(forgotten)} matching persistent memor{'y' if len(forgotten) == 1 else 'ies'}; the deletion is retained in the private audit file."
            if forgotten
            else "I found no active persistent memory matching that request."
        )
        return reply, "memory:forget", "persistent-memory"
    if intent.kind == "conversation.repeat-item":
        item = memory.repeat_item(device_id, int(intent.argument))
        reply = item or f"I cannot find point {intent.argument} in the current conversation ledger."
        return reply, "conversation:repeat-item", "conversation-ledger"
    raise RuntimeError(f"Unsupported deterministic intent {intent.kind}")


async def answer_request(request: TestChatRequest) -> dict[str, Any]:
    started = time.perf_counter()
    plan = plan_intents(request.text)
    answers: list[str] = []
    routes: list[str] = []
    providers: list[str] = []
    result = None
    for intent in plan.tools:
        answer, route, provider = await execute_tool_intent(intent, request.device_id)
        answers.append(answer)
        routes.append(route)
        providers.append(provider)
    if plan.residual:
        result = await services.converse_result(
            request.device_id,
            plan.residual,
            provider_override=request.provider,
            remember=False,
        )
        answers.append(result.text)
        routes.append(request.provider)
        providers.append(result.provider)
    reply = " ".join(answer.strip() for answer in answers if answer.strip())
    if not reply:
        reply = "I could not identify a usable request in that turn."
    memory.append(request.device_id, request.text.strip(), reply)
    if len(routes) == 1:
        route = routes[0]
        provider = providers[0]
    else:
        route = "multi:" + "+".join(routes)
        provider = "multi:" + "+".join(dict.fromkeys(providers))
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    payload = {
        "text": reply,
        "expression": choose_expression(reply),
        "route": route,
        "route_components": routes,
        "provider": provider,
        "fallback_used": bool(result and result.fallback_used),
        "google_search_used": bool(result and result.google_search_used),
        "grounding_source": result.grounding_source if result else None,
        "routing_reason": (
            "multi-intent-composition" if len(routes) > 1 else (result.routing_reason if result else "deterministic-tool")
        ),
        "finish_reason": result.finish_reason if result else "tool-result",
        "answer_complete": result.answer_complete if result else True,
        "server_ms": elapsed_ms,
    }
    telemetry.record(
        "chat",
        turn_id=request.turn_id,
        route=route,
        route_components=routes,
        provider=provider,
        fallback_used=payload["fallback_used"],
        google_search_used=payload["google_search_used"],
        grounding_source=payload["grounding_source"],
        routing_reason=payload["routing_reason"],
        finish_reason=payload["finish_reason"],
        answer_complete=payload["answer_complete"],
        inference_queue=current_inference_status(),
        server_ms=elapsed_ms,
        prompt_chars=len(request.text),
        prompt_words=word_count(request.text),
        response_chars=len(reply),
        response_words=word_count(reply),
        transcript=request.text,
        response_text=reply,
        status="ok",
    )
    return payload


@app.post("/v1/test/chat")
async def test_chat(
    request: TestChatRequest, x_james_token: str = Header(default="")
) -> dict[str, Any]:
    """Authenticated typed-input harness for integration and voice testing."""
    require_token(x_james_token)
    return await answer_request(request)


@app.post("/v1/test/stt")
async def test_stt(
    request: Request,
    x_james_token: str = Header(default=""),
    x_james_turn_id: str = Header(default=""),
) -> dict[str, Any]:
    """Transcribe raw 16 kHz mono PCM captured by the Windows test harness."""
    require_token(x_james_token)
    pcm = await request.body()
    if not pcm or len(pcm) % (SAMPLE_BITS // 8):
        raise HTTPException(status_code=400, detail="Audio must be non-empty PCM S16LE")
    if len(pcm) > settings.max_utterance_bytes:
        raise HTTPException(status_code=413, detail="Test utterance exceeds the configured limit")
    started = time.perf_counter()
    raw_transcript = await services.transcribe(pcm, speech_adaptation.prompt())
    transcript = speech_adaptation.apply(raw_transcript)
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    telemetry.record(
        "stt",
        turn_id=x_james_turn_id or None,
        server_ms=elapsed_ms,
        audio_bytes=len(pcm),
        audio_duration_ms=round(len(pcm) / (SAMPLE_RATE_HZ * 2) * 1000),
        transcript_chars=len(transcript),
        transcript_words=word_count(transcript),
        transcript=transcript,
        status="ok",
    )
    return {
        "transcript": transcript,
        "raw_transcript": raw_transcript,
        "adapted": transcript != raw_transcript,
        "server_ms": elapsed_ms,
    }


@app.post("/v1/test/speech")
async def test_speech(
    request: TestSpeechRequest, x_james_token: str = Header(default="")
) -> Response:
    """Synthesize a test response using the same TTS route as the P4."""
    require_token(x_james_token)
    started = time.perf_counter()
    pcm = await services.synthesize(request.text.strip())
    elapsed_ms = round((time.perf_counter() - started) * 1000)
    telemetry.record(
        "tts",
        turn_id=request.turn_id,
        server_ms=elapsed_ms,
        response_chars=len(request.text),
        response_words=word_count(request.text),
        audio_bytes=len(pcm),
        audio_duration_ms=round(len(pcm) / (SAMPLE_RATE_HZ * 2) * 1000),
        response_text=request.text,
        status="ok",
    )
    return Response(
        content=pcm_to_wav(pcm),
        media_type="audio/wav",
        headers={"X-James-Server-Ms": str(elapsed_ms)},
    )


async def finish_utterance(websocket: WebSocket, state: ConnectionState, payload: dict) -> None:
    utterance = state.active
    if utterance is None:
        raise ProtocolError("no_active_utterance", "audio.end received without audio.start")
    if payload.get("utterance_id") != utterance.utterance_id:
        raise ProtocolError("utterance_mismatch", "audio.end utterance_id does not match")
    if int(payload.get("dropped_frames", 0)) != 0:
        state.active = None
        raise ProtocolError("capture_incomplete", "Dropped capture frames make this utterance unusable")
    declared_last = payload.get("last_sequence")
    if declared_last is not None and declared_last != utterance.next_sequence - 1:
        raise ProtocolError("sequence_summary", "audio.end last_sequence does not match received data")

    started = time.perf_counter()
    raw_transcript = await services.transcribe(
        bytes(utterance.pcm), speech_adaptation.prompt()
    )
    transcript = speech_adaptation.apply(raw_transcript)
    transcribed = time.perf_counter()
    await websocket.send_json(
        state.response("stt.final", utterance_id=utterance.utterance_id, transcript=transcript)
    )
    conversation_outcome = None
    if transcript:
        conversation_outcome = await answer_request(
            TestChatRequest(
                text=transcript,
                device_id=state.device_id,
                provider="auto",
                turn_id=f"{state.session_id}:{utterance.utterance_id}",
            )
        )
        reply = conversation_outcome["text"]
    else:
        reply = "Sorry, I did not catch that. Please try again."
    replied = time.perf_counter()
    await websocket.send_json(
        state.response(
            "assistant.text",
            utterance_id=utterance.utterance_id,
            text=reply,
            expression=choose_expression(reply),
        )
    )
    tts_pcm = await services.synthesize(reply)
    synthesized = time.perf_counter()
    timings_ms = {
        "transcription_ms": round((transcribed - started) * 1000),
        "conversation_ms": round((replied - transcribed) * 1000),
        "synthesis_ms": round((synthesized - replied) * 1000),
        "gateway_total_ms": round((synthesized - started) * 1000),
    }
    telemetry.record(
        "websocket_turn",
        session_id=state.session_id,
        device_id=state.device_id,
        utterance_id=utterance.utterance_id,
        provider=conversation_outcome.get("provider") if conversation_outcome else None,
        fallback_used=conversation_outcome.get("fallback_used", False) if conversation_outcome else False,
        google_search_used=conversation_outcome.get("google_search_used", False) if conversation_outcome else False,
        grounding_source=conversation_outcome.get("grounding_source") if conversation_outcome else None,
        routing_reason=conversation_outcome.get("routing_reason") if conversation_outcome else None,
        finish_reason=conversation_outcome.get("finish_reason") if conversation_outcome else None,
        answer_complete=conversation_outcome.get("answer_complete", True) if conversation_outcome else True,
        input_audio_bytes=len(utterance.pcm),
        output_audio_bytes=len(tts_pcm),
        transcript_chars=len(transcript),
        transcript_words=word_count(transcript),
        response_chars=len(reply),
        response_words=word_count(reply),
        transcript=transcript,
        response_text=reply,
        status="ok",
        **timings_ms,
    )
    total_frames = len(tts_pcm) // BYTES_PER_FRAME
    await websocket.send_json(
        state.response(
            "tts.start",
            utterance_id=utterance.utterance_id,
            encoding="pcm_s16le",
            sample_rate_hz=SAMPLE_RATE_HZ,
            sample_bits=SAMPLE_BITS,
            channels=CHANNELS,
            frame_count=total_frames,
        )
    )
    last_sequence = -1
    for sequence, offset in enumerate(range(0, len(tts_pcm), PCM_BYTES_PER_CHUNK)):
        chunk = tts_pcm[offset : offset + PCM_BYTES_PER_CHUNK]
        await websocket.send_bytes(
            encode_audio_chunk(
                kind=KIND_TTS,
                utterance_id=utterance.utterance_id,
                sequence=sequence,
                timestamp_ms=(offset // BYTES_PER_FRAME) * 20,
                payload=chunk,
            )
        )
        last_sequence = sequence
    await websocket.send_json(
        state.response(
            "tts.end",
            utterance_id=utterance.utterance_id,
            last_sequence=last_sequence,
            frame_count=total_frames,
            timings_ms=timings_ms,
        )
    )
    state.active = None


@app.websocket("/ws/v1")
async def websocket_v1(websocket: WebSocket) -> None:
    if not websocket_authorized(websocket):
        await websocket.close(code=4401, reason="Invalid Project James token")
        return
    await websocket.accept()
    state = ConnectionState()
    try:
        while True:
            incoming = await websocket.receive()
            if incoming.get("type") == "websocket.disconnect":
                break
            if incoming.get("bytes") is not None:
                try:
                    if not state.session_id or state.active is None:
                        raise ProtocolError("binary_state", "Audio arrived without an active session and utterance")
                    chunk = decode_audio_chunk(incoming["bytes"], expected_kind=KIND_MICROPHONE)
                    if chunk.utterance_id != state.active.utterance_id:
                        raise ProtocolError("utterance_mismatch", "Binary chunk belongs to another utterance")
                    if chunk.sequence != state.active.next_sequence:
                        state.active = None
                        raise ProtocolError("sequence_gap", "Audio sequence is missing, duplicated, or reordered")
                    if len(state.active.pcm) + len(chunk.payload) > settings.max_utterance_bytes:
                        state.active = None
                        raise ProtocolError("utterance_too_large", "Utterance exceeds the configured limit")
                    state.active.pcm.extend(chunk.payload)
                    state.active.frame_count += chunk.frame_count
                    state.active.next_sequence += 1
                    await websocket.send_json(
                        state.response(
                            "ack",
                            utterance_id=chunk.utterance_id,
                            highest_contiguous_sequence=chunk.sequence,
                        )
                    )
                except ProtocolError as error:
                    await send_error(websocket, state, error)
                continue

            text = incoming.get("text")
            if text is None:
                continue
            related_message_id: int | None = None
            try:
                payload = json.loads(text)
                message_type, related_message_id = validate_control(state, payload)
                if message_type == "hello":
                    if state.session_id:
                        raise ProtocolError("duplicate_hello", "hello is only valid once per connection")
                    state.session_id = payload["session_id"]
                    state.device_id = str(payload.get("device_id", "p4")).strip() or "p4"
                    await websocket.send_json(
                        state.response(
                            "hello.ack",
                            selected_audio={
                                "encoding": "pcm_s16le",
                                "sample_rate_hz": SAMPLE_RATE_HZ,
                                "sample_bits": SAMPLE_BITS,
                                "channels": CHANNELS,
                                "frame_ms": 20,
                                "preferred_frames_per_chunk": FRAMES_PER_CHUNK,
                            },
                            capabilities=["stt.final", "assistant.text", "tts.binary", "ack", "ping"],
                            gateway_version=__version__,
                        )
                    )
                elif not state.session_id:
                    raise ProtocolError("hello_required", "hello must be the first control message")
                elif message_type == "ping":
                    await websocket.send_json(
                        state.response("pong", related_message_id=related_message_id)
                    )
                elif message_type == "audio.start":
                    if state.active is not None:
                        raise ProtocolError("utterance_active", "Only one utterance may be active")
                    if (
                        payload.get("sample_rate_hz") != SAMPLE_RATE_HZ
                        or payload.get("sample_bits") != SAMPLE_BITS
                        or payload.get("channels") != CHANNELS
                    ):
                        raise ProtocolError("audio_format", "Version 1 requires 16 kHz mono PCM S16LE")
                    utterance_id = payload.get("utterance_id")
                    if not isinstance(utterance_id, int) or utterance_id < 0:
                        raise ProtocolError("utterance_id", "utterance_id must be non-negative")
                    state.active = Utterance(utterance_id)
                elif message_type == "audio.end":
                    await finish_utterance(websocket, state, payload)
                elif message_type == "audio.cancel":
                    state.active = None
                else:
                    raise ProtocolError("control_unsupported", f"Unsupported control type {message_type}")
            except json.JSONDecodeError:
                await send_error(
                    websocket,
                    state,
                    ProtocolError("control_json", "Control message is not valid JSON"),
                )
            except ProtocolError as error:
                await send_error(
                    websocket,
                    state,
                    error,
                    related_message_id=related_message_id,
                    utterance_id=state.active.utterance_id if state.active else None,
                )
            except Exception:
                state.active = None
                await send_error(
                    websocket,
                    state,
                    ProtocolError("gateway_failure", "The Pi service could not complete this turn", retryable=True),
                    related_message_id=related_message_id,
                )
    except WebSocketDisconnect:
        return
