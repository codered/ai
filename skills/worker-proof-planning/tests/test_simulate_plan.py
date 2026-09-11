"""Tests for references/simulate_plan.py.

Each test builds a small git repository with no global git identity, writes a
plan in the step contract, and runs the tool on it the way a planner would.
Run with: python3 -m unittest discover -s skills/worker-proof-planning/tests -v
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REFS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
TOOL = os.path.join(REFS, "simulate_plan.py")
sys.path.insert(0, REFS)
import simulate_plan  # noqa: E402

F = "```"


def check(cmd, expected):
    """A Check step: a command and its complete expected output."""
    return f"{F}bash\n{cmd}\n{F}\n\nExpected output, exactly:\n\n{F}text\n{expected}\n{F}\n\n"


def edit(path, old, new):
    return f"In `{path}`, find:\n\n{F}text\n{old}\n{F}\n\nReplace with:\n\n{F}text\n{new}\n{F}\n\n"


class PlanRepo(unittest.TestCase):
    """A scratch repository with app.txt and one commit, and no git identity."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="wpp-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        self.repo = os.path.join(self.tmp, "repo")
        os.makedirs(self.repo)
        self.git("init", "-q")
        with open(os.path.join(self.repo, "app.txt"), "w") as f:
            f.write("alpha\nbeta\nbeta\n")
        self.git("add", "-A")
        self.git("-c", "user.email=setup@example.test", "-c", "user.name=setup", "commit", "-qm", "start")
        self.start = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.run(["git", "-C", self.repo, *args], check=True,
                              capture_output=True, text=True, env=self.env).stdout

    def simulate(self, plan, *extra):
        path = os.path.join(self.tmp, "plan.md")
        with open(path, "w") as f:
            f.write("# Plan\n\n" + plan)
        r = subprocess.run([sys.executable, TOOL, path, self.repo, *extra],
                           capture_output=True, text=True, env=self.env)
        return r.returncode, r.stdout + r.stderr


class CleanPlan(PlanRepo):

    def test_every_form_in_a_correct_plan_passes(self):
        script = os.path.join(self.tmp, "hello.sh")
        plan = (
            edit("app.txt", "alpha", "ALPHA")
            + check("head -1 app.txt", "ALPHA")
            + f"Append this to the end of `app.txt`:\n\n{F}text\ngamma\n{F}\n\n"
            + check("wc -l < app.txt", "5")
            + f"Replace the whole contents of `notes.txt` with:\n\n{F}text\nnotes\n{F}\n\n"
            + f"Create `new.txt` with:\n\n{F}text\nnew\n{F}\n\n"
            + check("cat notes.txt new.txt", "notes\nnew")
            + f"Save this exact content to `{script}`:\n\n{F}bash\necho hi\n{F}\n\n"
            + check(f"bash {script}", "hi")
            + check('git add -A && git commit -qm "step" && git log --oneline -1', "<sha> step")
            + check("git rev-parse HEAD~1", self.start)
            + check("git rev-parse HEAD", "<sha>")
            + check("printf -- '--- PASS: T (1.23s)\\n'", "--- PASS: T (0.00s)")
            + check("printf 'ok  \\tpkg\\t(cached)\\n'", "ok  \tpkg\t0.003s")
        )
        rc, out = self.simulate(plan, "--identity", "Worker <worker@example.test>")
        self.assertEqual(rc, 0, out)
        self.assertIn("9 check(s) matched, 0 problem(s)", out)

    def test_append_adds_one_blank_line_then_the_block(self):
        plan = (f"Append this to the end of `app.txt`:\n\n{F}text\ngamma\n{F}\n\n"
                + check("cat app.txt", "alpha\nbeta\nbeta\n\ngamma"))
        rc, out = self.simulate(plan)
        self.assertEqual(rc, 0, out)
        self.assertIn("APPEND app.txt: +2 lines", out)


class PlantedDefects(PlanRepo):

    def test_wrong_expected_output_is_reported(self):
        rc, out = self.simulate(check("echo two", "one"))
        self.assertEqual(rc, 1)
        self.assertIn("CHECK MISMATCH", out)
        self.assertIn("-one", out)
        self.assertIn("+two", out)

    def test_literal_hash_must_match_exactly(self):
        rc, out = self.simulate(check("git rev-parse HEAD", "0" * 40))
        self.assertEqual(rc, 1)
        self.assertIn("CHECK MISMATCH", out)

    def test_edit_whose_old_text_is_missing_stops(self):
        rc, out = self.simulate(edit("app.txt", "zzz", "yyy") + check("echo after", "after"))
        self.assertEqual(rc, 1)
        self.assertIn("matched 0; stopping", out)
        self.assertNotIn("echo after", out)

    def test_edit_whose_old_text_occurs_twice_stops(self):
        rc, out = self.simulate(edit("app.txt", "beta", "BETA"))
        self.assertEqual(rc, 1)
        self.assertIn("matched 2; stopping", out)

    def test_create_refuses_an_existing_file(self):
        rc, out = self.simulate(f"Create `app.txt` with:\n\n{F}text\nx\n{F}\n\n")
        self.assertEqual(rc, 1)
        self.assertIn("already exists", out)

    def test_saved_script_never_run_is_reported(self):
        unused = os.path.join(self.tmp, "unused.sh")
        rc, out = self.simulate(f"Save this exact content to `{unused}`:\n\n{F}bash\necho x\n{F}\n\n")
        self.assertEqual(rc, 1)
        self.assertIn("is never used by any", out)

    def test_failing_command_without_expected_output_is_reported(self):
        rc, out = self.simulate(f"{F}bash\nfalse\n{F}\n\n")
        self.assertEqual(rc, 1)
        self.assertIn("command exited 1", out)

    def test_expected_block_without_a_command_is_reported(self):
        rc, out = self.simulate(f"Expected output, exactly:\n\n{F}text\nx\n{F}\n\n")
        self.assertEqual(rc, 1)
        self.assertIn("no ```bash command directly before it", out)


class GitIdentity(PlanRepo):

    COMMIT = check('git commit -q --allow-empty -m "c" && git log --oneline -1', "<sha> c")

    def test_missing_identity_warns_and_the_commit_fails(self):
        rc, out = self.simulate(self.COMMIT)
        self.assertEqual(rc, 1)
        self.assertIn("WARNING: git user.email and user.name not configured", out)
        self.assertIn("CHECK MISMATCH", out)

    def test_identity_flag_supplies_one(self):
        rc, out = self.simulate(self.COMMIT, "--identity", "Worker <worker@example.test>")
        self.assertEqual(rc, 0, out)
        self.assertNotIn("WARNING", out)

    def test_repository_identity_is_copied_into_the_clone(self):
        self.git("config", "user.email", "local@example.test")
        self.git("config", "user.name", "local")
        rc, out = self.simulate(self.COMMIT)
        self.assertEqual(rc, 0, out)
        self.assertNotIn("WARNING", out)


class Matching(unittest.TestCase):

    def test_sha_placeholder_matches_any_hash(self):
        self.assertTrue(simulate_plan.matches("<sha> msg", "1a2b3c4 msg"))
        self.assertTrue(simulate_plan.matches("<sha>", "f" * 40))

    def test_literal_hash_does_not_match_another_hash(self):
        self.assertFalse(simulate_plan.matches("1a2b3c4 msg", "9f8e7d6 msg"))

    def test_test_durations_are_ignored(self):
        self.assertTrue(simulate_plan.matches("--- PASS: T (0.00s)", "--- PASS: T (12.5s)"))
        self.assertTrue(simulate_plan.matches("ok  \tp\t0.003s", "ok  \tp\t(cached)"))

    def test_other_text_must_match_exactly(self):
        self.assertFalse(simulate_plan.matches("--- PASS: T (0.00s)", "--- FAIL: T (0.00s)"))
        self.assertFalse(simulate_plan.matches("a\nb", "a\nb\nc"))

    def test_trailing_spaces_and_surrounding_blank_lines_are_ignored(self):
        self.assertTrue(simulate_plan.matches("a\nb", "\na  \nb\n\n"))


if __name__ == "__main__":
    unittest.main()
