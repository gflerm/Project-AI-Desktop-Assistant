from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
import asyncio
import logging
import re
import subprocess
import threading
import time
import wave

import httpx

from .protocol import CHANNELS, SAMPLE_BITS, SAMPLE_RATE_HZ, pad_pcm_frames
from .search import WikipediaSearchClient
from .local_learning import LocalLearning
from .persistent_memory import PersistentMemory


logger = logging.getLogger(__name__)


LIVE_QUERY_PATTERN = re.compile(
    r"\b(current|currently|latest|today|tonight|yesterday|tomorrow|news|"
    r"forecast|price|stock|score|schedule|president|prime minister|ceo|"
    r"search|look up|online|on the web|next game|next match)\b",
    re.IGNORECASE,
)

CLOUD_REQUIRED_PATTERN = re.compile(
    r"\b(medical|medicine|diagnos(?:e|is)|symptom|legal|lawyer|contract|"
    r"financial advice|investment|tax|safety critical|research|investigate|"
    r"verify|fact[- ]?check|sources?|citations?|nuclear (?:accident|disaster|meltdown)|"
    r"nuclear.{0,80}meltdown|"
    r"reactor (?:accident|meltdown)|radioactive leakage|radiation safety|"
    r"use (?:the )?cloud|use gemini)\b",
    re.IGNORECASE,
)

LOCAL_FAILURE_PATTERN = re.compile(
    r"\b(i (?:do not|don't|cannot|can't) (?:know|access|provide|retrieve|check)|"
    r"i am unable|i'm unable|no (?:internet|network|access)|not possible|"
    r"cannot help|can't help|information is unavailable|data is unavailable)\b",
    re.IGNORECASE,
)
AMBIGUOUS_MELTDOWN_PATTERN = re.compile(
    r"\bnuclear\b.{0,100}\bmeltdown\b", re.IGNORECASE | re.DOTALL
)
NAMED_MELTDOWN_PATTERN = re.compile(
    r"\b(chernobyl|fukushima|three mile island|japan|ukraine|united states|pennsylvania)\b",
    re.IGNORECASE,
)


def needs_live_grounding(text: str) -> bool:
    return bool(LIVE_QUERY_PATTERN.search(text))


def automatic_provider(text: str) -> tuple[str, str]:
    """Choose the first provider using explicit, auditable gateway policy."""
    if needs_live_grounding(text):
        return "gemini", "current-or-live-information"
    if CLOUD_REQUIRED_PATTERN.search(text):
        return "gemini", "complex-or-high-stakes"
    if len(text.split()) > 60:
        return "gemini", "long-context-request"
    return "ollama", "routine-local-first"


def local_reply_needs_cloud(reply: str) -> bool:
    """Detect an unusable local reply; this cannot prove factual correctness."""
    normalized = reply.strip()
    return not normalized or bool(LOCAL_FAILURE_PATTERN.search(normalized[:500]))


def answer_is_complete(text: str) -> bool:
    """Conservative spoken-answer completion check used before TTS."""
    normalized = text.strip()
    if not normalized or normalized.count("```") % 2:
        return False
    normalized = normalized.rstrip('"\'”’)]}')
    return bool(normalized) and normalized[-1] in ".?!"


def clarify_ambiguous_request(text: str) -> str:
    if AMBIGUOUS_MELTDOWN_PATTERN.search(text) and not NAMED_MELTDOWN_PATTERN.search(text):
        return (
            text
            + "\n\nThe event is not identified, so state that the question is ambiguous and "
            "briefly cover Three Mile Island, Chernobyl, and Fukushima with each name, "
            "date, and primary cause. Finish all three entries."
        )
    return text


def pcm_to_wav(pcm: bytes) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(SAMPLE_BITS // 8)
        wav.setframerate(SAMPLE_RATE_HZ)
        wav.writeframes(pcm)
    return output.getvalue()


def wav_to_16k_mono_pcm(wav_data: bytes) -> bytes:
    try:
        with wave.open(BytesIO(wav_data), "rb") as wav:
            if (
                wav.getnchannels() == CHANNELS
                and wav.getsampwidth() == SAMPLE_BITS // 8
                and wav.getframerate() == SAMPLE_RATE_HZ
            ):
                return pad_pcm_frames(wav.readframes(wav.getnframes()))
    except (wave.Error, EOFError):
        pass

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", "-",
            "-f", "s16le", "-ar", str(SAMPLE_RATE_HZ), "-ac", str(CHANNELS), "-",
        ],
        input=wav_data,
        capture_output=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        raise RuntimeError("TTS output could not be converted to 16 kHz mono PCM")
    return pad_pcm_frames(result.stdout)


@dataclass
class ConversationSession:
    messages: list[dict[str, str]] = field(default_factory=list)
    last_activity: float = field(default_factory=time.monotonic)


@dataclass(frozen=True)
class ConversationResult:
    text: str
    provider: str
    fallback_used: bool = False
    google_search_used: bool = False
    grounding_source: str | None = None
    routing_reason: str | None = None
    finish_reason: str | None = None
    answer_complete: bool = True


class ConversationMemory:
    def __init__(self, max_turns: int, idle_seconds: float):
        self.max_turns = max_turns
        self.idle_seconds = idle_seconds
        self._sessions: dict[str, ConversationSession] = {}
        self._lock = threading.Lock()

    def history(self, device_id: str) -> list[dict[str, str]]:
        now = time.monotonic()
        with self._lock:
            session = self._sessions.setdefault(device_id, ConversationSession())
            if now - session.last_activity > self.idle_seconds:
                session.messages.clear()
            session.last_activity = now
            return [dict(message) for message in session.messages]

    def append(self, device_id: str, user: str, assistant: str) -> None:
        with self._lock:
            session = self._sessions.setdefault(device_id, ConversationSession())
            session.messages.extend(
                [{"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
            )
            session.messages[:] = session.messages[-self.max_turns * 2 :]
            session.last_activity = time.monotonic()

    def repeat_item(self, device_id: str, number: int) -> str | None:
        if number < 1:
            return None
        for message in reversed(self.history(device_id)):
            if message.get("role") != "assistant":
                continue
            text = message.get("content", "")
            items = re.findall(
                r"(?:^|\n)\s*(\d+)[.)]\s*(.*?)(?=(?:\n\s*\d+[.)]\s)|\Z)",
                text,
                flags=re.DOTALL,
            )
            for item_number, item in items:
                if int(item_number) == number:
                    return f"Point {number}: {item.strip()}"
        return None


class PiServices:
    def __init__(
        self,
        whisper_url: str,
        piper_url: str,
        ollama_url: str,
        ollama_model: str,
        ollama_think: bool,
        llm_provider: str,
        llm_fallback_to_ollama: bool,
        gemini_url: str,
        gemini_model: str,
        gemini_api_key: str,
        gemini_google_search: bool,
        tts_length_scale: float,
        tts_noise_scale: float,
        tts_noise_w_scale: float,
        personality: str,
        memory: ConversationMemory,
        local_learning: LocalLearning | None = None,
        persistent_memory: PersistentMemory | None = None,
    ):
        self.whisper_url = whisper_url
        self.piper_url = piper_url
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.ollama_think = ollama_think
        self.llm_provider = llm_provider
        self.llm_fallback_to_ollama = llm_fallback_to_ollama
        self.gemini_url = gemini_url
        self.gemini_model = gemini_model
        self.gemini_api_key = gemini_api_key
        self.gemini_google_search = gemini_google_search
        self.tts_length_scale = tts_length_scale
        self.tts_noise_scale = tts_noise_scale
        self.tts_noise_w_scale = tts_noise_w_scale
        self.personality = personality
        self.memory = memory
        self.local_learning = local_learning
        self.persistent_memory = persistent_memory
        self.client = httpx.AsyncClient(timeout=180)
        self.wikipedia = WikipediaSearchClient(self.client)
        self.gemini_search_blocked_until = 0.0
        self.ollama_gate = asyncio.Semaphore(1)
        self.ollama_active = 0
        self.ollama_waiting = 0
        self.ollama_queue_high_water = 0
        self.ollama_last_queue_wait_ms = 0
        self.ollama_request_count = 0

    def inference_status(self) -> dict[str, object]:
        return {
            "model": self.ollama_model,
            "active": self.ollama_active,
            "waiting": self.ollama_waiting,
            "queue_high_water": self.ollama_queue_high_water,
            "last_queue_wait_ms": self.ollama_last_queue_wait_ms,
            "request_count": self.ollama_request_count,
            "maximum_parallel": 1,
            "automatic_local_deadline_seconds": 8,
        }

    async def close(self) -> None:
        await self.client.aclose()

    async def transcribe(self, pcm: bytes, prompt: str = "") -> str:
        wav_data = pcm_to_wav(pcm)
        response = await self.client.post(
            f"{self.whisper_url}/inference",
            files={"file": ("james-utterance.wav", wav_data, "audio/wav")},
            data={
                "response_format": "json",
                "temperature": "0.0",
                **({"prompt": prompt} if prompt else {}),
            },
            timeout=120,
        )
        response.raise_for_status()
        text = str(response.json().get("text", "")).strip()
        return "" if text.startswith("[") and text.endswith("]") else text

    async def _converse_ollama(
        self,
        messages: list[dict[str, str]],
        grounding_context: str | None = None,
        num_predict: int = 160,
    ) -> str:
        local_messages = [dict(message) for message in messages]
        if grounding_context:
            local_messages[0]["content"] += (
                "\n\nGROUNDED FALLBACK MODE: A freshly retrieved Wikipedia result follows. "
                "Answer the user's exact question concisely using only supported facts. "
                "Do not claim general web access. Mention Wikipedia only if source attribution "
                "is useful.\n\n" + grounding_context
            )
        else:
            local_messages[0]["content"] += (
                "\n\nLOCAL MODE: You have no live web, weather, news, price, schedule, "
                "location, telemetry, diagnostic, or device-control tools. Be explicit when "
                "a question requires current external information."
            )
        if self.local_learning:
            last_user = next(
                (
                    message["content"]
                    for message in reversed(local_messages)
                    if message.get("role") == "user"
                ),
                "",
            )
            lesson_context = self.local_learning.relevant_context(last_user)
            if lesson_context:
                local_messages[0]["content"] += "\n\n" + lesson_context
        if self.persistent_memory:
            last_user = next(
                (
                    message["content"]
                    for message in reversed(local_messages)
                    if message.get("role") == "user"
                ),
                "",
            )
            memory_context = self.persistent_memory.relevant_context(last_user)
            if memory_context:
                local_messages[0]["content"] += "\n\n" + memory_context
        queued_at = time.perf_counter()
        self.ollama_waiting += 1
        self.ollama_queue_high_water = max(self.ollama_queue_high_water, self.ollama_waiting)
        try:
            await self.ollama_gate.acquire()
        finally:
            self.ollama_waiting -= 1
        self.ollama_last_queue_wait_ms = round((time.perf_counter() - queued_at) * 1000)
        self.ollama_request_count += 1
        self.ollama_active += 1
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "stream": False,
                    "think": self.ollama_think,
                    "keep_alive": -1,
                    "messages": local_messages,
                    "options": {
                        "temperature": 0.4,
                        "num_ctx": 2048,
                        "num_predict": num_predict,
                    },
                },
                timeout=180,
            )
            response.raise_for_status()
            reply = str(response.json().get("message", {}).get("content", "")).strip()
        finally:
            self.ollama_active -= 1
            self.ollama_gate.release()
        if not reply:
            raise RuntimeError("Ollama returned an empty reply")
        return reply

    async def warm_ollama(self) -> None:
        """Load and pin the local fallback model before the first spoken turn."""
        queued_at = time.perf_counter()
        self.ollama_waiting += 1
        self.ollama_queue_high_water = max(self.ollama_queue_high_water, self.ollama_waiting)
        try:
            await self.ollama_gate.acquire()
        finally:
            self.ollama_waiting -= 1
        self.ollama_last_queue_wait_ms = round((time.perf_counter() - queued_at) * 1000)
        self.ollama_active += 1
        try:
            response = await self.client.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": "", "keep_alive": -1},
                timeout=180,
            )
            response.raise_for_status()
        finally:
            self.ollama_active -= 1
            self.ollama_gate.release()

    async def _converse_gemini(
        self, messages: list[dict[str, str]], use_google_search: bool
    ) -> tuple[str, bool, str | None, bool]:
        if not self.gemini_api_key:
            raise RuntimeError("Gemini is selected but GEMINI_API_KEY is not configured")
        contents = [
            {
                "role": "model" if message["role"] == "assistant" else "user",
                "parts": [{"text": message["content"]}],
            }
            for message in messages
            if message["role"] != "system"
        ]
        request_json = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": self.personality
                        + "\n\nCLOUD MODE: Google Search grounding is available for live or current public information. Use it when freshness matters."
                    }
                ]
            },
            "contents": contents,
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 320},
            **({"tools": [{"google_search": {}}]} if use_google_search else {}),
        }
        response = await self.client.post(
            f"{self.gemini_url}/models/{self.gemini_model}:generateContent",
            headers={"x-goog-api-key": self.gemini_api_key},
            json=request_json,
            timeout=8 if use_google_search else 30,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        reply = " ".join(
            str(part.get("text", "")).strip()
            for part in parts
            if part.get("text") and not part.get("thought", False)
        ).strip()
        if not reply:
            raise RuntimeError("Gemini returned an empty reply")
        grounded = bool(candidates and candidates[0].get("groundingMetadata"))
        finish_reason = str(candidates[0].get("finishReason", "")) or None
        complete = answer_is_complete(reply) and finish_reason not in {"MAX_TOKENS", "LENGTH"}
        if not complete:
            continuation_contents = contents + [
                {"role": "model", "parts": [{"text": reply}]},
                {
                    "role": "user",
                    "parts": [{"text": "Continue exactly where the answer stopped. Finish the missing requested parts concisely, without repeating earlier text."}],
                },
            ]
            continuation = await self.client.post(
                f"{self.gemini_url}/models/{self.gemini_model}:generateContent",
                headers={"x-goog-api-key": self.gemini_api_key},
                json={
                    "systemInstruction": request_json["systemInstruction"],
                    "contents": continuation_contents,
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 192},
                },
                timeout=12,
            )
            continuation.raise_for_status()
            extra_candidates = continuation.json().get("candidates", [])
            extra_parts = extra_candidates[0].get("content", {}).get("parts", []) if extra_candidates else []
            extra = " ".join(
                str(part.get("text", "")).strip()
                for part in extra_parts
                if part.get("text") and not part.get("thought", False)
            ).strip()
            if extra:
                reply = f"{reply.rstrip()} {extra}"
            extra_reason = str(extra_candidates[0].get("finishReason", "")) if extra_candidates else ""
            finish_reason = f"continued:{extra_reason or 'unknown'}"
            complete = answer_is_complete(reply) and extra_reason not in {"MAX_TOKENS", "LENGTH"}
        return reply, grounded, finish_reason, complete

    async def _ollama_fallback_result(
        self,
        messages: list[dict[str, str]],
        transcript: str,
        wants_live_grounding: bool,
        routing_reason: str | None = None,
    ) -> ConversationResult:
        search_result = None
        if wants_live_grounding:
            try:
                search_result = await self.wikipedia.search(transcript)
            except (httpx.HTTPError, ValueError) as search_error:
                logger.warning("Wikipedia fallback failed: %s", search_error)
        if search_result:
            reply = search_result.spoken_summary()
            return ConversationResult(
                reply,
                "wikipedia",
                fallback_used=True,
                grounding_source="wikipedia",
                routing_reason=routing_reason or "cloud-failed-wikipedia",
                finish_reason="tool-result",
                answer_complete=answer_is_complete(reply),
            )
        reply = await self._converse_ollama(messages)
        return ConversationResult(
            reply,
            "ollama",
            fallback_used=True,
            routing_reason=routing_reason or "cloud-failed-local-fallback",
            finish_reason="ollama-done",
            answer_complete=answer_is_complete(reply),
        )

    async def converse_result(
        self, device_id: str, transcript: str, provider_override: str | None = None,
        *, remember: bool = True,
    ) -> ConversationResult:
        model_transcript = clarify_ambiguous_request(transcript)
        messages = [{"role": "system", "content": self.personality}]
        messages.extend(self.memory.history(device_id))
        messages.append({"role": "user", "content": model_transcript})
        provider = provider_override or self.llm_provider
        automatic = provider == "auto"
        routing_reason = "explicit-provider"
        if provider not in {"auto", "gemini", "ollama"}:
            raise RuntimeError("Unsupported conversation provider")
        if automatic:
            provider, routing_reason = automatic_provider(transcript)
            if provider == "gemini" and not self.gemini_api_key:
                provider = "ollama"
                routing_reason = "cloud-unavailable-local-fallback"
        if provider == "gemini":
            wants_live_grounding = self.gemini_google_search and needs_live_grounding(transcript)
            if wants_live_grounding and time.monotonic() < self.gemini_search_blocked_until:
                result = await self._ollama_fallback_result(
                    messages,
                    transcript,
                    wants_live_grounding=True,
                    routing_reason="cloud-circuit-breaker-wikipedia",
                )
            else:
                try:
                    async with asyncio.timeout(8 if wants_live_grounding else 30):
                        reply, grounded, finish_reason, complete = await self._converse_gemini(
                            messages,
                            wants_live_grounding,
                        )
                except (httpx.HTTPError, RuntimeError, TimeoutError) as error:
                    if not self.llm_fallback_to_ollama:
                        raise
                    if wants_live_grounding and (
                        isinstance(error, (httpx.TimeoutException, TimeoutError))
                        or (
                            isinstance(error, httpx.HTTPStatusError)
                            and error.response.status_code == 429
                        )
                    ):
                        self.gemini_search_blocked_until = time.monotonic() + 300
                    logger.warning("Gemini failed; using Ollama fallback: %s", error)
                    result = await self._ollama_fallback_result(
                        messages,
                        transcript,
                        wants_live_grounding,
                        routing_reason=(
                            "cloud-failed-wikipedia"
                            if wants_live_grounding
                            else "cloud-failed-local-fallback"
                        ),
                    )
                else:
                    result = ConversationResult(
                        reply,
                        "gemini",
                        google_search_used=grounded,
                        grounding_source="google-search" if grounded else None,
                        routing_reason=routing_reason,
                        finish_reason=finish_reason,
                        answer_complete=complete,
                    )
        else:
            try:
                if automatic and self.gemini_api_key:
                    async with asyncio.timeout(8):
                        reply = await self._converse_ollama(messages)
                else:
                    reply = await self._converse_ollama(messages)
            except (httpx.HTTPError, RuntimeError, TimeoutError) as error:
                if not (automatic and self.gemini_api_key):
                    raise
                logger.warning("Local-first route failed; escalating to Gemini: %s", error)
                reply, grounded, finish_reason, complete = await self._converse_gemini(messages, False)
                result = ConversationResult(
                    reply,
                    "gemini",
                    fallback_used=True,
                    google_search_used=grounded,
                    routing_reason="local-error-or-timeout",
                    finish_reason=finish_reason,
                    answer_complete=complete,
                )
            else:
                if automatic and self.gemini_api_key and (
                    local_reply_needs_cloud(reply) or not answer_is_complete(reply)
                ):
                    local_reply = reply
                    try:
                        reply, grounded, finish_reason, complete = await self._converse_gemini(messages, False)
                    except (httpx.HTTPError, RuntimeError, TimeoutError):
                        reply = local_reply
                        result = ConversationResult(
                            reply,
                            "ollama",
                            routing_reason="cloud-recovery-failed",
                            finish_reason="ollama-done",
                            answer_complete=answer_is_complete(reply),
                        )
                    else:
                        result = ConversationResult(
                            reply,
                            "gemini",
                            fallback_used=True,
                            google_search_used=grounded,
                            routing_reason="local-refusal-recovery",
                            finish_reason=finish_reason,
                            answer_complete=complete,
                        )
                else:
                    result = ConversationResult(
                        reply,
                        "ollama",
                        routing_reason=routing_reason,
                        finish_reason="ollama-done",
                        answer_complete=answer_is_complete(reply),
                    )
        reply = result.text
        if remember:
            self.memory.append(device_id, transcript, reply)
        return result

    async def converse(
        self, device_id: str, transcript: str, provider_override: str | None = None
    ) -> str:
        return (await self.converse_result(device_id, transcript, provider_override)).text

    async def synthesize(self, text: str) -> bytes:
        response = await self.client.post(
            f"{self.piper_url}/synthesize",
            json={
                "text": text,
                "length_scale": self.tts_length_scale,
                "noise_scale": self.tts_noise_scale,
                "noise_w_scale": self.tts_noise_w_scale,
            },
            timeout=120,
        )
        response.raise_for_status()
        return wav_to_16k_mono_pcm(response.content)

    async def health(self) -> dict[str, bool]:
        checks = {
            "whisper": f"{self.whisper_url}/",
            "piper": f"{self.piper_url}/info",
            "ollama": f"{self.ollama_url}/api/tags",
        }
        results: dict[str, bool] = {}
        for name, url in checks.items():
            try:
                response = await self.client.get(url, timeout=3)
                results[name] = response.status_code < 500
            except httpx.HTTPError:
                results[name] = False
        gemini_ok = False
        if self.gemini_api_key:
            try:
                response = await self.client.get(
                    f"{self.gemini_url}/models/{self.gemini_model}",
                    headers={"x-goog-api-key": self.gemini_api_key},
                    timeout=3,
                )
                gemini_ok = response.status_code < 400
            except httpx.HTTPError:
                pass
        results["gemini"] = gemini_ok
        primary_ok = (
            results["gemini"]
            if self.llm_provider in {"auto", "gemini"} and self.gemini_api_key
            else results["ollama"]
        )
        results["llm"] = primary_ok or (
            self.llm_fallback_to_ollama and results["ollama"]
        )
        return results
