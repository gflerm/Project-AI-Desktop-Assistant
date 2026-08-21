#!/usr/bin/env python3
"""Verify live personality controls and persistent STT adaptation without exposing secrets."""

from __future__ import annotations

import json
import os
import urllib.request


token = os.environ.get("JAMES_TOKEN", "")
if len(token) < 24:
    raise SystemExit("JAMES_TOKEN is not configured")
base_url = "http://127.0.0.1:8090"


def request(path: str, payload: dict | None = None, method: str | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"X-James-Token": token}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


personality = request("/v1/settings/personality")
updated = request(
    "/v1/settings/personality",
    {"values": personality["values"]},
    method="PUT",
)
speech = request(
    "/v1/settings/speech/corrections",
    {
        "turn_id": "verified-loopback-dateway-gateway",
        "observed": "Dateway is ready",
        "corrected": "Gateway is ready",
        "audio_verified": True,
    },
    method="POST",
)
learning = request(
    "/v1/settings/local-learning/lessons",
    {
        "prompt": "When I ask your name, identify yourself correctly as James.",
        "response": "",
        "guidance": "Use the name James. Do not call yourself Dateway or imitate a film performance.",
    },
    method="POST",
)
local_reply = request(
    "/v1/test/chat",
    {
        "text": "What is your name?",
        "device_id": "verify-local-learning",
        "provider": "ollama",
    },
    method="POST",
)
print(
    json.dumps(
        {
            "personality_controls": len(updated["values"]),
            "humour": updated["values"]["humour"],
            "speech_phrase_corrections": speech["phrase_corrections"],
            "speech_word_corrections": speech["word_corrections"],
            "learned_words": speech["learned_words"],
            "local_lesson_count": learning["lesson_count"],
            "local_lessons_used_by": learning["used_by"],
            "local_reply_provider": local_reply.get("provider"),
            "local_reply": local_reply.get("text"),
        },
        indent=2,
    )
)
