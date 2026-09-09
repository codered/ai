# VHS tape for the README demo GIF.
# Regenerate with: VHS_NO_SANDBOX=true vhs demo.tape   (run from inside assets/demo/company-analysis/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)

Output demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1100
Set Height 560
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 60ms
Set Framerate 24

Hide
Type "clear && bash repl.sh"
Enter
Sleep 500ms
Show

Type "/company-analysis AAPL"
Sleep 600ms
Enter

Sleep 14s
