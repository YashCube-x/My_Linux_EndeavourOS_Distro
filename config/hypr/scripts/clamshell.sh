#!/bin/bash
LID_STATE=$(cat /proc/acpi/button/lid/*/state 2>/dev/null | awk '{print $2}')

if hyprctl monitors | grep -q "HDMI-A-1"; then
    if [ "$LID_STATE" = "closed" ]; then
        hyprctl keyword monitor "eDP-1, disable"
        hyprctl dispatch focusmonitor HDMI-A-1
    else
        hyprctl keyword monitor "eDP-1, 1920x1080@144, 0x0, 1"
        hyprctl dispatch focusmonitor HDMI-A-1
    fi
else
    if [ "$LID_STATE" = "closed" ]; then
        pidof hyprlock || hyprlock
    fi
fi
