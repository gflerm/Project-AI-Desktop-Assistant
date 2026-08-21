#!/usr/bin/env python3
"""Analyze private Project James tester recordings using only local Python."""

from __future__ import annotations

from array import array
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import wave

from james_feedback import migrate_record


ROOT = Path(__file__).resolve().parents[1]
SESSIONS = ROOT / "captures" / "james-sessions"
REPORT_MD = ROOT / "captures" / "james-session-analysis.md"
REPORT_JSON = ROOT / "captures" / "james-session-analysis.json"


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def distribution(values: list[float]) -> dict[str, float | int | None]:
    return {
        "count": len(values),
        "average": round(statistics.mean(values), 1) if values else None,
        "p50": round(percentile(values, 0.5), 1) if values else None,
        "p95": round(percentile(values, 0.95), 1) if values else None,
        "max": round(max(values), 1) if values else None,
    }


def audio_stats(path: Path) -> dict[str, float] | None:
    if not path.is_file():
        return None
    with wave.open(str(path), "rb") as source:
        frames = source.readframes(source.getnframes())
        rate = source.getframerate()
        channels = source.getnchannels()
        width = source.getsampwidth()
    if width != 2 or not frames:
        return None
    samples = array("h")
    samples.frombytes(frames)
    peak = max(abs(sample) for sample in samples) or 1
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    clipped = sum(abs(sample) >= 32700 for sample in samples) / len(samples) * 100
    return {
        "duration_ms": round(len(samples) / max(rate * channels, 1) * 1000),
        "rms_dbfs": round(20 * math.log10(max(rms, 1) / 32768), 1),
        "peak_percent": round(peak / 32768 * 100, 1),
        "clipped_percent": round(clipped, 3),
    }


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref = reference.casefold().split()
    hyp = hypothesis.casefold().split()
    previous = list(range(len(hyp) + 1))
    for row, expected in enumerate(ref, 1):
        current = [row]
        for column, actual in enumerate(hyp, 1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[column] + 1,
                    previous[column - 1] + (expected != actual),
                )
            )
        previous = current
    return previous[-1] / max(len(ref), 1)


records = []
for path in sorted(SESSIONS.glob("*/turn.json")):
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    record = migrate_record(record)
    record["_directory"] = str(path.parent)
    record["input_audio"] = audio_stats(path.parent / "input.wav")
    record["response_audio"] = audio_stats(path.parent / "response.wav")
    transcript_feedback = record.get("feedback", {}).get("transcript", {})
    corrected = transcript_feedback.get("corrected")
    raw = record.get("raw_transcript")
    if (
        corrected
        and raw
        and transcript_feedback.get("audio_verified")
        and transcript_feedback.get("approved_for_speech_dictionary")
    ):
        record["stt_wer"] = round(word_error_rate(corrected, raw), 4)
    records.append(record)

if not records:
    raise SystemExit("No recorded tester turns were found. Record a turn first.")

timing_keys = ("capture_ms", "stt_wall_ms", "llm_wall_ms", "tts_wall_ms", "total_ms")
timings = {
    key: distribution(
        [float(record.get("timing_ms", {}).get(key)) for record in records if record.get("timing_ms", {}).get(key) is not None]
    )
    for key in timing_keys
}
issues = Counter(
    tag
    for record in records
    for tag in record.get("feedback", {}).get("answer", {}).get("issue_tags", [])
)
providers = Counter(str(record.get("provider") or record.get("route") or "unknown") for record in records)
responses = [str(record.get("response_text", "")).strip().casefold() for record in records]
responses = [response for response in responses if response]
duplicate_responses = len(responses) - len(set(responses))
wers = [float(record["stt_wer"]) for record in records if "stt_wer" in record]
reviewed_answers = sum(
    record.get("feedback", {}).get("answer", {}).get("rating") != "unreviewed"
    for record in records
)
approved_regressions = sum(
    bool(record.get("feedback", {}).get("review", {}).get("approved_for_regression"))
    for record in records
)
quarantined_legacy_corrections = sum(
    bool(record.get("feedback", {}).get("legacy_import", {}).get("requires_manual_review"))
    for record in records
)
refusals = sum(
    any(phrase in str(record.get("response_text", "")).casefold() for phrase in (
        "i can't", "i cannot", "not available", "unable to", "don't have access",
    ))
    for record in records
)
input_audio = [record["input_audio"] for record in records if record.get("input_audio")]

recommendations = []
if refusals:
    recommendations.append(
        f"Review {refusals} refusal-style responses; implement the missing local tool or teach clearer local guidance."
    )
if wers and statistics.mean(wers) > 0.1:
    recommendations.append("STT corrected-turn WER exceeds 10%; expand hints and the multi-tone corpus.")
if input_audio and statistics.mean(item["rms_dbfs"] for item in input_audio) < -35:
    recommendations.append("Average microphone level is quiet; move closer or increase input gain.")
if input_audio and max(item["clipped_percent"] for item in input_audio) > 0.1:
    recommendations.append("Input clipping was detected; reduce microphone gain.")
if timings["total_ms"]["p95"] and timings["total_ms"]["p95"] > 8000:
    recommendations.append("End-to-end p95 exceeds eight seconds; inspect queueing and provider fallback events.")
if duplicate_responses:
    recommendations.append("Repeated exact responses were detected; review prompt diversity and local-model context.")
if not recommendations:
    recommendations.append("No automatic threshold was exceeded; review operator issue tags and notes next.")

summary = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    "turn_count": len(records),
    "providers": dict(providers),
    "issue_counts": dict(issues),
    "refusal_response_count": refusals,
    "duplicate_response_count": duplicate_responses,
    "audio_verified_corrected_stt_wer": distribution([value * 100 for value in wers]),
    "reviewed_answer_count": reviewed_answers,
    "approved_regression_count": approved_regressions,
    "quarantined_legacy_feedback_count": quarantined_legacy_corrections,
    "timing_ms": timings,
    "input_audio": {
        "average_rms_dbfs": round(statistics.mean(item["rms_dbfs"] for item in input_audio), 1) if input_audio else None,
        "maximum_clipped_percent": max((item["clipped_percent"] for item in input_audio), default=None),
    },
    "recommendations": recommendations,
    "turns": records,
}
REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
REPORT_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

lines = [
    "# James Private Session Analysis",
    "",
    f"Generated: {summary['generated_at_utc']}",
    f"Recorded turns: {len(records)}",
    "",
    "## Findings",
    "",
    f"- Refusal-style responses: {refusals}",
    f"- Exact duplicate responses: {duplicate_responses}",
    f"- Reviewed answers: {reviewed_answers}",
    f"- Approved regression cases: {approved_regressions}",
    f"- Quarantined legacy feedback records: {quarantined_legacy_corrections}",
    f"- Audio-verified corrected STT WER average: {summary['audio_verified_corrected_stt_wer']['average']}%",
    f"- Input average RMS: {summary['input_audio']['average_rms_dbfs']} dBFS",
    f"- Maximum input clipping: {summary['input_audio']['maximum_clipped_percent']}%",
    "",
    "## Timing",
    "",
    "| Stage | Count | Average ms | p50 ms | p95 ms | Maximum ms |",
    "|---|---:|---:|---:|---:|---:|",
]
for key in timing_keys:
    item = timings[key]
    lines.append(
        f"| {key} | {item['count']} | {item['average']} | {item['p50']} | {item['p95']} | {item['max']} |"
    )
lines.extend(["", "## Operator issue tags", ""])
if issues:
    lines.extend(f"- {name}: {count}" for name, count in issues.most_common())
else:
    lines.append("- No issues have been tagged yet.")
lines.extend(["", "## Recommendations", ""])
lines.extend(f"- {recommendation}" for recommendation in recommendations)
lines.extend(["", "## Turn review", ""])
for record in records:
    lines.extend(
        [
            f"### {record.get('recorded_at_utc', record.get('turn_id'))}",
            "",
            f"- Prompt/transcript: {record.get('prompt')}",
            f"- Response: {record.get('response_text')}",
            f"- Answer rating: {record.get('feedback', {}).get('answer', {}).get('rating', 'unreviewed')}",
            f"- Issues: {', '.join(record.get('feedback', {}).get('answer', {}).get('issue_tags', [])) or 'none tagged'}",
            f"- Notes: {record.get('feedback', {}).get('answer', {}).get('critique') or 'none'}",
            f"- Private files: {record.get('_directory')}",
            "",
        ]
    )
REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
print(REPORT_MD.resolve())
