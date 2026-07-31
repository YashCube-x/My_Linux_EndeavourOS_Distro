#!/usr/bin/env python3
"""Generates a keybind cheat-sheet from hyprland.lua and shows it via wofi with exact app names.
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

def get_desc(key, action, last_comment):
    k = key.strip().upper()
    act = action.lower()
    
    if k in ("SUPER + RETURN", "SUPER + Q"):
        return "Open Kitty Terminal"
    if k == "SUPER + C":
        return "Close Active Window"
    if k == "SUPER + M":
        return "Exit / Logout Hyprland Session"
    if k == "SUPER + E":
        return "Open Thunar File Manager"
    if k == "SUPER + SPACE":
        return "Open Wofi Application Launcher"
    if k == "SUPER + SHIFT + B":
        return "Open Firefox Web Browser"
    if k == "SUPER + V":
        return "Toggle Window Floating State"
    if k == "SUPER + P":
        return "Toggle Dwindle Pseudo-Tiling"
    if k == "SUPER + J":
        return "Toggle Dwindle Split Direction"
    if k == "SUPER + F":
        return "Toggle Fullscreen Mode"
    if k == "SUPER + SHIFT + F":
        return "Toggle Maximized Window Mode"
    if k == "SUPER + S":
        return "Toggle Dropdown Scratchpad Terminal"
    if k == "SUPER + ALT + V":
        return "Open Clipboard History Picker"
    if k == "ALT + TAB":
        return "Switch to Next Workspace"
    if k == "ALT + SHIFT + TAB":
        return "Switch to Previous Workspace"
    if k == "SUPER + TAB":
        return "Cycle Window Focus Next"
    if k == "SUPER + SHIFT + TAB":
        return "Cycle Window Focus Previous"
    if k == "SUPER + G":
        return "Toggle Tabbed Window Group"
    if k == "SUPER + SHIFT + P":
        return "Pin/Unpin Window on All Workspaces"
    if k == "SUPER + W":
        return "Open Wallpaper Picker"
    if k == "SUPER + H":
        return "Open Keybinding Cheatsheet"
    if k == "SUPER + ESCAPE":
        return "Open Power &amp; Logout Menu"
    if "PRINT" in k:
        return "Capture Screenshot (Auto-copy)"
    if "LEFT" in k or "RIGHT" in k or "UP" in k or "DOWN" in k:
        if "ALT" in k:
            return "Resize Window Bounds"
        if "CTRL" in k:
            return "Swap Window Position"
        if "SHIFT" in k:
            return "Move Window Position"
        return "Move Window Focus"
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
    if "firefox" in act or "browser" in act:
        return "Open Firefox Web Browser"
    if "terminal" in act or "kitty" in act:
        return "Open Kitty Terminal"
    if "filemanager" in act or "thunar" in act:
        return "Open Thunar File Manager"
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
    if last_comment and last_comment.lower() != "core apps":
        return last_comment
    return "App / Action"

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
            desc = get_desc(key, action_expr, last_comment)
            
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
        ["wofi", "--dmenu", "--prompt", "Keybinds", "-I", "--width", "700", "--height", "700",
         "--allow-markup"],
        input=text,
        text=True,
    )

if __name__ == "__main__":
    main()
