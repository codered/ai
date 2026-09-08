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

    # Try stdout first, then stderr if stdout is empty (hashline puts errors in stderr with --json)
    json_text = proc.stdout.strip()
    if not json_text and proc.stderr.strip():
        json_text = proc.stderr.strip()

    try:
        data = json.loads(json_text)
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
        self._committed = False
        self._trailing_nl = True

    def __enter__(self):
        self._lines = self._read()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None and not self._committed:
            self.commit()
        return False

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
        self._committed = True
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
