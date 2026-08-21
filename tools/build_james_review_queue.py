#!/usr/bin/env python3
"""Build a private, non-promoted review queue from all recorded James turns."""

from __future__ import annotations

import json
from pathlib import Path

from james_feedback import migrate_record


ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "captures" / "james-sessions"
OUTPUT = ROOT / "captures" / "james-review-queue.json"


def suggestions(record: dict) -> list[str]:
    prompt = str(record.get("prompt", "")).casefold()
    response = str(record.get("response_text", "")).casefold()
    found: list[str] = []
    if any(term in response for term in ("i cannot", "i can't", "don't have access")):
        found.append("review_false_refusal")
    if "?" in str(record.get("prompt", ""))[:-1]:
        found.append("review_multi_intent")
    if response and response[-1:] not in ".?!`\"'”’":
        found.append("review_incomplete_answer")
    if "weather" in response and any(term in prompt for term in ("script", "settings")):
        found.append("review_tool_misroute")
    if float(record.get("timing_ms", {}).get("total_ms") or 0) > 12000:
        found.append("review_latency")
    return found


def main() -> None:
    queue = []
    for path in sorted(SESSIONS.glob("*/turn.json")):
        try:
            record = migrate_record(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        queue.append(
            {
                "turn_id": record.get("turn_id"),
                "recorded_at_utc": record.get("recorded_at_utc"),
                "source": str(path.relative_to(ROOT)),
                "mode": record.get("mode"),
                "prompt": record.get("prompt"),
                "response_text": record.get("response_text"),
                "route": record.get("route"),
                "provider": record.get("provider"),
                "timing_ms": record.get("timing_ms", {}),
                "feedback": record["feedback"],
                "automatic_review_suggestions": suggestions(record),
            }
        )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": 1,
                "source_turn_count": len(queue),
                "promotion_policy": "Nothing is training data until explicitly approved.",
                "turns": queue,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(OUTPUT.resolve())
    print(f"Queued {len(queue)} turns for review; promoted 0 automatically.")


if __name__ == "__main__":
    main()
