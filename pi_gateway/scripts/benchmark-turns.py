#!/usr/bin/env python3
"""Run repeatable live gateway timing turns and print the persisted summary."""

from __future__ import annotations

from io import BytesIO
import json
import os
from pathlib import Path
import statistics
import sys
import time
import urllib.request
import uuid
import wave


token = os.environ.get("TARS_TOKEN", "").strip()
if len(token) < 24:
    raise SystemExit("TARS_TOKEN is not configured")
iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
base_url = "http://127.0.0.1:8090"
scenarios = (
    ("general", "auto", "In one concise sentence, report that the gateway is ready, with a touch of dry wit."),
    ("weather", "auto", "What is the weather in Cape Town right now?"),
    ("current", "auto", "Who is the current president of South Africa? Answer in one sentence."),
    ("local", "ollama", "In one concise sentence, report that the local gateway is ready."),
)


def request(path: str, payload: dict | bytes | None = None, headers: dict | None = None):
    request_headers = {"X-Tars-Token": token}
    request_headers.update(headers or {})
    if isinstance(payload, bytes):
        data = payload
        request_headers.setdefault("Content-Type", "application/octet-stream")
    elif payload is None:
        data = None
    else:
        data = json.dumps(payload).encode()
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url + path, data=data, headers=request_headers)
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=180) as response:
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        return response.read(), response_headers, (time.perf_counter() - started) * 1000


measurements: dict[str, list[dict]] = {name: [] for name, _, _ in scenarios}
last_audio = b""
for name, provider, prompt in scenarios:
    for iteration in range(iterations):
        turn_id = str(uuid.uuid4())
        total_started = time.perf_counter()
        chat_body, _, chat_wall = request(
            "/v1/test/chat",
            {
                "text": prompt,
                "device_id": f"benchmark-{name}-{iteration}",
                "provider": provider,
                "turn_id": turn_id,
            },
        )
        chat = json.loads(chat_body)
        audio, tts_headers, tts_wall = request(
            "/v1/test/speech", {"text": chat["text"], "turn_id": turn_id}
        )
        total_ms = (time.perf_counter() - total_started) * 1000
        duration_ms = max(0, (len(audio) - 44) / 32)
        request(
            "/v1/telemetry/client",
            {
                "turn_id": turn_id,
                "route": chat["route"],
                "llm_wall_ms": chat_wall,
                "tts_wall_ms": tts_wall,
                "total_ms": total_ms,
                "audio_bytes": len(audio),
                "audio_duration_ms": duration_ms,
                "status": "ok",
            },
        )
        measurements[name].append(
            {
                "chat_wall_ms": round(chat_wall),
                "chat_server_ms": chat.get("server_ms"),
                "tts_wall_ms": round(tts_wall),
                "tts_server_ms": int(tts_headers.get("x-tars-server-ms", "0")),
                "total_ms": round(total_ms),
                "audio_duration_ms": round(duration_ms),
                "provider": chat.get("provider", chat.get("route")),
                "fallback_used": chat.get("fallback_used", False),
                "google_search_used": chat.get("google_search_used", False),
                "grounding_source": chat.get("grounding_source"),
                "reply": chat["text"],
            }
        )
        if name == "general":
            last_audio = audio

if last_audio:
    Path("/tmp/tars-optimized-voice.wav").write_bytes(last_audio)
    with wave.open(BytesIO(last_audio), "rb") as wav:
        pcm = wav.readframes(wav.getnframes())
    stt_values = []
    for _ in range(iterations):
        turn_id = str(uuid.uuid4())
        body, _, wall_ms = request(
            "/v1/test/stt", pcm, {"X-Tars-Turn-Id": turn_id}
        )
        result = json.loads(body)
        stt_values.append(
            {"wall_ms": round(wall_ms), "server_ms": result.get("server_ms"), "transcript": result.get("transcript")}
        )
    measurements["stt_loopback"] = stt_values

compact = {}
for name, values in measurements.items():
    totals = [value.get("total_ms", value.get("wall_ms", 0)) for value in values]
    compact[name] = {
        "runs": len(values),
        "average_ms": round(statistics.mean(totals)) if totals else None,
        "min_ms": min(totals) if totals else None,
        "max_ms": max(totals) if totals else None,
        "measurements": values,
    }

summary = json.loads(request("/v1/telemetry/summary")[0])
print(json.dumps({"benchmark": compact, "telemetry_summary": summary}, indent=2))
