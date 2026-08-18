#!/bin/bash
# Check if wayvnc or HEADLESS monitor is active
if pgrep -x "wayvnc" > /dev/null || hyprctl monitors | grep -q "HEADLESS"; then
    echo '{"text":"󰢹","class":"connected","tooltip":"Tablet 2nd Screen: ACTIVE (ON)\n👉 Click to STOP / Disconnect"}'
else
    echo '{"text":"󰢹","class":"disconnected","tooltip":"Tablet 2nd Screen: OFF\n👉 Click to START / Connect"}'
fi
