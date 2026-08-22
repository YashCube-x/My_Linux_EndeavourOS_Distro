#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/istat_popup.pid"

def is_running():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, 9)
            os.remove(PID_FILE)
            return True
        except Exception:
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
    return False

if is_running():
    sys.exit(0)

with open(PID_FILE, 'w') as f:
    f.write(str(os.getpid()))

def get_stats():
    # 1. Memory parsing from /proc/meminfo
    meminfo = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    meminfo[key] = int(val) * 1024
    except Exception:
        pass

    total = meminfo.get('MemTotal', 1)
    free = meminfo.get('MemFree', 0)
    buffers = meminfo.get('Buffers', 0)
    cached = meminfo.get('Cached', 0) + meminfo.get('SReclaimable', 0)
    available = meminfo.get('MemAvailable', free + buffers + cached)
    used = max(0, total - available)

    app_mem = max(0, used - buffers)
    wired_mem = buffers
    compressed_mem = cached

    mem_pct = int((used / total) * 100) if total > 0 else 0

    # 2. Swap parsing
    swap_total = meminfo.get('SwapTotal', 0)
    swap_free = meminfo.get('SwapFree', 0)
    swap_used = max(0, swap_total - swap_free)
    swap_pct = int((swap_used / swap_total) * 100) if swap_total > 0 else 0

    # 3. CPU / Pressure parsing
    load1, load5, load15 = 0.0, 0.0, 0.0
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
            load1 = float(parts[0])
            load5 = float(parts[1])
    except Exception:
        pass
    
    cpu_count = os.cpu_count() or 4
    pressure_pct = min(100, int((load1 / cpu_count) * 100))

    # 4. Top 5 Processes by Memory
    processes = []
    try:
        output = subprocess.check_output(
            ["ps", "-eo", "comm,%mem,rss", "--sort=-rss"],
            universal_newlines=True
        )
        lines = output.strip().split('\n')[1:]
        seen_names = set()
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                try:
                    rss_kb = int(parts[-1])
                    raw_name = " ".join(parts[:-2])
                    
                    clean_names = {
                        "firefox": "Firefox Browser",
                        "Isolated Web Co": "Firefox Tab",
                        "WebExtensions": "Firefox Extension",
                        "chrome": "Google Chrome",
                        "antigravity-ide": "Antigravity IDE",
                        "language_server": "Language Server",
                        "claude": "Claude Code",
                        "node": "Node.js Server",
                        "wayvnc": "Tablet Screen Share",
                        "Hyprland": "Hyprland Compositor",
                        "waybar": "Waybar",
                        "kitty": "Terminal",
                        "btop": "Activity Monitor"
                    }
                    display_name = clean_names.get(raw_name, raw_name)
                    
                    if rss_kb > 1024 * 1024:
                        size_str = f"{rss_kb / (1024 * 1024):.1f} GB"
                    else:
                        size_str = f"{rss_kb / 1024:.0f} MB"
                    
                    processes.append({"name": display_name, "size": size_str})
                    if len(processes) >= 5:
                        break
                except Exception:
                    continue
    except Exception:
        pass

    def fmt_gb(b):
        return f"{b / (1024**3):.1f} GB"

    def fmt_mb(b):
        return f"{b / (1024**2):.0f} MB"

    return {
        "pressure_pct": pressure_pct,
        "mem_pct": mem_pct,
        "app_mem": fmt_gb(app_mem),
        "wired_mem": fmt_gb(wired_mem),
        "compressed_mem": fmt_gb(compressed_mem),
        "free_mem": fmt_gb(available),
        "swap_used": fmt_mb(swap_used) if swap_total > 0 else "0 MB",
        "swap_total": fmt_gb(swap_total) if swap_total > 0 else "0 GB",
        "swap_pct": swap_pct,
        "processes": processes
    }

class IStatPopup(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus")
        self.set_wmclass("istat_popup", "istat_popup")
        self.set_default_size(320, 480)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_position(Gtk.WindowPosition.NONE)
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.move(1580, 34)

        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("destroy", self.on_destroy)

        self.webview = WebKit2.WebView()
        self.webview.set_background_color(Gdk.RGBA(0, 0, 0, 0))

        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("actionHandler")
        content_manager.connect("script-message-received::actionHandler", self.on_js_action)

        html_path = os.path.expanduser("~/.config/waybar/scripts/istat.html")
        self.webview.load_uri(f"file://{html_path}")

        self.add(self.webview)
        self.show_all()

        GLib.timeout_add(1500, self.update_data)
        GLib.timeout_add(300, self.update_data)

    def on_js_action(self, content_manager, js_result):
        try:
            val = js_result.get_js_value().to_string()
            if val == "close":
                self.destroy()
            elif val == "terminal":
                subprocess.Popen(["kitty"])
                self.destroy()
            elif val == "btop":
                subprocess.Popen(["kitty", "-e", "btop"])
                self.destroy()
            elif val == "clean":
                subprocess.Popen(["sync"])
                self.update_data()
        except Exception:
            pass

    def update_data(self):
        stats = get_stats()
        json_data = json.dumps(stats)
        script = f"if (window.updateStats) {{ window.updateStats({json_data}); }}"
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
        return True

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def on_focus_out(self, widget, event):
        self.destroy()
        return False

    def on_destroy(self, widget):
        try:
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except Exception:
            pass
        Gtk.main_quit()

if __name__ == '__main__':
    app = IStatPopup()
    Gtk.main()
