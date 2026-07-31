#!/usr/bin/env python3
"""Generates a keybind cheat-sheet from hyprland.lua and shows it via wofi with full descriptions.
"""
import re
import subprocess
from pathlib import Path

CONFIG = Path.home() / ".config/hypr/hyprland.lua"

bind_re = re.compile(r'hl\.bind\(\s*(.+?)\s*,\s*(.+?)\)')
comment_re = re.compile(r'^\s*--\s*(.+)$')
loop_key_re = re.compile(r'mainMod \.\. " \+ " \.\. key')
loop_shift_key_re = re.compile(r'mainMod \.\. " \+ SHIFT \+ " \.\. key')

def format_key(expr):
    expr = expr.strip()
    if loop_shift_key_re.search(expr):
        return "SUPER + SHIFT + [0-9]"
    if loop_key_re.search(expr):
        return "SUPER + [0-9]"
    expr = expr.replace('mainMod .. " + ', "SUPER + ").replace('"', "")
    return expr

def get_desc(action, last_comment):
    act = action.lower()
    if "copy-screenshot" in act or "grim" in act:
        return "Capture Screenshot (Auto-copy)"
    if "smart_menu" in act:
        return "Open Wofi Application Launcher"
    if "toggle_scratchpad" in act:
        return "Toggle Dropdown Scratchpad Terminal"
    if "clipboard_picker" in act:
        return "Open Clipboard History Picker"
    if "window_switcher" in act:
        return "Open Visual Window Switcher"
    if "smart_powermenu" in act:
        return "Open Power &amp; Logout Menu"

    if "wallpaper_picker" in act:
        return "Open Wallpaper Picker"
    if "cheatsheet" in act:
        return "Open Keybinding Cheatsheet"
    if "firefox" in act:
        return "Open Firefox Web Browser"
    if "exec_cmd" in act and "kitty" in act:
        return "Open Kitty Terminal"
    if "window.close" in act:
        return "Close Active Window"
    if "window.float" in act:
        return "Toggle Floating State"
    if "window.pin" in act:
        return "Pin Window across Workspaces"
    if "focus" in act and "e+1" in act:
        return "Switch to Next Workspace"
    if "focus" in act and "e-1" in act:
        return "Switch to Previous Workspace"
    if "focus" in act and "workspace" in act:
        return "Switch to Workspace"
    if "window.move" in act and "workspace" in act:
        return "Move Window to Workspace"
    if "focus" in act and "direction" in act:
        return "Move Focus (Arrow Direction)"
    if "window.swap" in act:
        return "Swap Window Position"
    if "fullscreen" in act:
        return "Toggle Fullscreen Mode"
    if "group.toggle" in act:
        return "Toggle Tabbed Window Group"
    if last_comment:
        return last_comment
    return ""

divider_re = re.compile(r'^-+$')

def main():
    lines = CONFIG.read_text().splitlines()
    out = []
    seen_loop_keys = set()
    in_keybindings = False
    last_comment = ""

    for line in lines:
        cm = comment_re.match(line)
        if cm:
            text_c = cm.group(1).strip()
            if divider_re.match(text_c):
                continue
            if "KEYBINDINGS" in text_c:
                in_keybindings = True
                continue
            if "WINDOWS AND WORKSPACES" in text_c:
                break
            if in_keybindings:
                out.append(f"\n<b>== {text_c} ==</b>")
                last_comment = text_c
            continue

        if not in_keybindings:
            continue

        bm = bind_re.search(line)
        if bm:
            key_expr = bm.group(1)
            action_expr = bm.group(2)
            key = format_key(key_expr)
            desc = get_desc(action_expr, last_comment)
            
            if key in ("SUPER + [0-9]", "SUPER + SHIFT + [0-9]"):
                if key in seen_loop_keys:
                    continue
                seen_loop_keys.add(key)
                if key == "SUPER + [0-9]":
                    desc = "Switch to Workspace [1-10]"
                else:
                    desc = "Move Window to Workspace [1-10]"

            formatted_entry = f"  <b>{key:<22}</b>  ➜  <span foreground='#cba6f7'>{desc}</span>"
            out.append(formatted_entry)

    text = "\n".join(l for l in out if l.strip())
    subprocess.run(
        ["wofi", "--dmenu", "--prompt", "Keybinds", "-I", "--width", "680", "--height", "700",
         "--allow-markup"],
        input=text,
        text=True,
    )

if __name__ == "__main__":
    main()
