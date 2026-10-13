"""Tests for references/ste_lint.py.

Each error fixture in fixtures/ triggers exactly one error code. The tests run the
script the way an agent runs it and compare the complete output.
Run with: python3 -m unittest discover -s skills/taskfile-planning/tests -v
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

TESTS = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(TESTS, "fixtures")
REFS = os.path.join(os.path.dirname(TESTS), "references")
TOOL = os.path.join(REFS, "ste_lint.py")
sys.path.insert(0, REFS)
import ste_lint  # noqa: E402

BASE = """PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
"""


def run(name, *flags, cwd=FIXTURES):
    """Run the linter on a file name relative to cwd. Return (exit code, stdout, stderr)."""
    proc = subprocess.run([sys.executable, TOOL, name, *flags], cwd=cwd,
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def errors(source):
    """Lint source text in memory. Return the error lines without a file name."""
    return [f"{line}: {code} {message}" for line, code, message in ste_lint.lint(source)[1]]


class LintCase(unittest.TestCase):
    def assert_fixture(self, name, expected):
        code, out, _ = run(name)
        self.assertEqual(out.splitlines(), [f"{name}:{line}" for line in expected])
        self.assertEqual(code, 1 if expected else 0)


class CliTest(LintCase):
    def test_base_file_is_valid(self):
        self.assertEqual(errors(BASE), [])

    def test_missing_file_exits_2(self):
        code, out, err = run("no-such-file.ste")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no-such-file.ste", err)

    def test_every_code_has_one_fixture(self):
        names = os.listdir(FIXTURES)
        for code in ste_lint.CODES:
            matching = [n for n in names if n.startswith(code.lower() + "-")]
            self.assertEqual(len(matching), 1, code)

    def test_comments_and_blank_lines(self):
        source = BASE.replace("  GOAL Add the module.",
                              "  # A comment line.\n\n  GOAL Add the module.  # a trailing comment")
        self.assertEqual(errors(source), [])

    def test_hash_inside_a_word_is_not_a_comment(self):
        source = BASE.replace("FILES src/one.py", "FILES src/one#two.py")
        self.assertEqual(errors(source), [])

    def test_crlf_line_endings(self):
        self.assertEqual(errors(BASE.replace("\n", "\r\n")), [])


class StructureTest(LintCase):
    def test_s001_plan_not_first(self):
        self.assert_fixture("s001-plan-not-first.ste",
                            ["1: S001 the first directive must be PLAN <name> <version>"])

    def test_s001_empty_file(self):
        self.assertEqual(errors(""), [
            "1: S001 the first directive must be PLAN <name> <version>",
            "1: S005 the file needs at least one TASK block",
            "1: S009 the file needs exactly one GLOBAL block",
        ])

    def test_s002_unknown_keyword(self):
        self.assert_fixture("s002-unknown-keyword.ste", ["14: S002 unknown keyword NOTE"])

    def test_s003_wrong_scope(self):
        self.assert_fixture("s003-wrong-scope.ste", ["9: S003 GOAL is not allowed in GLOBAL"])

    def test_s003_directive_outside_a_block(self):
        source = BASE + "\nGOAL Add the module.\n"
        self.assertEqual(errors(source), ["18: S003 GOAL must be inside a GLOBAL or TASK block"])

    def test_s004_too_many(self):
        self.assert_fixture("s004-too-many.ste", ["14: S004 GOAL can appear only once in TASK one"])

    def test_s005_missing_required(self):
        self.assert_fixture("s005-missing-required.ste", ["12: S005 TASK one needs VERIFY"])

    def test_s006_bad_id(self):
        self.assert_fixture("s006-bad-id.ste", ['12: S006 task id "One" must match [a-z][a-z0-9-]*'])

    def test_s007_duplicate_id(self):
        self.assert_fixture("s007-duplicate-id.ste", ["18: S007 duplicate task id one"])

    def test_s008_block_not_closed(self):
        self.assert_fixture("s008-block-not-closed.ste", ["12: S008 TASK one is not closed"])

    def test_s008_end_without_block(self):
        self.assertEqual(errors(BASE + "END\n"), ["17: S008 END without an open block"])

    def test_s009_two_globals(self):
        self.assert_fixture("s009-two-globals.ste",
                            ["12: S009 the file needs exactly one GLOBAL block"])

    def test_s010_bad_arguments(self):
        self.assert_fixture("s010-bad-arguments.ste",
                            ["4: S010 AGENTS needs max <n> with n >= 1"])

    def test_s010_status_because_without_reason(self):
        source = BASE.replace("  VERIFY pytest tests/test_one.py\n",
                              "  VERIFY pytest tests/test_one.py\n  STATUS completed_failure BECAUSE\n")
        self.assertEqual(errors(source),
                         ["16: S010 STATUS needs <state> [BECAUSE <sentence>] [BY <id>]"])


if __name__ == "__main__":
    unittest.main()
