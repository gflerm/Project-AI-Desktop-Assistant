#!/usr/bin/env python3
"""Run a real authenticated TARS chat/TTS turn and save the WAV response."""

from __future__ import annotations

import json
from io import BytesIO
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import wave


token = os.environ.get("TARS_TOKEN", "").strip()
if len(token) < 24:
    raise SystemExit("TARS_TOKEN is not configured")
output = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tars-response-test.wav")
provider = sys.argv[2] if len(sys.argv) > 2 else "auto"
if provider not in {"auto", "gemini", "ollama"}:
    raise SystemExit("Provider must be auto, gemini, or ollama")
scenario = sys.argv[3] if len(sys.argv) > 3 else "intro"
prompts = {
    "intro": "Introduce yourself in two short sentences and confirm that the voice gateway is ready.",
    "weather": "What is the weather in Cape Town right now?",
    "current": "Who is the current president of South Africa? Answer in one sentence.",
    "status": "TARS, report the Pi temperature, memory, disk, load, uptime, and service health.",
    "local": "What is 17 multiplied by 23? Answer in one short sentence.",
}
if scenario not in prompts:
    raise SystemExit("Scenario must be intro, weather, current, status, or local")
prompt = prompts[scenario]


def post(path: str, payload: dict) -> tuple[bytes, str]:
    request = urllib.request.Request(
        f"http://127.0.0.1:8090{path}",
        data=json.dumps(payload).encode(),
        headers={"X-Tars-Token": token, "Content-Type": "application/json"},
    )
    for attempt in range(20):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read(), response.headers.get_content_type()
        except urllib.error.URLError:
            if attempt == 19:
                raise
            time.sleep(0.25)
    raise RuntimeError("unreachable")


def post_pcm(pcm: bytes) -> dict:
    request = urllib.request.Request(
        "http://127.0.0.1:8090/v1/test/stt",
        data=pcm,
        headers={"X-Tars-Token": token, "Content-Type": "application/octet-stream"},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


chat, _ = post(
    "/v1/test/chat",
    {"text": prompt, "device_id": "deployment-test", "provider": provider},
)
chat_result = json.loads(chat)
reply = chat_result["text"]
audio, content_type = post("/v1/test/speech", {"text": reply})
if content_type != "audio/wav" or not audio.startswith(b"RIFF"):
    raise SystemExit("TARS TTS did not return WAV audio")
output.write_bytes(audio)
with wave.open(BytesIO(audio), "rb") as wav:
    pcm = wav.readframes(wav.getnframes())
loopback = post_pcm(pcm).get("transcript", "").strip()
print(
    f"TARS_REPLY\tprovider={provider}\troute={chat_result.get('route')}\t"
    f"routing_reason={chat_result.get('routing_reason')}\t"
    f"server_ms={chat_result.get('server_ms')}\t{reply}"
)
print(f"TARS_AUDIO\t{output}\tbytes={len(audio)}")
print(f"TARS_STT_LOOPBACK\t{loopback}")
