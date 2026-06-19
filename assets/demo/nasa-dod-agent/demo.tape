# VHS tape for the README demo GIF.
# Regenerate with: vhs demo.tape   (run from inside assets/demo/nasa-dod-agent/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)
# Requires: OPENAI_API_KEY exported in the shell that runs `vhs` — this is a
# real, live run of the CLI against the buggy fixture in sample/, not a
# pre-recorded transcript.

Output demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 620
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 60ms
Set PlaybackSpeed 3.0

Hide
Type "export PATH=$PWD:$PATH && cp fixture/readconfig.go sample/readconfig.go && rm -rf sample/.nasa-dod-agent && clear"
Enter
Show

Type "cat sample/readconfig.go"
Sleep 600ms
Enter
Sleep 2.5s

Type "nasa-dod-agent review --reset --max-rounds 2 sample/"
Sleep 600ms
Enter

Sleep 280s

Type "cat sample/readconfig.go"
Sleep 600ms
Enter
Sleep 4s
