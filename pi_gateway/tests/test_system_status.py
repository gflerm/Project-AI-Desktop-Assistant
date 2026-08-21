from __future__ import annotations

import unittest

from tars_gateway.system_status import SystemSnapshot, system_status_requested


class SystemStatusTests(unittest.TestCase):
    def test_explicit_pi_metric_queries_match(self) -> None:
        self.assertTrue(system_status_requested("How hot is the Pi?"))
        self.assertTrue(system_status_requested("Show titanium memory and disk usage"))
        self.assertTrue(system_status_requested("What is the gateway system status?"))

    def test_unrelated_queries_do_not_match(self) -> None:
        self.assertFalse(system_status_requested("How hot is Cape Town?"))
        self.assertFalse(system_status_requested("Explain computer memory"))
        self.assertFalse(system_status_requested("Status?"))

    def test_description_contains_measured_values_and_health(self) -> None:
        snapshot = SystemSnapshot(
            temperature_c=51.25,
            fan_rpm=2911,
            fan_percent=29.4,
            cooling_state=1,
            cooling_max_state=4,
            load_1m=0.25,
            load_5m=0.5,
            load_15m=0.75,
            memory_used_gib=3.2,
            memory_total_gib=7.9,
            disk_used_gib=67.0,
            disk_total_gib=235.0,
            uptime_seconds=7200,
        )
        reply = snapshot.describe({"whisper": True, "piper": True, "ollama": False})
        self.assertIn("51.2 degrees Celsius", reply)
        self.assertIn("2911 RPM", reply)
        self.assertIn("29 percent PWM", reply)
        self.assertIn("cooling state 1 of 4", reply)
        self.assertIn("3.2 of 7.9", reply)
        self.assertIn("Healthy services: piper, whisper", reply)
        self.assertIn("Services needing attention: ollama", reply)


if __name__ == "__main__":
    unittest.main()
