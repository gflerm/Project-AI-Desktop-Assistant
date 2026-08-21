from __future__ import annotations

import unittest
from pathlib import Path
import tempfile

from tars_gateway.personality import (
    PersonalityStore,
    personality_prompt_from_environment,
)


class PersonalityTests(unittest.TestCase):
    def test_default_profile_contains_trust_and_voice_policy(self) -> None:
        prompt = personality_prompt_from_environment()
        self.assertIn("honesty 98", prompt)
        self.assertIn("humour 65", prompt)
        self.assertIn("adult male voice", prompt)
        self.assertIn("Never claim an action", prompt)
        self.assertIn("no humour", prompt)
        self.assertIn("answer every requested part", prompt)
        self.assertIn("Never end mid-sentence", prompt)
        self.assertIn("Do not turn a simple question into an encyclopedia entry", prompt)
        self.assertIn("dry observation after the answer", prompt)

    def test_runtime_controls_persist_without_changing_other_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "personality.json"
            store = PersonalityStore(str(path))
            original_honesty = store.values["honesty"]
            store.update({"humour": 70})
            reloaded = PersonalityStore(str(path))
            self.assertEqual(reloaded.values["humour"], 70)
            self.assertEqual(reloaded.values["honesty"], original_honesty)


if __name__ == "__main__":
    unittest.main()
