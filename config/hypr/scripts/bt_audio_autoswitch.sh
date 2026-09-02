#!/usr/bin/env bash
# ==============================================================================
# Automatic Bluetooth Audio Switcher for PipeWire / WirePlumber
# Seamlessly moves all audio streams to Bluetooth devices on connect
# ==============================================================================

# On launch, check if bluetooth audio is already connected and switch
BT_SINK=$(pactl list short sinks 2>/dev/null | grep -i "bluez" | awk '{print $2}' | head -n 1)
if [ -n "$BT_SINK" ]; then
    pactl set-default-sink "$BT_SINK" 2>/dev/null || true
    for stream in $(pactl list short sink-inputs 2>/dev/null | awk '{print $1}'); do
        pactl move-sink-input "$stream" "$BT_SINK" 2>/dev/null || true
    done
fi

# Event-driven listener for real-time connection/disconnection
pactl subscribe 2>/dev/null | while read -r event; do
    if echo "$event" | grep -q "sink" || echo "$event" | grep -q "card"; then
        BT_SINK=$(pactl list short sinks 2>/dev/null | grep -i "bluez" | awk '{print $2}' | head -n 1)
        if [ -n "$BT_SINK" ]; then
            CURRENT_DEF=$(pactl get-default-sink 2>/dev/null)
            if [ "$CURRENT_DEF" != "$BT_SINK" ]; then
                pactl set-default-sink "$BT_SINK" 2>/dev/null || true
                for stream in $(pactl list short sink-inputs 2>/dev/null | awk '{print $1}'); do
                    pactl move-sink-input "$stream" "$BT_SINK" 2>/dev/null || true
                done
            fi
        fi
    fi
done
