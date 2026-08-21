#!/usr/bin/env python3
"""Exercise live automatic TARS routing without adding STT/TTS loopback time."""

from __future__ import annotations

import json
import os
import urllib.request


token = os.environ.get("TARS_TOKEN", "").strip()
if len(token) < 24:
    raise SystemExit("TARS_TOKEN is not configured")

cases = {
    "tool": "TARS, show the Pi temperature and memory usage.",
    "local": "What is 17 multiplied by 23? Answer in one sentence.",
    "cloud": "Who is the current president of South Africa? Answer in one sentence.",
}

for name, prompt in cases.items():
    request = urllib.request.Request(
        "http://127.0.0.1:8090/v1/test/chat",
        data=json.dumps(
            {"text": prompt, "device_id": f"routing-test-{name}", "provider": "auto"}
        ).encode(),
        headers={"X-Tars-Token": token, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.load(response)
    print(
        json.dumps(
            {
                "case": name,
                "provider": result.get("provider"),
                "route": result.get("route"),
                "routing_reason": result.get("routing_reason"),
                "server_ms": result.get("server_ms"),
                "text": result.get("text"),
            }
        )
    )
