#!/usr/bin/env python3
"""Verify the live teaching, multi-intent, memory and capability upgrade."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


TOKEN = os.environ.get("JAMES_TOKEN", "").strip()
BASE = "http://127.0.0.1:8090"
if len(TOKEN) < 24:
    raise SystemExit("JAMES_TOKEN is not configured")


def request(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"X-James-Token": TOKEN}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)


def chat(text: str, device: str = "teaching-upgrade-verifier") -> dict:
    return request(
        "/v1/test/chat",
        {"text": text, "device_id": device, "provider": "auto"},
    )


results = {}
results["capabilities"] = chat("What offline tools can you access right now?")
assert results["capabilities"]["route"] == "system:capabilities"

results["multi"] = chat(
    "What is the current weather in Cape Town? What is the current time?"
)
assert results["multi"]["route"].startswith("multi:")
assert "weather:open-meteo" in results["multi"]["route_components"]
assert "time:system-clock" in results["multi"]["route_components"]

results["multi_model"] = chat(
    "What is the current weather in Cape Town? What is the current time? Do we have a nuclear power station in South Africa?"
)
assert results["multi_model"]["route"].startswith("multi:")
assert "auto" in results["multi_model"]["route_components"]
assert "nuclear" in results["multi_model"]["text"].casefold() or "koeberg" in results["multi_model"]["text"].casefold()

results["meltdown"] = chat(
    "What was the main cause of the nuclear power station that had a meltdown? When was it? And the name please?"
)
assert results["meltdown"]["answer_complete"] is True
for required in ("three mile island", "chernobyl", "fukushima", "1979", "1986", "2011"):
    assert required in results["meltdown"]["text"].casefold()

results["settings_not_weather"] = chat("How can we tweak your temperature settings?")
assert results["settings_not_weather"]["route"] == "auto"

marker = "teaching upgrade verification uses Celsius"
results["remember"] = chat(f"Remember that {marker}.")
assert results["remember"]["route"] == "memory:remember"
results["memory_list"] = chat("What do you remember?")
assert marker in results["memory_list"]["text"]
results["forget"] = chat(f"Forget {marker}.")
assert results["forget"]["route"] == "memory:forget"

results["network"] = request("/v1/system/network")
results["inference"] = request("/v1/system/inference")
assert results["inference"]["maximum_parallel"] == 1

try:
    request(
        "/v1/settings/speech/corrections",
        {
            "turn_id": "unverified-test",
            "observed": "wrong",
            "corrected": "right",
            "audio_verified": False,
        },
    )
except urllib.error.HTTPError as error:
    assert error.code == 422
else:
    raise AssertionError("An unverified speech correction was accepted")

print(
    json.dumps(
        {
            "verified": True,
            "capability_route": results["capabilities"]["route"],
            "multi_route": results["multi"]["route"],
            "multi_model_route": results["multi_model"]["route"],
            "meltdown_provider": results["meltdown"]["provider"],
            "meltdown_finish_reason": results["meltdown"]["finish_reason"],
            "meltdown_answer_complete": results["meltdown"]["answer_complete"],
            "settings_route": results["settings_not_weather"]["route"],
            "memory_routes": [
                results["remember"]["route"],
                results["memory_list"]["route"],
                results["forget"]["route"],
            ],
            "network": results["network"]["metrics"],
            "inference": results["inference"],
            "unverified_speech_correction_rejected": True,
        },
        indent=2,
    )
)
