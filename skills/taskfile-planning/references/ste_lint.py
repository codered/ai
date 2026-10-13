#!/usr/bin/env python3
"""Validate a Taskfile.ste plan.

Usage: ste_lint.py FILE [--waves | --json | --audit TASK_ID]

Exit 0: the file is valid. Exit 1: errors, one per line as FILE:LINE: CODE message.
Exit 2: usage or IO error. Standard library only.

--audit TASK_ID reads changed paths from stdin, one per line, and prints each path
that the task's FILES do not match. It exits 1 when it prints a path. It exits 2, with
the lint errors on stderr, when FILE is invalid or TASK_ID is unknown.
"""
import argparse
import json
import re
import sys

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
    "G001": "DEPENDS names an unknown task",
    "G002": "${id.key} names an unknown task",
    "G003": "${id.key} names an OUTPUT the task does not declare",
    "G004": "dependency cycle",
    "G005": "FILES overlap within a wave",
    "P001": "task PERMIT is not inside a GLOBAL PERMIT",
    "P002": "FILES glob is not inside the write PERMIT",
    "P003": "PERMIT or FILES glob is forbidden by a DENY",
    "P004": "PERMIT spawn is not allowed",
    "P005": "VERIFY command is not inside PERMIT run",
    "F001": "FLOW step is not a TOOL role or a built-in step",
    "F002": "SKIP names a step that is not in FLOW",
    "F003": "SKIP of verify or report",
    "F004": "TOOL role declared twice",
    "X001": "unknown state",
    "X002": "BECAUSE must go with completed_failure, and only with it",
    "X003": "BY must go with blocked, and only with it",
    "X004": "BY names a task that is not a failed or blocked dependency",
    "X005": "task started or finished before a dependency succeeded",
    "T001": "sentence has more than 20 words",
    "T002": "rejected word; use the approved word",
    "T003": "word that adds no meaning",
    "T004": "sentence starts with an -ing word",
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


def lint(source):
    """Return (model, errors). errors is a sorted list of (line, code, message)."""
    model = parse(source)
    if not model.errors:
        for check in SEMANTIC_CHECKS:
            check(model)
    return model, sorted(model.errors, key=lambda e: (e[0], e[1]))


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
    parser = argparse.ArgumentParser(description="Validate a Taskfile.ste plan.")
    parser.add_argument("file")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--waves", action="store_true", help="print one line per wave")
    mode.add_argument("--json", action="store_true", help="print the plan as JSON")
    mode.add_argument("--audit", metavar="TASK_ID",
                      help="print each path from stdin that the task's FILES do not match")
    args = parser.parse_args(argv)
    try:
        with open(args.file, encoding="utf-8") as handle:
            source = handle.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"{args.file}: {exc}", file=sys.stderr)
        return 2
    model, errors = lint(source)
    if errors:
        # In --audit mode stdout carries only paths, so lint errors go to stderr with exit 2.
        auditing = args.audit is not None
        for line, code, message in errors:
            print(f"{args.file}:{line}: {code} {message}", file=sys.stderr if auditing else sys.stdout)
        return 2 if auditing else 1
    if args.waves:
        for number, wave in enumerate(model.waves, 1):
            print(f"wave {number}: {' '.join(wave)}")
    elif args.json:
        print(json.dumps(to_json(model), indent=2))
    elif args.audit is not None:
        return audit(model, args.audit, sys.stdin.read().splitlines())
    return 0


if __name__ == "__main__":
    sys.exit(main())
