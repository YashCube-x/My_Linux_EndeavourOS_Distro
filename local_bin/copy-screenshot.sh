#!/usr/bin/env bash
mkdir -p ~/Pictures/Screenshots
FILE="$HOME/Pictures/Screenshots/Screenshot_$(date +'%Y%m%d_%H%M%S').png"

if grim -g "$(slurp)" "$FILE"; then
    wl-copy "$FILE" 2>/dev/null || true
    echo -n "$FILE" | wl-copy -p 2>/dev/null || true
    (
        ACTION=$(notify-send --action="default=Open Image" "Screenshot Copied!" "Image path copied to clipboard.\nPress Ctrl+Shift+V in terminal to paste." -i "$FILE" -a "Screenshot")
        if [ "$ACTION" = "default" ]; then
            imv "$FILE" &
        fi
    ) &
fi
