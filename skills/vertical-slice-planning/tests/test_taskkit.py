import unittest

from helpers import ScratchRepo

import taskkit
from taskkit import Editor, gate


class TestThinSlice(ScratchRepo):
    def test_swap_lands_the_edit(self):
        with Editor("client.py") as ed:
            ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])
        self.assertIn("retries=3", self.read("client.py"))
        self.assertEqual(taskkit.REPORT["backend"], "hashline")

    def test_gate_run_applies_then_passes(self):
        def apply():
            with Editor("client.py") as ed:
                ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])

        def verify():
            gate.structural("retries threaded", lambda: taskkit.file_contains("client.py", "retries=3"))

        self.assertEqual(gate.run(apply, verify), 0)
        self.assertIn("retries=3", self.read("client.py"))

    def test_gate_run_is_idempotent(self):
        calls = []

        def apply():
            calls.append(1)
            with Editor("client.py") as ed:
                ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])

        def verify():
            gate.structural("retries threaded", lambda: taskkit.file_contains("client.py", "retries=3"))

        self.assertEqual(gate.run(apply, verify), 0)
        self.assertEqual(gate.run(apply, verify), 0)
        self.assertEqual(len(calls), 1, "apply() must be skipped when already applied")

    def test_gate_failure_exits_1(self):
        def apply():
            pass

        def verify():
            gate.structural("never true", lambda: False)

        self.assertEqual(gate.run(apply, verify), 1)


if __name__ == "__main__":
    unittest.main()
