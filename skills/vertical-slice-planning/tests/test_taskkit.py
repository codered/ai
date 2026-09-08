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


class TestDrift(ScratchRepo):
    def test_missing_expected_line_is_drift_not_guesswork(self):
        with self.assertRaises(taskkit.Drift):
            with Editor("client.py") as ed:
                ed.swap(ed.locate("    return _post(req)  # gone"), ["x"])

    def test_drift_exits_3_and_writes_nothing(self):
        before = self.read("client.py")

        def apply():
            with Editor("client.py") as ed:
                ed.swap(ed.locate("    line that never existed"), ["x"])

        def verify():
            gate.structural("impossible", lambda: False)

        self.assertEqual(gate.run(apply, verify), 3)
        self.assertEqual(self.read("client.py"), before)

    def test_stale_hash_from_a_concurrent_write_is_drift(self):
        with Editor("client.py") as ed:
            anchor = ed.locate("    return _post(req)")
            # Someone else edits the file after our read.
            self.write("client.py", "def send(req):\n    return _post(req, retries=9)\n")
            ed.swap(anchor, ["    return _post(req, retries=3)"])
            with self.assertRaises(taskkit.Drift):
                ed.commit()
        self.assertIn("retries=9", self.read("client.py"))

    def test_hashline_detected_drift_through_gate_run(self):
        concurrent_content = "def send(req):\n    return _post(req, retries=9)\n"

        def apply():
            with Editor("client.py") as ed:
                anchor = ed.locate("    return _post(req)")
                # Concurrent writer modifies the file after our read but before commit.
                self.write("client.py", concurrent_content)
                ed.swap(anchor, ["    return _post(req, retries=3)"])

        def verify():
            gate.structural("retries=3 present", lambda: taskkit.file_contains("client.py", "retries=3"))

        self.assertEqual(gate.run(apply, verify), 3)
        # Verify nothing was written: concurrent content persists
        self.assertEqual(self.read("client.py"), concurrent_content)


if __name__ == "__main__":
    unittest.main()
