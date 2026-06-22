# VHS tape for the README "budget cap" demo GIF.
# Regenerate with: vhs demo-budget.tape   (run from inside assets/demo/nasa-dod-agent/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)
#
# Unlike demo.tape (a real, live LLM run), this one REPLAYS a real,
# captured transcript (budget-demo/transcript.txt) instead of calling the
# live agent — that transcript is genuine output from an actual run against
# the iseven/ fixture, it just took ~21 real minutes against a live LLM,
# which isn't practical to re-record on demand. budget-demo/nasa-dod-agent
# is a shim (first on PATH below) that streams the saved transcript back
# with realistic pacing instead of doing a real review.
#
# Goal: show the max_total_fix_attempts guardrail firing — the agent
# stopping itself and reporting why, instead of grinding silently.

Output demo-budget.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 620
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 60ms

Hide
Type "export PATH=$PWD/budget-demo:$PATH && cd budget-demo && clear"
Enter
Show

Type "cat sample/test/iseven_test.go | head -20"
Sleep 600ms
Enter
Sleep 3s

Type "nasa-dod-agent review --reset sample/"
Sleep 800ms
Enter

Sleep 1.2s

Hide
Sleep 21s
Show

Sleep 3s
