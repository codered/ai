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
