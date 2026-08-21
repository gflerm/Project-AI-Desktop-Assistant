#!/usr/bin/env python3
"""Replay only explicitly approved private James regression cases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "captures" / "james-review-queue.json"
OUTPUT = ROOT / "captures" / "james-regression-results.json"


def evaluate_case(case: dict, result: dict) -> list[str]:
    expected = case.get("feedback", {}).get("expected", {})
    failures: list[str] = []
    route = str(result.get("route", ""))
    provider = str(result.get("provider", ""))
    expected_route = expected.get("route")
    if expected_route == "tool" and not any(
        marker in route for marker in ("system:", "time:", "weather:", "memory:", "conversation:")
    ):
        failures.append(f"expected a tool route, got {route}")
    elif expected_route == "local" and "ollama" not in provider:
        failures.append(f"expected local provider, got {provider}")
    elif expected_route == "cloud" and "gemini" not in provider:
        failures.append(f"expected cloud provider, got {provider}")
    elif expected_route == "multi" and not route.startswith("multi:"):
        failures.append(f"expected multi route, got {route}")
    expected_tool = expected.get("tool")
    route_components = list(result.get("route_components") or [])
    if expected_tool and expected_tool not in route and expected_tool not in route_components:
        failures.append(f"expected tool {expected_tool}, got {route_components or route}")
    response = str(result.get("text", "")).casefold()
    for required in expected.get("must_include") or []:
        if str(required).casefold() not in response:
            failures.append(f"missing required text: {required}")
    for forbidden in expected.get("must_not_include") or []:
        if str(forbidden).casefold() in response:
            failures.append(f"included forbidden text: {forbidden}")
    if result.get("answer_complete") is False:
        failures.append("answer was marked incomplete")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Send approved cases to the gateway")
    args = parser.parse_args()
    payload = json.loads(QUEUE.read_text(encoding="utf-8"))
    approved = [
        case
        for case in payload.get("turns", [])
        if case.get("feedback", {}).get("review", {}).get("approved_for_regression")
    ]
    if not args.run:
        print(f"Review queue: {len(payload.get('turns', []))} turns; approved: {len(approved)}.")
        print("Use the tester to review cases, then pass --run to replay approved cases only.")
        return
    token = os.environ.get("JAMES_TOKEN", "").strip()
    if len(token) < 24:
        raise SystemExit("JAMES_TOKEN is required for --run")
    base = os.environ.get("JAMES_GATEWAY_URL", "http://192.168.8.107:8090").rstrip("/")
    results = []
    for case in approved:
        request = urllib.request.Request(
            base + "/v1/test/chat",
            data=json.dumps(
                {
                    "text": case.get("prompt", ""),
                    "device_id": "private-regression-replay",
                    "provider": "auto",
                    "turn_id": case.get("turn_id"),
                }
            ).encode(),
            headers={"X-James-Token": token, "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
        failures = evaluate_case(case, result)
        results.append(
            {
                "turn_id": case.get("turn_id"),
                "passed": not failures,
                "failures": failures,
                "route": result.get("route"),
                "provider": result.get("provider"),
                "server_ms": result.get("server_ms"),
            }
        )
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "approved_count": len(approved),
        "passed_count": sum(item["passed"] for item in results),
        "failed_count": sum(not item["passed"] for item in results),
        "results": results,
    }
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(OUTPUT.resolve())
    if report["failed_count"]:
        raise SystemExit(f"{report['failed_count']} approved regression cases failed")


if __name__ == "__main__":
    main()
