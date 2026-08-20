#!/usr/bin/env python3
"""Beginner-friendly format and signal check for one or more PCM WAV files."""

from __future__ import annotations

import argparse
import glob
import math
import struct
import sys
import wave
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="WAV paths; wildcards are accepted")
    return parser.parse_args()


def expand_files(values: list[str]) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        matches = glob.glob(value)
        paths.extend(Path(match) for match in matches)
    return list(dict.fromkeys(paths))


def dbfs(value: float) -> str:
    return f"{20.0 * math.log10(value / 32768.0):.1f} dBFS" if value else "silence"


def inspect(path: Path) -> bool:
    try:
        with wave.open(str(path), "rb") as audio:
            channels = audio.getnchannels()
            width = audio.getsampwidth()
            rate = audio.getframerate()
            frames = audio.getnframes()
            compression = audio.getcomptype()
            raw = audio.readframes(frames)
    except (OSError, EOFError, wave.Error) as exc:
        print(f"FAIL  {path}\n      Cannot read PCM WAV: {exc}")
        return False

    problems: list[str] = []
    if channels != 1:
        problems.append(f"expected mono, found {channels} channels")
    if width != 2:
        problems.append(f"expected 16-bit, found {width * 8}-bit")
    if rate != 16000:
        problems.append(f"expected 16000 Hz, found {rate} Hz")
    if compression != "NONE":
        problems.append(f"expected uncompressed PCM, found {compression}")

    duration = frames / rate if rate else 0.0
    signal = "signal statistics unavailable for non-16-bit audio"
    if width == 2:
        count = len(raw) // 2
        samples = struct.unpack(f"<{count}h", raw) if count else ()
        peak = max((abs(sample) for sample in samples), default=0)
        rms = math.sqrt(sum(sample * sample for sample in samples) / count) if count else 0
        clipped = sum(abs(sample) >= 32760 for sample in samples)
        clipped_percent = clipped * 100.0 / count if count else 0.0
        signal = f"peak {dbfs(peak)}, RMS {dbfs(rms)}, clipping {clipped_percent:.4f}%"
        if clipped_percent > 0.01:
            problems.append("digital clipping detected; reduce microphone level")

    status = "PASS" if not problems else "FAIL"
    print(f"{status}  {path}")
    print(
        f"      {duration:.2f}s, {channels} channel(s), {width * 8}-bit, "
        f"{rate} Hz, {compression}; {signal}"
    )
    for problem in problems:
        print(f"      - {problem}")
    return not problems


def main() -> int:
    paths = expand_files(parse_args().files)
    if not paths:
        print("No WAV files matched the supplied path.", file=sys.stderr)
        return 2
    return 0 if all(inspect(path) for path in paths) else 1


if __name__ == "__main__":
    raise SystemExit(main())
