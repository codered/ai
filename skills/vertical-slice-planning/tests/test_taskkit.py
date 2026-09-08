import sys
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


class TestFallback(ScratchRepo):
    def _break_hashline(self):
        import taskkit
        self.addCleanup(setattr, taskkit, "HASHLINE_BIN", taskkit.HASHLINE_BIN)
        taskkit.HASHLINE_BIN = "/nonexistent/hashline"

    def test_edit_still_lands_when_hashline_is_missing(self):
        self._break_hashline()
        with Editor("client.py") as ed:
            ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])
        self.assertIn("retries=3", self.read("client.py"))

    def test_fallback_is_recorded_and_warned(self):
        self._break_hashline()
        with Editor("client.py") as ed:
            ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])
        self.assertEqual(taskkit.REPORT["backend"], "fallback")
        self.assertTrue(
            any("fallback backend used" in w for w in taskkit.REPORT["warnings"]),
            taskkit.REPORT["warnings"],
        )

    def test_fallback_still_refuses_drifted_content(self):
        self._break_hashline()
        with Editor("client.py") as ed:
            anchor = ed.locate("    return _post(req)")
            self.write("client.py", "def send(req):\n    return _post(req, retries=9)\n")
            ed.swap(anchor, ["    return _post(req, retries=3)"])
            with self.assertRaises(taskkit.Drift):
                ed.commit()
        self.assertIn("retries=9", self.read("client.py"))

    def test_fallback_preserves_the_rest_of_the_file(self):
        self._break_hashline()
        with Editor("client.py") as ed:
            ed.swap(ed.locate('    return "ok"'), ['    return "pong"'])
        text = self.read("client.py")
        self.assertIn("def send(req):", text)
        self.assertIn('return "pong"', text)
        self.assertTrue(text.endswith("\n"))


class TestOps(ScratchRepo):
    def test_insert_after(self):
        with Editor("client.py") as ed:
            ed.insert_after(ed.locate("def send(req):"), ["    log.debug('send')"])
        self.assertIn("def send(req):\n    log.debug('send')\n", self.read("client.py"))

    def test_insert_before(self):
        with Editor("client.py") as ed:
            ed.insert_before(ed.locate("def send(req):"), ["import log"])
        self.assertTrue(self.read("client.py").startswith("import log\ndef send(req):"))

    def test_delete(self):
        with Editor("client.py") as ed:
            ed.delete(ed.locate('    return "ok"'))
        self.assertNotIn('return "ok"', self.read("client.py"))

    def test_multiple_ops_in_one_patch_use_original_numbering(self):
        with Editor("client.py") as ed:
            ed.insert_before(ed.locate("def send(req):"), ["import log"])
            ed.swap(ed.locate("    return _post(req)"), ["    return _post(req, retries=3)"])
        text = self.read("client.py")
        self.assertTrue(text.startswith("import log\n"))
        self.assertIn("retries=3", text)

    def test_locate_block_replaces_a_whole_function(self):
        with Editor("client.py") as ed:
            first, last = ed.locate_block("def ping():")
            ed.swap_range(first, last, ["def ping():", '    return "pong"'])
        text = self.read("client.py")
        self.assertIn('return "pong"', text)
        self.assertNotIn('return "ok"', text)
        self.assertIn("def send(req):", text)

    def test_locate_contains(self):
        with Editor("client.py") as ed:
            ed.swap(ed.locate_contains("_post("), ["    return _post(req, retries=3)"])
        self.assertIn("retries=3", self.read("client.py"))

    def test_create_file_is_idempotent(self):
        taskkit.create_file("svc/orders.py", "def handle(req):\n    return {}\n")
        taskkit.create_file("svc/orders.py", "def handle(req):\n    return {}\n")
        self.assertIn("def handle(req):", self.read("svc/orders.py"))

    def test_create_file_conflicting_content_is_drift(self):
        taskkit.create_file("svc/orders.py", "a\n")
        with self.assertRaises(taskkit.Drift):
            taskkit.create_file("svc/orders.py", "b\n")

    def test_locate_block_mid_file(self):
        with Editor("client.py") as ed:
            first, last = ed.locate_block("def send(req):")
            # send() is lines 1-2, but hashline's block includes separator blank lines
            # Verify the block range and that replacement works correctly
            ed.swap_range(first, last, ["def send(req, timeout=5):", "    return _post(req, retries=3)"])
        text = self.read("client.py")
        self.assertIn("def send(req, timeout=5):", text)
        self.assertIn("retries=3", text)
        # Verify ping function is still there (wasn't in the mid-file block)
        self.assertIn("def ping():", text)

    def test_locate_block_concurrent_growth(self):
        with Editor("client.py") as ed:
            # Open editor, capturing snapshot of file (6 lines)
            # External writer appends indented content that extends the ping() block
            current = self.read("client.py")
            self.write("client.py", current + "    # extra body line\n")
            # locate_block on ping() should now detect that find-block returns
            # a line beyond our snapshot with non-empty content (the new body line)
            with self.assertRaises(taskkit.Drift) as cm:
                ed.locate_block("def ping():")
            self.assertIn("grown", str(cm.exception).lower())


class TestTiers(ScratchRepo):
    def test_component_gate_passes_on_zero_exit(self):
        gate.component("unit tests", [sys.executable, "-c", "print('ok')"])
        entry = taskkit.REPORT["tiers"][-1]
        self.assertEqual(entry["tier"], "T1")
        self.assertTrue(entry["ok"])
        self.assertGreaterEqual(entry["seconds"], 0.0)

    def test_component_gate_fails_on_nonzero_exit(self):
        with self.assertRaises(taskkit.GateFailure):
            gate.component("unit tests", [sys.executable, "-c", "raise SystemExit(1)"])
        self.assertFalse(taskkit.REPORT["tiers"][-1]["ok"])

    def test_crossing_gate_accepts_a_callable(self):
        gate.crossing("client reaches orders", check=lambda: True)
        self.assertEqual(taskkit.REPORT["tiers"][-1]["tier"], "T2")

    def test_crossing_failure_detail_carries_output(self):
        with self.assertRaises(taskkit.GateFailure):
            gate.crossing("seam", cmd=[sys.executable, "-c", "import sys; sys.stderr.write('boom'); raise SystemExit(2)"])
        self.assertIn("boom", taskkit.REPORT["tiers"][-1]["detail"])

    def test_all_three_tiers_recorded_in_order(self):
        def apply():
            pass

        def verify():
            gate.structural("file present", lambda: True)
            gate.component("unit", [sys.executable, "-c", "pass"])
            gate.crossing("seam", check=lambda: True)

        self.assertEqual(gate.run(apply, verify), 0)
        self.assertEqual([t["tier"] for t in taskkit.REPORT["tiers"]], ["T0", "T1", "T2"])


if __name__ == "__main__":
    unittest.main()
