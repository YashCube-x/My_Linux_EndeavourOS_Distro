#!/bin/bash
# Check if wayvnc or HEADLESS monitor is active
if pgrep -x "wayvnc" > /dev/null || hyprctl monitors | grep -q "HEADLESS"; then
    printf '{"text": "󰢹 Tablet ON", "class": "connected", "tooltip": "Tablet 2nd Screen: ACTIVE (Left 1.5x)\n👉 Click to STOP / Disconnect"}\n'
else
    printf '{"text": "󰢹 Tablet OFF", "class": "disconnected", "tooltip": "Tablet 2nd Screen: OFF\n👉 Click to START / Connect"}\n'
fi
