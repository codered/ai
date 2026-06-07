# VHS tape for the README demo GIF.
# Regenerate with: vhs demo.tape   (run from inside assets/demo/nasa-dod-code-review/)
# Requires: https://github.com/charmbracelet/vhs (and ffmpeg + ttyd)

Output demo.gif

Set Shell "bash"
Set FontSize 16
Set Width 1000
Set Height 560
Set Padding 20
Set Theme "Dracula"
Set TypingSpeed 60ms

Hide
Type "export PATH=$PWD:$PATH && clear"
Enter
Show

Type "nasa-dod review"
Sleep 600ms
Enter

Sleep 9.5s
