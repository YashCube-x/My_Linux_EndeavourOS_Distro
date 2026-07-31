#!/usr/bin/env bash
# Interactively switch between open windows using Wofi

selected=$(hyprctl clients -j | jq -r '.[] | select(.mapped == true and .title != "") | "\(.address)\t[\(.workspace.name)] \t\(.class) — \(.title)"' | sed 's/&/\&amp;/g' | wofi --dmenu --prompt "Switch Window" --width 700 --height 350)

if [ -n "$selected" ]; then
    addr=$(echo "$selected" | awk '{print $1}')
    hyprctl dispatch focuswindow "address:$addr" 2>/dev/null || hyprctl dispatch 'hl.dsp.window.focus({ address = "'"$addr"'" })'
fi
