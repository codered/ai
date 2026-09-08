"""Test that the real task_template.py file runs correctly when used as documented."""
import os
import sys
import json
import tempfile
import shutil
import subprocess
import unittest
import re

from helpers import REFS

sys.path.insert(0, REFS)
from run import run_task  # noqa: E402


class TestRealTemplate(unittest.TestCase):
    """Test the real references/task_template.py by extracting and executing its blocks."""

    @classmethod
    def setUpClass(cls):
        """Read the real template file once and extract blocks by marker comments."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "references", "task_template.py"
        )
        with open(template_path, "r") as fh:
            cls.template_source = fh.read()

        # Extract preamble (lines 1-9, up to first block marker)
        preamble_match = re.search(r"(.*?)(# -+)", cls.template_source, re.DOTALL)
        if preamble_match:
            cls.preamble = preamble_match.group(1).rstrip()
        else:
            raise ValueError("Could not find preamble in template")

        # Extract scripted block (from "# --- scripted --" to next "# ---" or end)
        scripted_match = re.search(
            r"# -+ scripted -+\n(.*?)(?:# -+ manual -+|$)",
            cls.template_source, re.DOTALL
        )
        if scripted_match:
            cls.scripted_body = scripted_match.group(1).rstrip()
        else:
            raise ValueError("Could not find scripted block in template")

        # Extract manual block (from "# --- manual --" to end)
        manual_match = re.search(r"# -+ manual -+\n(.*)", cls.template_source, re.DOTALL)
        if manual_match:
            cls.manual_commented = manual_match.group(1)
        else:
            raise ValueError("Could not find manual block in template")

    def _build_plan(self, tmpdir):
        """Build minimal plan directory structure."""
        plan_dir = tmpdir
        tasks_dir = os.path.join(plan_dir, "tasks")
        os.makedirs(tasks_dir)

        # Copy taskkit and run from references (not embedded strings)
        ref_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        shutil.copy(os.path.join(ref_dir, "references", "taskkit.py"), plan_dir)
        shutil.copy(os.path.join(ref_dir, "references", "run.py"), plan_dir)

        return plan_dir, tasks_dir

    def test_scripted_task_preamble_resolves_taskkit(self):
        """Scripted block from real template: import preamble resolves taskkit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir, tasks_dir = self._build_plan(tmpdir)

            # Create minimal fixture files for the script's locate() calls
            client_http = os.path.join(plan_dir, "client", "http.py")
            os.makedirs(os.path.dirname(client_http))
            with open(client_http, "w") as fh:
                fh.write("def send(req):\n    return self._send(req)\n")

            svc_orders_handler = os.path.join(plan_dir, "svc", "orders", "handler.py")
            os.makedirs(os.path.dirname(svc_orders_handler))
            with open(svc_orders_handler, "w") as fh:
                fh.write("def handle(req):\n    pass\n")

            # Build task using REAL preamble and scripted block from template
            task_script = os.path.join(tasks_dir, "task_01_scripted.py")
            task_content = self.preamble + "\n\n" + self.scripted_body
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run it — the preamble must resolve taskkit, or ModuleNotFoundError
            exit_code, report = run_task(task_script, verify_only=False, repo_root=plan_dir)

            # Should complete without import error (may fail on gate, but import succeeds)
            # Look for import success indicator: either exit 0 (all gates pass) or
            # non-zero but valid report structure (gate ran, didn't error on import)
            self.assertIn("tiers", report,
                        f"Report missing tiers (import error?): {report}")
            self.assertIsNotNone(report.get("exit"),
                        f"Report missing exit code: {report}")
            # Most importantly, should not have a traceback about taskkit import
            stderr = report.get("stderr", "")
            self.assertNotIn("ModuleNotFoundError", stderr,
                        f"ModuleNotFoundError in stderr: {stderr}")
            self.assertNotIn("No module named", stderr,
                        f"Import error in stderr: {stderr}")

    def test_manual_task_raises_manualtask_exit_4(self):
        """Manual block from real template: uncommented, raises ManualTask, exits 4."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir, tasks_dir = self._build_plan(tmpdir)

            # Build task: preamble + manual block (uncommented) + no scripted block
            # To uncomment, remove all leading "# " from each line
            manual_uncommented = "\n".join(
                line[2:] if line.startswith("# ") else line
                for line in self.manual_commented.splitlines()
            )

            task_script = os.path.join(tasks_dir, "task_02_manual.py")
            task_content = self.preamble + "\n\n" + manual_uncommented
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run it — manual task should exit 4 (ManualTask raised)
            exit_code, report = run_task(task_script, verify_only=False, repo_root=plan_dir)

            # Manual task raises ManualTask → exit 4
            self.assertEqual(exit_code, 4,
                        f"Manual task should exit 4, got {exit_code}: {report}")
            self.assertEqual(report.get("exit"), 4,
                        f"Report should have exit=4: {report}")
            # Verify it actually called apply() and raised ManualTask
            stderr = report.get("stderr", "")
            self.assertIn("MANUAL", stderr,
                        f"Should print MANUAL marker, got stderr: {stderr}")

    def test_manual_task_doesnt_report_green(self):
        """Manual task should not be reported as passing (exit 0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_dir, tasks_dir = self._build_plan(tmpdir)

            # Uncomment the manual block
            manual_uncommented = "\n".join(
                line[2:] if line.startswith("# ") else line
                for line in self.manual_commented.splitlines()
            )

            task_script = os.path.join(tasks_dir, "task_02_manual.py")
            task_content = self.preamble + "\n\n" + manual_uncommented
            with open(task_script, "w") as fh:
                fh.write(task_content)

            # Run with verify_only
            exit_code, report = run_task(task_script, verify_only=True, repo_root=plan_dir)

            # Should NOT exit 0 (which would be reported as green)
            self.assertNotEqual(exit_code, 0,
                        f"Manual task should not exit 0 (green), got {exit_code}")
            # When verify fails (file doesn't exist), exit 1
            self.assertEqual(exit_code, 1,
                        f"Incomplete manual task should fail gate with exit 1, got {exit_code}")


if __name__ == "__main__":
    unittest.main()
