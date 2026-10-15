# Taskfile Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `taskfile-planning` skill: a stdlib linter for `Taskfile.ste` files, its format reference and golden example, a `SKILL.md` with the Author and Run modes, recorded scenario runs, and a README entry with a plugin version bump.

**Architecture:** `references/ste_lint.py` is one standard-library script. It parses the file into a model and reports structure errors (S). Only when the structure is valid does it run the semantic checks: graph (G), permissions (P), flow (F), STE (T), and status (X). Each later task adds one check family as a function, registers it in `SEMANTIC_CHECKS`, and adds its fixtures. `--json` and `--audit` give the Run-mode orchestrator everything it needs, so it never parses the file itself. `SKILL.md` holds both modes and the FLOW contract, and `references/format.md` holds the grammar and the error codes. Tests check that the two documents and the linter agree.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `re`, `unittest`), git worktrees, Markdown.

**Spec:** `docs/superpowers/specs/2026-09-12-taskfile-planning-design.md`

## Global Constraints

- Work on branch `skill/taskfile-planning`, created from `main`.
- Skill name `taskfile-planning`; location `skills/taskfile-planning/`.
- `ste_lint.py` uses the Python standard library only and is a single file.
- Linter interface: `python3 ste_lint.py <file> [--waves | --json | --audit TASK_ID]`. Exit 0 valid, exit 1 errors, exit 2 usage or IO error.
- Error line format, exactly: `file:line: CODE message`, one per line on stdout, sorted by line, then code.
- STE limits: 20 words or fewer per sentence; no rejected words; no filler words; no sentence that starts with an `-ing` word. Checked on GOAL, STEP, RULE, and BECAUSE text only.
- Branch and worktree names (amended, see "Spec amendments"): integration branch `taskfile/<plan>/integration`, integration worktree `<WORKTREES>/<plan>/integration`, task branch `taskfile/<plan>/tasks/<id>`, task worktree `<WORKTREES>/<plan>/tasks/<id>`.
- Tests follow repo style: `python3 -m unittest discover -s skills/taskfile-planning/tests -v`.
- Every commit message ends with the trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. The commit commands below pass it as a second `-m`.
- Code blocks in this plan are exact. Copy them byte for byte, including blank lines and indentation.

## Spec amendments

Planning found four problems in the spec. This plan resolves them as follows. Task 8 records them in the spec.

1. **Branch names cannot coexist.** Git cannot hold `taskfile/<plan>` and `taskfile/<plan>/<id>` at the same time (`cannot lock ref ... exists`). So the integration branch becomes `taskfile/<plan>/integration` and task branches become `taskfile/<plan>/tasks/<id>`. Task ids cannot collide with `integration`, because they sit under `tasks/`.
2. **The reset after a failed post-merge VERIFY would wipe the Taskfile.** If the main working tree had the integration branch checked out, `git reset --hard` would also discard the orchestrator's uncommitted STATUS edits. So merges and resets happen in a dedicated integration worktree. The main working tree keeps the base branch and the Taskfile.
3. **The orchestrator's own reason text fails the STE check.** `BECAUSE VERIFY failed after merge` contains "verify", which is a rejected word. So the word checks skip UPPERCASE words (directive names and acronyms). Lowercase "verify" is still rejected.
4. **Glob matching by hand is error-prone.** The new `--audit TASK_ID` flag reads `git diff --name-only` output on stdin and prints each path outside the task's FILES. The attribution step uses it.

Two smaller additions: an interrupted task's uncommitted changes are committed before its worktree is removed, so no work is lost. A second test file, `tests/test_skill_files.py`, checks the documents against the linter.

## Review Focus

1. **Text the orchestrator writes must pass the linter.** A Taskfile part-way through a run contains `completed_failure BECAUSE VERIFY failed after merge`. If that fails T002, a re-run refuses its own file. Pinned by `SteTest.test_orchestrator_reasons_pass` (Task 5) and `SkillDocTest.test_failure_reasons_pass_the_linter` (Task 8).
2. **A file part-way through a run must lint valid.** A file with `in_progress`, `completed_failure`, and a two-step `blocked BY` chain must exit 0, or Mode 2 cannot resume. Pinned by `StatusTest.test_interrupted_run_is_valid` and `valid-interrupted-run.ste` (Task 4).
3. **Ordinary DENY narrowing is valid, and undecidable globs are errors, never passes.** `PERMIT write src/**` with `DENY write src/secrets/**` must pass. `FILES src/o*.py` under `PERMIT write src/*.py` must fail with "cannot decide". Pinned by `test_deny_inside_a_permit_is_valid` and `test_p002_cannot_decide` (Task 3).
4. **Files written on Windows or with comments.** CRLF line endings, trailing comments, and `#` inside a path must parse correctly. Pinned by `CliTest.test_crlf_line_endings`, `test_comments_and_blank_lines`, and `test_hash_inside_a_word_is_not_a_comment` (Task 1).
5. **Every name in SKILL.md must be one git accepts and the linter emits.** Pinned by `SkillDocTest.test_names_match_the_linter` (Task 8) and by the worktree scenario (Task 9).

---
### Task 1: Linter parser and structure checks

**Files:**
- Create: `skills/taskfile-planning/references/ste_lint.py`
- Create: `skills/taskfile-planning/tests/test_ste_lint.py`
- Create: `skills/taskfile-planning/tests/fixtures/s001-plan-not-first.ste` through `s010-bad-arguments.ste` (10 files)

**Interfaces:**
- Produces, in `ste_lint.py`: `CODES: dict[str, str]`; `KEYWORDS: set[str]`; classes `Model` (fields `plan_name`, `plan_version`, `plan_line`, `global_block`, `tasks`, `waves`, `errors`; method `err(line, code, message)`), `Global`, and `Task` (fields `id`, `line`, `label`, `lines`, `depends`, `refs`, `goal`, `steps`, `files`, `outputs`, `skips`, `verify`, `permit`, `deny`, `status`, `deps`, `wave`); `parse(source) -> Model`; `SEMANTIC_CHECKS: list` of functions `check(model) -> None`; `lint(source) -> (Model, list[(line, code, message)])`; `main(argv) -> int`.
- Produces, in `test_ste_lint.py`: `BASE` (a valid Taskfile string), `run(name, *flags, cwd=FIXTURES) -> (exit, stdout, stderr)`, `errors(source) -> list[str]`, and `LintCase.assert_fixture(name, expected_lines)`. Later tasks add test classes above the `if __name__ == "__main__":` line.

- [ ] **Step 1: Create the branch**

```bash
git switch main
git pull --ff-only
git switch -c skill/taskfile-planning
```

- [ ] **Step 2: Create the structure fixtures**

Create `skills/taskfile-planning/tests/fixtures/s001-plan-not-first.ste` with:

```text
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
```

Create `skills/taskfile-planning/tests/fixtures/s002-unknown-keyword.ste` with:

```text
PLAN demo 1

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
  NOTE This keyword does not exist.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/s003-wrong-scope.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  GOAL Add the module.
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/s004-too-many.ste` with:

```text
PLAN demo 1

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
  GOAL Add the tests.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/s005-missing-required.ste` with:

```text
PLAN demo 1

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
END
```

Create `skills/taskfile-planning/tests/fixtures/s006-bad-id.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK One
  GOAL Add the module.
  FILES src/One.py
  VERIFY pytest tests/test_One.py
END
```

Create `skills/taskfile-planning/tests/fixtures/s007-duplicate-id.ste` with:

```text
PLAN demo 1

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

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/s008-block-not-closed.ste` with:

```text
PLAN demo 1

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
```

Create `skills/taskfile-planning/tests/fixtures/s009-two-globals.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

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
```

Create `skills/taskfile-planning/tests/fixtures/s010-bad-arguments.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 0
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
```

- [ ] **Step 3: Write the failing tests**

Create `skills/taskfile-planning/tests/test_ste_lint.py` with:

```python
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
```

- [ ] **Step 4: Run the tests to make sure they fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 1 test
FAILED (errors=1)
```

The error is `ModuleNotFoundError: No module named 'ste_lint'`.

- [ ] **Step 5: Write the linter**

Create `skills/taskfile-planning/references/ste_lint.py` with:

```python
#!/usr/bin/env python3
"""Validate a Taskfile.ste plan.

Usage: ste_lint.py FILE [--waves]

Exit 0: the file is valid. Exit 1: errors, one per line as FILE:LINE: CODE message.
Exit 2: usage or IO error. Standard library only.
"""
import argparse
import re
import sys

CODES = {
    "S001": "PLAN must be the first directive and appear once",
    "S002": "unknown keyword",
    "S003": "directive outside its allowed scope",
    "S004": "directive appears more times than allowed",
    "S005": "required directive or block missing",
    "S006": "task id has the wrong format",
    "S007": "duplicate task id",
    "S008": "block not closed, or END without a block",
    "S009": "the file needs exactly one GLOBAL block",
    "S010": "directive arguments have the wrong form",
}

ID_RE = re.compile(r"[a-z][a-z0-9-]*\Z")
REF_RE = re.compile(r"\$\{([^}.]*)\.([^}]*)\}")
ACTIONS = ("read", "write", "run", "network", "spawn")
STATES = ("pending", "in_progress", "completed_success", "completed_failure", "blocked")
BUILTINS = ("read", "tasklist", "heartbeat", "verify", "report")

GLOBAL_LIMITS = {  # count key: (minimum, maximum); None means no maximum
    "ENV": (0, None), "STACK": (0, None), "TOOL": (1, None), "FLOW": (1, 1),
    "RULE": (0, None), "AGENTS": (1, 1), "HEARTBEAT": (0, 1),
    "COMPACT when": (0, 1), "COMPACT after": (0, 1), "TASKLIST": (0, 1),
    "WORKTREES": (0, 1), "PERMIT": (0, None), "DENY": (0, None),
}
TASK_LIMITS = {
    "PERMIT": (0, None), "DENY": (0, None), "DEPENDS": (0, None), "GOAL": (1, 1),
    "STEP": (0, None), "FILES": (1, None), "OUTPUT": (0, None), "SKIP": (0, None),
    "VERIFY": (1, None), "STATUS": (0, 1),
}
KEYWORDS = ({"PLAN", "GLOBAL", "TASK", "END"} | {k.split()[0] for k in GLOBAL_LIMITS}
            | set(TASK_LIMITS))


class Block:
    def __init__(self, line):
        self.line = line
        self.lines = []  # verbatim source lines, from the opening line to END
        self.counts = {}


class Global(Block):
    label = "GLOBAL"
    limits = GLOBAL_LIMITS
    words = {k.split()[0] for k in GLOBAL_LIMITS}

    def __init__(self, line):
        super().__init__(line)
        self.env, self.stack, self.tools, self.flow, self.rules = {}, [], [], [], []
        self.flow_line = line
        self.agents, self.heartbeat, self.compact_pct = None, None, None
        self.compact_after, self.tasklist, self.worktrees = False, False, ".worktrees"
        self.permit, self.deny = [], []  # (action, [globs], line)


class Task(Block):
    limits = TASK_LIMITS
    words = set(TASK_LIMITS)

    def __init__(self, task_id, line):
        super().__init__(line)
        self.id = task_id
        self.label = "TASK " + task_id
        self.depends, self.refs = [], []  # (id, line), (id, key, line)
        self.goal, self.steps, self.files = None, [], []  # (text, line), ..., (glob, line)
        self.outputs, self.skips, self.verify = {}, [], []  # key: value, (step, reason, line)
        self.permit, self.deny = [], []
        self.status = None  # {"state", "because", "by", "line"}
        self.deps, self.wave = [], None


class Model:
    def __init__(self):
        self.plan_name, self.plan_version, self.plan_line = None, None, None
        self.global_block, self.tasks, self.waves = None, [], []
        self.errors = []

    def err(self, line, code, message):
        self.errors.append((line, code, message))


def strip_comment(raw):
    match = re.search(r"(^|\s)#", raw)
    return raw[:match.start()] if match else raw


def count(model, block, key, line):
    block.counts[key] = block.counts.get(key, 0) + 1
    maximum = block.limits[key][1]
    if maximum is not None and block.counts[key] > maximum:
        model.err(line, "S004", f"{key} can appear only once in {block.label}")


def finish(model, block):
    for key, (minimum, _) in block.limits.items():
        if block.counts.get(key, 0) < minimum:
            model.err(block.line, "S005", f"{block.label} needs {key}")


def parse_global(model, g, word, rest, n):
    bad = lambda form: model.err(n, "S010", f"{word} needs {form}")
    if word == "ENV":
        pairs = [p.partition("=") for p in rest.split()]
        if any(not k or not sep for k, sep, _ in pairs):
            return bad("<key>=<value> pairs")
        g.env.update({k: v for k, _, v in pairs})
    elif word == "STACK":
        g.stack.extend(rest.split())
    elif word == "TOOL":
        parts = rest.split(None, 1)
        if len(parts) != 2 or not ID_RE.match(parts[0]):
            return bad("<role> <command>")
        g.tools.append((parts[0], parts[1], n))
    elif word == "FLOW":
        steps = [s.strip() for s in rest.split("->")]
        if any(not s or len(s.split()) != 1 for s in steps):
            return bad("steps separated by ->")
        g.flow, g.flow_line = steps, n
    elif word == "RULE":
        g.rules.append((rest, n))
    elif word == "AGENTS":
        match = re.fullmatch(r"max\s+(\d+)", rest)
        if not match or int(match.group(1)) < 1:
            return bad("max <n> with n >= 1")
        g.agents = int(match.group(1))
    elif word == "HEARTBEAT":
        match = re.fullmatch(r"every\s+(\d+)\s+steps?", rest)
        if not match or int(match.group(1)) < 1:
            return bad("every <n> steps with n >= 1")
        g.heartbeat = int(match.group(1))
    elif word == "COMPACT":
        match = re.fullmatch(r"when\s+context\s*>\s*(\d+)%", rest)
        if match and 1 <= int(match.group(1)) <= 99:
            g.compact_pct = int(match.group(1))
            count(model, g, "COMPACT when", n)
        elif re.fullmatch(r"after\s+wave", rest):
            g.compact_after = True
            count(model, g, "COMPACT after", n)
        else:
            return bad("when context > <pct>% or after wave")
    elif word == "TASKLIST":
        if rest not in ("on", "off"):
            return bad("on or off")
        g.tasklist = rest == "on"
    elif word == "WORKTREES":
        if len(rest.split()) != 1 or rest.startswith("/") or ".." in rest.split("/"):
            return bad("one relative directory without ..")
        g.worktrees = rest
    elif word in ("PERMIT", "DENY"):
        parse_permission(model, g, word, rest, n)


def parse_permission(model, block, word, rest, n):
    parts = rest.split()
    if parts[0] not in ACTIONS:
        return model.err(n, "S010", f"{word} needs an action: {', '.join(ACTIONS)}")
    globs = parts[1:]
    if not globs:
        if parts[0] in ("read", "write", "run"):
            return model.err(n, "S010", f"{word} {parts[0]} needs at least one glob")
        globs = ["**"]
    (block.permit if word == "PERMIT" else block.deny).append((parts[0], globs, n))


def parse_task(model, t, word, rest, n):
    bad = lambda form: model.err(n, "S010", f"{word} needs {form}")
    for ref_id, ref_key in REF_RE.findall(rest):
        t.refs.append((ref_id, ref_key, n))
    if word == "DEPENDS":
        t.depends.extend((d, n) for d in rest.split())
    elif word == "GOAL":
        t.goal = (rest, n)
    elif word == "STEP":
        t.steps.append((rest, n))
    elif word == "FILES":
        t.files.extend((f, n) for f in rest.split())
    elif word == "OUTPUT":
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(\S.*)", rest)
        if not match:
            return bad("<key> = <value>")
        if match.group(1) in t.outputs:
            return bad(f"a unique key; {match.group(1)} appears twice")
        t.outputs[match.group(1)] = match.group(2)
    elif word == "SKIP":
        match = re.fullmatch(r"(\S+)\s+BECAUSE\s+(\S.*)", rest)
        if not match:
            return bad("<flow-step> BECAUSE <sentence>")
        t.skips.append((match.group(1), match.group(2), n))
    elif word == "VERIFY":
        t.verify.append((rest, n))
    elif word in ("PERMIT", "DENY"):
        parse_permission(model, t, word, rest, n)
    elif word == "STATUS":
        match = re.fullmatch(r"(\S+)(?:\s+BECAUSE\s+(\S.*?))?(?:\s+BY\s+(\S+))?", rest)
        if not match:
            return bad("<state> [BECAUSE <sentence>] [BY <id>]")
        t.status = {"state": match.group(1), "because": match.group(2),
                    "by": match.group(3), "line": n}


def parse(source):
    model = Model()
    err = model.err
    block, seen, task_blocks = None, False, 0
    ids = set()
    for n, raw in enumerate(source.splitlines(), 1):
        text = strip_comment(raw).strip()
        if block is not None:
            block.lines.append(raw)
        if not text:
            continue
        parts = text.split(None, 1)
        word, rest = parts[0], (parts[1].strip() if len(parts) > 1 else "")
        first, seen = not seen, True
        if word == "PLAN":
            if not first:
                err(n, "S001", "PLAN must appear once, as the first directive")
                continue
            args = rest.split()
            if len(args) != 2 or not ID_RE.match(args[0]):
                err(n, "S001", "PLAN needs a name that matches [a-z][a-z0-9-]* and a version")
            else:
                model.plan_name, model.plan_version = args
            model.plan_line = n
            continue
        if first:
            err(n, "S001", "the first directive must be PLAN <name> <version>")
        if word not in KEYWORDS:
            err(n, "S002", f"unknown keyword {word}")
            continue
        if word in ("GLOBAL", "TASK"):
            if block is not None:
                err(block.line, "S008", f"{block.label} is not closed before line {n}")
                finish(model, block)
            if word == "GLOBAL":
                block = Global(n)
                if rest:
                    err(n, "S010", "GLOBAL takes no arguments")
                if model.global_block is not None:
                    err(n, "S009", "the file needs exactly one GLOBAL block")
                else:
                    model.global_block = block
            else:
                task_blocks += 1
                block = Task(rest, n)
                if not ID_RE.match(rest):
                    err(n, "S006", f'task id "{rest}" must match [a-z][a-z0-9-]*')
                elif rest in ids:
                    err(n, "S007", f"duplicate task id {rest}")
                else:
                    ids.add(rest)
                    model.tasks.append(block)
            block.lines.append(raw)
            continue
        if word == "END":
            if block is None:
                err(n, "S008", "END without an open block")
                continue
            finish(model, block)
            block = None
            continue
        if block is None:
            err(n, "S003", f"{word} must be inside a GLOBAL or TASK block")
            continue
        if word not in block.words:
            err(n, "S003", f"{word} is not allowed in {block.label}")
            continue
        if word != "COMPACT":
            count(model, block, word, n)
        if not rest:
            err(n, "S010", f"{word} needs arguments")
            continue
        if isinstance(block, Global):
            parse_global(model, block, word, rest, n)
        else:
            parse_task(model, block, word, rest, n)
    if block is not None:
        err(block.line, "S008", f"{block.label} is not closed")
        finish(model, block)
    if not seen:
        err(1, "S001", "the first directive must be PLAN <name> <version>")
    if model.global_block is None:
        err(model.plan_line or 1, "S009", "the file needs exactly one GLOBAL block")
    if task_blocks == 0:
        err(model.plan_line or 1, "S005", "the file needs at least one TASK block")
    return model


SEMANTIC_CHECKS = []


def lint(source):
    """Return (model, errors). errors is a sorted list of (line, code, message)."""
    model = parse(source)
    if not model.errors:
        for check in SEMANTIC_CHECKS:
            check(model)
    return model, sorted(model.errors, key=lambda e: (e[0], e[1]))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a Taskfile.ste plan.")
    parser.add_argument("file")
    parser.add_argument("--waves", action="store_true", help="print one line per wave")
    args = parser.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"{args.file}: {exc}", file=sys.stderr)
        return 2
    model, errors = lint(source)
    if errors:
        for line, code, message in errors:
            print(f"{args.file}:{line}: {code} {message}")
        return 1
    if args.waves:
        for number, wave in enumerate(model.waves, 1):
            print(f"wave {number}: {' '.join(wave)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 20 tests
OK
```


- [ ] **Step 7: Commit**

```bash
git add skills/taskfile-planning/references/ste_lint.py skills/taskfile-planning/tests
git commit -m "Add the taskfile-planning linter parser and structure checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: Dependency graph and waves

**Files:**
- Modify: `skills/taskfile-planning/references/ste_lint.py`
- Modify: `skills/taskfile-planning/tests/test_ste_lint.py`
- Create: `skills/taskfile-planning/references/example.ste`
- Create: `g001-unknown-depends.ste`, `g002-unknown-ref-task.ste`, `g003-unknown-ref-key.ste`, `g004-cycle.ste`, `g005-files-overlap.ste`, `valid-three-waves.ste` in `skills/taskfile-planning/tests/fixtures/`

**Interfaces:**
- Consumes: `Model`, `Task.depends`, `Task.refs`, `Task.outputs`, `Task.files`, `SEMANTIC_CHECKS` from Task 1.
- Produces: `has_wild(glob) -> bool`, `literal_prefix(glob) -> str`, `glob_regex(glob) -> re.Pattern`, `globs_overlap(a, b) -> bool`, and `check_graph(model)`. `check_graph` fills `Task.deps` (direct dependency ids, from DEPENDS and `${id.key}`), `Task.wave`, and `Model.waves`. It must run first: Task 4's status checks read `Task.deps`.

- [ ] **Step 1: Create the fixtures**

Create `skills/taskfile-planning/tests/fixtures/g001-unknown-depends.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  DEPENDS two
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/g002-unknown-ref-task.ste` with:

```text
PLAN demo 1

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
  STEP Import ${two.module} in the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/g003-unknown-ref-key.ste` with:

```text
PLAN demo 1

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
  OUTPUT module = one
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END

TASK two
  GOAL Add the module.
  STEP Import ${one.package} in the module.
  FILES src/two.py
  VERIFY pytest tests/test_two.py
END
```

Create `skills/taskfile-planning/tests/fixtures/g004-cycle.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  DEPENDS two
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END

TASK two
  DEPENDS one
  GOAL Add the module.
  FILES src/two.py
  VERIFY pytest tests/test_two.py
END
```

Create `skills/taskfile-planning/tests/fixtures/g005-files-overlap.ste` with:

```text
PLAN demo 1

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

TASK two
  GOAL Add the module.
  FILES src/*.py
  VERIFY pytest tests/test_two.py
END
```

Create `skills/taskfile-planning/tests/fixtures/valid-three-waves.ste` with:

```text
PLAN three-waves 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK model
  GOAL Add the data model.
  FILES src/model.py
  OUTPUT class = Record
  VERIFY pytest tests/test_model.py
END

TASK docs
  GOAL Add the module docstrings.
  FILES src/docs.py
  VERIFY pytest tests/test_docs.py
END

TASK store
  GOAL Save each ${model.class} to disk.
  FILES src/store.py
  VERIFY pytest tests/test_store.py
END

TASK api
  DEPENDS store
  GOAL Add the read endpoint.
  FILES src/api.py
  VERIFY pytest tests/test_api.py
END
```

- [ ] **Step 2: Write the failing tests**

In `skills/taskfile-planning/tests/test_ste_lint.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 28 tests
FAILED (failures=8)
```

Only the new tests fail. The tests from earlier tasks still pass.

- [ ] **Step 4: Implement the checks**

The golden example also goes into `references/example.ste`. It is the spec's example.

Create `skills/taskfile-planning/references/example.ste` with:

```text
PLAN health-check 1

GLOBAL
  ENV        os=linux python=3.12
  STACK      fastapi postgres
  AGENTS     max 3
  PERMIT     read **
  PERMIT     write src/** tests/** migrations/**
  PERMIT     run uv pytest ruff
  DENY       network
  TOOL edit  hashline
  TOOL fmt   ruff format
  TOOL build uv build
  FLOW       read -> tasklist -> edit -> fmt -> build -> verify -> report
  RULE       Do not change files outside FILES.
  HEARTBEAT  every 2 steps
  COMPACT    after wave
  TASKLIST   on
END

TASK schema
  GOAL      Add the table "health_log".
  FILES     migrations/004_health.sql
  OUTPUT    table = health_log
  VERIFY    pytest tests/test_migrations.py
  STATUS    completed_success
END

TASK endpoint
  DEPENDS   schema
  GOAL      Add the GET /health endpoint.
  STEP      Write one row to ${schema.table} for each request.
  FILES     src/api.py tests/test_health.py
  SKIP      build BECAUSE This task does not change the package.
  VERIFY    pytest tests/test_health.py
END
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
}

ID_RE = re.compile(
```

Replace with:

```python
    "G001": "DEPENDS names an unknown task",
    "G002": "${id.key} names an unknown task",
    "G003": "${id.key} names an OUTPUT the task does not declare",
    "G004": "dependency cycle",
    "G005": "FILES overlap within a wave",
}

ID_RE = re.compile(
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
SEMANTIC_CHECKS = []
```

Replace with:

```python
WILD = re.compile(r"[*?]")


def has_wild(glob):
    return bool(WILD.search(glob))


def literal_prefix(glob):
    match = WILD.search(glob)
    return glob[:match.start()] if match else glob


def glob_regex(glob):
    """Translate a glob: ** crosses directories, * and ? stay inside one directory."""
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def globs_overlap(a, b):
    """Conservative: two wildcard globs overlap when one literal prefix starts the other."""
    if not has_wild(a) and not has_wild(b):
        return a == b
    if not has_wild(a):
        return bool(glob_regex(b).match(a))
    if not has_wild(b):
        return bool(glob_regex(a).match(b))
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def check_graph(model):
    """Resolve each task's dependencies, check them, and compute the waves."""
    err = model.err
    by_id = {t.id: t for t in model.tasks}
    for t in model.tasks:
        for dep, line in t.depends:
            if dep not in by_id:
                err(line, "G001", f"DEPENDS names unknown task {dep}")
        for ref_id, ref_key, line in t.refs:
            ref = "${" + ref_id + "." + ref_key + "}"
            if ref_id not in by_id:
                err(line, "G002", f"{ref} names unknown task {ref_id}")
            elif ref_key not in by_id[ref_id].outputs:
                err(line, "G003", f"{ref}: task {ref_id} has no OUTPUT {ref_key}")
        for dep in [d for d, _ in t.depends] + [r for r, _, _ in t.refs]:
            if dep in by_id and dep not in t.deps:
                t.deps.append(dep)
    progress = True
    while progress:
        progress = False
        for t in model.tasks:
            if t.wave is None and all(by_id[d].wave is not None for d in t.deps):
                t.wave = 1 + max((by_id[d].wave for d in t.deps), default=0)
                progress = True
    waiting = [t for t in model.tasks if t.wave is None]
    if waiting:
        path, t = [], waiting[0]
        while t.id not in path:
            path.append(t.id)
            t = next(by_id[d] for d in t.deps if by_id[d].wave is None)
        cycle = path[path.index(t.id):] + [t.id]
        err(by_id[cycle[0]].line, "G004", "dependency cycle: " + " -> ".join(cycle))
        return
    model.waves = [[t.id for t in model.tasks if t.wave == number]
                   for number in range(1, max(t.wave for t in model.tasks) + 1)]
    for number, wave in enumerate(model.waves, 1):
        tasks = [by_id[i] for i in wave]
        for i, first in enumerate(tasks):
            for second in tasks[i + 1:]:
                for glob_a, _ in first.files:
                    for glob_b, line in second.files:
                        if globs_overlap(glob_a, glob_b):
                            err(line, "G005", f"FILES {glob_b} overlaps FILES {glob_a} "
                                              f"of task {first.id} in wave {number}")


SEMANTIC_CHECKS = [check_graph]
```

- [ ] **Step 5: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 28 tests
OK
```


- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/references skills/taskfile-planning/tests
git commit -m "Add the taskfile-planning dependency graph and wave checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 3: Permission checks

**Files:**
- Modify: `skills/taskfile-planning/references/ste_lint.py`
- Modify: `skills/taskfile-planning/tests/test_ste_lint.py`
- Create: `p001-permit-not-narrower.ste`, `p002-files-outside-write.ste`, `p003-permit-denied.ste`, `p004-permit-spawn.ste`, `p005-verify-not-permitted.ste` in `skills/taskfile-planning/tests/fixtures/`

**Interfaces:**
- Consumes: `has_wild`, `literal_prefix`, `glob_regex` from Task 2; `Global.permit`, `Global.deny`, `Task.permit`, `Task.deny`, `Task.files`, `Task.verify` from Task 1.
- Produces: `glob_contains(outer, inner) -> True | False | None` (None means it cannot decide), `inside(glob, outers) -> True | False | None`, `group(entries) -> dict[action, list[glob]]`, and `check_permissions(model)`. Task 6 uses `group` in `to_json`.

- [ ] **Step 1: Create the fixtures**

Create `skills/taskfile-planning/tests/fixtures/p001-permit-not-narrower.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  PERMIT write docs/** src/one.py
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/p002-files-outside-write.ste` with:

```text
PLAN demo 1

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
  FILES docs/one.md
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/p003-permit-denied.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  DENY write tests/**
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/p004-permit-spawn.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  PERMIT spawn
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/p005-verify-not-permitted.ste` with:

```text
PLAN demo 1

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
  VERIFY make test
END
```

- [ ] **Step 2: Write the failing tests**

In `skills/taskfile-planning/tests/test_ste_lint.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 36 tests
FAILED (failures=7)
```

Only the new tests fail. The tests from earlier tasks still pass.

- [ ] **Step 4: Implement the checks**

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
}

ID_RE = re.compile(
```

Replace with:

```python
    "P001": "task PERMIT is not inside a GLOBAL PERMIT",
    "P002": "FILES glob is not inside the write PERMIT",
    "P003": "PERMIT or FILES glob is forbidden by a DENY",
    "P004": "PERMIT spawn is not allowed",
    "P005": "VERIFY command is not inside PERMIT run",
}

ID_RE = re.compile(
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
SEMANTIC_CHECKS = [check_graph]
```

Replace with:

```python
def glob_contains(outer, inner):
    """True when outer matches every path inner matches. None when it cannot decide."""
    if outer == inner:
        return True
    if not has_wild(inner):
        return bool(glob_regex(outer).match(inner))
    if not has_wild(outer):
        return False
    prefix = literal_prefix(outer)
    if outer[len(prefix):] == "**" and (prefix == "" or prefix.endswith("/")):
        return inner.startswith(prefix)
    return None


def inside(glob, outers):
    results = [glob_contains(outer, glob) for outer in outers]
    if True in results:
        return True
    return None if None in results else False


def group(entries):
    """Map each action to its globs, from (action, globs, line) entries."""
    out = {}
    for action, globs, _ in entries:
        out.setdefault(action, []).extend(globs)
    return out


def check_permissions(model):
    err = model.err
    g = model.global_block
    global_permit, global_deny = group(g.permit), group(g.deny)

    def check_deny(permits, denies):
        for action, globs, line in permits:
            for glob in globs:
                for deny in denies.get(action, []):
                    if action != "spawn" and glob_contains(deny, glob) is True:
                        err(line, "P003", f"PERMIT {action} {glob} is forbidden by DENY {action} {deny}")
                        break

    for action, _, line in g.permit:
        if action == "spawn":
            err(line, "P004", "PERMIT spawn is not allowed; tasks never start agents")
    check_deny(g.permit, global_deny)
    for t in model.tasks:
        denies = group(g.deny + t.deny)
        for action, globs, line in t.permit:
            if action == "spawn":
                err(line, "P004", "PERMIT spawn is not allowed; tasks never start agents")
                continue
            for glob in globs:
                result = inside(glob, global_permit.get(action, []))
                if result is False:
                    err(line, "P001", f"PERMIT {action} {glob} is not inside a GLOBAL PERMIT {action}")
                elif result is None:
                    err(line, "P001", f"cannot decide whether PERMIT {action} {glob} "
                                      f"is inside a GLOBAL PERMIT {action}")
        check_deny(t.permit, denies)
        task_permit = group(t.permit)
        writes = task_permit.get("write") or global_permit.get("write", [])
        runs = task_permit.get("run") or global_permit.get("run", [])
        for glob, line in t.files:
            result = inside(glob, writes)
            if result is False:
                err(line, "P002", f"FILES {glob} is not inside PERMIT write")
            elif result is None:
                err(line, "P002", f"cannot decide whether FILES {glob} is inside PERMIT write")
            for deny in denies.get("write", []):
                if glob_contains(deny, glob) is True:
                    err(line, "P003", f"FILES {glob} is forbidden by DENY write {deny}")
                    break
        for command, line in t.verify:
            program = command.split()[0]
            if inside(program, runs) is not True:
                err(line, "P005", f"VERIFY command {program} is not inside PERMIT run")
            elif any(glob_contains(deny, program) is True for deny in denies.get("run", [])):
                err(line, "P005", f"VERIFY command {program} is forbidden by DENY run")


SEMANTIC_CHECKS = [check_graph, check_permissions]
```

- [ ] **Step 5: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 36 tests
OK
```


- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/references skills/taskfile-planning/tests
git commit -m "Add the taskfile-planning permission checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 4: Flow and status checks

**Files:**
- Modify: `skills/taskfile-planning/references/ste_lint.py`
- Modify: `skills/taskfile-planning/tests/test_ste_lint.py`
- Create: `f001-unknown-flow-step.ste`, `f002-skip-not-in-flow.ste`, `f003-skip-verify.ste`, `f004-duplicate-tool-role.ste`, `x001-unknown-state.ste`, `x002-failure-without-because.ste`, `x003-blocked-without-by.ste`, `x004-by-not-failed-dependency.ste`, `x005-started-before-dependency.ste`, `valid-interrupted-run.ste` in `skills/taskfile-planning/tests/fixtures/`

**Interfaces:**
- Consumes: `Global.tools`, `Global.flow`, `Global.flow_line`, `Task.skips`, `Task.status`, `Task.deps` (filled by `check_graph`), `BUILTINS`, `STATES` from Tasks 1 and 2.
- Produces: `check_flow(model)` and `check_status(model)`.

- [ ] **Step 1: Create the fixtures**

Create `skills/taskfile-planning/tests/fixtures/f001-unknown-flow-step.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> lint -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/f002-skip-not-in-flow.ste` with:

```text
PLAN demo 1

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
  SKIP build BECAUSE The task does not change the package.
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/f003-skip-verify.ste` with:

```text
PLAN demo 1

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
  SKIP verify BECAUSE The task has no tests.
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/f004-duplicate-tool-role.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  TOOL edit sed
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Add the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/x001-unknown-state.ste` with:

```text
PLAN demo 1

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
  STATUS done
END
```

Create `skills/taskfile-planning/tests/fixtures/x002-failure-without-because.ste` with:

```text
PLAN demo 1

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
  STATUS completed_failure
END
```

Create `skills/taskfile-planning/tests/fixtures/x003-blocked-without-by.ste` with:

```text
PLAN demo 1

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
  STATUS completed_failure BECAUSE The tests failed.
END

TASK two
  DEPENDS one
  GOAL Add the module.
  FILES src/two.py
  VERIFY pytest tests/test_two.py
  STATUS blocked
END
```

Create `skills/taskfile-planning/tests/fixtures/x004-by-not-failed-dependency.ste` with:

```text
PLAN demo 1

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
  STATUS completed_success
END

TASK two
  DEPENDS one
  GOAL Add the module.
  FILES src/two.py
  VERIFY pytest tests/test_two.py
  STATUS blocked BY one
END
```

Create `skills/taskfile-planning/tests/fixtures/x005-started-before-dependency.ste` with:

```text
PLAN demo 1

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

TASK two
  DEPENDS one
  GOAL Add the module.
  FILES src/two.py
  VERIFY pytest tests/test_two.py
  STATUS completed_success
END
```

Create `skills/taskfile-planning/tests/fixtures/valid-interrupted-run.ste` with:

```text
PLAN interrupted 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK model
  GOAL Add the data model.
  FILES src/model.py
  VERIFY pytest tests/test_model.py
  STATUS completed_success
END

TASK store
  DEPENDS model
  GOAL Add the storage layer.
  FILES src/store.py
  VERIFY pytest tests/test_store.py
  STATUS completed_failure BECAUSE VERIFY failed after merge.
END

TASK api
  DEPENDS store
  GOAL Add the read endpoint.
  FILES src/api.py
  VERIFY pytest tests/test_api.py
  STATUS blocked BY store
END

TASK client
  DEPENDS api
  GOAL Add the client.
  FILES src/client.py
  VERIFY pytest tests/test_client.py
  STATUS blocked BY api
END

TASK cli
  DEPENDS model
  GOAL Add the command line.
  FILES src/cli.py
  VERIFY pytest tests/test_cli.py
  STATUS in_progress
END
```

- [ ] **Step 2: Write the failing tests**

In `skills/taskfile-planning/tests/test_ste_lint.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 46 tests
FAILED (failures=9)
```

Only the new tests fail. The tests from earlier tasks still pass.

- [ ] **Step 4: Implement the checks**

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
}

ID_RE = re.compile(
```

Replace with:

```python
    "F001": "FLOW step is not a TOOL role or a built-in step",
    "F002": "SKIP names a step that is not in FLOW",
    "F003": "SKIP of verify or report",
    "F004": "TOOL role declared twice",
    "X001": "unknown state",
    "X002": "BECAUSE must go with completed_failure, and only with it",
    "X003": "BY must go with blocked, and only with it",
    "X004": "BY names a task that is not a failed or blocked dependency",
    "X005": "task started or finished before a dependency succeeded",
}

ID_RE = re.compile(
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
SEMANTIC_CHECKS = [check_graph, check_permissions]
```

Replace with:

```python
def check_flow(model):
    err = model.err
    g = model.global_block
    roles = set()
    for role, _, line in g.tools:
        if role in roles:
            err(line, "F004", f"TOOL role {role} is declared twice")
        roles.add(role)
    for step in g.flow:
        if step not in roles and step not in BUILTINS:
            err(g.flow_line, "F001", f"FLOW step {step} is not a TOOL role or a built-in step")
    for t in model.tasks:
        for step, _, line in t.skips:
            if step in ("verify", "report"):
                err(line, "F003", f"SKIP {step} is not allowed; verify and report always run")
            elif step not in g.flow:
                err(line, "F002", f"SKIP {step} names a step that is not in FLOW")


def check_status(model):
    err = model.err
    by_id = {t.id: t for t in model.tasks}

    def state(t):
        return t.status["state"] if t.status else "pending"

    for t in model.tasks:
        s = t.status
        if s is None:
            continue
        line = s["line"]
        if s["state"] not in STATES:
            err(line, "X001", f"unknown state {s['state']}; use one of: {', '.join(STATES)}")
            continue
        if s["state"] == "completed_failure" and not s["because"]:
            err(line, "X002", "completed_failure needs BECAUSE <sentence>")
        if s["because"] and s["state"] != "completed_failure":
            err(line, "X002", "BECAUSE is allowed only with completed_failure")
        if s["state"] == "blocked" and not s["by"]:
            err(line, "X003", "blocked needs BY <id>")
        if s["by"] and s["state"] != "blocked":
            err(line, "X003", "BY is allowed only with blocked")
        if s["by"] and s["state"] == "blocked":
            if s["by"] not in t.deps:
                err(line, "X004", f"BY {s['by']} is not a dependency of task {t.id}")
            elif state(by_id[s["by"]]) not in ("completed_failure", "blocked"):
                err(line, "X004", f"BY {s['by']} names a task in state {state(by_id[s['by']])}")
        if s["state"] in ("in_progress", "completed_success", "completed_failure"):
            for dep in t.deps:
                if state(by_id[dep]) != "completed_success":
                    err(line, "X005", f"task {t.id} is {s['state']} but dependency {dep} "
                                      f"is {state(by_id[dep])}")


SEMANTIC_CHECKS = [check_graph, check_permissions, check_flow, check_status]
```

- [ ] **Step 5: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 46 tests
OK
```


- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/references skills/taskfile-planning/tests
git commit -m "Add the taskfile-planning flow and status checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 5: STE checks

**Files:**
- Modify: `skills/taskfile-planning/references/ste_lint.py`
- Modify: `skills/taskfile-planning/tests/test_ste_lint.py`
- Create: `t001-long-sentence.ste`, `t002-rejected-word.ste`, `t003-filler-word.ste`, `t004-leading-gerund.ste` in `skills/taskfile-planning/tests/fixtures/`

**Interfaces:**
- Consumes: `Global.rules`, `Task.goal`, `Task.steps`, `Task.skips`, `Task.status` from Task 1.
- Produces: the STE tables `MAX_WORDS`, `REPLACE`, `DELETE`, `GERUND_OK` at the top of the script; `prose(model)` yielding `(line, text)`; `ste_problems(text) -> list[(code, message)]`; and `check_ste(model)`. Task 8's tests call `ste_problems`.

- [ ] **Step 1: Create the fixtures**

Create `skills/taskfile-planning/tests/fixtures/t001-long-sentence.ste` with:

```text
PLAN demo 1

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
  STEP Add one function that reads the config file and returns a dictionary with one entry for each section in the file.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/t002-rejected-word.ste` with:

```text
PLAN demo 1

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
  STEP Ensure that the module has a docstring.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/t003-filler-word.ste` with:

```text
PLAN demo 1

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
  STEP Just add one function to the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

Create `skills/taskfile-planning/tests/fixtures/t004-leading-gerund.ste` with:

```text
PLAN demo 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/** tests/**
  PERMIT run pytest
  TOOL edit hashline
  FLOW read -> edit -> verify -> report
END

TASK one
  GOAL Adding the module.
  FILES src/one.py
  VERIFY pytest tests/test_one.py
END
```

- [ ] **Step 2: Write the failing tests**

In `skills/taskfile-planning/tests/test_ste_lint.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 55 tests
FAILED (failures=4, errors=5)
```

Only the new tests fail. The tests from earlier tasks still pass.

- [ ] **Step 4: Implement the checks**

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
CODES = {
```

Replace with:

```python
# STE rules: the countable subset of skills/nfc/references/style-rules.md.
MAX_WORDS = 20
REPLACE = [  # (rejected forms, approved word)
    (("ensure", "ensures", "ensured"), "make sure"),
    (("verify", "verifies", "verified"), "make sure"),
    (("confirm", "confirms", "confirmed"), "make sure"),
    (("validate", "validates", "validated"), "make sure"),
    (("utilize", "utilizes", "utilized", "employ", "employs", "employed"), "use"),
    (("commence", "commences", "commenced", "initiate", "initiates", "initiated"), "start"),
    (("terminate", "terminates", "terminated", "cease", "ceases", "ceased"), "stop"),
    (("endeavour", "endeavor", "attempt", "attempts", "attempted"), "try"),
    (("accomplish", "accomplishes", "accomplished", "execute", "executes", "executed",
      "perform", "performs", "performed"), "do"),
    (("obtain", "obtains", "obtained", "acquire", "acquires", "acquired",
      "procure", "procures", "procured"), "get"),
    (("require", "requires", "required", "necessitate", "necessitates"), "need"),
    (("assist", "assists", "assisted", "aid"), "help"),
    (("permit", "permits", "permitted"), "let"),
    (("prior to",), "before"),
    (("subsequent to", "following"), "after"),
    (("in order to", "so as to"), "to"),
    (("in the event that",), "if"),
    (("at this point in time",), "now"),
    (("in the vicinity of",), "near"),
    (("a number of", "numerous"), "many"),
    (("the majority of",), "most"),
    (("approximately",), "about"),
    (("sufficient",), "enough"),
    (("additional",), "more"),
    (("initial",), "first"),
    (("is able to", "has the ability to"), "can"),
    (("it is necessary that you",), "you must"),
    (("it is recommended that",), "we recommend that you"),
    (("there is a possibility that",), "possibly"),
    (("due to the fact that",), "because"),
    (("in spite of the fact that",), "although"),
]
DELETE = ("basically", "essentially", "actually", "really", "very", "quite", "simply",
          "just", "obviously", "clearly", "of course", "needless to say",
          "it should be noted that", "as you may know", "at the end of the day")
GERUND_OK = {"bring", "string", "spring", "thing", "nothing", "something", "anything",
             "everything", "during", "morning", "evening", "ceiling"}

CODES = {
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
}

ID_RE = re.compile(
```

Replace with:

```python
    "T001": "sentence has more than 20 words",
    "T002": "rejected word; use the approved word",
    "T003": "word that adds no meaning",
    "T004": "sentence starts with an -ing word",
}

ID_RE = re.compile(
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
SEMANTIC_CHECKS = [check_graph, check_permissions, check_flow, check_status]
```

Replace with:

```python
def prose(model):
    """Yield (line, text) for every GOAL, STEP, RULE, and BECAUSE text."""
    for text, line in model.global_block.rules:
        yield line, text
    for t in model.tasks:
        yield t.goal[1], t.goal[0]
        for text, line in t.steps:
            yield line, text
        for _, reason, line in t.skips:
            yield line, reason
        if t.status and t.status["because"]:
            yield t.status["line"], t.status["because"]


def ste_problems(text):
    """Return (code, message) pairs for the countable STE rules."""
    clean = re.sub(r'"[^"]*"|`[^`]*`|\$\{[^}]*\}', "X", text)
    problems = []
    for sentence in re.split(r"(?<=[.!?])\s+", clean.strip()):
        words = sentence.split()
        if not words:
            continue
        if len(words) > MAX_WORDS:
            problems.append(("T001", f"sentence has {len(words)} words; the limit is {MAX_WORDS}"))
        first = words[0].strip(".,;:!?").lower()
        if first.endswith("ing") and len(first) > 4 and first not in GERUND_OK:
            problems.append(("T004", f'sentence starts with "{words[0]}"; start with a verb'))
    # Uppercase words are directive names or acronyms, such as VERIFY or FILES.
    lowered = " ".join(re.sub(r"\b[A-Z][A-Z0-9_]+\b", "X", clean).lower().split())
    for forms, approved in REPLACE:
        for form in forms:
            if re.search(r"\b" + re.escape(form) + r"\b", lowered):
                problems.append(("T002", f'replace "{form}" with "{approved}"'))
                break
    for word in DELETE:
        if re.search(r"\b" + re.escape(word) + r"\b", lowered):
            problems.append(("T003", f'delete "{word}"'))
    return problems


def check_ste(model):
    for line, text in prose(model):
        for code, message in ste_problems(text):
            model.err(line, code, message)


SEMANTIC_CHECKS = [check_graph, check_permissions, check_flow, check_status, check_ste]
```

- [ ] **Step 5: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 55 tests
OK
```


- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/references skills/taskfile-planning/tests
git commit -m "Add the taskfile-planning STE checks" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 6: Orchestrator interface: `--json` and `--audit`

**Files:**
- Modify: `skills/taskfile-planning/references/ste_lint.py`
- Modify: `skills/taskfile-planning/tests/test_ste_lint.py`

**Interfaces:**
- Consumes: `group` (Task 3), `glob_regex` (Task 2), `Model.waves` and `Task.deps` (Task 2).
- Produces: `to_json(model) -> dict` with keys `plan` (`name`, `version`, `integration_branch`, `integration_worktree`), `global` (`env`, `stack`, `tools`, `flow`, `rules`, `agents_max`, `heartbeat_every`, `compact_when_context_pct`, `compact_after_wave`, `tasklist`, `worktrees`, `permit`, `deny`, `text`), `tasks` (each with `id`, `line`, `wave`, `depends`, `goal`, `steps`, `files`, `outputs`, `skips`, `verify`, `permit`, `deny`, `status`, `branch`, `worktree`, `text`), and `waves`. Also `audit(model, task_id, paths) -> int`. SKILL.md (Task 8) names these fields.

- [ ] **Step 1: Write the failing tests**

In `skills/taskfile-planning/tests/test_ste_lint.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
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

    def test_unknown_task_exits_2(self):
        self.assertEqual(self.audit("nope", "")[0], 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 62 tests
FAILED (failures=4, errors=1)
```


- [ ] **Step 3: Implement `--json` and `--audit`**

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
Usage: ste_lint.py FILE [--waves]

Exit 0: the file is valid. Exit 1: errors, one per line as FILE:LINE: CODE message.
Exit 2: usage or IO error. Standard library only.
"""
import argparse
import re
```

Replace with:

```python
Usage: ste_lint.py FILE [--waves | --json | --audit TASK_ID]

Exit 0: the file is valid. Exit 1: errors, one per line as FILE:LINE: CODE message.
Exit 2: usage or IO error. Standard library only.

--audit TASK_ID reads changed paths from stdin, one per line, and prints each path
that the task's FILES do not match. It exits 1 when it prints a path.
"""
import argparse
import json
import re
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python



def main(argv=None):
```

Replace with:

```python



def to_json(model):
    """The plan as data, so that the orchestrator never parses the file."""
    g = model.global_block
    name = model.plan_name
    return {
        "plan": {"name": name, "version": model.plan_version,
                 "integration_branch": f"taskfile/{name}/integration",
                 "integration_worktree": f"{g.worktrees}/{name}/integration"},
        "global": {
            "env": g.env, "stack": g.stack,
            "tools": {role: command for role, command, _ in g.tools},
            "flow": g.flow, "rules": [text for text, _ in g.rules],
            "agents_max": g.agents, "heartbeat_every": g.heartbeat,
            "compact_when_context_pct": g.compact_pct, "compact_after_wave": g.compact_after,
            "tasklist": g.tasklist, "worktrees": g.worktrees,
            "permit": group(g.permit), "deny": group(g.deny),
            "text": "\n".join(g.lines),
        },
        "tasks": [{
            "id": t.id, "line": t.line, "wave": t.wave, "depends": t.deps,
            "goal": t.goal[0], "steps": [text for text, _ in t.steps],
            "files": [glob for glob, _ in t.files], "outputs": t.outputs,
            "skips": {step: reason for step, reason, _ in t.skips},
            "verify": [command for command, _ in t.verify],
            "permit": group(t.permit), "deny": group(t.deny),
            "status": {"state": t.status["state"] if t.status else "pending",
                       "because": t.status["because"] if t.status else None,
                       "by": t.status["by"] if t.status else None},
            "branch": f"taskfile/{name}/tasks/{t.id}",
            "worktree": f"{g.worktrees}/{name}/tasks/{t.id}",
            "text": "\n".join(t.lines),
        } for t in model.tasks],
        "waves": model.waves,
    }


def audit(model, task_id, paths):
    """Print each path outside the task's FILES. Return the exit code."""
    task = next((t for t in model.tasks if t.id == task_id), None)
    if task is None:
        print(f"no task {task_id}", file=sys.stderr)
        return 2
    patterns = [glob_regex(glob) for glob, _ in task.files]
    outside = [p for p in (p.strip() for p in paths) if p and not any(r.match(p) for r in patterns)]
    for path in outside:
        print(path)
    return 1 if outside else 0


def main(argv=None):
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
    parser.add_argument("--waves", action="store_true", help="print one line per wave")
```

Replace with:

```python
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--waves", action="store_true", help="print one line per wave")
    mode.add_argument("--json", action="store_true", help="print the plan as JSON")
    mode.add_argument("--audit", metavar="TASK_ID",
                      help="print each path from stdin that the task's FILES do not match")
```

In `skills/taskfile-planning/references/ste_lint.py`, find:

```python
            print(f"wave {number}: {' '.join(wave)}")
    return 0
```

Replace with:

```python
            print(f"wave {number}: {' '.join(wave)}")
    elif args.json:
        print(json.dumps(to_json(model), indent=2))
    elif args.audit:
        return audit(model, args.audit, sys.stdin.read().splitlines())
    return 0
```

- [ ] **Step 4: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 62 tests
OK
```


- [ ] **Step 5: Check the command line by hand**

```bash
python3 skills/taskfile-planning/references/ste_lint.py skills/taskfile-planning/references/example.ste --waves
printf 'src/api.py\nREADME.md\n' | python3 skills/taskfile-planning/references/ste_lint.py skills/taskfile-planning/references/example.ste --audit endpoint; echo "exit $?"
```

Expected output, exactly:

```text
wave 1: schema
wave 2: endpoint
README.md
exit 1
```

- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/references/ste_lint.py skills/taskfile-planning/tests/test_ste_lint.py
git commit -m "Add --json and --audit to the taskfile-planning linter" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 7: Format reference

**Files:**
- Create: `skills/taskfile-planning/tests/test_skill_files.py`
- Create: `skills/taskfile-planning/references/format.md`

**Interfaces:**
- Consumes: `ste_lint.KEYWORDS`, `ste_lint.CODES`.
- Produces: `test_skill_files.py` with `SKILL_DIR` and `read(rel_path) -> str`. Task 8 adds `SkillDocTest` above its `if __name__ == "__main__":` line.

- [ ] **Step 1: Write the failing tests**

Create `skills/taskfile-planning/tests/test_skill_files.py` with:

```python
"""Structural tests for SKILL.md and references/format.md.

They check that the documents name every file, keyword, error code, and branch
name that the linter defines, so the documents and the linter cannot drift apart.
Run with: python3 -m unittest discover -s skills/taskfile-planning/tests -v
"""
import os
import re
import sys
import unittest

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "references"))
import ste_lint  # noqa: E402


def read(rel_path):
    with open(os.path.join(SKILL_DIR, rel_path), encoding="utf-8") as handle:
        return handle.read()


class FormatDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read("references/format.md")

    def test_every_keyword_is_documented(self):
        for keyword in ste_lint.KEYWORDS:
            self.assertRegex(self.text, r"`" + keyword + r"\b", keyword)

    def test_every_code_has_its_row(self):
        for code, meaning in ste_lint.CODES.items():
            row = f"| {code} | {meaning[0].upper() + meaning[1:]} |"
            self.assertIn(row, self.text.replace("`${id.key}`", "${id.key}"), code)

    def test_no_unknown_codes(self):
        documented = set(re.findall(r"^\| ([SGPFTX]\d{3}) \|", self.text, re.M))
        self.assertEqual(documented, set(ste_lint.CODES))

    def test_links_the_example(self):
        self.assertIn("`example.ste`", self.text)
        self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, "references", "example.ste")))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 66 tests
FAILED (errors=4)
```

Each error is a `FileNotFoundError` for `references/format.md`.

- [ ] **Step 3: Write the reference**

Create `skills/taskfile-planning/references/format.md` with:

```markdown
# Taskfile.ste format

Reference for `skills/taskfile-planning/SKILL.md`. Load this file when you write a
Taskfile, fix a lint error, or need the exact meaning of a directive.

## Lexical rules

- The file is line-oriented. Each line holds one directive: an UPPERCASE keyword, then
  its arguments.
- `#` starts a comment when it is the first character of a line or follows whitespace.
  `src/a#b.py` contains no comment.
- Blank lines are ignored. Indentation is cosmetic.
- There is no line continuation. Write long prose as more STEP lines.
- Blocks are `GLOBAL` … `END` and `TASK <id>` … `END`. Blocks do not nest.
- Task ids and the plan name match `[a-z][a-z0-9-]*`. Task ids are unique.

## Directives

| Directive | Scope | Count | Meaning |
|---|---|---|---|
| `PLAN <name> <version>` | file top | 1, first line | Plan identity |
| `ENV <k>=<v> …` | GLOBAL | 0..n | Environment facts |
| `STACK <item> …` | GLOBAL | 0..n | Tech stack |
| `TOOL <role> <command…>` | GLOBAL | 1..n | The one tool for a role (edit, fmt, build…). Roles are unique. |
| `FLOW <step> -> <step> …` | GLOBAL | 1 | Ordered steps every task runs |
| `RULE <sentence>` | GLOBAL | 0..n | Methodology rule, in STE |
| `AGENTS max <n>` | GLOBAL | 1 | Maximum concurrent subagents, n ≥ 1 |
| `HEARTBEAT every <n> steps` | GLOBAL | 0..1 | Subagent sends a heartbeat after every n STEP lines |
| `COMPACT when context > <pct>%` | GLOBAL | 0..1 | Orchestrator compacts at this context usage, 1 ≤ pct ≤ 99 |
| `COMPACT after wave` | GLOBAL | 0..1 | Orchestrator compacts between waves |
| `TASKLIST on\|off` | GLOBAL | 0..1 | Orchestrator mirrors tasks into its todo list. Default off. |
| `WORKTREES <dir>` | GLOBAL | 0..1 | Directory for worktrees, relative to the repo root. Default `.worktrees`. |
| `PERMIT <action> <glob…>` | GLOBAL, TASK | 0..n | Allow an action. In a TASK, narrowing only. |
| `DENY <action> <glob…>` | GLOBAL, TASK | 0..n | Forbid an action. A TASK may only add restrictions. |
| `DEPENDS <id> …` | TASK | 0..n | Explicit dependency |
| `GOAL <sentence>` | TASK | 1 | Result of the task, in STE |
| `STEP <sentence>` | TASK | 0..n | Ordered instruction, in STE |
| `FILES <glob…>` | TASK | 1..n | Files the task may change |
| `OUTPUT <key> = <value>` | TASK | 0..n | Value other tasks read as `${id.key}`. Keys are unique per task. |
| `SKIP <flow-step> BECAUSE <sentence>` | TASK | 0..n | Omit one FLOW step, with a reason |
| `VERIFY <command…>` | TASK | 1..n | Command that must exit 0 |
| `STATUS <state> [BECAUSE <sentence>] [BY <id>]` | TASK | 0..1 | Execution state. Only the orchestrator writes it. |

## Permissions

Actions: `read`, `write`, `run`, `network`, `spawn`.

- `read`, `write`, and `run` need at least one glob. A `run` glob matches a program name,
  for example `pytest` or `py*`.
- `network` takes no glob, which means every host, or host globs.
- `spawn` is reserved. Every task has an implicit `DENY spawn`. `PERMIT spawn` is an error.
- A task with no PERMIT for an action uses the GLOBAL PERMIT globs for that action. A task
  with a PERMIT for an action uses only its own globs, and each one must be inside a
  GLOBAL PERMIT for the same action.
- GLOBAL DENY lines apply to every task.

## Globs

- `**` matches across directories. `*` and `?` match inside one directory.
- Paths are relative to the repository root. They mean the same thing in every worktree.
- **Subset rule.** Glob A is inside glob B when B's literal prefix contains A, and B's
  wildcard part is exactly `**`. `src/**` contains `src/api.py` and `src/*.py`. A literal
  path is inside B when B matches it. If the linter cannot decide, it reports an error.
  It never decides in favour of the task.
- **DENY rule.** A PERMIT or FILES glob fails only when a DENY glob contains it fully.
  `PERMIT write src/**` with `DENY write src/secrets/**` is valid.
- **Overlap rule.** Two FILES globs overlap when one literal prefix starts the other.
  The rule is conservative: `src/*.py` and `src/*.md` overlap.

## FLOW steps

A FLOW step is a TOOL role declared in GLOBAL or one of these built-ins:

| Built-in | The subagent does this |
|---|---|
| `read` | Reads its FILES and the targets its dependencies' OUTPUT values name |
| `tasklist` | Loads its STEP lines into its todo list and marks each done |
| `heartbeat` | Sends the orchestrator one line: task id, current step, `in_progress` |
| `verify` | Runs every VERIFY command; all must exit 0 |
| `report` | Sends the final state, VERIFY output, and changed files to the orchestrator |

`report` always runs last, whether or not FLOW lists it. `verify` and `report` cannot be
skipped. Compaction is not a FLOW step. Only the orchestrator compacts.

## States

| State | Meaning | Needs |
|---|---|---|
| `pending` | Not started. The default when STATUS is absent. | — |
| `in_progress` | Dispatched. On a new run, this means the last run stopped. | — |
| `completed_success` | Audited, verified, and merged | — |
| `completed_failure` | Failed | `BECAUSE <sentence>` |
| `blocked` | A dependency failed or is blocked | `BY <id>` |

`BY` names the direct dependency that failed or is blocked. Follow the BY links to find
the root failure.

## Semantics

- **Inheritance.** A task inherits all of GLOBAL. A task cannot contain ENV, STACK, TOOL,
  FLOW, RULE, AGENTS, HEARTBEAT, COMPACT, TASKLIST, or WORKTREES.
- **Dependency graph.** Edges come from DEPENDS and from every `${id.key}` in the task's
  text. Waves are the topological levels of the graph: a task with no dependencies is in
  wave 1, and every other task is one wave after its latest dependency.
- **Parallel safety.** Each task runs in its own git worktree. Two tasks in the same wave
  must not have overlapping FILES, so their branches merge without conflicts.

## STE checks

The linter checks GOAL, STEP, RULE, and BECAUSE text. It counts only the mechanical rules
from `skills/nfc/references/style-rules.md`:

- A sentence has 20 words or fewer. Quoted text, backticked text, and `${id.key}` each
  count as one word.
- No rejected word from the substitution table, such as "ensure" or "prior to". The error
  names the approved word.
- No word that adds no meaning, such as "just" or "basically".
- No sentence starts with an `-ing` word.

Quoted text, backticked text, `${id.key}`, and UPPERCASE words are not checked for
rejected words. `VERIFY failed after merge` is valid. Apply the other STE rules, such as
the active voice, yourself.

## Error codes

Each error prints as `FILE:LINE: CODE message`.

| Code | Meaning |
|---|---|
| S001 | PLAN must be the first directive and appear once |
| S002 | Unknown keyword |
| S003 | Directive outside its allowed scope |
| S004 | Directive appears more times than allowed |
| S005 | Required directive or block missing |
| S006 | Task id has the wrong format |
| S007 | Duplicate task id |
| S008 | Block not closed, or END without a block |
| S009 | The file needs exactly one GLOBAL block |
| S010 | Directive arguments have the wrong form |
| G001 | DEPENDS names an unknown task |
| G002 | `${id.key}` names an unknown task |
| G003 | `${id.key}` names an OUTPUT the task does not declare |
| G004 | Dependency cycle |
| G005 | FILES overlap within a wave |
| P001 | Task PERMIT is not inside a GLOBAL PERMIT |
| P002 | FILES glob is not inside the write PERMIT |
| P003 | PERMIT or FILES glob is forbidden by a DENY |
| P004 | PERMIT spawn is not allowed |
| P005 | VERIFY command is not inside PERMIT run |
| F001 | FLOW step is not a TOOL role or a built-in step |
| F002 | SKIP names a step that is not in FLOW |
| F003 | SKIP of verify or report |
| F004 | TOOL role declared twice |
| T001 | Sentence has more than 20 words |
| T002 | Rejected word; use the approved word |
| T003 | Word that adds no meaning |
| T004 | Sentence starts with an -ing word |
| X001 | Unknown state |
| X002 | BECAUSE must go with completed_failure, and only with it |
| X003 | BY must go with blocked, and only with it |
| X004 | BY names a task that is not a failed or blocked dependency |
| X005 | Task started or finished before a dependency succeeded |

The linter reports structure errors (S) first. It runs the other checks only when the
structure is valid.

## Linter interface

    python3 ste_lint.py FILE                    # exit 0 valid, 1 errors, 2 usage or IO error
    python3 ste_lint.py FILE --waves            # wave N: id id …
    python3 ste_lint.py FILE --json             # {plan, global, tasks, waves}
    git diff --name-only A..B | python3 ste_lint.py FILE --audit TASK_ID
                                                # prints each path outside FILES; exit 1 if any

`--json` gives each task its `branch`, `worktree`, `depends`, `wave`, `status`, and
verbatim `text`. It gives `plan.integration_branch`, `plan.integration_worktree`, and the
verbatim GLOBAL block as `global.text`.

## Example

The golden example is `example.ste` in this directory. `--waves` prints:

    wave 1: schema
    wave 2: endpoint
```

- [ ] **Step 4: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 66 tests
OK
```


- [ ] **Step 5: Commit**

```bash
git add skills/taskfile-planning/references/format.md skills/taskfile-planning/tests/test_skill_files.py
git commit -m "Add the taskfile-planning format reference" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 8: SKILL.md and spec amendments

**Files:**
- Modify: `skills/taskfile-planning/tests/test_skill_files.py`
- Create: `skills/taskfile-planning/SKILL.md`
- Modify: `docs/superpowers/specs/2026-09-12-taskfile-planning-design.md`

**Interfaces:**
- Consumes: `ste_lint.lint`, `ste_lint.to_json`, `ste_lint.ste_problems`, and the JSON field names from Task 6.

- [ ] **Step 1: Write the failing tests**

In `skills/taskfile-planning/tests/test_skill_files.py`, find:

```python
if __name__ == "__main__":
    unittest.main()
```

Replace with:

```python
class SkillDocTest(unittest.TestCase):
    def setUp(self):
        self.text = read("SKILL.md")

    def test_frontmatter(self):
        self.assertTrue(self.text.startswith("---\nname: taskfile-planning\ndescription: "))
        for trigger in ("write a taskfile", "plan this as a Taskfile.ste",
                        "taskfile-planning", "run Taskfile.ste"):
            self.assertIn(trigger, self.text.split("---")[1], trigger)

    def test_length(self):
        self.assertLessEqual(len(self.text.splitlines()), 260)

    def test_every_linked_file_exists(self):
        links = set(re.findall(r"`(references/[\w.-]+)`", self.text))
        self.assertEqual(links, {"references/format.md", "references/ste_lint.py",
                                 "references/example.ste"})
        for rel in links:
            self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, rel)), rel)

    def test_mode_1_stops_at_the_question(self):
        self.assertIn('"Run this plan now, or later?"', self.text)
        self.assertIn("Never start it on your own.", self.text)

    def test_names_match_the_linter(self):
        model, errors = ste_lint.lint(read("references/example.ste"))
        self.assertEqual(errors, [])
        data = ste_lint.to_json(model)
        self.assertEqual(data["plan"]["integration_branch"], "taskfile/health-check/integration")
        for name in ("taskfile/<plan>/integration", "<WORKTREES>/<plan>/integration",
                     "taskfile/<plan>/tasks/<id>", "<WORKTREES>/<plan>/tasks/<id>"):
            self.assertIn(f"`{name}`", self.text, name)

    def test_flow_contract(self):
        contract = self.text.split("### FLOW contract")[1].split("\n## ")[0]
        for phrase in ("Work only in your worktree", "Do not merge, rebase, or push",
                       "Omit only the steps your SKIP lines name", "Use only the TOOL",
                       "Stay inside PERMIT, DENY, and FILES", "Do not start agents",
                       "Do not edit the Taskfile", "Send a heartbeat",
                       "End with `report`, including on failure",
                       "completed_failure BECAUSE context limit"):
            self.assertIn(phrase, contract, phrase)

    def test_audit_steps_in_order(self):
        audit = self.text.split("### Audit and merge")[1].split("###")[0]
        steps = re.findall(r"^\d\. \*\*(.+?)\*\*", audit, re.M)
        self.assertEqual(steps, ["Save everything.", "Attribute.", "Verify in isolation.",
                                 "Merge.", "Verify after the merge.", "Clean up."])

    def test_failure_reasons_pass_the_linter(self):
        reasons = set(re.findall(r"`[^`\n]*BECAUSE ([A-Za-z ]+)`", self.text))
        self.assertEqual(reasons, {"changed files outside FILES", "merge conflict",
                                   "VERIFY failed after merge", "context limit"})
        for reason in reasons:
            self.assertEqual(ste_lint.ste_problems(reason), [], reason)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to make sure the new ones fail**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 74 tests
FAILED (errors=8)
```

Each error is a `FileNotFoundError` for `SKILL.md`.

- [ ] **Step 3: Write SKILL.md**

Create `skills/taskfile-planning/SKILL.md` with:

```markdown
---
name: taskfile-planning
description: Use when the user asks to write or run a Taskfile.ste, a line-oriented plan of LLM work with dependencies, permissions, and STE prose that an orchestrator runs as parallel waves of subagents in git worktrees. Triggers include "write a taskfile", "plan this as a Taskfile.ste", "taskfile-planning", and "run Taskfile.ste".
---

# Taskfile Planning

## Overview

A `Taskfile.ste` is a Dockerfile-style plan for LLM work. One GLOBAL block fixes the
environment, permissions, tools, and working method (FLOW). TASK blocks describe units
of work and their dependencies. Independent tasks run in parallel waves, each in its own
git worktree.

This skill has two modes:

- **Mode 1, Author:** write a Taskfile and make it pass the linter.
- **Mode 2, Run:** act as the orchestrator and run the Taskfile.

Mode 2 starts only on an explicit request. Never start it on your own.

**Files:**

- `references/format.md`: the grammar, every directive, the glob rules, and every error
  code. Load it before you write or fix a Taskfile.
- `references/ste_lint.py`: the linter. Standard library only.
- `references/example.ste`: a valid example.
- `skills/nfc/references/style-rules.md` (in this repository): the STE rules.

In the commands below, `LINT` means `python3 <this skill's directory>/references/ste_lint.py`.
Run every command from the repository root unless a step names a worktree.

## Mode 1: Author

**Triggers:** "write a taskfile", "plan this as a Taskfile.ste", "taskfile-planning".

1. **Globals.** Read the repo: lockfiles, CI config, and formatter config. Propose ENV,
   STACK, TOOL, and FLOW. Confirm them with the user in one message. In the same message,
   ask for what the repo does not show:
   - permissions, especially `network` and paths outside the repo;
   - `AGENTS max`;
   - the FLOW order.
2. **Tasks.** Make each task one unit that one subagent can finish and verify inside its
   own context. Add a dependency only when a task uses another task's result. Give each
   task the narrowest FILES.
3. **STE.** Write GOAL, STEP, RULE, and BECAUSE text under the `codered:nfc` strict rules.
   One instruction per STEP. Start each STEP with an imperative verb.
4. **Lint loop.** Run `LINT <file>` until it exits 0. Fix each error at its line.
   Never widen a GLOBAL permission to pass a check without asking the user.
5. **Present and stop.** Show the path, the `LINT <file> --waves` output, and one line
   per task. Then ask exactly: "Run this plan now, or later?"
   - On "later", stop. Give the command to run it: "run Taskfile.ste".
   - On "now", start Mode 2.

**Location:** write `Taskfile.ste` at the repo root. Use `plans/<name>.ste` when a
Taskfile already exists or the user wants several plans. Never overwrite an existing
file without asking.

## Mode 2: Run

**Start:** only on an explicit request, from the Mode 1 question or a later
"run <file>".

The orchestrator is the only writer of the Taskfile and the integration branch.
Subagents never edit either. The Taskfile's STATUS lines are the source of truth.

### Names

Take every name from `LINT <file> --json`. Do not parse the Taskfile yourself.

| Item | Value | JSON field |
|---|---|---|
| Base branch | The branch checked out when the run starts | — |
| Integration branch | `taskfile/<plan>/integration` | `plan.integration_branch` |
| Integration worktree | `<WORKTREES>/<plan>/integration` | `plan.integration_worktree` |
| Task branch | `taskfile/<plan>/tasks/<id>` | `tasks[].branch` |
| Task worktree | `<WORKTREES>/<plan>/tasks/<id>` | `tasks[].worktree` |

The Taskfile stays in the main working tree. Edit it there. Do not commit STATUS changes.
Create worktrees with `git worktree add`. Do not use a harness isolation feature that
picks its own paths or cleans up by itself, because the plan must control the names.

### Steps

1. **Validate.** Run `LINT <file> --json`. If it exits 1, show the errors and stop.
   When `tasklist` is true, mirror every task into your todo list.
2. **Prepare the workspace.**
   - Run `git status --porcelain`. Every line except the Taskfile must be absent.
     Otherwise stop and name the files.
   - Run `git check-ignore -q <WORKTREES>/`. If it exits non-zero, stop and tell the user
     to add `<WORKTREES>/` to `.gitignore`.
   - If the integration branch does not exist, create it from the base branch:
     `git branch <integration-branch> HEAD`.
   - If the integration worktree does not exist, run
     `git worktree add <integration-worktree> <integration-branch>`.
3. **Reset interrupted tasks.** For each task in `in_progress`:
   - If its worktree exists and `git -C <worktree> status --porcelain` is not empty,
     commit everything there as `<id>: uncommitted changes at interrupt`.
   - Run `git worktree remove --force <worktree>`.
   - Rename the branch: `git branch -m <branch> <branch>-attempt-<n>`. `n` is one more
     than the number of `<branch>-attempt-*` branches that exist.
   - Set the task's STATUS to `pending`. The old branch keeps its commits.
4. **For each wave, in order:**
   - Skip tasks at `completed_success`.
   - Write `STATUS blocked BY <dep>` on a task whose dependency is `completed_failure` or
     `blocked`.
   - For each remaining task, run
     `git worktree add -b <branch> <worktree> <integration-branch>`.
     Set its STATUS to `in_progress` and save the Taskfile.
   - Dispatch one subagent per task. Never run more than `agents_max` at once. Queue the
     rest, and start one each time a slot frees.
   - Each subagent prompt contains: its worktree path; `global.text`; the task's `text`
     with each `${id.key}` replaced by that dependency's OUTPUT value; and the FLOW
     contract below.
   - For each report, do "Audit and merge" below. Write `STATUS completed_success` or
     `STATUS completed_failure BECAUSE <reason>`.
   - After the wave, apply the COMPACT triggers (see "Compaction").
5. **Finish.** Run `git worktree remove <integration-worktree>`. Print one table row per
   task: id, final STATUS, BY chain, branch, and the worktree path of each failed task.
   Stop. There are no automatic retries. A re-run skips completed tasks. Never merge the
   integration branch into the user's branch. The user decides that.

### Audit and merge

Do these steps for each report, in the order that reports arrive. Merge one task at a
time. Let `INT` be the integration worktree and `WT` the task worktree.

1. **Save everything.** If `git -C WT status --porcelain` is not empty, run
   `git -C WT add -A` and commit as `<id>: uncommitted changes at report`.
2. **Attribute.** Run
   `git diff --name-only $(git merge-base <integration-branch> <branch>)..<branch> | LINT <file> --audit <id>`.
   If it exits 1, fail the task `BECAUSE changed files outside FILES`.
3. **Verify in isolation.** Run each VERIFY command in `WT`. Any non-zero exit fails the
   task. A report that claims success does not override this.
4. **Merge.** Save `PRE=$(git -C INT rev-parse HEAD)`. Run
   `git -C INT merge --no-ff -m "taskfile(<plan>): merge <id>" <branch>`.
   On a conflict, run `git -C INT merge --abort` and fail the task `BECAUSE merge conflict`.
5. **Verify after the merge.** Run each VERIFY command in `INT`. If one fails, run
   `git -C INT reset --hard $PRE` and fail the task `BECAUSE VERIFY failed after merge`.
   The task branch stays as it is.
6. **Clean up.** On success, run `git worktree remove WT` and keep the branch. On failure,
   keep both the worktree and the branch so the user can inspect them.

You own the integration branch, so step 5 can reset it. Never reset the base branch or a
task branch. Never run `git reset` in the main working tree: it holds the Taskfile's
uncommitted STATUS lines.

### Compaction

- `compact_after_wave`: compact between waves.
- `compact_when_context_pct`: compact when your context usage passes the threshold.

If you cannot start compaction yourself, stop at the end of the wave. Tell the user to
compact and then say "run <file>". The STATUS lines let the run continue. After any
compaction, read the Taskfile again before you continue.

### Heartbeats

Relay each heartbeat to the user in one line. Never write heartbeats to the Taskfile.

### FLOW contract (send it to each subagent verbatim)

- Work only in your worktree. Do not change the main working tree or another worktree.
- Commit your changes on your task branch before `report`. Do not merge, rebase, or push.
- Do the FLOW steps in order. Omit only the steps your SKIP lines name.
- Use only the TOOL named for each role.
- Stay inside PERMIT, DENY, and FILES.
- Do not start agents or subagents.
- Do not edit the Taskfile.
- Send a heartbeat after every n STEP lines when HEARTBEAT is set. If you have no way to
  send a message before you finish, put the heartbeats in your report.
- End with `report`, including on failure.
- If your context runs out, report `completed_failure BECAUSE context limit`.

## Errors

| Situation | Action |
|---|---|
| Invalid file | Mode 2 refuses to start and prints the lint errors |
| Subagent failure | The task becomes `completed_failure`; dependents become `blocked BY` it; independent tasks continue |
| False success report | The VERIFY check in step 3 fails the task |
| Changes outside FILES | `completed_failure BECAUSE changed files outside FILES` |
| Uncommitted changes | The orchestrator commits them on the task branch, then audits |
| VERIFY fails after the merge | The integration branch resets to `PRE`; `completed_failure BECAUSE VERIFY failed after merge` |
| Merge conflict | Abort the merge; `completed_failure BECAUSE merge conflict` |
| Dirty working tree, or WORKTREES not ignored | Mode 2 refuses to start and names the problem |
| Interrupted run | The old branch becomes `-attempt-<n>`; the task resets to `pending` |
| Subagent context exhausted | `completed_failure BECAUSE context limit`; the user splits the task |

## Red flags

| Thought | Reality |
|---|---|
| "The plan is valid, so I can start running it." | Mode 2 needs an explicit yes. Ask "Run this plan now, or later?" and stop. |
| "I will widen the GLOBAL PERMIT so the lint passes." | Ask the user first. |
| "The subagent says the tests pass." | Run VERIFY yourself, in the worktree and after the merge. |
| "Two tasks are independent, so I can start a third agent." | Never exceed `agents_max`. |
| "I will reset the main working tree to undo the merge." | Reset only the integration worktree. |
| "The integration branch looks good, so I will merge it into main." | The user decides that. |
```


- [ ] **Step 4: Run the tests to make sure they pass**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 74 tests
OK
```


- [ ] **Step 5: Amend the spec**

In `docs/superpowers/specs/2026-09-12-taskfile-planning-design.md`, find:

```markdown
| Integration branch | `taskfile/<plan-name>`, created from the base branch on the first run and reused on later runs |
| Task branch | `taskfile/<plan-name>/<task-id>` |
| Task worktree | `<WORKTREES>/<plan-name>/<task-id>` |
```

Replace with:

```markdown
| Integration branch | `taskfile/<plan-name>/integration`, created from the base branch on the first run and reused on later runs |
| Integration worktree | `<WORKTREES>/<plan-name>/integration`. The orchestrator merges, verifies, and resets here. |
| Task branch | `taskfile/<plan-name>/tasks/<task-id>` |
| Task worktree | `<WORKTREES>/<plan-name>/tasks/<task-id>` |
```

Append this section to the end of `docs/superpowers/specs/2026-09-12-taskfile-planning-design.md`:

```markdown

## Amendments (implementation plan, 2026-10-13)

- Git cannot hold `taskfile/<plan>` and `taskfile/<plan>/<id>` at once, so the branches are
  `taskfile/<plan>/integration` and `taskfile/<plan>/tasks/<id>`.
- Merges, post-merge VERIFY, and resets happen in an integration worktree. A reset in the
  main working tree would discard the Taskfile's uncommitted STATUS lines.
- The STE word checks skip UPPERCASE words, so `BECAUSE VERIFY failed after merge` is valid.
- `ste_lint.py --audit TASK_ID` reads changed paths on stdin and prints each path outside
  FILES. The attribution step uses it.
- An interrupted task's uncommitted changes are committed before its worktree is removed.
```

- [ ] **Step 6: Commit**

```bash
git add skills/taskfile-planning/SKILL.md skills/taskfile-planning/tests/test_skill_files.py docs/superpowers/specs/2026-09-12-taskfile-planning-design.md
git commit -m "Add the taskfile-planning SKILL.md and amend the spec" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 9: Scenario runs

This task needs judgement. Run it with a sonnet agent. That agent dispatches the scenario subagents and judges them.

**Files:**
- Create: `skills/taskfile-planning/tests/fixtures/make_scenario_repo.sh`
- Create: `skills/taskfile-planning/tests/RESULTS.md`
- Modify: `skills/taskfile-planning/SKILL.md` (only if a scenario fails because of the skill's wording)

**Interfaces:**
- Consumes: the whole skill from Tasks 1–8.

- [ ] **Step 1: Create the scenario repository script**

Create `skills/taskfile-planning/tests/fixtures/make_scenario_repo.sh` with:

```bash
#!/usr/bin/env bash
# Create a scratch git repository with a Taskfile for the Mode 2 scenario run.
# Usage: make_scenario_repo.sh DIR   (DIR must not exist)
set -euo pipefail
dir="$1"
if [ -e "$dir" ]; then
  echo "$dir exists" >&2
  exit 2
fi
mkdir -p "$dir/src"
cd "$dir"
git init -q -b main
git config user.name "Scenario"
git config user.email "scenario@example.invalid"
echo ".worktrees/" > .gitignore
echo "Scenario repository for taskfile-planning." > README.md
touch src/.keep
cat > Taskfile.ste <<'TASKFILE'
PLAN scenario 1

GLOBAL
  AGENTS max 2
  PERMIT read **
  PERMIT write src/**
  PERMIT run test grep
  TOOL edit Write
  FLOW read -> edit -> verify -> report
  RULE Do not change files outside FILES.
END

TASK alpha
  GOAL Create the file src/alpha.txt with the word "alpha".
  FILES src/alpha.txt
  OUTPUT word = alpha
  VERIFY grep -q alpha src/alpha.txt
END

TASK beta
  GOAL Create the file src/beta.txt with the word "beta".
  FILES src/beta.txt
  VERIFY grep -q beta src/beta.txt
END

TASK delta
  GOAL Create the file src/delta.txt with the word "delta".
  FILES src/delta.txt
  VERIFY test -f src/never.txt
END

TASK gamma
  DEPENDS beta
  GOAL Create the file src/gamma.txt with the word ${alpha.word}.
  FILES src/gamma.txt
  VERIFY grep -q alpha src/gamma.txt
END

TASK epsilon
  DEPENDS delta
  GOAL Create the file src/epsilon.txt with the word "epsilon".
  FILES src/epsilon.txt
  VERIFY test -f src/epsilon.txt
END
TASKFILE
git add .gitignore README.md src/.keep
git commit -q -m "Scenario start"
echo "$dir"
```

Then run:

```bash
chmod +x skills/taskfile-planning/tests/fixtures/make_scenario_repo.sh
S=$(mktemp -d)/repo
skills/taskfile-planning/tests/fixtures/make_scenario_repo.sh "$S" >/dev/null
python3 skills/taskfile-planning/references/ste_lint.py "$S/Taskfile.ste" --waves
```

Expected output, exactly:

```text
wave 1: alpha beta delta
wave 2: gamma epsilon
```

- [ ] **Step 2: Scenario M1, Author mode**

Create a scratch repo with `git init` that holds a small Python package: `pyproject.toml`, `src/calc.py` with an `add` function, and `tests/test_calc.py`. Dispatch a fresh subagent with this prompt: "Load `skills/taskfile-planning/SKILL.md` and follow it. In the repository at <path>, write a Taskfile to add `subtract` and `multiply` functions with tests, and a README section that documents both. The user answers in advance: confirm your proposed globals; no network; AGENTS max 2; the FLOW order you propose is fine." Pass criteria:
  1. It proposes ENV, STACK, TOOL, and FLOW from the repo files, and asks about permissions, AGENTS max, and FLOW order.
  2. The final `Taskfile.ste` lints with exit 0, and the transcript shows the lint loop.
  3. The README task depends on the code tasks only if it uses their results. The FILES sets are narrow.
  4. It ends by asking exactly "Run this plan now, or later?" and starts no subagent and no worktree.

- [ ] **Step 3: Scenario M2, Run mode**

Run `make_scenario_repo.sh` into a new directory. Dispatch a fresh subagent with this prompt: "Load `skills/taskfile-planning/SKILL.md` and follow it. The user says: run Taskfile.ste in <path>." Then check these points against the repository and the transcript:
  1. No more than 2 subagents run at once. Wave 1 has 3 tasks, so one must queue.
  2. Final STATUS lines: `alpha`, `beta`, and `gamma` are `completed_success`. `delta` is `completed_failure` with a BECAUSE reason. `epsilon` is `blocked BY delta`. `python3 skills/taskfile-planning/references/ste_lint.py Taskfile.ste` exits 0.
  3. `git branch --list 'taskfile/*'` shows `taskfile/scenario/integration` and `taskfile/scenario/tasks/<id>` for each of the 4 dispatched tasks.
  4. `git log --merges --format=%s taskfile/scenario/integration` shows exactly 3 lines, `taskfile(scenario): merge <id>` for alpha, beta, and gamma.
  5. `src/gamma.txt` on the integration branch contains `alpha`, which shows that the `${alpha.word}` value was passed.
  6. `.worktrees/scenario/tasks/delta` still exists. The worktrees for the successful tasks and the integration worktree are gone.
  7. `main` still points at the "Scenario start" commit, and the integration branch was not merged into it.

- [ ] **Step 4: Scenario W, audit without a subagent**

In a fresh scenario repository, act as a subagent that breaks the rules. Run the commands from SKILL.md's "Prepare the workspace" step. Create the `alpha` worktree. In it, write `src/alpha.txt` and also change `README.md`. Commit both. Then run the "Attribute" command from SKILL.md for `alpha`. Expected: it prints `README.md` and exits 1. Then reset that worktree with the "Reset interrupted tasks" step and check that the branch is renamed `taskfile/scenario/tasks/alpha-attempt-1`.

- [ ] **Step 5: Record the results**

Write `skills/taskfile-planning/tests/RESULTS.md` with: the run date; one section per scenario with a table of pass criteria and PASS or FAIL with evidence (a command and its output, or a transcript quote); and a list of the SKILL.md changes made in Step 6. Use `skills/intel-analyst/tests/RESULTS.md` as the style model.

- [ ] **Step 6: Fix and rerun**

For each FAIL caused by the skill's wording, change `SKILL.md`, rerun `python3 -m unittest discover -s skills/taskfile-planning/tests`, and rerun only the failed scenario with a fresh subagent. Record each round in `RESULTS.md`. If a scenario fails twice for the same reason, stop and report it to the user. Do not weaken a pass criterion.

- [ ] **Step 7: Commit**

```bash
git add skills/taskfile-planning/tests skills/taskfile-planning/SKILL.md
git commit -m "Record taskfile-planning scenario runs" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 10: README, version bump, and PR

**Files:**
- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Add the README section**

In `README.md`, find:

```markdown
### 🕵️ [Intel Analyst](skills/intel-analyst/)
```

Replace with:

```markdown
### 🧾 [Taskfile Planning](skills/taskfile-planning/)

Writes and runs a `Taskfile.ste`: a line-oriented, Dockerfile-style plan for LLM work. One GLOBAL block fixes the environment, permissions, tools, and the steps every task follows. TASK blocks declare their files, checks, and dependencies, so independent tasks run in parallel waves. Every instruction is written in Simplified Technical English, so a subagent reads exactly one meaning.

A bundled standard-library linter makes the format strict: structure, dependency cycles, permission narrowing, file overlap between parallel tasks, and countable STE rules, each with an exact error code and line. In Run mode, the orchestrator gives each task its own git worktree and branch, then audits the changed files, runs the task's checks itself, and merges with `--no-ff` into an integration branch. A failed task keeps its worktree for inspection, and its dependents are marked `blocked BY` it.

| | |
|---|---|
| **Trigger** | "write a taskfile" · "plan this as a Taskfile.ste" · "run Taskfile.ste" |
| **Output** | A `Taskfile.ste` that lints clean, then an integration branch with one merge per successful task |
| **Checks** | `ste_lint.py` before every run · file audit, isolated checks, and post-merge checks for every task |
| **Scope** | Plans and orchestrates. It never merges into your branch; you decide that |

### 🕵️ [Intel Analyst](skills/intel-analyst/)
```

Then change the skill count badge:

In `README.md`, find:

```text
badge/skills-17-brightgreen
```

Replace with:

```text
badge/skills-18-brightgreen
```

- [ ] **Step 2: Bump the plugin version**

A new skill reaches installed copies only when the version changes.

In `.claude-plugin/plugin.json`, find:

```json
  "version": "1.6.0",
```

Replace with:

```json
  "version": "1.7.0",
```

In `.claude-plugin/marketplace.json`, find:

```json
      "version": "1.6.0",
```

Replace with:

```json
      "version": "1.7.0",
```

Then run:

```bash
grep -c 'skills-18' README.md
grep -h '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json
python3 -c "import json; [json.load(open(f)) for f in ('.claude-plugin/plugin.json', '.claude-plugin/marketplace.json')]; print('json ok')"
```

Expected output, exactly:

```text
1
  "version": "1.7.0",
      "version": "1.7.0",
json ok
```

- [ ] **Step 3: Run the full suite**

```bash
python3 -m unittest discover -s skills/taskfile-planning/tests 2>&1 | grep -E '^(Ran|OK|FAILED)' | sed 's/ in [0-9.]*s$//'
```

Expected output, exactly:

```text
Ran 74 tests
OK
```


- [ ] **Step 4: Commit**

```bash
git add README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "List taskfile-planning in the README and bump the plugin to 1.7.0" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Whole-branch review**

Dispatch a sonnet reviewer against the spec, the "Spec amendments" section of this plan, and `git diff main...skill/taskfile-planning`. Fix each finding. Verify each fix with a sonnet re-review.

- [ ] **Step 6: Push and open the PR**

Push `skill/taskfile-planning` and open a PR against `main`. The PR body lists the summary, the test count, the scenario results from `RESULTS.md`, and the four spec amendments. End the PR body with:

```text
🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
