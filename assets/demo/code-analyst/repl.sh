#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — prints a prompt, reads the
# user's natural-language request, then replays a condensed, authentic
# code-analyst pass (mirrors skills/code-analyst/SKILL.md's real
# status-line + structured-Markdown output, trimmed for length).

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

p "⏱ [~10s] Reading the code — entry point: poll_sensor()" 0.7
p "⏱ [~25s] Mapping control flow — bounded retry loop, one external call" 0.8
echo
p "Writing poll_sensor_analysis.md ..." 0.6
echo
p "## Overview" 0.2
p "Polls a sensor connection with a bounded retry loop, swallowing" 0.2
p "transient connection errors and returning None on exhaustion." 0.5
echo
p "## Parameters" 0.2
p "| Name | Type | Notes |" 0.15
p "|------|------|-------|" 0.1
p "| connection | Connection | must implement .read() |" 0.15
p "| max_retries | int | defaults to 3, bounds the loop |" 0.4
echo
p "## Edge Cases" 0.2
p "- All retries exhausted → returns None (caller must check)" 0.2
p "- ConnectionError is the only handled exception type" 0.5
echo
p "✅ Saved to poll_sensor_analysis.md  (elapsed: 47s)" 0.8
