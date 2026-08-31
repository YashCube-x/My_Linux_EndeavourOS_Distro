#!/usr/bin/env bash
# Wofi-based power & logout menu for Waybar and Hyprland.

options="🔒 Lock\n🌙 Suspend\n🚪 Logout\n🔄 Reboot\n⏻ Shutdown"
chosen=$(echo -e "$options" | wofi --dmenu --prompt "Power Menu" --width 240 --height 210 | xargs)

case "$chosen" in
    "🔒 Lock")
        pidof hyprlock || hyprlock
        ;;
    "🌙 Suspend")
        pidof hyprlock || hyprlock &
        sleep 0.5
        systemctl suspend
        ;;
    "🚪 Logout")
        hyprctl dispatch exit
        ;;
    "🔄 Reboot")
        systemctl reboot
        ;;
    "⏻ Shutdown")
        systemctl poweroff
        ;;
esac
