# VHS tape for the README demo GIF.
# Regenerate with: vhs demo.tape   (run from inside assets/demo/nasa-dod-agent/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)
# Requires: OPENAI_API_KEY exported in the shell that runs `vhs` — this is a
# real, live run of the CLI against the buggy fixture in sample/, not a
# pre-recorded transcript.
#
# IMPORTANT: vhs does not synchronize with the shell — it just plays through
# this script's Sleep/Type timeline on its own clock and tears down the whole
# session (browser, ttyd, the pty, and anything still running in it) once the
# script ends, regardless of whether a command is still running. So the Sleep
# below must be longer than the real review can possibly take, and Hide/Show
# (which only pauses frame *capture*, not real time) is what keeps that long
# wait from being visible as dead air in the rendered gif.

Output demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 620
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 60ms

Hide
Type "export PATH=$PWD:$PATH && cp fixture/divide.go sample/divide.go && rm -rf sample/.nasa-dod-agent && clear"
Enter
Show

Type "cat sample/divide.go"
Sleep 600ms
Enter
Sleep 2.5s

Type "nasa-dod-agent review --reset --max-rounds 2 sample/  # calls a real LLM, finishes in a few minutes..."
Sleep 800ms
Enter

Hide
Sleep 650s
Show

Sleep 1s
Type "git diff --no-index --color=always -- fixture/divide.go sample/divide.go"
Sleep 600ms
Enter
Sleep 12s
