#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic memory-skill pass (triage → dispatch → one-line receipt,
# mirroring skills/memory/SKILL.md's delegation flow).

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

p "Scratch-list — what's new this session:" 0.25
p "  • Refactored auth middleware to use JWT (commit a1b2c3d)" 0.2
p "  • Open thread: PR #12 awaiting Security review" 0.2
p "  • Decision: switched test runner from Mocha to Vitest" 0.6
echo
p "Dispatching memory sub-agent → target: . · trigger: user-requested" 0.7
echo
p "[sub-agent] memory/ not found here — seed mode" 0.4
p "[sub-agent] surveying repo: structure, README, recent git log, configs..." 0.6
p "[sub-agent] filing 31 facts → short: 12 (active work, frequent lookups)" 0.25
p "[sub-agent]                   long: 19 (architecture, history, rationale)" 0.4
p "[sub-agent] writing index.json, short/_index.json, long/_index.json" 0.7
echo
p "Indexed 31 facts, memory/ now has 12 short / 19 long entries — ready" 0.25
p "for next session." 0.9
