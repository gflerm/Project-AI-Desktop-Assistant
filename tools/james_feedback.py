"""Versioned, turn-bound feedback records for the private James tester."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
ANSWER_RATINGS = {"unreviewed", "correct", "partial", "wrong"}


def empty_feedback() -> dict[str, Any]:
    return {
        "transcript": {
            "corrected": None,
            "audio_verified": False,
            "approved_for_speech_dictionary": False,
        },
        "answer": {
            "rating": "unreviewed",
            "issue_tags": [],
            "critique": "",
            "preferred_answer": "",
            "approved_for_local_lesson": False,
        },
        "expected": {
            "route": None,
            "tool": None,
            "must_include": [],
            "must_not_include": [],
        },
        "review": {
            "status": "needs_review",
            "approved_for_regression": False,
        },
    }


def migrate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return schema v2 without trusting ambiguous legacy corrections."""
    migrated = deepcopy(record)
    if int(migrated.get("schema", 1)) >= SCHEMA_VERSION and isinstance(
        migrated.get("feedback"), dict
    ):
        return migrated

    feedback = empty_feedback()
    legacy_correction = migrated.get("corrected_transcript")
    legacy_tags = list(migrated.get("issue_tags") or [])
    legacy_notes = str(migrated.get("operator_notes") or "")
    if legacy_correction:
        feedback["transcript"]["corrected"] = str(legacy_correction)
    feedback["answer"]["issue_tags"] = legacy_tags
    feedback["answer"]["critique"] = legacy_notes
    feedback["legacy_import"] = {
        "requires_manual_review": bool(legacy_correction or legacy_tags or legacy_notes),
        "source_schema": int(migrated.get("schema", 1)),
    }
    migrated["schema"] = SCHEMA_VERSION
    migrated["feedback"] = feedback
    return migrated


def update_turn(path: Path, turn_id: str, feedback: dict[str, Any]) -> dict[str, Any]:
    """Atomically replace feedback only when the immutable turn ID matches."""
    record = migrate_record(json.loads(path.read_text(encoding="utf-8")))
    if str(record.get("turn_id")) != str(turn_id):
        raise ValueError("Feedback target does not match the recorded turn ID")
    rating = str(feedback.get("answer", {}).get("rating", "unreviewed"))
    if rating not in ANSWER_RATINGS:
        raise ValueError(f"Unsupported answer rating: {rating}")
    record["feedback"] = deepcopy(feedback)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return record
