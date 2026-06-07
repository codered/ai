#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic agent-team pipeline tick (mirrors the rolling-pipeline
# mechanic — Dev never blocks on review — from skills/agent-team/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.32}"; }

printf '> '
read -r _request
echo

p "[PM]   Phase 2/4 — 5 tasks planned, gate criteria recorded" 0.6
echo
p "[Dev]  TASK-007 implemented (TDD, nasa-dod self-review clean)" 0.25
p "[Dev]  → marked in_review · picking up TASK-008 now" 0.7
echo
p "[QA]        reviewing TASK-007 — coverage 94%, 0 findings" 0.4
p "[Security]  reviewing TASK-007 — 1 finding: P2, missing rate-limit log" 0.7
echo
p "[Dev]  still on TASK-008 — not blocked, findings queued for next pass" 0.9
echo
p "[Dev]  TASK-008 implemented · marked in_review · picking up TASK-009" 0.5
p "[Dev]  circling back: TASK-007 P2 addressed, re-review requested" 0.9
echo
p "[PM]   Phase 2/4 — 2 of 5 done · pipeline rolling, no idle agents" 0.8
