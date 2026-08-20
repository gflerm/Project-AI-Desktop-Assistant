#!/usr/bin/env python3
"""Compare one-interval VAD predictions with labeled corpus boundaries."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((len(ordered) - 1) * fraction)))
    return ordered[index]


def main() -> int:
    args = parse_args()
    truth = {row["file"]: row for row in read_rows(args.manifest)}
    predictions = {row["file"]: row for row in read_rows(args.predictions)}

    start_errors: list[float] = []
    end_errors: list[float] = []
    clipped_leading: list[float] = []
    detected_speech = missed_speech = false_activations = true_silence = 0
    details: list[dict[str, object]] = []

    for filename, row in truth.items():
        speech_start = float(row["speech_start_ms"] or 0)
        speech_end = float(row["speech_end_ms"] or 0)
        has_speech = speech_end > speech_start
        prediction = predictions.get(filename)
        detected = bool(prediction) and prediction["detected"].lower() in {
            "true",
            "yes",
            "1",
        }
        detail: dict[str, object] = {
            "file": filename,
            "tone": row.get("tone", ""),
            "noise": row.get("noise", ""),
            "has_speech": has_speech,
            "detected": detected,
        }

        if has_speech and detected and prediction:
            predicted_start = float(prediction["predicted_start_ms"])
            predicted_end = float(prediction["predicted_end_ms"])
            start_error = predicted_start - speech_start
            end_error = predicted_end - speech_end
            clipped = max(0.0, start_error)
            start_errors.append(start_error)
            end_errors.append(end_error)
            clipped_leading.append(clipped)
            detected_speech += 1
            detail.update(
                start_error_ms=start_error,
                end_error_ms=end_error,
                clipped_leading_ms=clipped,
            )
        elif has_speech:
            missed_speech += 1
        elif detected:
            false_activations += 1
        else:
            true_silence += 1
        details.append(detail)

    speech_total = detected_speech + missed_speech
    report = {
        "summary": {
            "speech_files": speech_total,
            "detected_speech": detected_speech,
            "missed_speech": missed_speech,
            "speech_recall": detected_speech / speech_total if speech_total else None,
            "false_activations": false_activations,
            "true_silence": true_silence,
            "mean_start_error_ms": statistics.fmean(start_errors)
            if start_errors
            else None,
            "p95_start_error_ms": percentile(start_errors, 0.95),
            "mean_end_error_ms": statistics.fmean(end_errors) if end_errors else None,
            "p95_end_error_ms": percentile(end_errors, 0.95),
            "mean_clipped_leading_ms": statistics.fmean(clipped_leading)
            if clipped_leading
            else None,
            "p95_clipped_leading_ms": percentile(clipped_leading, 0.95),
        },
        "details": details,
    }
    output = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
