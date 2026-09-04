#!/usr/bin/env bash
# ==============================================================================
# Smart Audio Switcher for PipeWire / WirePlumber
# - Auto-switches to Bluetooth when connected
# - Auto-falls back to working Speakers when USB/Bluetooth unplugs
# - Prevents audio deadlock that freezes YouTube / browser playback
# ==============================================================================

# Ensure single instance
PIDFILE="/tmp/smart_audio_switcher.pid"
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE" 2>/dev/null)" 2>/dev/null; then
    exit 0
fi
echo "$$" > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

switch_audio() {
    # 1. Prefer Bluetooth if connected
    BT_SINK=$(pactl list short sinks 2>/dev/null | grep -i "bluez" | awk '{print $2}' | head -n 1)
    if [ -n "$BT_SINK" ]; then
        TARGET_SINK="$BT_SINK"
    else
        # 2. Check if current default sink still physically exists
        CURRENT_DEF=$(pactl get-default-sink 2>/dev/null)
        if pactl list short sinks 2>/dev/null | grep -q "$CURRENT_DEF"; then
            TARGET_SINK="$CURRENT_DEF"
        else
            # Default sink disconnected! Fall back to live Speaker / Analog Stereo
            FALLBACK_SINK=$(pactl list short sinks 2>/dev/null | grep -iE "Speaker|analog-stereo" | awk '{print $2}' | head -n 1)
            [ -z "$FALLBACK_SINK" ] && FALLBACK_SINK=$(pactl list short sinks 2>/dev/null | awk '{print $2}' | head -n 1)
            TARGET_SINK="$FALLBACK_SINK"
        fi
    fi

    if [ -n "$TARGET_SINK" ]; then
        CURRENT=$(pactl get-default-sink 2>/dev/null)
        if [ "$CURRENT" != "$TARGET_SINK" ]; then
            pactl set-default-sink "$TARGET_SINK" 2>/dev/null || true
        fi
        for stream in $(pactl list short sink-inputs 2>/dev/null | awk '{print $1}'); do
            pactl move-sink-input "$stream" "$TARGET_SINK" 2>/dev/null || true
        done
    fi
}

# Initial sync
switch_audio

# Event-driven listener
pactl subscribe 2>/dev/null | while read -r event; do
    if echo "$event" | grep -qE "'new'|'remove'|'change'" && echo "$event" | grep -qE "sink|card"; then
        sleep 0.2
        switch_audio
    fi
done
