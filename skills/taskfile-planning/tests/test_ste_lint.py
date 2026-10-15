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


class GraphTest(LintCase):
    def test_g001_unknown_depends(self):
        self.assert_fixture("g001-unknown-depends.ste", ["13: G001 DEPENDS names unknown task two"])

    def test_g002_unknown_ref_task(self):
        self.assert_fixture("g002-unknown-ref-task.ste",
                            ["14: G002 ${two.module} names unknown task two"])

    def test_g003_unknown_ref_key(self):
        self.assert_fixture("g003-unknown-ref-key.ste",
                            ["21: G003 ${one.package}: task one has no OUTPUT package"])

    def test_g004_cycle(self):
        self.assert_fixture("g004-cycle.ste", ["12: G004 dependency cycle: one -> two -> one"])

    def test_g004_self_reference(self):
        source = BASE.replace("  GOAL Add the module.",
                              "  GOAL Add the module.\n  OUTPUT name = one\n  STEP Name the module ${one.name}.")
        self.assertEqual(errors(source), ["12: G004 dependency cycle: one -> one"])

    def test_g005_files_overlap(self):
        self.assert_fixture("g005-files-overlap.ste",
                            ["20: G005 FILES src/*.py overlaps FILES src/one.py of task one in wave 1"])

    def test_three_waves(self):
        code, out, _ = run("valid-three-waves.ste", "--waves")
        self.assertEqual((code, out), (0, "wave 1: model docs\nwave 2: store\nwave 3: api\n"))

    def test_golden_example(self):
        code, out, _ = run("example.ste", "--waves", cwd=REFS)
        self.assertEqual((code, out), (0, "wave 1: schema\nwave 2: endpoint\n"))


class PermissionTest(LintCase):
    def test_p001_permit_not_narrower(self):
        self.assert_fixture("p001-permit-not-narrower.ste",
                            ["13: P001 PERMIT write docs/** is not inside a GLOBAL PERMIT write"])

    def test_p002_files_outside_write(self):
        self.assert_fixture("p002-files-outside-write.ste",
                            ["14: P002 FILES docs/one.md is not inside PERMIT write"])

    def test_p002_cannot_decide(self):
        source = BASE.replace("PERMIT write src/** tests/**", "PERMIT write src/*.py tests/**") \
                     .replace("FILES src/one.py", "FILES src/o*.py")
        self.assertEqual(errors(source),
                         ["14: P002 cannot decide whether FILES src/o*.py is inside PERMIT write"])

    def test_p003_permit_denied(self):
        self.assert_fixture("p003-permit-denied.ste",
                            ["6: P003 PERMIT write tests/** is forbidden by DENY write tests/**"])

    def test_p004_permit_spawn(self):
        self.assert_fixture("p004-permit-spawn.ste",
                            ["8: P004 PERMIT spawn is not allowed; tasks never start agents"])

    def test_p005_verify_not_permitted(self):
        self.assert_fixture("p005-verify-not-permitted.ste",
                            ["15: P005 VERIFY command make is not inside PERMIT run"])

    def test_deny_inside_a_permit_is_valid(self):
        source = BASE.replace("  TOOL edit", "  DENY write src/secrets/**\n  TOOL edit")
        self.assertEqual(errors(source), [])

    def test_files_under_a_deny_fail(self):
        source = BASE.replace("  TOOL edit", "  DENY write src/one.py\n  TOOL edit")
        self.assertEqual(errors(source), ["15: P003 FILES src/one.py is forbidden by DENY write src/one.py"])


class FlowTest(LintCase):
    def test_f001_unknown_flow_step(self):
        self.assert_fixture("f001-unknown-flow-step.ste",
                            ["9: F001 FLOW step lint is not a TOOL role or a built-in step"])

    def test_f002_skip_not_in_flow(self):
        self.assert_fixture("f002-skip-not-in-flow.ste",
                            ["15: F002 SKIP build names a step that is not in FLOW"])

    def test_f003_skip_verify(self):
        self.assert_fixture("f003-skip-verify.ste",
                            ["15: F003 SKIP verify is not allowed; verify and report always run"])

    def test_f004_duplicate_tool_role(self):
        self.assert_fixture("f004-duplicate-tool-role.ste", ["9: F004 TOOL role edit is declared twice"])


class StatusTest(LintCase):
    def test_x001_unknown_state(self):
        self.assert_fixture("x001-unknown-state.ste", [
            "16: X001 unknown state done; use one of: pending, in_progress, "
            "completed_success, completed_failure, blocked"])

    def test_x002_failure_without_because(self):
        self.assert_fixture("x002-failure-without-because.ste",
                            ["16: X002 completed_failure needs BECAUSE <sentence>"])

    def test_x003_blocked_without_by(self):
        self.assert_fixture("x003-blocked-without-by.ste", ["24: X003 blocked needs BY <id>"])

    def test_x004_by_not_failed_dependency(self):
        self.assert_fixture("x004-by-not-failed-dependency.ste",
                            ["24: X004 BY one names a task in state completed_success"])

    def test_x005_started_before_dependency(self):
        self.assert_fixture("x005-started-before-dependency.ste",
                            ["23: X005 task two is completed_success but dependency one is pending"])

    def test_interrupted_run_is_valid(self):
        code, out, _ = run("valid-interrupted-run.ste")
        self.assertEqual((code, out), (0, ""))


class SteTest(LintCase):
    def test_t001_long_sentence(self):
        self.assert_fixture("t001-long-sentence.ste", ["14: T001 sentence has 21 words; the limit is 20"])

    def test_t002_rejected_word(self):
        self.assert_fixture("t002-rejected-word.ste", ['14: T002 replace "ensure" with "make sure"'])

    def test_t003_filler_word(self):
        self.assert_fixture("t003-filler-word.ste", ['14: T003 delete "just"'])

    def test_t004_leading_gerund(self):
        self.assert_fixture("t004-leading-gerund.ste",
                            ['13: T004 sentence starts with "Adding"; start with a verb'])

    def test_quoted_text_and_placeholders_are_not_checked(self):
        problems = ste_lint.ste_problems('Add the label "Just ensure it works" and use `verify_all`.')
        self.assertEqual(problems, [])

    def test_placeholder_counts_as_one_word(self):
        text = "Write " + " ".join(["word"] * 18) + " ${schema.table}."
        self.assertEqual(ste_lint.ste_problems(text), [])

    def test_allowed_ing_words(self):
        self.assertEqual(ste_lint.ste_problems("Bring the server up. String the values together."), [])

    def test_orchestrator_reasons_pass(self):
        for reason in ("changed files outside FILES", "VERIFY failed after merge",
                       "merge conflict", "context limit"):
            self.assertEqual(ste_lint.ste_problems(reason), [], reason)
        self.assertEqual(ste_lint.ste_problems("Verify the output."),
                         [("T002", 'replace "verify" with "make sure"')])

    def test_each_sentence_is_counted_alone(self):
        text = " ".join(["word"] * 15) + ". " + " ".join(["word"] * 15) + "."
        self.assertEqual(ste_lint.ste_problems(text), [])


class JsonTest(unittest.TestCase):
    def test_waves_and_json_together_exit_2(self):
        self.assertEqual(run("valid-three-waves.ste", "--waves", "--json")[0], 2)

    def test_json_shape(self):
        code, out, _ = run("example.ste", "--json", cwd=REFS)
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(sorted(data), ["global", "plan", "tasks", "waves"])
        self.assertEqual(data["plan"], {
            "name": "health-check", "version": "1",
            "integration_branch": "taskfile/health-check/integration",
            "integration_worktree": ".worktrees/health-check/integration"})
        g = data["global"]
        self.assertEqual(g["agents_max"], 3)
        self.assertEqual(g["flow"], ["read", "tasklist", "edit", "fmt", "build", "verify", "report"])
        self.assertEqual(g["tools"]["fmt"], "ruff format")
        self.assertEqual(g["deny"], {"network": ["**"]})
        self.assertEqual((g["heartbeat_every"], g["compact_after_wave"], g["tasklist"]), (2, True, True))
        self.assertEqual(g["worktrees"], ".worktrees")
        self.assertTrue(g["text"].startswith("GLOBAL\n") and g["text"].endswith("END"))
        self.assertEqual(data["waves"], [["schema"], ["endpoint"]])
        endpoint = data["tasks"][1]
        self.assertEqual(endpoint["id"], "endpoint")
        self.assertEqual(endpoint["depends"], ["schema"])
        self.assertEqual(endpoint["wave"], 2)
        self.assertEqual(endpoint["skips"], {"build": "This task does not change the package."})
        self.assertEqual(endpoint["status"], {"state": "pending", "because": None, "by": None})
        self.assertEqual(endpoint["branch"], "taskfile/health-check/tasks/endpoint")
        self.assertEqual(endpoint["worktree"], ".worktrees/health-check/tasks/endpoint")
        self.assertIn("${schema.table}", endpoint["text"])
        self.assertEqual(data["tasks"][0]["outputs"], {"table": "health_log"})



class AuditTest(unittest.TestCase):
    def audit(self, task_id, stdin):
        proc = subprocess.run([sys.executable, TOOL, "example.ste", "--audit", task_id], cwd=REFS,
                              input=stdin, capture_output=True, text=True)
        return proc.returncode, proc.stdout

    def test_paths_inside_files_pass(self):
        self.assertEqual(self.audit("endpoint", "src/api.py\ntests/test_health.py\n"), (0, ""))

    def test_paths_outside_files_are_printed(self):
        self.assertEqual(self.audit("endpoint", "src/api.py\nsrc/db.py\nREADME.md\n"),
                         (1, "src/db.py\nREADME.md\n"))

    def test_glob_files(self):
        model, _ = ste_lint.lint(BASE.replace("FILES src/one.py", "FILES src/**"))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ste_lint.audit(model, "one", ["src/a/b.py", "tests/x.py"])
        self.assertEqual((code, out.getvalue()), (1, "tests/x.py\n"))

    def test_empty_diff_passes(self):
        self.assertEqual(self.audit("schema", ""), (0, ""))

    def run_audit(self, source, task_id, paths):
        model, errors = ste_lint.lint(source)
        self.assertEqual(errors, [])
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ste_lint.audit(model, task_id, paths)
        return code, out.getvalue()

    def test_path_under_global_deny_write_is_printed(self):
        source = BASE.replace("  PERMIT run pytest", "  PERMIT run pytest\n  DENY write src/secret/**") \
                     .replace("FILES src/one.py", "FILES src/**")
        self.assertEqual(self.run_audit(source, "one", ["src/one.py", "src/secret/key.txt"]),
                         (1, "src/secret/key.txt\n"))

    def test_path_under_task_deny_write_is_printed(self):
        source = BASE.replace("FILES src/one.py", "FILES src/**\n  DENY write src/gen/**")
        self.assertEqual(self.run_audit(source, "one", ["src/a.py", "src/gen/b.py"]),
                         (1, "src/gen/b.py\n"))

    def test_path_inside_files_and_not_denied_passes(self):
        source = BASE.replace("  PERMIT run pytest", "  PERMIT run pytest\n  DENY write src/secret/**")
        self.assertEqual(self.run_audit(source, "one", ["src/one.py"]), (0, ""))

    def test_bom_file_lints(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bom.ste")
            with open(path, "w", encoding="utf-8-sig") as handle:
                handle.write(BASE)
            proc = subprocess.run([sys.executable, TOOL, path], capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))

    def test_unknown_task_exits_2(self):
        self.assertEqual(self.audit("nope", "")[0], 2)

    def test_invalid_plan_exits_2_on_stderr(self):
        proc = subprocess.run([sys.executable, TOOL, "x005-started-before-dependency.ste", "--audit", "two"],
                              cwd=FIXTURES, input="src/two.py\n", capture_output=True, text=True)
        self.assertEqual((proc.returncode, proc.stdout), (2, ""))
        self.assertIn("X005", proc.stderr)


if __name__ == "__main__":
    unittest.main()
