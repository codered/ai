#!/usr/bin/env bash
# Minimal fake agent REPL for the demo GIF — replays a condensed,
# authentic teach-me exchange (intake, outline + approval checkpoint,
# chapter generation, mirroring skills/teach-me/SKILL.md).

p() { printf '%s\n' "$1"; sleep "${2:-0.35}"; }

printf '> '
read -r _request
echo

p "What depth should I aim for — beginner, intermediate, or advanced?" 0.5
echo
printf '> intermediate, and I already know basic Python\n'
sleep 0.6
echo

p "Got it — I'd suggest 6 chapters for an intermediate course. Sound" 0.25
p "right, or would you like more/fewer?" 0.7
echo
printf '> 6 sounds good\n'
sleep 0.6
echo

p "Here's the proposed outline — want me to start writing, or adjust" 0.2
p "anything first (reorder, merge, add/remove a chapter)?" 0.5
echo
p "  1. What Decorators Actually Are" 0.15
p "  2. Writing Your First Decorator" 0.15
p "  3. Decorators That Take Arguments" 0.15
p "  4. Preserving Metadata with functools.wraps" 0.15
p "  5. Stacking and Ordering Decorators" 0.15
p "  6. Real-World Patterns: Caching, Logging, Retries" 0.6
echo
printf '> looks great, go ahead\n'
sleep 0.6
echo

p "Writing lessons/python-decorators/01_what-decorators-are.md ..." 0.3
p "  + intro, core content, mermaid diagram, worked example" 0.2
p "  + key takeaways, 4-question quiz" 0.2
p "  + answers appended to ANSWERS.md with reasoning" 0.7
p "Writing lessons/python-decorators/02_writing-your-first-decorator.md ..." 1.0
