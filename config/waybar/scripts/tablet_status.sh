#!/bin/bash
# Check if wayvnc or HEADLESS monitor is active
if pgrep -x "wayvnc" > /dev/null || hyprctl monitors | grep -q "HEADLESS"; then
    echo '{"text":"󰢹 Tablet ON","class":"connected","tooltip":"Tablet 2nd Screen: ACTIVE\\nClick to STOP"}'
else
    echo '{"text":"󰢹 Tablet OFF","class":"disconnected","tooltip":"Tablet 2nd Screen: OFF\\nClick to START"}'
fi
