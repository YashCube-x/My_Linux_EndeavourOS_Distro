#!/bin/bash
# Hides waybar if it's running, shows it again if it's hidden.
if pgrep -x waybar >/dev/null; then
    killall waybar
else
    waybar &>/dev/null & disown
fi
