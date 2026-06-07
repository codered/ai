#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic devils-advocate exchange (auto-offer + high-stakes
# structured findings, mirroring skills/devils-advocate/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

p "Before we lock this in — want me to play devil's advocate on it" 0.3
p "for a minute? I've spotted a couple of things worth pressure-testing." 0.9
echo
printf '> yes, go ahead\n'
sleep 0.6
echo

p "**Hidden assumption — this assumes the cache was only ever a" 0.25
p "performance layer, never a correctness boundary**" 0.5
p "Why it matters: if any read path relies on the cache to dedupe" 0.2
p "concurrent writes, removing it changes behavior, not just speed." 0.6
echo
p "**Missed edge case — cold-start load on the database**" 0.3
p "Why it matters: every request that the cache used to absorb now" 0.2
p "lands directly on Postgres at once on deploy — that's a thundering" 0.2
p "herd, not a gradual ramp." 0.6
echo
p "Worth a quick check before this ships: which of these have you" 0.2
p "already ruled out?" 1.0
