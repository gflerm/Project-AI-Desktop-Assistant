from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tars_gateway.speech_adaptation import SpeechAdaptation


class SpeechAdaptationTests(unittest.TestCase):
    def test_teaches_reusable_word_correction_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "speech.json"
            adaptation = SpeechAdaptation(str(path))
            adaptation.teach("Dateway is ready", "Gateway is ready")
            self.assertEqual(adaptation.apply("Dateway remains ready"), "Gateway remains ready")
            self.assertIn("Gateway", adaptation.prompt())
            reloaded = SpeechAdaptation(str(path))
            self.assertEqual(reloaded.apply("Dateway is ready"), "Gateway is ready")
