# Vertical Slice Planning Skill — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `vertical-slice-planning` skill — a plan-only skill that emits an executable plan directory whose every task is an idempotent Python script that applies its change through hashline and proves it with runnable gates.

**Architecture:** The deliverable is a skill directory containing `SKILL.md`, three reference documents, and `taskkit.py` — a stdlib-only edit-and-gate engine that emitted task scripts import. `taskkit.Editor` shells out to the `hashline` CLI (`read --json` / `patch --json`), resolving anchors at run time so scripts written today survive earlier tasks landing tomorrow; drift halts with exit 3 while genuine hashline unavailability degrades to a loud, recorded AST/line fallback. `gate.run` makes each script idempotent by probing `verify()` before calling `apply()`.

**Tech Stack:** Python 3.10+ (stdlib only — `subprocess`, `json`, `ast`, `unittest`), the `hashline` binary (developed against 0.9.1), Markdown for skill docs.

**Spec:** `docs/superpowers/specs/2026-09-07-vertical-slice-planning-design.md`

## Global Constraints

- Skill lives at `skills/vertical-slice-planning/`, following the repo's existing skill layout (`SKILL.md` + `references/`).
- `taskkit.py` is **stdlib only**. No third-party imports, ever — it is copied verbatim into arbitrary target repositories.
- Python floor: **3.10**.
- hashline is **mandatory** for editing existing files. Generated task code may not use `grep`, `sed`, string-replace edit tools, or `open(...).write()`.
- All hashline invocations use `--json`. Success is `{"success": true, ...}`; failure is a dict with an `"error"` key and exit status 1.
- Anchors are resolved at **run** time. Never bake a `line:hash` into a plan-time script.
- **Drift halts (exit 3); tool failure degrades (fallback).** Never collapse the two.
- Task exit contract: `0` applied/already-applied and gates pass · `1` gate failed · `3` drift, halt and replan · `4` manual task awaiting edit.
- Gate tiers: `T0` structural (always) · `T1` component tests (always) · `T2` crossing end-to-end (mandatory when a task touches ≥2 components).
- **Deviation from spec, deliberate:** the spec says "pytest"; pytest is not installed in this repo and `taskkit.py` must stay dependency-free, so tests use stdlib `unittest`. Run with `python3 -m unittest discover -s tests -v` from `skills/vertical-slice-planning/`.
- Emitted plan directories (the skill's *output*, not this repo's plans) go to `docs/plans/YYYY-MM-DD-<feature>/` in the target repo.
- Commit after every task.

---

## File Structure

| File | Responsibility |
|---|---|
| `skills/vertical-slice-planning/SKILL.md` | Trigger, the six planning steps, red-flags table |
| `skills/vertical-slice-planning/references/taskkit.py` | Edit + gate engine; copied verbatim into every emitted plan |
| `skills/vertical-slice-planning/references/task_template.py` | Canonical scripted and manual task shapes |
| `skills/vertical-slice-planning/references/run.py` | Ordered runner + `--status`; copied into every emitted plan |
| `skills/vertical-slice-planning/references/plan_formats.md` | `plan.md` schema and `plan_superpowers.md` header rules |
| `skills/vertical-slice-planning/references/hashline_rules.md` | Fallback ladder, exit codes, banned-tool list |
| `skills/vertical-slice-planning/tests/helpers.py` | Scratch-repo fixture builder shared by all tests |
| `skills/vertical-slice-planning/tests/test_taskkit.py` | Unit coverage of the engine |
| `skills/vertical-slice-planning/tests/test_runner.py` | Coverage of `run.py` ordering, stopping, `--status` |
| `skills/vertical-slice-planning/tests/test_end_to_end.py` | Two-component fixture repo planned and executed to green |

Task ordering follows the skill's own rule: **Task 1 is a thin vertical slice through the entire seam** (task script → `taskkit` → `hashline` CLI → real file → gate → exit code). Later tasks thicken that path rather than adding unproven layers.

---

### Task 1: Thin end-to-end slice — read, swap, gate, exit 0

The whole seam, minimally: one `SWAP` op through the real `hashline` binary, verified, idempotent.

**Files:**
- Create: `skills/vertical-slice-planning/references/taskkit.py`
- Create: `skills/vertical-slice-planning/tests/helpers.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Anchor = namedtuple("Anchor", "n hash content")`
  - `class Drift(Exception)`, `class ManualTask(Exception)`, `class GateFailure(Exception)`, `class BackendUnavailable(Exception)`
  - `REPORT: dict` with keys `backend` (`"hashline"`/`"fallback"`), `tiers` (list), `warnings` (list)
  - `_hl(args: list[str]) -> dict`
  - `class Editor(path)` — context manager, methods `locate(expected, occurrence=1)`, `swap(anchor, lines)`, `commit()`
  - `class gate` with `structural(desc, predicate)` and `run(apply, verify) -> int`
  - `file_contains(path, text) -> bool`

- [ ] **Step 1: Write the fixture helper**

Create `skills/vertical-slice-planning/tests/helpers.py`:

```python
"""Shared scratch-repo fixture for taskkit tests."""
import os
import shutil
import sys
import tempfile
import unittest

REFS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "references")
sys.path.insert(0, REFS)

SAMPLE = 'def send(req):\n    return _post(req)\n\n\ndef ping():\n    return "ok"\n'


class ScratchRepo(unittest.TestCase):
    """Gives each test a temp dir, a sample file, and a clean taskkit REPORT."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="taskkit-test-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self.cwd)
        self.write("client.py", SAMPLE)
        import taskkit
        taskkit.REPORT.update(backend="hashline", tiers=[], warnings=[])

    def write(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path

    def read(self, name):
        with open(os.path.join(self.dir, name), encoding="utf-8") as fh:
            return fh.read()
```

- [ ] **Step 2: Write the failing test**

Create `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'taskkit'`

- [ ] **Step 4: Write the minimal engine**

Create `skills/vertical-slice-planning/references/taskkit.py`:

```python
"""taskkit — apply+verify engine for vertical-slice plan tasks.

Stdlib only. Copied verbatim into every emitted plan directory.
Edits go through the hashline CLI so that a stale anchor is rejected
instead of landing on the wrong line.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections import namedtuple

HASHLINE_BIN = os.environ.get("HASHLINE_BIN", "hashline")

Anchor = namedtuple("Anchor", "n hash content")
Op = namedtuple("Op", "kind first last lines")


class Drift(Exception):
    """The file moved under us: anchor gone or hash mismatch. Halt and replan."""


class ManualTask(Exception):
    """This task's edit needs a human or agent; its gate is still runnable."""


class GateFailure(Exception):
    """A gate ran and said no."""


class BackendUnavailable(Exception):
    """hashline could not be used at all. Internal: triggers the fallback."""


REPORT = {"backend": "hashline", "tiers": [], "warnings": []}


def _warn(msg):
    REPORT["warnings"].append(msg)
    print("WARN: " + msg, file=sys.stderr)


def _hl(args):
    """Run hashline with JSON output. Returns the parsed dict.

    Raises Drift on an anchor/hash rejection, FileNotFoundError on a missing
    target, BackendUnavailable when hashline itself cannot be used.
    """
    if shutil.which(HASHLINE_BIN) is None and not os.path.isfile(HASHLINE_BIN):
        raise BackendUnavailable(HASHLINE_BIN + " not found on PATH")
    try:
        proc = subprocess.run([HASHLINE_BIN] + args, capture_output=True, text=True)
    except OSError as exc:
        raise BackendUnavailable(str(exc))
    try:
        data = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        raise BackendUnavailable(
            "non-JSON output from hashline: %r / %r" % (proc.stdout[:200], proc.stderr[:200])
        )
    if "error" in data:
        err = data["error"]
        if "I/O error" in err or "No such file" in err:
            raise FileNotFoundError(err)
        if "changed since last read" in err or "hash" in err:
            raise Drift(err)
        raise BackendUnavailable(err)
    return data


def file_contains(path, text):
    """Structural-gate helper: does the file exist and contain this text?"""
    if not os.path.exists(path):
        return False
    with open(path, encoding="utf-8") as fh:
        return text in fh.read()


class Editor:
    """Anchored editor over one file. Buffers ops, emits one patch on exit."""

    def __init__(self, path):
        self.path = str(path)
        self._ops = []
        self._lines = []

    def __enter__(self):
        self._lines = self._read()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        return False

    def _read(self):
        data = _hl(["read", "--json", self.path])
        return [Anchor(l["n"], l["hash"], l["content"]) for l in data["lines"]]

    def locate(self, expected, occurrence=1):
        """Return the anchor of the line whose content is exactly `expected`.

        This replaces grep: matching and drift-checking are the same act,
        because the anchor carries the hash hashline will re-check.
        """
        hits = [a for a in self._lines if a.content == expected]
        if len(hits) < occurrence:
            raise Drift("%s: expected line not found: %r" % (self.path, expected))
        return hits[occurrence - 1]

    def swap(self, anchor, lines):
        self._ops.append(Op("swap", anchor, anchor, list(lines)))

    def commit(self):
        if not self._ops:
            return
        patch = self._render_patch()
        _hl(["patch", "--json", "--dry-run", self.path, patch])
        _hl(["patch", "--json", self.path, patch])
        self._ops = []

    def _render_patch(self):
        """Ops address ORIGINAL line numbers; hashline does not re-number."""
        out = ["*** Begin Patch"]
        for op in sorted(self._ops, key=lambda o: o.first.n):
            first, last = op.first, op.last
            if op.kind == "swap":
                if first.n == last.n:
                    out.append("SWAP %d:%s:" % (first.n, first.hash))
                else:
                    out.append("SWAP %d:%s..%d:%s:" % (first.n, first.hash, last.n, last.hash))
                out.extend("+" + line for line in op.lines)
            else:
                raise NotImplementedError(op.kind)
        out.append("*** End Patch")
        return "\n".join(out)


def _record(tier, desc, ok, seconds, detail=""):
    REPORT["tiers"].append(
        {"tier": tier, "desc": desc, "ok": bool(ok), "seconds": round(seconds, 3), "detail": detail}
    )
    if not ok:
        raise GateFailure("[%s] %s%s" % (tier, desc, (": " + detail) if detail else ""))


_PROBE_EXC = (GateFailure, Drift, AssertionError, FileNotFoundError, OSError)


class gate:
    """Tiered, runnable gates. T0 structural, T1 component, T2 crossing."""

    @staticmethod
    def structural(desc, predicate):
        start = time.time()
        ok = bool(predicate())
        _record("T0", desc, ok, time.time() - start)

    @staticmethod
    def run(apply, verify):
        """Idempotent driver. Probes verify() first, so a re-run is a no-op."""
        verify_only = "--verify-only" in sys.argv
        code = 0
        try:
            if verify_only:
                verify()
            else:
                if not _probe(verify):
                    apply()
                verify()
        except ManualTask as exc:
            print("MANUAL: %s" % exc, file=sys.stderr)
            code = 4
        except Drift as exc:
            print("DRIFT: %s" % exc, file=sys.stderr)
            code = 3
        except GateFailure as exc:
            print("GATE FAILED: %s" % exc, file=sys.stderr)
            code = 1
        REPORT["exit"] = code
        print(json.dumps(REPORT))
        return code


def _probe(verify):
    """Has this task already been done? Probe failures are answers, not errors."""
    saved = list(REPORT["tiers"])
    try:
        verify()
        return True
    except _PROBE_EXC:
        REPORT["tiers"] = saved
        return False
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): thin vertical slice — hashline-backed Editor, gate.run, exit contract"
```

---

### Task 2: Drift halts with exit 3

A stale anchor must stop the run, not fall back and not overwrite.

**Files:**
- Modify: `skills/vertical-slice-planning/references/taskkit.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: `Editor`, `gate.run`, `Drift` from Task 1.
- Produces: no new names — `Drift` now also raised by `Editor._read()` when a plan-time expected line is absent, and `gate.run` returns `3` for it.

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
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
```

Note: the `with` block's `__exit__` calls `commit()` only when no exception escaped; the explicit `commit()` inside the block is what raises here, so the outer block exits via that exception and does not commit twice.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_taskkit.TestDrift -v`
Expected: `test_drift_exits_3_and_writes_nothing` FAILS — `gate.run` currently lets `Drift` escape from `apply()` only if `_probe` did not swallow it; confirm the actual failure text before proceeding.

- [ ] **Step 3: Make drift survive the probe and reach the exit code**

In `taskkit.py`, replace `_probe` so a `Drift` raised *during probing* is treated as "not applied yet" (correct — the target line is not there because the work has not been done), while a `Drift` raised during `apply()` propagates. The code in Task 1 already does this; the change needed is in `commit()`, which must not swallow a rejected patch:

```python
    def commit(self):
        if not self._ops:
            return
        patch = self._render_patch()
        _hl(["patch", "--json", "--dry-run", self.path, patch])  # Drift raises here
        _hl(["patch", "--json", self.path, patch])
        self._ops = []
```

The dry run is what makes "writes nothing" true: the anchor is validated before any write is attempted. Confirm `_hl` maps `"changed since last read"` to `Drift` and not to `BackendUnavailable` — if the test fails, that mapping is the bug.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): drift halts with exit 3 and writes nothing"
```

---

### Task 3: Fallback backend — loud, recorded, and never used for drift

**Files:**
- Modify: `skills/vertical-slice-planning/references/taskkit.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: `Editor`, `Op`, `Anchor`, `REPORT`, `_warn`, `BackendUnavailable`.
- Produces:
  - `Editor._fallback_read() -> list[Anchor]` (hash is `None`)
  - `Editor._apply_fallback() -> None`
  - `REPORT["backend"] == "fallback"` and a `WARN: fallback backend used: ...` entry in `REPORT["warnings"]`

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_taskkit.TestFallback -v`
Expected: FAIL — `BackendUnavailable: /nonexistent/hashline not found on PATH`

- [ ] **Step 3: Add the fallback ladder**

In `taskkit.py`, replace `Editor._read` and `Editor.commit` and add the two fallback methods:

```python
    def __init__(self, path):
        self.path = str(path)
        self._ops = []
        self._lines = []
        self._trailing_nl = True

    def _read(self):
        try:
            data = _hl(["read", "--json", self.path])
            return [Anchor(l["n"], l["hash"], l["content"]) for l in data["lines"]]
        except BackendUnavailable as exc:
            _warn("fallback backend used: %s" % exc)
            REPORT["backend"] = "fallback"
            return self._fallback_read()

    def _fallback_read(self):
        with open(self.path, encoding="utf-8") as fh:
            text = fh.read()
        self._trailing_nl = text.endswith("\n")
        return [Anchor(i + 1, None, c) for i, c in enumerate(text.splitlines())]

    def commit(self):
        if not self._ops:
            return
        if REPORT["backend"] == "fallback":
            self._apply_fallback()
            self._ops = []
            return
        patch = self._render_patch()
        try:
            _hl(["patch", "--json", "--dry-run", self.path, patch])
            _hl(["patch", "--json", self.path, patch])
        except BackendUnavailable as exc:
            # Tool failure degrades. Drift, raised above as Drift, does not.
            _warn("fallback backend used: %s" % exc)
            REPORT["backend"] = "fallback"
            self._lines = self._fallback_read()
            self._apply_fallback()
        self._ops = []

    def _apply_fallback(self):
        """Re-verify every op's captured content, then splice bottom-up."""
        with open(self.path, encoding="utf-8") as fh:
            text = fh.read()
        lines = text.splitlines()
        trailing_nl = text.endswith("\n")
        for op in self._ops:
            for anchor in {op.first, op.last}:
                idx = anchor.n - 1
                if idx >= len(lines) or lines[idx] != anchor.content:
                    raise Drift(
                        "%s:%d changed since read (expected %r, got %r)"
                        % (self.path, anchor.n, anchor.content,
                           lines[idx] if idx < len(lines) else "<EOF>")
                    )
        for op in sorted(self._ops, key=lambda o: o.first.n, reverse=True):
            start, end = op.first.n - 1, op.last.n
            if op.kind == "swap":
                lines[start:end] = list(op.lines)
            elif op.kind == "delete":
                del lines[start:end]
            elif op.kind == "insert_before":
                lines[start:start] = list(op.lines)
            elif op.kind == "insert_after":
                lines[end:end] = list(op.lines)
            else:
                raise NotImplementedError(op.kind)
        out = "\n".join(lines) + ("\n" if trailing_nl else "")
        tmp = self.path + ".taskkit.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(out)
        os.replace(tmp, self.path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 11 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): loud recorded fallback backend for hashline unavailability"
```

---

### Task 4: Full op coverage — insert, delete, block swap, file creation

**Files:**
- Modify: `skills/vertical-slice-planning/references/taskkit.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: `Editor`, `Op`, `Drift`, `_hl`, `REPORT`.
- Produces:
  - `Editor.locate_contains(needle, occurrence=1) -> Anchor`
  - `Editor.locate_block(head_expected) -> tuple[Anchor, Anchor]`
  - `Editor.swap_range(first, last, lines)`, `Editor.insert_before(anchor, lines)`, `Editor.insert_after(anchor, lines)`, `Editor.delete(anchor)`
  - `create_file(path, content) -> None` (module level)

Note on hashline semantics, verified against 0.9.1: `SWAP.BLK` replaces only the *body* around an anchor, which is not what "replace this function" means. `locate_block` therefore uses `find-block --json` to get the exact line range and emits an explicit range `SWAP`, which is hash-checked at both ends.

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_taskkit.TestOps -v`
Expected: FAIL — `AttributeError: 'Editor' object has no attribute 'insert_after'`

- [ ] **Step 3: Implement the ops**

Add to `Editor` in `taskkit.py`:

```python
    def locate_contains(self, needle, occurrence=1):
        hits = [a for a in self._lines if needle in a.content]
        if len(hits) < occurrence:
            raise Drift("%s: no line containing %r" % (self.path, needle))
        return hits[occurrence - 1]

    def locate_block(self, head_expected):
        """Return (first, last) anchors of the syntactic block headed by this line."""
        head = self.locate(head_expected)
        if REPORT["backend"] == "hashline":
            try:
                data = _hl(["find-block", "--json", self.path, "%d:%s" % (head.n, head.hash)])
                numbers = [b["n"] for b in data["block_lines"]]
                return self._lines[min(numbers) - 1], self._lines[max(numbers) - 1]
            except BackendUnavailable as exc:
                _warn("fallback backend used: %s" % exc)
                REPORT["backend"] = "fallback"
        return self._fallback_block(head)

    def _fallback_block(self, head):
        """Indentation-scan block detection: head line plus its more-indented body."""
        base = len(head.content) - len(head.content.lstrip())
        last = head
        for anchor in self._lines[head.n:]:
            stripped = anchor.content.strip()
            indent = len(anchor.content) - len(anchor.content.lstrip())
            if stripped and indent <= base:
                break
            if stripped:
                last = anchor
        return head, last

    def swap_range(self, first, last, lines):
        self._ops.append(Op("swap", first, last, list(lines)))

    def insert_before(self, anchor, lines):
        self._ops.append(Op("insert_before", anchor, anchor, list(lines)))

    def insert_after(self, anchor, lines):
        self._ops.append(Op("insert_after", anchor, anchor, list(lines)))

    def delete(self, anchor):
        self._ops.append(Op("delete", anchor, anchor, []))
```

Extend `_render_patch` to emit the remaining op kinds:

```python
            elif op.kind == "delete":
                if first.n == last.n:
                    out.append("DEL %d:%s" % (first.n, first.hash))
                else:
                    out.append("DEL %d..%d" % (first.n, last.n))
            elif op.kind in ("insert_before", "insert_after"):
                keyword = "INS.PRE" if op.kind == "insert_before" else "INS.POST"
                out.append("%s %d:%s:" % (keyword, first.n, first.hash))
                out.extend("+" + line for line in op.lines)
```

Add the module-level file creator:

```python
def create_file(path, content):
    """Create a new file. Idempotent; conflicting existing content is Drift."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
        if existing == content:
            return
        raise Drift("%s already exists with different content" % path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    try:
        _hl(["write", "--json", path, content])
    except BackendUnavailable as exc:
        _warn("fallback backend used: %s" % exc)
        REPORT["backend"] = "fallback"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 19 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): insert/delete/block-swap ops and idempotent file creation"
```

---

### Task 5: Gate tiers T1 and T2 with timing in the report

**Files:**
- Modify: `skills/vertical-slice-planning/references/taskkit.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: `_record`, `GateFailure`, `REPORT`.
- Produces:
  - `gate.component(desc, cmd, cwd=None)` — T1, runs a command, non-zero exit is a gate failure
  - `gate.crossing(desc, cmd=None, check=None)` — T2, same but tier `T2`; accepts either a command or a callable
  - Each `REPORT["tiers"]` entry: `{"tier", "desc", "ok", "seconds", "detail"}`

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
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
```

Add `import sys` at the top of the test file.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_taskkit.TestTiers -v`
Expected: FAIL — `AttributeError: type object 'gate' has no attribute 'component'`

- [ ] **Step 3: Implement the tiers**

Add to `class gate` in `taskkit.py`:

```python
    @staticmethod
    def _cmd(tier, desc, cmd, cwd=None):
        start = time.time()
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        detail = ((proc.stdout or "") + (proc.stderr or "")).strip()[-2000:]
        _record(tier, desc, proc.returncode == 0, time.time() - start, detail)

    @staticmethod
    def component(desc, cmd, cwd=None):
        """T1 — the touched component's own tests."""
        gate._cmd("T1", desc, cmd, cwd)

    @staticmethod
    def crossing(desc, cmd=None, check=None, cwd=None):
        """T2 — a real end-to-end call through the seam this task wired.

        Mandatory whenever a task touches two or more components.
        """
        if cmd is not None:
            gate._cmd("T2", desc, cmd, cwd)
            return
        if check is None:
            raise ValueError("crossing() needs cmd= or check=")
        start = time.time()
        ok = bool(check())
        _record("T2", desc, ok, time.time() - start)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 24 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): T1 component and T2 crossing gates with timed report entries"
```

---

### Task 6: Manual tasks — exit 4, gate still runnable

**Files:**
- Modify: `skills/vertical-slice-planning/references/taskkit.py`
- Test: `skills/vertical-slice-planning/tests/test_taskkit.py`

**Interfaces:**
- Consumes: `ManualTask`, `gate.run`.
- Produces: `gate.run` returns `4` when `apply()` raises `ManualTask`, and `0` once the edit exists — with the instructions printed to stderr.

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_taskkit.py`:

```python
class TestManual(ScratchRepo):
    def _task(self):
        def apply():
            raise taskkit.ManualTask(
                "Rewrite send() to take a RetryPolicy object; see plan_superpowers.md Task 07."
            )

        def verify():
            gate.structural("RetryPolicy threaded", lambda: taskkit.file_contains("client.py", "RetryPolicy"))

        return apply, verify

    def test_manual_task_exits_4_when_not_done(self):
        apply, verify = self._task()
        self.assertEqual(gate.run(apply, verify), 4)

    def test_manual_task_exits_0_once_the_edit_exists(self):
        self.write("client.py", "def send(req, policy: RetryPolicy):\n    return _post(req)\n")
        apply, verify = self._task()
        self.assertEqual(gate.run(apply, verify), 0)

    def test_manual_instructions_are_printed(self):
        apply, verify = self._task()
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            gate.run(apply, verify)
        self.assertIn("RetryPolicy object", err.getvalue())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_taskkit.TestManual -v`
Expected: `test_manual_task_exits_4_when_not_done` FAILS if `ManualTask` is not caught before the generic handlers — run it and confirm the actual behavior. If Task 1's `gate.run` already handles it, these tests pass immediately; that is a valid outcome, and Step 3 is then a no-op verification.

- [ ] **Step 3: Confirm or fix the ordering in `gate.run`**

`except ManualTask` must precede `except Drift` and `except GateFailure`, and `_PROBE_EXC` must **not** include `ManualTask` — a manual task's gate is probed like any other, and `apply()` is reached only when the probe says the work is undone:

```python
        except ManualTask as exc:
            print("MANUAL: %s" % exc, file=sys.stderr)
            code = 4
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 27 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): manual tasks exit 4 with runnable gates"
```

---

### Task 7: `run.py` — ordered execution that stops at the first red gate

**Files:**
- Create: `skills/vertical-slice-planning/references/run.py`
- Test: `skills/vertical-slice-planning/tests/test_runner.py`

**Interfaces:**
- Consumes: the task exit contract (`0/1/3/4`) and the JSON report line each task prints as its last line of stdout.
- Produces:
  - `discover(plan_dir) -> list[str]` — sorted `tasks/task_*.py` paths
  - `run_task(path, verify_only=False) -> tuple[int, dict]`
  - `main(argv) -> int` — CLI: `python3 run.py [--status]`

- [ ] **Step 1: Write the failing test**

Create `skills/vertical-slice-planning/tests/test_runner.py`:

```python
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


class TestRunner(ScratchRepo):
    def _plan(self, specs):
        os.makedirs("tasks", exist_ok=True)
        out = os.path.join(self.dir, "order.log")
        for name, template in specs:
            body = template.format(refs=REFS, out=out, name=name)
            self.write(os.path.join("tasks", name + ".py"), body)
        return out

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


if __name__ == "__main__":
    unittest.main()
```

Note: `run_task` must tolerate a task whose stdout has content before the report line — it reads the **last** parseable JSON line.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_runner -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'run'`

- [ ] **Step 3: Write the runner**

Create `skills/vertical-slice-planning/references/run.py`:

```python
#!/usr/bin/env python3
"""Ordered runner for a vertical-slice plan directory.

    python3 run.py            # run tasks in order, stop at the first non-zero
    python3 run.py --status   # probe every gate, report state, change nothing
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

EXIT_MEANING = {
    0: "PASS",
    1: "GATE FAILED",
    3: "DRIFT — halt and replan",
    4: "MANUAL — awaiting edit",
}


def discover(plan_dir):
    """Task scripts in execution order, sorted by their numeric prefix."""
    paths = glob.glob(os.path.join(plan_dir, "tasks", "task_*.py"))

    def key(path):
        match = re.search(r"task_(\d+)", os.path.basename(path))
        return (int(match.group(1)) if match else 0, os.path.basename(path))

    return sorted(paths, key=key)


def run_task(path, verify_only=False):
    """Run one task script. Returns (exit_code, report_dict)."""
    cmd = [sys.executable, path] + (["--verify-only"] if verify_only else [])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    report = {}
    for line in reversed(proc.stdout.splitlines()):
        try:
            candidate = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(candidate, dict):
            report = candidate
            break
    report.setdefault("stderr", proc.stderr.strip()[-2000:])
    return proc.returncode, report


def main(argv):
    argv = list(argv)
    status_only = "--status" in argv
    if status_only:
        argv.remove("--status")
    plan_dir = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))

    tasks = discover(plan_dir)
    if not tasks:
        print("no tasks found in %s/tasks" % plan_dir, file=sys.stderr)
        return 1

    results = []
    for path in tasks:
        name = os.path.basename(path)
        code, report = run_task(path, verify_only=status_only)
        results.append((name, code, report))
        label = EXIT_MEANING.get(code, "EXIT %d" % code)
        print("%-40s %s" % (name, label))
        if report.get("backend") == "fallback":
            print("    backend: fallback — %s" % "; ".join(report.get("warnings", [])))
        if code != 0:
            print(json.dumps(report, indent=2))
            if not status_only:
                print("stopping: %s exited %d" % (name, code), file=sys.stderr)
                return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 31 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): ordered runner that stops at the first red gate"
```

---

### Task 8: `--status` probes gates and syncs the human plan's checkboxes

**Files:**
- Modify: `skills/vertical-slice-planning/references/run.py`
- Test: `skills/vertical-slice-planning/tests/test_runner.py`

**Interfaces:**
- Consumes: `discover`, `run_task`, `main` from Task 7.
- Produces: `sync_checkboxes(plan_dir, results) -> int` — rewrites `plan_superpowers.md`, returns the number of lines changed. Marker convention: each task's checkbox line ends with `<!-- task_NN_name.py -->`.

- [ ] **Step 1: Write the failing tests**

Append to `skills/vertical-slice-planning/tests/test_runner.py`:

```python
PLAN_MD = """\
# Demo Implementation Plan

- [ ] **Task 01 — write the log line** <!-- task_01_a.py -->
- [x] **Task 02 — stale tick that must be cleared** <!-- task_02_bad.py -->
- [ ] **Task 99 — no such script** <!-- task_99_ghost.py -->
"""


class TestStatusSync(ScratchRepo):
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
        changed = runner.sync_checkboxes(self.dir, [("task_01_a.py", 0, {}), ("task_02_bad.py", 1, {})])
        self.assertEqual(changed, 1)
```

`TestStatusSync` reuses `_plan` — move that helper from `TestRunner` onto a shared base class in the same file (`class PlanFixture(ScratchRepo)`) and have both test classes inherit it.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_runner.TestStatusSync -v`
Expected: FAIL — `AttributeError: module 'run' has no attribute 'sync_checkboxes'`

- [ ] **Step 3: Implement checkbox syncing**

Add to `run.py`:

```python
CHECKBOX = re.compile(r"^(\s*- \[)([ x])(\]\s.*<!--\s*(task_[\w.]+\.py)\s*-->\s*)$")


def sync_checkboxes(plan_dir, results):
    """Rewrite plan_superpowers.md checkboxes from measured gate results.

    A line is touched only when its marker names a task we actually ran, so
    hand-written checkboxes for anything else are left alone.
    """
    path = os.path.join(plan_dir, "plan_superpowers.md")
    if not os.path.exists(path):
        return 0
    state = {name: code == 0 for name, code, _ in results}
    changed = 0
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for i, line in enumerate(lines):
        match = CHECKBOX.match(line)
        if not match:
            continue
        head, mark, tail, name = match.groups()
        if name not in state:
            continue
        want = "x" if state[name] else " "
        if want != mark:
            lines[i] = head + want + tail
            changed += 1
    if changed:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    return changed
```

Then, in `main`, after the loop and before `return 0`, sync when probing:

```python
    if status_only:
        changed = sync_checkboxes(plan_dir, results)
        passing = sum(1 for _, code, _ in results if code == 0)
        print("%d/%d gates green (%d checkbox lines updated)" % (passing, len(results), changed))
```

and make the mid-loop early return conditional on `not status_only` (already the case in Task 7's code — confirm it).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 34 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "feat(vsp): --status probes gates and syncs plan_superpowers.md checkboxes"
```

---

### Task 9: The skill documents

**Files:**
- Create: `skills/vertical-slice-planning/SKILL.md`
- Create: `skills/vertical-slice-planning/references/task_template.py`
- Create: `skills/vertical-slice-planning/references/plan_formats.md`
- Create: `skills/vertical-slice-planning/references/hashline_rules.md`
- Test: manual review plus a syntax check on the template

**Interfaces:**
- Consumes: every name produced by Tasks 1–8 — the documents must reference them exactly.
- Produces: no code interfaces; `task_template.py` must be importable and syntactically valid.

- [ ] **Step 1: Write `task_template.py`**

Create `skills/vertical-slice-planning/references/task_template.py`:

```python
"""Canonical task shapes. Copy one of these per task; delete the other."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import taskkit
from taskkit import Editor, ManualTask, gate

# ---------------------------------------------------------------- scripted --
KIND = "scripted"
TIER = "T2"
TOUCHES = ["client", "svc/orders"]
CROSSES = ["client -> orders HTTP"]


def apply():
    """Thread the retry setting from the client through to the orders service."""
    with Editor("client/http.py") as ed:
        ed.swap(
            ed.locate("    return self._send(req)"),
            ["    return self._send(req, retries=self.retries)"],
        )
    with Editor("svc/orders/handler.py") as ed:
        ed.insert_after(
            ed.locate("def handle(req):"),
            ["    retries = int(req.headers.get('x-retries', 0))"],
        )
    taskkit.create_file("svc/orders/retry.py", "MAX = 3\n")


def verify():
    gate.structural(
        "client passes retries",
        lambda: taskkit.file_contains("client/http.py", "retries=self.retries"),
    )
    gate.component("orders unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "svc/orders/tests"])
    gate.crossing("client reaches orders with a retry header", cmd=["./scripts/smoke_retry.sh"])


if __name__ == "__main__":
    raise SystemExit(gate.run(apply, verify))


# ------------------------------------------------------------------ manual --
# KIND = "manual"
#
# def apply():
#     raise ManualTask(
#         "Rewrite OrderService.dispatch() to take a RetryPolicy instead of an int.\n"
#         "Steps are in plan_superpowers.md, Task 07. The gate below is runnable now."
#     )
#
# def verify():
#     gate.structural("RetryPolicy in use", lambda: taskkit.file_contains("svc/orders/service.py", "RetryPolicy"))
#     gate.component("orders unit tests", [sys.executable, "-m", "unittest", "discover", "-s", "svc/orders/tests"])
```

- [ ] **Step 2: Verify the template is syntactically valid**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m py_compile references/task_template.py && echo OK`
Expected: `OK`

- [ ] **Step 3: Write `hashline_rules.md`**

Create `skills/vertical-slice-planning/references/hashline_rules.md`:

```markdown
# hashline Rules for Emitted Tasks

hashline is mandatory for editing existing files. Emitted task code must not use
`grep`, `sed`, string-replace edit tools, or `open(...).write()` — those bypass
the drift check that makes anchored editing worth having.

## Why anchors, not line numbers

Every line carries an `xxh32` hash. You target `line:hash`. If the file drifted
since the read, the patch is rejected instead of landing on the wrong line.
`Editor.locate()` is the replacement for search: it matches content in
hashline's own read output and hands back the anchor, so finding and
drift-checking are one act.

**Anchors are resolved at run time, never at plan time.** This is what lets
task 07's script — written before tasks 01–06 ran — still target the right line.

## The fallback ladder

| Situation | Response |
|---|---|
| Patch applies | `exit 0`, `backend: hashline` |
| hashline rejects on drift (`content changed since last read`) | `exit 3`, halt and replan. **Never fall back.** |
| Anchor content not present at all | `Drift` → `exit 3` |
| hashline binary missing, crashes, or returns non-JSON | AST/line fallback, `WARN: fallback backend used`, `backend: fallback` in the report |

**Drift halts; tool failure degrades.** Collapsing the two would let a genuine
conflict be silently overwritten by the fallback path.

## Exit contract

| Code | Meaning |
|---|---|
| `0` | Applied (or already applied) and all gates pass |
| `1` | Gate failed — the work is wrong |
| `3` | Drift — halt and replan |
| `4` | Manual task awaiting a human or agent edit |

## CLI facts (hashline 0.9.1)

- `hashline read --json <file>` → `{"hash", "path", "lines": [{"n", "hash", "content"}]}`
- `hashline patch --json [--dry-run] <file> <patch>` → `{"success": true, ...}` or
  `{"error": ...}` with exit status 1
- `hashline find-block --json <file> <line:hash>` → `{"block_lines": [...]}`
- Ops within one patch address **original** line numbers; do not re-number for
  earlier inserts or deletes in the same patch.
- Prefer `find-block` plus an explicit range `SWAP` over `SWAP.BLK`: `SWAP.BLK`
  replaces only the body around the anchor, which is not what "replace this
  function" means.
```

- [ ] **Step 4: Write `plan_formats.md`**

Create `skills/vertical-slice-planning/references/plan_formats.md`:

```markdown
# Plan Directory Formats

    docs/plans/YYYY-MM-DD-<feature>/
      plan.md                machine-facing index
      plan_superpowers.md    human-facing plan
      taskkit.py             copied verbatim from the skill
      run.py                 copied verbatim from the skill
      tasks/task_NN_*.py     one apply+verify script per task

The `tasks/` scripts are the single source of truth. Both markdown files are
generated views. `run.py --status` probes every gate and rewrites the
checkboxes in `plan_superpowers.md`, so the human document reports measured
state rather than remembered state.

## plan.md — machine-facing

A seam map, then one table row per task. No prose beyond the seam map.

```markdown
# <Feature> — Plan Index

## Seams

| Seam | From | To | Verified by |
|---|---|---|---|
| client -> orders HTTP | client | svc/orders | scripts/smoke_retry.sh |

## Tasks

| # | Title | Kind | Tier | Touches | Crosses | Files | Script |
|---|---|---|---|---|---|---|---|
| 01 | Wire retry header end-to-end | scripted | T2 | client, svc/orders | client -> orders HTTP | client/http.py, svc/orders/handler.py | tasks/task_01_wire_seam.py |
```

## plan_superpowers.md — human-facing

Follows the superpowers writing-plans format: the plan header (Goal,
Architecture, Tech Stack, Spec), a Global Constraints section with
project-wide requirements copied verbatim, then per-task bite-sized steps.

Every task gets exactly one checkbox line carrying its script marker, which is
what `--status` rewrites:

```markdown
- [ ] **Task 01 — Wire retry header end-to-end** <!-- task_01_wire_seam.py -->
```

The marker comment must be the last thing on the line. Lines without a marker,
or whose marker names a script the runner did not run, are never touched.
```

- [ ] **Step 5: Write `SKILL.md`**

Create `skills/vertical-slice-planning/SKILL.md`:

```markdown
---
name: vertical-slice-planning
description: >
  Use this skill when the user asks for an implementation plan for work that spans
  multiple components or services — "plan this out", "break this into tasks",
  "write a plan for wiring X to Y". Produces an executable plan directory: tasks
  ordered as vertical slices so every unit of work verifies the whole path it
  touches instead of deferring integration to the end, each task a single
  idempotent Python script that applies its change through hashline and proves it
  with runnable gates. Plan-only — it emits the directory and stops.
---

# Vertical Slice Planning

Ordinary plans are horizontal: build the backend, then the client, then wire them
together. Every integration defect surfaces at the end, at maximum cost, and
progress is unmeasurable until the last step. Two habits cause it — gates written
as prose that nothing forces to run, and edits described rather than executed.

This skill emits a plan where neither is possible. Each task is a Python script
that applies its own change and proves it, and the ordering guarantees a task
never defers the integration it depends on.

**Announce at start:** "I'm using the vertical-slice-planning skill to create the plan."

**This skill is plan-only.** Emit the directory and stop. Execution is a separate
act by a human or another agent.

## Output

    docs/plans/YYYY-MM-DD-<feature>/
      plan.md                machine-facing index
      plan_superpowers.md    human-facing plan
      taskkit.py             copied verbatim from references/
      run.py                 copied verbatim from references/
      tasks/task_NN_*.py     one apply+verify script per task

See `references/plan_formats.md` for both document schemas.

## The Six Steps

**1. Seam map first.** Before any task exists, enumerate the components and the
*seams* between them — HTTP route, queue topic, DB table, module import. Seams,
not components, drive the ordering.

**2. Order as vertical slices.** Each task is a thin path through every component
it touches. Task 1 of a multi-component feature wires the seam end-to-end with
the most trivial payload that can be verified: a hardcoded response, one field,
one row. Later tasks thicken it. A task that adds capability to exactly one
component without exercising a seam is allowed only when no seam is yet in scope.

**3. Assign gate tiers.** Each task's `verify()` composes these; declare the tier
in `plan.md`.

| Tier | Runs | Required when |
|---|---|---|
| T0 structural | asserts the edit landed | always |
| T1 component | the touched component's own tests | always |
| T2 crossing | a real end-to-end call through the seam this task wired | task touches 2+ components |

T2 is neither optional nor deferrable — it is the property this skill exists to
buy. If a T2 gate cannot be run in the target environment, **the plan is wrong**:
say so now rather than emitting a task that cannot prove itself.

**4. Decide scripted vs manual**, per task, in this order:

- New file → **scripted**, full content embedded in `apply()` via `create_file`.
- Edit whose target set and result are determinable now → **scripted** via `Editor`.
- Otherwise (design judgement, ambiguous refactor) → **manual**: prose steps in
  `plan_superpowers.md`, `apply()` raises `ManualTask` carrying them.

`verify()` is always fully written and runnable. **The gate never goes manual.**

**5. Emit the directory.** Scripts first; both markdown files are generated from
them. Copy `references/taskkit.py` and `references/run.py` in verbatim — do not
regenerate or edit them. Start each task from `references/task_template.py`.

**6. Self-check before handing over.** Run `python3 run.py --status` in the emitted
directory. Every gate must **fail cleanly** (exit 1) rather than error. A gate
that errors is a defect in the plan — fix it before handing over.

## Editing Rules

All edits go through `taskkit.Editor`, which uses hashline. `grep`, `sed`,
string-replace tools and `open(...).write()` are banned in emitted code. Anchors
are resolved at run time, never baked in at plan time. Drift halts with exit 3;
hashline being unavailable degrades to a loud recorded fallback. Full details and
the exit contract: `references/hashline_rules.md`.

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll add the integration test as the last task" | That is the horizontal plan this skill exists to prevent. T2 belongs to the first task that crosses the seam. |
| "This task only touches the backend, so T1 is enough" | Check the seam map. If it changes something the other side reads, it crosses. |
| "The gate is obvious, prose is fine" | A gate that isn't runnable code isn't a gate. Write `verify()`. |
| "I'll bake in the line number I read just now" | The file will have moved by then. Use `locate()` at run time. |
| "hashline rejected the patch, I'll use the fallback" | Rejection is drift — a true signal. Exit 3 and replan. |
| "This edit is too subtle to script, so the task is manual" | Manual means the *edit* is manual. The gate is still fully written. |
| "The plan is done, I'll start on task 1" | This skill is plan-only. Emitting the directory is the deliverable. |
```

- [ ] **Step 6: Verify every referenced name exists**

Run:
```bash
cd ~/development/ai/skills/vertical-slice-planning
for name in Editor locate locate_contains locate_block swap swap_range insert_before insert_after delete create_file ManualTask Drift GateFailure file_contains; do
  grep -q "$name" references/taskkit.py || echo "MISSING from taskkit.py: $name"
done
python3 -m unittest discover -s tests -v
```
Expected: no `MISSING` lines; 34 tests PASS

- [ ] **Step 7: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "docs(vsp): SKILL.md, task template, plan formats, hashline rules"
```

---

### Task 10: End-to-end proof — a two-component fixture planned and run to green

The skill's own crossing gate. Everything before this proves parts; this proves the artifact runs.

**Files:**
- Create: `skills/vertical-slice-planning/tests/test_end_to_end.py`
- Modify: `skills/vertical-slice-planning/SKILL.md` (only if the run reveals a documented step that does not hold)

**Interfaces:**
- Consumes: `taskkit`, `run.py`, `task_template.py`, and the formats in `plan_formats.md`.
- Produces: no new interfaces — a regression test that the emitted shape works.

- [ ] **Step 1: Write the failing end-to-end test**

Create `skills/vertical-slice-planning/tests/test_end_to_end.py`:

```python
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
assert "x-retries" in send.__doc__ or True
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
        self.assertEqual(runner.main([self.dir]), 0)
        self.assertIn("x-retries", self.read("client.py"))
        self.assertIn("retries", self.read("service.py"))

    def test_rerunning_the_whole_plan_is_a_no_op(self):
        self._build_plan()
        runner.main([self.dir])
        after_first = (self.read("client.py"), self.read("service.py"))
        self.assertEqual(runner.main([self.dir]), 0)
        self.assertEqual((self.read("client.py"), self.read("service.py")), after_first)

    def test_status_ticks_the_checkbox_after_a_green_run(self):
        self._build_plan()
        runner.main([self.dir])
        runner.main(["--status", self.dir])
        self.assertIn("- [x] **Task 01", self.read("plan_superpowers.md"))

    def test_gates_fail_cleanly_before_the_work_is_done(self):
        """Step 6 of the skill: every gate must fail, not error, on a fresh plan."""
        self._build_plan()
        code, report = runner.run_task(
            os.path.join(self.dir, "tasks", "task_01_wire_seam.py"), verify_only=True
        )
        self.assertEqual(code, 1, report)
        self.assertFalse(report["tiers"][0]["ok"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest tests.test_end_to_end -v`
Expected: FAIL — the fixture files are unedited, so the crossing gate's `smoke.py` raises `KeyError: 'retries'` before `apply()` runs. Confirm the failure is the *gate*, not a `taskkit` error.

- [ ] **Step 3: Fix whatever the run exposes**

No new feature is expected here. If a test fails for any reason other than the fixture's own logic, the defect is in `taskkit.py` or `run.py` — fix it there, not in the test. Likely candidates, in order:
1. `_probe` swallowing an exception type it should not (adjust `_PROBE_EXC`).
2. `run_task` running with the wrong `cwd`, so relative paths in a task miss.
3. Brace escaping in the fixture template — the task source uses `.format()`, so literal braces must be doubled (they are, above).

- [ ] **Step 4: Run the full suite**

Run: `cd ~/development/ai/skills/vertical-slice-planning && python3 -m unittest discover -s tests -v`
Expected: 38 tests PASS

- [ ] **Step 5: Commit**

```bash
cd ~/development/ai
git add skills/vertical-slice-planning
git commit -m "test(vsp): end-to-end fixture — two components, one seam, run to green"
```

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| Artifact layout | 7, 8, 9 (`plan_formats.md`), 10 |
| `plan.md` schema | 9 |
| `plan_superpowers.md` + generated views | 8, 9 |
| Task script shape, `gate.run` idempotence | 1, 9 |
| Exit contract 0/1/3/4 | 1, 2, 5, 6, 7 |
| `Editor`, run-time anchors, `locate` replaces search | 1, 4 |
| One patch per file, original numbering | 1, 4 |
| Fallback ladder, drift-vs-tool-failure | 2, 3 |
| Gate tiers T0/T1/T2 | 1, 5 |
| Planning algorithm (6 steps) | 9 |
| Scripted vs manual | 6, 9 |
| Skill structure | 9 |
| Testing: apply, idempotence, drift, fallback, `Error:` handling | 1, 2, 3 |
| End-to-end fixture repo | 10 |

`run.py` is listed in the spec's artifact but not its skill-structure block; this plan ships it from `references/` alongside `taskkit.py`, for the same reason — one tested copy, inherited by every plan.

**Placeholder scan:** no TBDs; every code step carries runnable code; Task 6 Step 3 and Task 10 Step 3 are verification steps with explicit criteria rather than "implement later".

**Type consistency:** `Anchor`/`Op` field names, `REPORT` keys (`backend`, `tiers`, `warnings`, `exit`), `_PROBE_EXC`, and the `gate.structural/component/crossing/run` signatures are used identically in Tasks 1–10 and in `task_template.py`. The checkbox marker format is identical in `run.py`, `plan_formats.md`, and both test files.
