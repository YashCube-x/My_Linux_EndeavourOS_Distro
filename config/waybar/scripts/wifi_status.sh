#!/bin/bash
if [ "$(nmcli radio wifi)" != "enabled" ]; then
    printf '{"text": " Off", "class": "off", "tooltip": "WiFi disabled"}\n'
    exit 0
fi

SSID=$(nmcli -t -f active,ssid dev wifi | awk -F: '$1=="yes"{print $2; exit}' | xargs)

if [ -z "$SSID" ]; then
    printf '{"text": " Off", "class": "disconnected", "tooltip": "Not connected"}\n'
else
    printf '{"text": " %s", "class": "connected", "tooltip": "Connected to %s"}\n' "$SSID" "$SSID"
fi
