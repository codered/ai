#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic TDD-first response (mirrors the Iron Law and red-green-
# refactor cycle from skills/applying-nasa-dod-coding-standards/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.32}"; }

printf '> '
read -r _request
echo

p "  NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST" 1.0
echo
p "Writing the failing test first — this is what proves the limiter" 0.25
p "actually has a bound, not just code that looks like it does." 0.6
echo
p "test_rate_limiter.py" 0.2
p "  def test_blocks_after_limit_reached():" 0.18
p "      limiter = RateLimiter(max_calls=3, window_s=1)" 0.18
p "      for _ in range(3):" 0.18
p "          assert limiter.allow()" 0.18
p "      assert limiter.allow() is False   # 🔴 fails — no implementation yet" 0.7
echo
p "🔴 Red — running pytest... 1 failed (RateLimiter not defined)" 0.6
echo
p "Now the minimum code to make it pass:" 0.3
p "  rate_limiter.py" 0.18
p "    class RateLimiter:" 0.16
p "        def __init__(self, max_calls, window_s):" 0.16
p "            self._calls = collections.deque(maxlen=max_calls)  # bounded" 0.5
echo
p "🟢 Green — 1 passed. Refactoring with tests held green." 0.8
