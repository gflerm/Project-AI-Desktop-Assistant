#!/usr/bin/env python3
"""Run the Project James ten-question chat/TTS/STT acceptance set."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import statistics
import time
import urllib.request
import uuid
import wave


TOKEN = os.environ.get("JAMES_TOKEN", "").strip()
BASE = os.environ.get("JAMES_GATEWAY_URL", "http://127.0.0.1:8090").rstrip("/")
OUTPUT = Path(os.environ.get("JAMES_ACCEPTANCE_OUTPUT", "/tmp/james-voice-acceptance.json"))
if len(TOKEN) < 24:
    raise SystemExit("JAMES_TOKEN is not configured")


CASES = [
    {
        "id": "south-africa-time",
        "prompt": "What is the current time in South Africa?",
        "route_contains": ["time:system-clock"],
    },
    {
        "id": "weather-and-time",
        "prompt": "Give me the current Cape Town weather. What is the current time?",
        "route_contains": ["weather:open-meteo", "time:system-clock"],
    },
    {
        "id": "model-temperature-settings",
        "prompt": "How can we adjust your temperature settings?",
        "route_excludes": ["weather:open-meteo"],
    },
    {
        "id": "capabilities",
        "prompt": "What offline tools can you access?",
        "route_contains": ["system:capabilities"],
    },
    {
        "id": "memory-remember",
        "prompt": "Remember that I prefer temperatures in Celsius.",
        "route_contains": ["memory:remember"],
        "response_contains": ["Celsius"],
    },
    {
        "id": "memory-list",
        "prompt": "What do you remember?",
        "route_contains": ["memory:list"],
        "response_contains": ["Celsius"],
    },
    {
        "id": "memory-forget",
        "prompt": "Forget that I prefer temperatures in Celsius.",
        "route_contains": ["memory:forget"],
    },
    {
        "id": "ambiguous-meltdown",
        "prompt": "What caused the nuclear power station meltdown? Give the name and date.",
        "provider_contains": ["gemini"],
        "response_contains": [
            "Three Mile Island", "Chernobyl", "Fukushima", "1979", "1986", "2011"
        ],
    },
    {
        "id": "weather-python-script",
        "prompt": "Write a Python script to retrieve Cape Town weather.",
        "route_excludes": ["weather:open-meteo"],
        "response_contains_any": ["python", "requests", "urllib", "httpx", "open-meteo"],
    },
    {
        "id": "pi-and-network-status",
        "prompt": "Check the Pi status and check the network status.",
        "route_contains": ["system:pi-status", "system:network-status"],
    },
]


def post_json(path: str, payload: dict, timeout: int = 120) -> tuple[dict, float]:
    started = time.perf_counter()
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={"X-James-Token": TOKEN, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    return result, round((time.perf_counter() - started) * 1000, 1)


def post_audio(
    path: str,
    payload: bytes,
    content_type: str,
    timeout: int = 120,
    extra_headers: dict[str, str] | None = None,
) -> tuple[bytes, float]:
    started = time.perf_counter()
    headers = {"X-James-Token": TOKEN, "Content-Type": content_type}
    headers.update(extra_headers or {})
    request = urllib.request.Request(
        BASE + path,
        data=payload,
        headers=headers,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = response.read()
    return result, round((time.perf_counter() - started) * 1000, 1)


def transcribe_pcm(pcm: bytes, turn_id: str) -> tuple[str, float, int]:
    """Transcribe long TTS output in chunks below the live utterance limit."""
    chunk_bytes = 900_000
    transcripts = []
    wall_ms = 0.0
    chunks = 0
    for offset in range(0, len(pcm), chunk_bytes):
        payload = pcm[offset : offset + chunk_bytes]
        stt_data, chunk_wall_ms = post_audio(
            "/v1/test/stt",
            payload,
            "application/octet-stream",
            extra_headers={"X-James-Turn-Id": turn_id},
        )
        transcripts.append(str(json.loads(stt_data).get("transcript", "")).strip())
        wall_ms += chunk_wall_ms
        chunks += 1
    return " ".join(item for item in transcripts if item), round(wall_ms, 1), chunks


def failures(case: dict, chat: dict, loopback: str) -> list[str]:
    found = []
    route = str(chat.get("route", ""))
    provider = str(chat.get("provider", ""))
    response = str(chat.get("text", ""))
    for required in case.get("route_contains", []):
        if required not in route and required not in chat.get("route_components", []):
            found.append(f"missing route {required}")
    for forbidden in case.get("route_excludes", []):
        if forbidden in route or forbidden in chat.get("route_components", []):
            found.append(f"forbidden route {forbidden}")
    for required in case.get("provider_contains", []):
        if required.casefold() not in provider.casefold():
            found.append(f"missing provider {required}")
    for required in case.get("response_contains", []):
        if required.casefold() not in response.casefold():
            found.append(f"response missing {required}")
    alternatives = case.get("response_contains_any", [])
    if alternatives and not any(item.casefold() in response.casefold() for item in alternatives):
        found.append("response missed every expected content alternative")
    if chat.get("answer_complete") is False:
        found.append("answer marked incomplete")
    if not loopback.strip():
        found.append("TTS-to-STT loopback was empty")
    return found


records = []
for case in CASES:
    turn_id = str(uuid.uuid4())
    overall_started = time.perf_counter()
    chat, chat_wall_ms = post_json(
        "/v1/test/chat",
        {
            "text": case["prompt"],
            "device_id": "ten-question-acceptance",
            "provider": "auto",
            "turn_id": turn_id,
        },
    )
    wav_data, tts_wall_ms = post_audio(
        "/v1/test/speech",
        json.dumps({"text": chat["text"], "turn_id": turn_id}).encode(),
        "application/json",
    )
    with wave.open(BytesIO(wav_data), "rb") as source:
        pcm = source.readframes(source.getnframes())
        audio_duration_ms = round(source.getnframes() / source.getframerate() * 1000)
    loopback, stt_wall_ms, stt_chunks = transcribe_pcm(pcm, turn_id)
    total_ms = round((time.perf_counter() - overall_started) * 1000, 1)
    problems = failures(case, chat, loopback)
    records.append(
        {
            "id": case["id"],
            "turn_id": turn_id,
            "prompt": case["prompt"],
            "passed": not problems,
            "failures": problems,
            "response": chat.get("text"),
            "loopback_transcript": loopback,
            "route": chat.get("route"),
            "route_components": chat.get("route_components"),
            "provider": chat.get("provider"),
            "routing_reason": chat.get("routing_reason"),
            "finish_reason": chat.get("finish_reason"),
            "answer_complete": chat.get("answer_complete"),
            "timing_ms": {
                "chat_wall": chat_wall_ms,
                "chat_server": chat.get("server_ms"),
                "tts_wall": tts_wall_ms,
                "stt_loopback_wall": stt_wall_ms,
                "stt_loopback_chunks": stt_chunks,
                "response_audio_duration": audio_duration_ms,
                "chat_tts_stt_total": total_ms,
            },
        }
    )
    print(
        f"{case['id']}\t{'PASS' if not problems else 'FAIL'}\t"
        f"route={chat.get('route')}\tprovider={chat.get('provider')}\t"
        f"chat={chat_wall_ms:.0f}ms\ttotal={total_ms:.0f}ms"
    )

chat_times = [record["timing_ms"]["chat_wall"] for record in records]
totals = [record["timing_ms"]["chat_tts_stt_total"] for record in records]
report = {
    "schema": 1,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "scope": "Typed prompt, live chat, TTS, and synthesized STT loopback; no operator microphone capture.",
    "case_count": len(records),
    "passed_count": sum(record["passed"] for record in records),
    "failed_count": sum(not record["passed"] for record in records),
    "timing_ms": {
        "chat_average": round(statistics.mean(chat_times), 1),
        "chat_max": max(chat_times),
        "chat_tts_stt_total_average": round(statistics.mean(totals), 1),
        "chat_tts_stt_total_max": max(totals),
    },
    "cases": records,
}
OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(OUTPUT.resolve())
print(json.dumps({key: report[key] for key in ("case_count", "passed_count", "failed_count", "timing_ms")}, indent=2))
if report["failed_count"]:
    raise SystemExit(f"{report['failed_count']} acceptance cases failed")
