#!/usr/bin/env python3
"""Sweep speaker-verification thresholds and report FAR/FRR trade-offs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scores", type=Path)
    parser.add_argument("--step", type=float, default=0.01)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.scores.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise SystemExit("Score file is empty")
    if args.step <= 0 or args.step > 1:
        raise SystemExit("--step must be greater than 0 and no greater than 1")

    trials = []
    for row in rows:
        genuine = row["claimed_speaker"] == row["actual_speaker"]
        trials.append((float(row["score"]), genuine, row))

    genuine_count = sum(genuine for _, genuine, _ in trials)
    impostor_count = len(trials) - genuine_count
    if not genuine_count or not impostor_count:
        raise SystemExit("Need both genuine and impostor trials")

    thresholds = []
    threshold = 0.0
    while threshold <= 1.0000001:
        false_accepts = sum(
            1 for score, genuine, _ in trials if not genuine and score >= threshold
        )
        false_rejects = sum(
            1 for score, genuine, _ in trials if genuine and score < threshold
        )
        far = false_accepts / impostor_count
        frr = false_rejects / genuine_count
        thresholds.append(
            {
                "threshold": round(threshold, 6),
                "far": far,
                "frr": frr,
                "tar": 1.0 - frr,
                "false_accepts": false_accepts,
                "false_rejects": false_rejects,
            }
        )
        threshold += args.step

    equal_error = min(thresholds, key=lambda item: abs(item["far"] - item["frr"]))
    report = {
        "summary": {
            "trials": len(trials),
            "genuine_trials": genuine_count,
            "impostor_trials": impostor_count,
            "closest_equal_error_operating_point": equal_error,
        },
        "thresholds": thresholds,
    }
    output = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
