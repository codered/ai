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


def run_task(path, verify_only=False, repo_root=None):
    """Run one task script. Returns (exit_code, report_dict).

    Tasks always run with cwd = the target repo root, never the plan directory.
    """
    if repo_root is None:
        repo_root = os.getcwd()
    cmd = [sys.executable, path] + (["--verify-only"] if verify_only else [])
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)
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

    repo_root = os.getcwd()
    if "--repo-root" in argv:
        idx = argv.index("--repo-root")
        if idx + 1 < len(argv):
            repo_root = argv[idx + 1]
            argv.pop(idx + 1)
            argv.pop(idx)

    plan_dir = argv[0] if argv else os.path.dirname(os.path.abspath(__file__))

    tasks = discover(plan_dir)
    if not tasks:
        print("no tasks found in %s/tasks" % plan_dir, file=sys.stderr)
        return 1

    results = []
    for path in tasks:
        name = os.path.basename(path)
        code, report = run_task(path, verify_only=status_only, repo_root=repo_root)
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
