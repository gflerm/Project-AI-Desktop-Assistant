from __future__ import annotations

from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from replay_james_review_queue import evaluate_case


class RegressionReplayTests(unittest.TestCase):
    def test_expected_route_content_and_completion_are_checked(self) -> None:
        case = {
            "feedback": {
                "expected": {
                    "route": "tool",
                    "tool": "time:system-clock",
                    "must_include": ["South African Standard Time"],
                    "must_not_include": ["no clock"],
                }
            }
        }
        passing = {
            "route": "time:system-clock",
            "route_components": ["time:system-clock"],
            "provider": "system-clock",
            "text": "It is noon in South African Standard Time.",
            "answer_complete": True,
        }
        self.assertEqual(evaluate_case(case, passing), [])
        failing = dict(passing, text="I have no clock", answer_complete=False)
        self.assertGreaterEqual(len(evaluate_case(case, failing)), 3)


if __name__ == "__main__":
    unittest.main()
