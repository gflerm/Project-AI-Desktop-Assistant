from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from tars_feedback import empty_feedback, migrate_record, update_turn


class FeedbackSchemaTests(unittest.TestCase):
    def test_legacy_correction_is_quarantined_not_approved(self) -> None:
        record = migrate_record(
            {"schema": 1, "turn_id": "turn-a", "corrected_transcript": "different text"}
        )
        self.assertEqual(record["schema"], 2)
        self.assertEqual(record["feedback"]["transcript"]["corrected"], "different text")
        self.assertFalse(
            record["feedback"]["transcript"]["approved_for_speech_dictionary"]
        )
        self.assertTrue(record["feedback"]["legacy_import"]["requires_manual_review"])

    def test_update_rejects_a_different_turn_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "turn.json"
            path.write_text(json.dumps({"schema": 2, "turn_id": "turn-a", "feedback": empty_feedback()}))
            with self.assertRaisesRegex(ValueError, "turn ID"):
                update_turn(path, "turn-b", empty_feedback())

    def test_update_preserves_record_and_writes_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "turn.json"
            path.write_text(json.dumps({"schema": 2, "turn_id": "turn-a", "prompt": "hello", "feedback": empty_feedback()}))
            feedback = empty_feedback()
            feedback["answer"]["rating"] = "correct"
            saved = update_turn(path, "turn-a", feedback)
            self.assertEqual(saved["prompt"], "hello")
            self.assertEqual(saved["feedback"]["answer"]["rating"], "correct")


if __name__ == "__main__":
    unittest.main()
