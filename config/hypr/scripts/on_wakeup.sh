#!/usr/bin/env bash
# Wake up script executed by hypridle after system resumes from sleep

# Turn display back ON instantly
hyprctl dispatch 'hl.dsp.dpms("on")'

# Force DPMS state on
sleep 0.5
hyprctl dispatch 'hl.dsp.dpms("on")'
