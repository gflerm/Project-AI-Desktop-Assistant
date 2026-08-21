from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from tars_gateway.local_learning import LocalLearning


class LocalLearningTests(unittest.TestCase):
    def test_retrieves_relevant_persistent_operator_lesson(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "lessons.json"
            learning = LocalLearning(str(path))
            learning.add(
                "How should you report gateway health?",
                "I cannot do that.",
                "Use the health result when it is supplied and state which component failed.",
            )
            self.assertIn("which component failed", learning.relevant_context("Report gateway health"))
            self.assertEqual(LocalLearning(str(path)).status()["lesson_count"], 1)
            self.assertEqual(learning.relevant_context("Write a poem"), "")
