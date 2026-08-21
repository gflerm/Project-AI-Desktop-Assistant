from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from james_gateway.persistent_memory import PersistentMemory


class PersistentMemoryTests(unittest.TestCase):
    def test_explicit_memory_survives_reload_and_is_local_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "memory.json"
            memory = PersistentMemory(str(path))
            memory.remember("The operator prefers Celsius")
            reloaded = PersistentMemory(str(path))
            self.assertEqual(len(reloaded.active()), 1)
            self.assertIn("prefers Celsius", reloaded.relevant_context("preferred Celsius"))
            self.assertEqual(reloaded.relevant_context("preferred Celsius", for_cloud=True), "")

    def test_forget_is_soft_delete_and_bulk_delete_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            memory = PersistentMemory(str(Path(directory) / "memory.json"))
            memory.remember("The preferred unit is Celsius")
            self.assertEqual(len(memory.forget("preferred unit")), 1)
            self.assertEqual(memory.active(), [])
            with self.assertRaisesRegex(ValueError, "Bulk deletion"):
                memory.forget("everything")


if __name__ == "__main__":
    unittest.main()
