#!/usr/bin/env bash
mkdir -p ~/Pictures/Screenshots
FILE="$HOME/Pictures/Screenshots/Screenshot_$(date +'%Y%m%d_%H%M%S').png"

if grim -g "$(slurp)" "$FILE"; then
    wl-copy -t image/png < "$FILE"
    (
        ACTION=$(notify-send --action="default=Open Image" "Screenshot Copied!" "Saved & Copied to clipboard.\nClick notification to view image." -i "$FILE" -a "Screenshot")
        if [ "$ACTION" = "default" ]; then
            imv "$FILE" &
        fi
    ) &
fi
