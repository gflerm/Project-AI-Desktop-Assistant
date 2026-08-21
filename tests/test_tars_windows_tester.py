from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import wave
import json


try:
    import tkinter  # noqa: F401
except ModuleNotFoundError as error:
    raise unittest.SkipTest("The selected Python runtime does not include tkinter") from error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from tars_windows_tester import TarsTester


class WindowsTesterCaptureTests(unittest.TestCase):
    @staticmethod
    def wav_bytes(pcm: bytes) -> bytes:
        output = BytesIO()
        with wave.open(output, "wb") as target:
            target.setnchannels(1)
            target.setsampwidth(2)
            target.setframerate(16000)
            target.writeframes(pcm)
        return output.getvalue()

    def test_private_turn_capture_writes_audio_and_metadata(self) -> None:
        tester = TarsTester.__new__(TarsTester)
        tester._personality_values = {"humour": 65}
        tester._last_turn_path = None
        pcm = bytes(640)
        with tempfile.TemporaryDirectory() as directory, patch.object(
            TarsTester, "_captures_root", return_value=Path(directory)
        ):
            tester._save_recorded_turn(
                turn_id="12345678-test",
                mode="ptt",
                prompt="Hello TARS",
                raw_transcript="Hello TARS",
                adapted_transcript="Hello TARS",
                result={"text": "Ready.", "route": "ollama", "provider": "ollama"},
                timing={"total_ms": 1200},
                input_pcm=pcm,
                response_wav=self.wav_bytes(pcm),
            )
            self.assertTrue(tester._last_turn_path.is_file())
            self.assertTrue((tester._last_turn_path.parent / "input.wav").is_file())
            self.assertTrue((tester._last_turn_path.parent / "response.wav").is_file())
            record = json.loads(tester._last_turn_path.read_text(encoding="utf-8"))
            self.assertEqual(record["schema"], 2)
            self.assertEqual(record["feedback"]["answer"]["rating"], "unreviewed")
            self.assertEqual(tester._active_feedback_turn_id, "12345678-test")


if __name__ == "__main__":
    unittest.main()
