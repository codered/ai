"""Two components, one seam: build a plan directory by hand in the shape the
skill emits, then prove it runs to green and is idempotent."""
import os
import sys
import unittest

from helpers import REFS, ScratchRepo

sys.path.insert(0, REFS)
import run as runner  # noqa: E402

CLIENT = 'def send(payload):\n    return _post("/orders", payload)\n'
SERVICE = 'def handle(req):\n    return {"ok": True}\n'

SMOKE = '''\
import sys
sys.path.insert(0, ".")
from client import send
from service import handle
req = {"headers": {"x-retries": "2"}}
assert handle(req)["retries"] == 2, handle(req)
print("seam ok")
'''

TASK_01 = '''\
import sys, os
sys.path.insert(0, {refs!r})
import taskkit
from taskkit import Editor, gate


def apply():
    with Editor("service.py") as ed:
        ed.swap(
            ed.locate('    return {{"ok": True}}'),
            ['    return {{"ok": True, "retries": int(req["headers"].get("x-retries", 0))}}'],
        )
    with Editor("client.py") as ed:
        ed.swap(
            ed.locate('    return _post("/orders", payload)'),
            ['    return _post("/orders", payload, headers={{"x-retries": "2"}})'],
        )


def verify():
    gate.structural("service reads the header", lambda: taskkit.file_contains("service.py", "x-retries"))
    gate.structural("client sends the header", lambda: taskkit.file_contains("client.py", "x-retries"))
    gate.crossing("client header reaches service", cmd=[sys.executable, "smoke.py"])


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''

PLAN_MD = """\
# Retry Header Plan

- [ ] **Task 01 — wire the retry header end to end** <!-- task_01_wire_seam.py -->
"""


class TestEndToEnd(ScratchRepo):
    def _build_plan(self):
        self.write("client.py", CLIENT)
        self.write("service.py", SERVICE)
        self.write("smoke.py", SMOKE)
        self.write("plan_superpowers.md", PLAN_MD)
        os.makedirs("tasks", exist_ok=True)
        self.write(os.path.join("tasks", "task_01_wire_seam.py"), TASK_01.format(refs=REFS))

    def test_plan_runs_to_green(self):
        self._build_plan()
        self.assertEqual(runner.main(["--repo-root", self.dir, self.dir]), 0)
        self.assertIn("x-retries", self.read("client.py"))
        self.assertIn("retries", self.read("service.py"))

    def test_rerunning_the_whole_plan_is_a_no_op(self):
        self._build_plan()
        runner.main(["--repo-root", self.dir, self.dir])
        after_first = (self.read("client.py"), self.read("service.py"))
        self.assertEqual(runner.main(["--repo-root", self.dir, self.dir]), 0)
        self.assertEqual((self.read("client.py"), self.read("service.py")), after_first)

    def test_status_ticks_the_checkbox_after_a_green_run(self):
        self._build_plan()
        runner.main(["--repo-root", self.dir, self.dir])
        runner.main(["--repo-root", self.dir, "--status", self.dir])
        self.assertIn("- [x] **Task 01", self.read("plan_superpowers.md"))

    def test_gates_fail_cleanly_before_the_work_is_done(self):
        """Step 6 of the skill: every gate must fail, not error, on a fresh plan."""
        self._build_plan()
        code, report = runner.run_task(
            os.path.join(self.dir, "tasks", "task_01_wire_seam.py"), verify_only=True, repo_root=self.dir
        )
        self.assertEqual(code, 1, report)
        self.assertFalse(report["tiers"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
