#!/bin/bash
# Toggle Tablet Second Monitor on click

if pgrep -x "wayvnc" > /dev/null || hyprctl monitors | grep -q "HEADLESS"; then
    /home/suyash/.local/bin/android-monitor stop
else
    /home/suyash/.local/bin/android-monitor start
fi

# Refresh Waybar module
sleep 1
pkill -RTMIN+8 waybar 2>/dev/null || true
