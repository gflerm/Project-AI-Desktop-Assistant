from __future__ import annotations

import unittest

from tars_gateway.services import automatic_provider, local_reply_needs_cloud


class RoutingPolicyTests(unittest.TestCase):
    def test_current_information_goes_directly_to_cloud(self) -> None:
        self.assertEqual(
            automatic_provider("Who is the current president of South Africa?"),
            ("gemini", "current-or-live-information"),
        )

    def test_high_stakes_and_research_go_directly_to_cloud(self) -> None:
        self.assertEqual(automatic_provider("Give me medical advice for chest pain")[0], "gemini")
        self.assertEqual(automatic_provider("Research this and provide sources")[0], "gemini")
        self.assertEqual(
            automatic_provider("What caused the Fukushima nuclear disaster?")[0],
            "gemini",
        )
        self.assertEqual(
            automatic_provider(
                "What was the main cause of the nuclear power station that had a meltdown?"
            )[0],
            "gemini",
        )

    def test_routine_question_starts_locally(self) -> None:
        self.assertEqual(
            automatic_provider("Why is the sky blue?"),
            ("ollama", "routine-local-first"),
        )

    def test_local_refusal_escalates_but_normal_answer_does_not(self) -> None:
        self.assertTrue(local_reply_needs_cloud("I can't access that information."))
        self.assertTrue(local_reply_needs_cloud(""))
        self.assertFalse(local_reply_needs_cloud("Rayleigh scattering makes the sky appear blue."))


if __name__ == "__main__":
    unittest.main()
