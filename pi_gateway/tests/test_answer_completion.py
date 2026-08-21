from __future__ import annotations

import unittest

from james_gateway.services import ConversationMemory, answer_is_complete, clarify_ambiguous_request


class AnswerCompletionTests(unittest.TestCase):
    def test_incomplete_sentence_and_code_fence_are_detected(self) -> None:
        self.assertFalse(answer_is_complete("Fukushima was caused by a massive"))
        self.assertFalse(answer_is_complete("```python\nprint('hello')"))
        self.assertTrue(answer_is_complete("Fukushima followed the earthquake and tsunami."))

    def test_numbered_item_can_be_repeated_from_conversation_ledger(self) -> None:
        memory = ConversationMemory(3, 1800)
        memory.append("desk", "List items", "1. Alpha.\n2. Beta.\n3. Gamma.")
        self.assertEqual(memory.repeat_item("desk", 3), "Point 3: Gamma.")

    def test_ambiguous_meltdown_question_requests_all_three_cases(self) -> None:
        clarified = clarify_ambiguous_request(
            "What caused the nuclear power station that had a meltdown?"
        )
        self.assertIn("Three Mile Island", clarified)
        self.assertIn("Chernobyl", clarified)
        self.assertIn("Fukushima", clarified)
        self.assertEqual(
            clarify_ambiguous_request("What caused the Fukushima nuclear meltdown?"),
            "What caused the Fukushima nuclear meltdown?",
        )


if __name__ == "__main__":
    unittest.main()
