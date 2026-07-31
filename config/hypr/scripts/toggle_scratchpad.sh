#!/usr/bin/env bash
# Toggles a dedicated floating Kitty scratchpad terminal in Hyprland.

if hyprctl clients | grep -q "class: scratchpad_kitty"; then
    hyprctl dispatch 'hl.dsp.workspace.toggle_special("magic")'
else
    kitty --class scratchpad_kitty &
    sleep 0.2
    hyprctl dispatch 'hl.dsp.window.move({ workspace = "special:magic" })'
    hyprctl dispatch 'hl.dsp.workspace.toggle_special("magic")'
fi
