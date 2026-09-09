# VHS tape for the README demo GIF.
# Regenerate with: VHS_NO_SANDBOX=true vhs demo.tape   (run from inside assets/demo/vertical-slice-planning/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)

Output demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
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

Type "plan wiring the retry header from the client through orders to the job queue"
Sleep 600ms
Enter

Sleep 13s
