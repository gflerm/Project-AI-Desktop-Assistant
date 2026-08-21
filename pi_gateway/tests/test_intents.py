from __future__ import annotations

import unittest

from tars_gateway.intents import plan_intents


class IntentPlanningTests(unittest.TestCase):
    def test_identity_is_deterministic(self) -> None:
        plan = plan_intents("Who are you and what do you do?")
        self.assertEqual([intent.kind for intent in plan.tools], ["system.identity"])
        self.assertEqual(plan.residual, "")

    def test_compound_request_preserves_every_clause(self) -> None:
        plan = plan_intents(
            "Current weather conditions for Cape Town? What is the current time? Do we have nuclear power in South Africa?"
        )
        self.assertEqual(
            [intent.kind for intent in plan.tools],
            ["weather.current", "time.system-clock"],
        )
        self.assertIn("nuclear power", plan.residual)

    def test_settings_and_code_requests_remain_model_requests(self) -> None:
        self.assertFalse(plan_intents("How can we tweak your temperature settings?").tools)
        self.assertFalse(plan_intents("Write a Python script for current weather.").tools)

    def test_memory_and_follow_up_are_explicit_tools(self) -> None:
        self.assertEqual(plan_intents("Remember that I prefer Celsius.").tools[0].kind, "memory.remember")
        self.assertEqual(plan_intents("Repeat point 3 please.").tools[0].argument, 3)

    def test_capability_request_is_not_left_to_model_self_report(self) -> None:
        plan = plan_intents("What offline tools can you access right now?")
        self.assertEqual(plan.tools[0].kind, "system.capabilities")

    def test_related_pi_metrics_stay_one_status_intent(self) -> None:
        plan = plan_intents("How hot is the Pi and what is its memory usage?")
        self.assertEqual([intent.kind for intent in plan.tools], ["system.status.readonly"])
        self.assertEqual(plan.residual, "")


if __name__ == "__main__":
    unittest.main()
