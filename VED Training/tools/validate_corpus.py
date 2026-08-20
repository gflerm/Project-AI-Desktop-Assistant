#!/usr/bin/env python3
"""Validate private WAV corpus metadata and report basic signal statistics."""

from __future__ import annotations

import argparse
import csv
import json
import math
import struct
import wave
from pathlib import Path


REQUIRED_COLUMNS = {
    "file",
    "split",
    "speaker_id",
    "session_id",
    "phrase_id",
    "transcript",
    "tone",
    "distance_m",
    "noise",
    "device",
    "consent",
    "speech_start_ms",
    "speech_end_ms",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--sample-rate", type=int, default=16000)
    parser.add_argument("--allow-missing", action="store_true")
    return parser.parse_args()


def wav_metrics(path: Path) -> dict[str, object]:
    with wave.open(str(path), "rb") as audio:
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        rate = audio.getframerate()
        frames = audio.getnframes()
        compression = audio.getcomptype()
        raw = audio.readframes(frames)

    if width != 2:
        return {
            "channels": channels,
            "sample_width_bits": width * 8,
            "sample_rate_hz": rate,
            "frames": frames,
            "duration_ms": frames * 1000.0 / rate if rate else 0.0,
            "compression": compression,
            "rms_dbfs": None,
            "peak_dbfs": None,
            "clipped_sample_percent": None,
        }

    count = len(raw) // 2
    samples = struct.unpack(f"<{count}h", raw) if count else ()
    square_sum = sum(sample * sample for sample in samples)
    rms = math.sqrt(square_sum / count) if count else 0.0
    peak = max((abs(sample) for sample in samples), default=0)
    clipped = sum(1 for sample in samples if abs(sample) >= 32760)

    def dbfs(value: float) -> float | None:
        return 20.0 * math.log10(value / 32768.0) if value > 0 else None

    return {
        "channels": channels,
        "sample_width_bits": 16,
        "sample_rate_hz": rate,
        "frames": frames,
        "duration_ms": frames * 1000.0 / rate if rate else 0.0,
        "compression": compression,
        "rms_dbfs": dbfs(rms),
        "peak_dbfs": dbfs(peak),
        "clipped_sample_percent": clipped * 100.0 / count if count else 0.0,
    }


def resolve_audio_path(manifest: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidates = [manifest.parent / path, Path.cwd() / path]
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    results: list[dict[str, object]] = []

    with args.manifest.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            raise SystemExit(f"Missing manifest columns: {sorted(missing_columns)}")

        for row_number, row in enumerate(reader, start=2):
            audio_path = resolve_audio_path(args.manifest, row["file"])
            item: dict[str, object] = {
                "row": row_number,
                "file": row["file"],
                "resolved_path": str(audio_path),
                "split": row["split"],
                "tone": row["tone"],
                "noise": row["noise"],
            }

            if row["consent"].strip().lower() not in {"true", "yes", "1"}:
                errors.append(f"row {row_number}: consent is not true")

            if not audio_path.is_file():
                item["missing"] = True
                results.append(item)
                if not args.allow_missing:
                    errors.append(f"row {row_number}: missing WAV {audio_path}")
                continue

            try:
                metrics = wav_metrics(audio_path)
            except (wave.Error, EOFError) as exc:
                errors.append(f"row {row_number}: invalid WAV: {exc}")
                item["invalid_wav"] = str(exc)
                results.append(item)
                continue

            item.update(metrics)
            results.append(item)

            if metrics["channels"] != 1:
                errors.append(f"row {row_number}: expected mono audio")
            if metrics["sample_width_bits"] != 16:
                errors.append(f"row {row_number}: expected 16-bit PCM")
            if metrics["sample_rate_hz"] != args.sample_rate:
                errors.append(
                    f"row {row_number}: expected {args.sample_rate} Hz, "
                    f"found {metrics['sample_rate_hz']} Hz"
                )
            if metrics["compression"] != "NONE":
                errors.append(f"row {row_number}: expected uncompressed PCM")
            clipped = metrics["clipped_sample_percent"]
            if isinstance(clipped, float) and clipped > 0.01:
                errors.append(
                    f"row {row_number}: clipping is {clipped:.4f}% of samples"
                )

            start = float(row["speech_start_ms"] or 0)
            end = float(row["speech_end_ms"] or 0)
            duration = float(metrics["duration_ms"])
            if start < 0 or end < start or end > duration:
                errors.append(
                    f"row {row_number}: invalid speech interval {start}--{end} ms "
                    f"for {duration:.1f} ms file"
                )

    report = {
        "manifest": str(args.manifest),
        "files": results,
        "summary": {
            "rows": len(results),
            "missing": sum(bool(item.get("missing")) for item in results),
            "errors": len(errors),
        },
        "errors": errors,
    }
    output = json.dumps(report, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
