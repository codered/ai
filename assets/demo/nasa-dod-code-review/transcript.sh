#!/usr/bin/env bash
# Replays a condensed nasa-dod-code-review finding for the README demo GIF.
# The finding format (severity, rule citation, why, three fix options, gate)
# mirrors skills/nasa-dod-code-review/SKILL.md exactly — only trimmed for length.

type_line() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

type_line "🔍 Detected: Python · solo developer · dev mode (full scan)" 0.5
type_line "📡 Loading standards: NASA Power of Ten · SEI CERT · OWASP" 0.6
echo
type_line "Reviewing sensor/poll.py ..." 0.8
echo
type_line "──────────────────────────────────────────────────────────" 0.05
type_line "🔴 P0 · Critical — Unbounded loop" 0.3
type_line "sensor/poll.py:2 — NASA Power of Ten, Rule 2 (Bounded Loops)" 0.5
echo
type_line "    while True:" 0.15
type_line "        reading = connection.read()" 0.15
echo
type_line "Why this must be fixed: a loop with no provable upper bound" 0.25
type_line "can spin forever on a stuck connection — and silently swallows" 0.25
type_line "every exception, so it never even reports the hang." 0.5
echo
type_line "Fix options:" 0.25
type_line "  1. Bound it — for _ in range(MAX_POLL_CYCLES): ..." 0.25
type_line "  2. Add a checked timeout exit condition each iteration" 0.25
type_line "  3. Move polling under a supervised scheduler with its own bound" 0.4
type_line "──────────────────────────────────────────────────────────" 0.6
echo
type_line "🔴 This PR is BLOCKED. 1 P0/Critical issue must be resolved" 0.3
type_line "   before merge." 0.6
echo
type_line "As a solo developer you may override this block. Please" 0.25
type_line "provide your reason — it will be recorded in the findings." 1.2
