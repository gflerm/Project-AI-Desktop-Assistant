#!/usr/bin/env python3
"""Convert privacy-safe TARS JSONL telemetry to CSV and a local analysis report."""

from __future__ import annotations

from collections import Counter
import csv
import json
import math
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "captures" / "tars-telemetry-2026-08-20.jsonl"
CSV_PATH = ROOT / "captures" / "tars-telemetry-2026-08-20.csv"
REPORT = ROOT / "captures" / "tars-telemetry-analysis.md"


records = []
for line in SOURCE.read_text(encoding="utf-8").splitlines():
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        continue
    if isinstance(item, dict):
        records.append(item)
if not records:
    raise SystemExit("No telemetry records were found")

fields = sorted({key for record in records for key in record})
with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as output:
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    writer.writerows(records)


def distribution(values):
    values = sorted(float(value) for value in values)
    if not values:
        return {"count": 0, "average": None, "p50": None, "p95": None, "max": None}
    pick = lambda fraction: values[max(0, math.ceil(len(values) * fraction) - 1)]
    return {
        "count": len(values),
        "average": round(statistics.mean(values), 1),
        "p50": round(pick(0.5), 1),
        "p95": round(pick(0.95), 1),
        "max": round(values[-1], 1),
    }


events = Counter(str(record.get("event", "unknown")) for record in records)
providers = Counter(str(record["provider"]) for record in records if record.get("provider"))
fallbacks = sum(bool(record.get("fallback_used")) for record in records)
errors = sum(record.get("status") == "error" for record in records)
timing_fields = sorted(
    key for key in fields if key.endswith("_ms")
)
timings = {
    key: distribution([record[key] for record in records if isinstance(record.get(key), (int, float))])
    for key in timing_fields
}
confidence_count = sum(isinstance(record.get("transcript_confidence"), (int, float)) for record in records)

lines = [
    "# TARS Telemetry Analysis",
    "",
    f"- Events: {len(records)}",
    f"- Period: {records[0].get('timestamp_utc')} to {records[-1].get('timestamp_utc')}",
    f"- Fallback events: {fallbacks}",
    f"- Recorded error events: {errors}",
    f"- Transcript-confidence observations: {confidence_count} (not exposed by the current Whisper route)",
    f"- Raw audio present: {'yes' if any('raw_audio' in record for record in records) else 'no'}",
    f"- Full transcripts present: {'yes' if any('transcript' in record for record in records) else 'no'}",
    "",
    "## Event counts",
    "",
]
lines.extend(f"- {name}: {count}" for name, count in events.most_common())
lines.extend(["", "## Providers", ""])
lines.extend(f"- {name}: {count}" for name, count in providers.most_common())
lines.extend(
    [
        "",
        "## Timing distributions",
        "",
        "| Field | Count | Average ms | p50 ms | p95 ms | Maximum ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
)
for key, values in timings.items():
    lines.append(
        f"| {key} | {values['count']} | {values['average']} | {values['p50']} | {values['p95']} | {values['max']} |"
    )
lines.extend(
    [
        "",
        "## Interpretation",
        "",
        "- Compare p50 with p95/max to identify queueing and cold-start outliers.",
        "- Correlate `turn_id` across STT, chat, TTS and client-turn rows.",
        "- Use explicit private-session recordings for qualitative STT, answer and voice review.",
        "- Do not infer transcription accuracy from latency; corrected reference text is required for WER.",
    ]
)
REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(REPORT.resolve())
