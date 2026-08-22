#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib, GtkLayerShell

PID_FILE = "/tmp/istat_popup.pid"

# Toggle logic: if already open, close it
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, 'r') as f:
            old_pid = int(f.read().strip())
        os.kill(old_pid, 0)
        # Process is alive, kill it to toggle OFF
        os.kill(old_pid, 9)
        os.remove(PID_FILE)
        sys.exit(0)
    except Exception:
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

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
    load1 = 0.0
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
            load1 = float(parts[0])
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
                        "wayvnc": "Tablet Share",
                        "Hyprland": "Hyprland",
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
        self.set_default_size(325, 485)
        self.set_app_paintable(True)

        # Initialize GtkLayerShell for native Wayland layer surface
        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_namespace(self, "istat-popup")
        
        # Anchor to Top-Right
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.RIGHT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, 34)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.RIGHT, 12)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        # Set transparent RGBA visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # WebKit View
        self.webview = WebKit2.WebView()
        self.webview.set_background_color(Gdk.RGBA(0, 0, 0, 0))

        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("actionHandler")
        content_manager.connect("script-message-received::actionHandler", self.on_js_action)

        html_path = os.path.expanduser("~/.config/waybar/scripts/istat.html")
        self.webview.load_uri(f"file://{html_path}")

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.add(self.webview)
        self.show_all()

        GLib.timeout_add(1500, self.update_data)
        GLib.timeout_add(200, self.update_data)

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
