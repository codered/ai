"""Test the task_template.py to ensure it runs correctly when used."""
import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest

# Add parent to path for importing run
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from run import run_task


class TestTemplateScriptedTask(unittest.TestCase):
    """Test that the scripted task block runs and imports taskkit correctly."""

    def test_import_preamble_resolves_from_tasks_directory(self):
        """The template's import preamble should resolve taskkit from plan root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build plan structure: plan/taskkit.py, plan/run.py, plan/tasks/task_01_test.py
            plan_dir = tmpdir
            tasks_dir = os.path.join(plan_dir, "tasks")
            os.makedirs(tasks_dir)

            # Copy taskkit and run to plan root
            ref_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            shutil.copy(os.path.join(ref_dir, "references", "taskkit.py"), plan_dir)
            shutil.copy(os.path.join(ref_dir, "references", "run.py"), plan_dir)

            # Create a minimal task using the template's import preamble and a scripted apply/verify
            task_script = os.path.join(tasks_dir, "task_01_test.py")
            task_content = '''"""Minimal test task."""
import sys
import os

# Resolve taskkit in the plan root (one level above tasks/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import taskkit
from taskkit import Editor, ManualTask, gate

def apply():
    """Minimal apply: just create a marker file."""
    taskkit.create_file("marker.txt", "done\\n")

def verify():
    gate.structural("marker exists", lambda: taskkit.file_contains("marker.txt", "done"))

if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run the task from the plan directory as run.py does
            exit_code, report = run_task(task_script, verify_only=False, repo_root=plan_dir)

            # Should succeed with exit code 0 and have a T0 gate recorded
            self.assertEqual(exit_code, 0, f"Task failed: {report}")
            self.assertTrue(any(t["tier"] == "T0" for t in report.get("tiers", [])),
                          "T0 gate not recorded")
            # Verify the file was actually created in plan_dir (the repo_root)
            marker_path = os.path.join(plan_dir, "marker.txt")
            self.assertTrue(os.path.exists(marker_path),
                          f"marker.txt not created in repo root {plan_dir}")


class TestTemplateManualTask(unittest.TestCase):
    """Test that the manual task block exits 4, not 0, and doesn't silently pass."""

    def test_manual_task_exits_4_not_0(self):
        """Manual task with ManualTask exception should exit 4, not silently pass as 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build plan structure
            plan_dir = tmpdir
            tasks_dir = os.path.join(plan_dir, "tasks")
            os.makedirs(tasks_dir)

            # Copy taskkit and run to plan root
            ref_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            shutil.copy(os.path.join(ref_dir, "references", "taskkit.py"), plan_dir)
            shutil.copy(os.path.join(ref_dir, "references", "run.py"), plan_dir)

            # Create a manual task using the template's manual block (with its own guard)
            task_script = os.path.join(tasks_dir, "task_02_manual.py")
            task_content = '''"""Manual task test."""
import sys
import os

# Resolve taskkit in the plan root (one level above tasks/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import taskkit
from taskkit import ManualTask, gate

KIND = "manual"

def apply():
    raise ManualTask(
        "This is a manual task that requires human judgment.\\n"
        "See plan_superpowers.md for steps."
    )

def verify():
    # Gate that checks for a file that doesn't exist initially
    gate.structural("manual edit complete", lambda: taskkit.file_contains("manual_done.txt", "done"))

if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run the task from the plan directory
            exit_code, report = run_task(task_script, verify_only=False, repo_root=plan_dir)

            # Manual task should exit with code 4
            self.assertEqual(exit_code, 4,
                           f"Manual task should exit 4, got {exit_code}: {report}")
            self.assertEqual(report.get("exit"), 4,
                           f"Report should have exit=4, got {report.get('exit')}")

    def test_manual_task_not_reported_green(self):
        """Manual task should not be reported as green (exit 0) when incomplete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Build plan structure
            plan_dir = tmpdir
            tasks_dir = os.path.join(plan_dir, "tasks")
            os.makedirs(tasks_dir)

            # Copy taskkit and run to plan root
            ref_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            shutil.copy(os.path.join(ref_dir, "references", "taskkit.py"), plan_dir)
            shutil.copy(os.path.join(ref_dir, "references", "run.py"), plan_dir)

            # Create minimal plan_superpowers.md for checkbox rewrite
            plan_md_path = os.path.join(plan_dir, "plan_superpowers.md")
            with open(plan_md_path, "w") as fh:
                fh.write("- [ ] **Task 02** <!-- task_02_manual.py -->\n")

            # Create a manual task
            task_script = os.path.join(tasks_dir, "task_02_manual.py")
            task_content = '''"""Manual task test."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import taskkit
from taskkit import ManualTask, gate

def apply():
    raise ManualTask("Manual work required")

def verify():
    # Gate that checks for a file that doesn't exist initially
    gate.structural("manual edit complete", lambda: taskkit.file_contains("manual_done.txt", "done"))

if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))
'''
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run the task with --verify-only (as run.py --status does)
            exit_code, report = run_task(task_script, verify_only=True, repo_root=plan_dir)

            # When verify-only on incomplete manual task: gate fails (exit 1), not passes (exit 0)
            self.assertNotEqual(exit_code, 0,
                           f"Manual task should not exit 0 when incomplete")
            self.assertEqual(exit_code, 1,
                           f"Manual task gate should fail with exit 1, got {exit_code}")

            # Read the plan file to see if checkbox was updated (it shouldn't be for non-zero exit)
            with open(plan_md_path) as fh:
                content = fh.read()
            # If checkbox is still unchecked [ ], the task was not reported as green
            self.assertIn("- [ ]", content,
                        "Checkbox should not be checked when gate fails")


if __name__ == "__main__":
    unittest.main()
