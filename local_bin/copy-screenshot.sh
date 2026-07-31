#!/usr/bin/env bash
mkdir -p ~/Pictures/Screenshots
FILE="$HOME/Pictures/Screenshots/Screenshot_$(date +'%Y%m%d_%H%M%S').png"

if grim -g "$(slurp)" "$FILE"; then
    # Main Clipboard: Image bytes for Chat / Web Apps (Ctrl+V)
    wl-copy -t image/png < "$FILE"
    
    # Primary Selection: File path text for Terminal / CLI (Ctrl+Shift+V)
    echo -n "$FILE" | wl-copy -p
    
    (
        ACTION=$(notify-send --action="default=Open Image" "Screenshot Copied!" "Chat (Ctrl+V): Image\nTerminal (Ctrl+Shift+V): File Path" -i "$FILE" -a "Screenshot")
        if [ "$ACTION" = "default" ]; then
            imv "$FILE" &
        fi
    ) &
fi
