from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from james_gateway.telemetry import TelemetryRecorder


class TelemetryTests(unittest.TestCase):
    def test_summary_and_text_privacy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "telemetry.jsonl"
            recorder = TelemetryRecorder(str(path), include_text=False)
            recorder.record(
                "chat", route="auto", provider="gemini", server_ms=100,
                transcript="private words", response_text="private answer", status="ok",
            )
            recorder.record(
                "chat", route="auto", provider="ollama", server_ms=300,
                fallback_used=True, status="error",
            )
            summary = recorder.summary()
            self.assertEqual(summary["total_events"], 2)
            self.assertEqual(summary["timing_ms"]["server_ms"]["average"], 200)
            self.assertEqual(summary["fallback_count"], 1)
            self.assertEqual(summary["error_count"], 1)
            stored = path.read_text(encoding="utf-8")
            self.assertNotIn("private words", stored)
            self.assertNotIn("private answer", stored)


if __name__ == "__main__":
    unittest.main()
