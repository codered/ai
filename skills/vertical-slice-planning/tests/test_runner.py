import os
import subprocess
import sys
import unittest

from helpers import REFS, ScratchRepo

sys.path.insert(0, REFS)
import run as runner  # noqa: E402

TASK = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate
import taskkit


def apply():
    with open({out!r}, "a", encoding="utf-8") as fh:
        fh.write("{name}\\n")


def verify():
    gate.structural("ran", lambda: taskkit.file_contains({out!r}, "{name}"))


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''

FAILING = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate


def apply():
    pass


def verify():
    gate.structural("never", lambda: False)


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''

NOISE_FIRST = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate
import taskkit


def apply():
    with open({out!r}, "a", encoding="utf-8") as fh:
        fh.write("{name}\\n")


def verify():
    gate.structural("ran", lambda: taskkit.file_contains({out!r}, "{name}"))


if __name__ == "__main__":
    print("noise before report")
    print("[1, 2, 3]")
    raise SystemExit(gate.run(apply, verify))
'''

EMPTY_STDOUT = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate


def apply():
    pass


def verify():
    gate.structural("pass", lambda: True)


if __name__ == "__main__":
    # Suppress all output
    import io
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    raise SystemExit(gate.run(apply, verify))
'''

PLAN_MD = """\
# Demo Implementation Plan

- [ ] **Task 01 — write the log line** <!-- task_01_a.py -->
- [x] **Task 02 — stale tick that must be cleared** <!-- task_02_bad.py -->
- [ ] **Task 99 — no such script** <!-- task_99_ghost.py -->
"""


class PlanFixture(ScratchRepo):
    def _plan(self, specs):
        os.makedirs("tasks", exist_ok=True)
        out = os.path.join(self.dir, "order.log")
        for name, template in specs:
            body = template.format(refs=REFS, out=out, name=name)
            self.write(os.path.join("tasks", name + ".py"), body)
        return out


class TestRunner(PlanFixture):

    def test_tasks_run_in_order(self):
        out = self._plan([("task_01_a", TASK), ("task_02_b", TASK), ("task_10_c", TASK)])
        code = runner.main([self.dir])
        self.assertEqual(code, 0)
        with open(out, encoding="utf-8") as fh:
            self.assertEqual(fh.read().split(), ["task_01_a", "task_02_b", "task_10_c"])

    def test_discover_sorts_numerically_not_lexically(self):
        self._plan([("task_02_b", TASK), ("task_10_c", TASK)])
        names = [os.path.basename(p) for p in runner.discover(self.dir)]
        self.assertEqual(names, ["task_02_b.py", "task_10_c.py"])

    def test_stops_at_first_red_gate(self):
        out = self._plan([("task_01_a", TASK), ("task_02_bad", FAILING), ("task_03_c", TASK)])
        code = runner.main([self.dir])
        self.assertEqual(code, 1)
        with open(out, encoding="utf-8") as fh:
            self.assertNotIn("task_03_c", fh.read())

    def test_report_json_is_captured(self):
        self._plan([("task_01_a", TASK)])
        code, report = runner.run_task(os.path.join(self.dir, "tasks", "task_01_a.py"))
        self.assertEqual(code, 0)
        self.assertEqual(report["backend"], "hashline")
        self.assertEqual(report["tiers"][-1]["tier"], "T0")

    def test_tasks_tolerate_noise_before_report(self):
        """Task stdout with noise and non-dict JSON before report is extracted correctly."""
        out = self._plan([("task_01_a", NOISE_FIRST)])
        code, report = runner.run_task(os.path.join(self.dir, "tasks", "task_01_a.py"))
        self.assertEqual(code, 0)
        self.assertEqual(report["backend"], "hashline")
        # Verify the file was actually written (edit landed correctly)
        with open(out, encoding="utf-8") as fh:
            self.assertIn("task_01_a", fh.read())

    def test_empty_stdout_returns_empty_report_with_stderr(self):
        """Task with no stdout returns empty report dict with stderr key."""
        self._plan([("task_01_a", EMPTY_STDOUT)])
        code, report = runner.run_task(os.path.join(self.dir, "tasks", "task_01_a.py"))
        self.assertEqual(code, 0)
        self.assertIn("stderr", report)
        # Report should only have stderr key when no JSON found
        self.assertEqual(set(report.keys()), {"stderr"})

    def test_repo_root_parameter_runs_tasks_in_repo_root(self):
        """Tasks run with cwd=repo_root, not plan_dir, so relative edits land in repo root."""
        # Create nested plan directory structure: repo_root/docs/plans/demo/tasks/
        os.makedirs(os.path.join(self.dir, "docs", "plans", "demo", "tasks"), exist_ok=True)
        plan_dir = os.path.join(self.dir, "docs", "plans", "demo")

        # Create task that uses RELATIVE path to edit file in repo root
        # This task will create order.log relative to cwd
        task_with_relative_path = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate
import taskkit


def apply():
    with open("order.log", "a", encoding="utf-8") as fh:
        fh.write("{name}\\n")


def verify():
    gate.structural("ran", lambda: taskkit.file_contains("order.log", "{name}"))


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''
        task_content = task_with_relative_path.format(refs=REFS, name="task_01_nested")
        task_path = os.path.join(plan_dir, "tasks", "task_01_nested.py")
        with open(task_path, "w", encoding="utf-8") as fh:
            fh.write(task_content)

        # cd to repo root and run plan from nested directory
        cwd_backup = os.getcwd()
        try:
            os.chdir(self.dir)
            # Pass repo_root explicitly (also the cwd now)
            code, report = runner.run_task(task_path, repo_root=self.dir)
            self.assertEqual(code, 0)
            # Verify edit landed in repo root, not in plan directory
            repo_file = os.path.join(self.dir, "order.log")
            self.assertTrue(os.path.exists(repo_file), "File should exist in repo root")
            with open(repo_file, encoding="utf-8") as fh:
                self.assertIn("task_01_nested", fh.read())
            # Verify there's no file in the plan directory
            bad_path = os.path.join(plan_dir, "order.log")
            self.assertFalse(os.path.exists(bad_path), "File should NOT exist in plan directory")
        finally:
            os.chdir(cwd_backup)

    def test_main_with_nested_plan_and_repo_root(self):
        """main() with --repo-root runs nested plan tasks with cwd=repo_root."""
        # Create nested plan directory structure
        os.makedirs(os.path.join(self.dir, "docs", "plans", "demo", "tasks"), exist_ok=True)
        plan_dir = os.path.join(self.dir, "docs", "plans", "demo")

        # Create task with RELATIVE path
        task_with_relative_path = '''\
import sys
sys.path.insert(0, {refs!r})
from taskkit import gate
import taskkit


def apply():
    with open("order.log", "a", encoding="utf-8") as fh:
        fh.write("{name}\\n")


def verify():
    gate.structural("ran", lambda: taskkit.file_contains("order.log", "{name}"))


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''
        task_content = task_with_relative_path.format(refs=REFS, name="task_01_main")
        task_path = os.path.join(plan_dir, "tasks", "task_01_main.py")
        with open(task_path, "w", encoding="utf-8") as fh:
            fh.write(task_content)

        # cd to repo root and invoke main with --repo-root and plan_dir
        cwd_backup = os.getcwd()
        try:
            os.chdir(self.dir)
            code = runner.main([plan_dir, "--repo-root", self.dir])
            self.assertEqual(code, 0)
            # Verify edit landed in repo root
            repo_file = os.path.join(self.dir, "order.log")
            self.assertTrue(os.path.exists(repo_file), "File should exist in repo root")
            with open(repo_file, encoding="utf-8") as fh:
                self.assertIn("task_01_main", fh.read())
            # Verify there's no file in plan dir
            bad_path = os.path.join(plan_dir, "order.log")
            self.assertFalse(os.path.exists(bad_path), "File should NOT exist in plan directory")
        finally:
            os.chdir(cwd_backup)


class TestStatusSync(PlanFixture):
    def test_status_ticks_passing_and_clears_failing(self):
        out = self._plan([("task_01_a", TASK), ("task_02_bad", FAILING)])
        self.write("plan_superpowers.md", PLAN_MD)
        # Do the work task 01 checks for, without running its apply().
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("task_01_a\n")

        code = runner.main(["--status", self.dir])
        self.assertEqual(code, 0, "--status never fails the run")

        text = self.read("plan_superpowers.md")
        self.assertIn("- [x] **Task 01", text)
        self.assertIn("- [ ] **Task 02", text)
        self.assertIn("- [ ] **Task 99", text, "unknown scripts are left alone")

    def test_status_changes_no_files(self):
        self._plan([("task_01_a", TASK)])
        before = self.read("tasks/task_01_a.py")
        runner.main(["--status", self.dir])
        self.assertEqual(self.read("tasks/task_01_a.py"), before)

    def test_sync_returns_count_of_changed_lines(self):
        self._plan([("task_01_a", TASK)])
        self.write("plan_superpowers.md", PLAN_MD)
        # task_01_a.py (code 0) flips - [ ] → - [x]; task_02_bad.py (code 1) flips - [x] → - [ ]
        changed = runner.sync_checkboxes(self.dir, [("task_01_a.py", 0, {}), ("task_02_bad.py", 1, {})])
        self.assertEqual(changed, 2)

    def test_sync_updates_checkboxes_for_results_without_files(self):
        """A result without a file in tasks/ still syncs its checkbox."""
        self._plan([])  # No files created
        self.write("plan_superpowers.md", PLAN_MD)
        # task_02_bad.py (code 1) should flip - [x] → - [ ] even though file doesn't exist
        changed = runner.sync_checkboxes(self.dir, [("task_02_bad.py", 1, {})])
        self.assertEqual(changed, 1)
        text = self.read("plan_superpowers.md")
        self.assertIn("- [ ] **Task 02", text)


if __name__ == "__main__":
    unittest.main()
