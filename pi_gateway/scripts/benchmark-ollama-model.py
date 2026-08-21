#!/usr/bin/env python3
"""Run a compact spoken-assistant benchmark against a local Ollama model."""

from __future__ import annotations

import json
import sys
import time
import urllib.request


model = sys.argv[1] if len(sys.argv) > 1 else "qwen3:4b-instruct"
prompts = [
    "Answer in one sentence: what is 17 multiplied by 23?",
    "A user asks for the current weather and you have a weather tool. What should you do? Answer in one sentence.",
    "A user asks for the exact current time and you have a system-clock tool. What should you do? Answer in one sentence.",
    "Explain in one short sentence why the daytime sky usually looks blue.",
]

for index, prompt in enumerate(prompts, start=1):
    payload = json.dumps(
        {
            "model": model,
            "stream": False,
            "think": False,
            "keep_alive": "5m",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are TARS, a concise truthful desktop assistant. "
                        "Use an available tool for live measurements instead of guessing."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0.2, "num_ctx": 2048, "num_predict": 80},
        }
    ).encode()
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.load(response)
    wall_seconds = time.perf_counter() - started
    eval_count = int(result.get("eval_count", 0))
    eval_seconds = int(result.get("eval_duration", 0)) / 1_000_000_000
    print(
        json.dumps(
            {
                "case": index,
                "wall_seconds": round(wall_seconds, 2),
                "load_seconds": round(int(result.get("load_duration", 0)) / 1_000_000_000, 2),
                "tokens_per_second": round(eval_count / eval_seconds, 2) if eval_seconds else 0,
                "response": result.get("message", {}).get("content", "").strip(),
            }
        )
    )
