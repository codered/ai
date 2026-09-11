#!/usr/bin/env python3
"""Execute a worker plan in a scratch clone and check every stated expected output.

Usage:
    simulate_plan.py PLAN.md REPO [--at REV] [--identity "NAME <EMAIL>"] [--keep] [--timeout SECONDS]

The plan is read the way a worker reads it. These directives are executed;
every other code block is treated as illustration and ignored:

  In `path`, find: <block>  Replace with: <block>   exact replace; old text must occur once
  Replace the whole contents of `path` with: <block>  overwrite the file
  Create `path` with: <block>                         new file; fails if it exists
  Append ... to the end of `path`: <block>            append after one blank line
  Save this exact content to `path`: <block>          write a file (chmod +x for .sh)
  ```bash block                                       run from the repository root
  ```bash block, then "Expected ..." + ```text block  run, then compare output exactly

Output comparison ignores Go test durations. Write <sha> wherever a commit
hash may vary; a literal hash must match exactly, so a plan can pin its
starting commit. The clone contains only committed files, as a worker's fresh
checkout would, except that REPO's git identity is copied into the clone,
because a worker commits in REPO itself. No identity is ever invented: pass
--identity only if the worker will be told to set one. Exit status is 0 only
if no problem was found.
"""
import argparse
import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile

FENCE = re.compile(r'^```([\w-]*)\s*$')
DIRECTIVES = {
    'save': re.compile(r'Save this exact content to `([^`]+)`'),
    'find': re.compile(r'In `([^`]+)`, find\b'),
    'whole': re.compile(r'Replace the whole contents of `([^`]+)` with'),
    'create': re.compile(r'\bCreate `([^`]+)` with\b'),
    'append': re.compile(r'\b(?:Append|Add)\b[^\n]*?\bend\**\s+of\s+`([^`]+)`'),
}


def parse_blocks(text):
    """Return one dict per fenced block, with the prose that precedes it."""
    lines = text.split('\n')
    blocks, prose_start, i = [], 0, 0
    while i < len(lines):
        m = FENCE.match(lines[i])
        if not m:
            i += 1
            continue
        j = i + 1
        while j < len(lines) and lines[j].rstrip() != '```':
            j += 1
        if j == len(lines):
            sys.exit(f"plan error: code block opened at line {i + 1} is never closed")
        blocks.append({'prose': '\n'.join(lines[prose_start:i]), 'lang': m.group(1),
                       'body': '\n'.join(lines[i + 1:j]) + '\n', 'line': i + 1})
        i = prose_start = j + 1
    return blocks


def directive(prose):
    """Return (kind, path) for the directive nearest the block, or (None, None)."""
    best = (None, None, -1)
    for kind, pat in DIRECTIVES.items():
        for m in pat.finditer(prose):
            if m.start() > best[2]:
                best = (kind, m.group(1), m.start())
    return best[0], best[1]


WILDCARD = re.compile(r'(<sha>|\(\d+(?:\.\d+)?s\)|\t(?:\d+(?:\.\d+)?s|\(cached\))$)')


def clean(s):
    return '\n'.join(line.rstrip() for line in s.strip('\n').split('\n'))


def matches(expected, actual):
    """True if actual equals expected, where <sha> stands for any commit hash
    and test durations may differ. Everything else must match exactly."""
    pattern = []
    for line in clean(expected).split('\n'):
        part = ''
        for tok in WILDCARD.split(line):
            if tok == '<sha>':
                part += r'[0-9a-f]{7,40}'
            elif tok.startswith('('):
                part += r'\(\d+(?:\.\d+)?s\)'
            elif tok.startswith('\t') and WILDCARD.fullmatch(tok):
                part += r'\t(?:\d+(?:\.\d+)?s|\(cached\))'
            else:
                part += re.escape(tok)
        pattern.append(part)
    return re.fullmatch('\n'.join(pattern), clean(actual)) is not None


def run(cmd, cwd, timeout):
    try:
        r = subprocess.run(['bash', '-c', cmd], cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or '')
        return None, out + f"\n[timed out after {timeout}s]"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('plan')
    ap.add_argument('repo')
    ap.add_argument('--at', help='commit to start from (default: the repo HEAD)')
    ap.add_argument('--keep', action='store_true', help='keep the scratch clone for inspection')
    ap.add_argument('--timeout', type=int, default=900, help='seconds per command (default 900)')
    ap.add_argument('--identity', metavar='"NAME <EMAIL>"',
                    help='git identity to set in the clone, as a worker told to set one would')
    args = ap.parse_args()

    blocks = parse_blocks(open(args.plan).read())
    tmp = tempfile.mkdtemp(prefix='plan-sim-')
    repo = os.path.join(tmp, 'repo')
    subprocess.run(['git', 'clone', '-q', args.repo, repo], check=True)
    if args.at:
        subprocess.run(['git', '-C', repo, 'reset', '-q', '--hard', args.at], check=True)
    # A clone does not copy .git/config, but a worker commits in REPO itself,
    # so carry REPO's identity (local or global) over to the clone.
    for key in ('user.email', 'user.name'):
        r = subprocess.run(['git', '-C', args.repo, 'config', key], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            subprocess.run(['git', '-C', repo, 'config', key, r.stdout.strip()], check=True)
    if args.identity:
        m = re.fullmatch(r'\s*(.+?)\s*<([^>]+)>\s*', args.identity)
        if not m:
            sys.exit('--identity must look like "Name <email>"')
        subprocess.run(['git', '-C', repo, 'config', 'user.name', m.group(1)], check=True)
        subprocess.run(['git', '-C', repo, 'config', 'user.email', m.group(2)], check=True)
    missing = [key for key in ('user.email', 'user.name')
               if subprocess.run(['git', '-C', repo, 'config', key], capture_output=True).returncode]
    if missing:
        print(f"WARNING: git {' and '.join(missing)} not configured for {args.repo}. Commits will fail "
              "here, as they would for the worker. Pass --identity only if the worker will be told to "
              "set one.\n")

    problems, saved, ran_cmds, matched = [], {}, [], 0
    resolve = lambda p: p if os.path.isabs(p) else os.path.join(repo, p)

    def problem(line, msg):
        problems.append(f"plan line {line}: {msg}")
        print(f"  !! {msg}")

    k = 0
    while k < len(blocks):
        b = blocks[k]
        kind, path = directive(b['prose'])
        tag = f"[plan line {b['line']}]"
        if kind == 'find':
            nxt = blocks[k + 1] if k + 1 < len(blocks) else None
            if not nxt or 'Replace with' not in nxt['prose']:
                print(f"{tag} EDIT {path}")
                problem(b['line'], "a find block must be followed by a 'Replace with:' block")
                break
            old, new = b['body'][:-1], nxt['body'][:-1]
            try:
                src = open(resolve(path)).read()
            except OSError as e:
                print(f"{tag} EDIT {path}")
                problem(b['line'], f"cannot read {path}: {e}")
                break
            n = src.count(old)
            print(f"{tag} EDIT {path}: old text matches {n} time(s)")
            if n != 1:
                problem(b['line'], f"old text must match exactly once in {path}, matched {n}; stopping")
                break
            with open(resolve(path), 'w') as f:
                f.write(src.replace(old, new))
            k += 2
            continue
        if kind in ('whole', 'create', 'save'):
            target = resolve(path)
            print(f"{tag} {kind.upper()} {path}")
            if kind == 'create' and os.path.exists(target):
                problem(b['line'], f"{path} already exists; 'Create' needs a new file; stopping")
                break
            os.makedirs(os.path.dirname(target) or '.', exist_ok=True)
            with open(target, 'w') as f:
                f.write(b['body'])
            if kind == 'save':
                saved[path] = b['line']
                if path.endswith('.sh'):
                    os.chmod(target, 0o755)
        elif kind == 'append':
            target = resolve(path)
            before = open(target).read() if os.path.exists(target) else ''
            after = (before.rstrip('\n') + '\n\n' if before else '') + b['body']
            with open(target, 'w') as f:
                f.write(after)
            print(f"{tag} APPEND {path}: +{after.count(chr(10)) - before.count(chr(10))} lines")
        elif b['lang'] in ('bash', 'sh', 'shell'):
            rc, out = run(b['body'], repo, args.timeout)
            ran_cmds.append(b['body'])
            nxt = blocks[k + 1] if k + 1 < len(blocks) else None
            first = b['body'].strip().split('\n')[0][:70]
            if nxt and nxt['lang'] in ('text', '') and re.search(r'\bExpected\b', nxt['prose']):
                got, want = clean(out), clean(nxt['body'])
                if matches(want, got):
                    matched += 1
                    print(f"{tag} CHECK MATCH     {first}")
                else:
                    print(f"{tag} CHECK MISMATCH  {first}")
                    diff = difflib.unified_diff(want.split('\n'), got.split('\n'),
                                                'expected (plan)', 'actual', lineterm='')
                    print('     ' + '\n     '.join(diff))
                    problem(b['line'], f"output differs from the expected block at plan line {nxt['line']}")
                k += 2
                continue
            print(f"{tag} RUN  exit={rc}  {first}")
            if rc != 0:
                print('     ' + '\n     '.join(out.rstrip().split('\n')[-8:]))
                problem(b['line'], f"command exited {rc} and has no expected output to explain it")
        elif b['lang'] in ('text', '') and re.search(r'\bExpected\b', b['prose']):
            problem(b['line'], "expected output with no ```bash command directly before it")
        k += 1

    for path, line in saved.items():
        if not any(path in cmd for cmd in ran_cmds):
            problem(line, f"saved file {path} is never used by any ```bash command")

    print(f"\nSUMMARY: {matched} check(s) matched, {len(problems)} problem(s)")
    for p in problems:
        print(f"  - {p}")
    if args.keep:
        print(f"scratch clone kept at {repo}")
    else:
        shutil.rmtree(tmp)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
