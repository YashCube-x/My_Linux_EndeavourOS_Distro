#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/istat_popup.pid"

TARGET_VIEW = "ram"
if len(sys.argv) > 1:
    arg = sys.argv[1].lower()
    if arg in ["ram", "memory"]:
        TARGET_VIEW = "ram"
    elif arg in ["cpu", "processor"]:
        TARGET_VIEW = "cpu"
    elif arg in ["ssd", "disk", "storage"]:
        TARGET_VIEW = "ssd"

# Toggle logic
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, 'r') as f:
            lines = f.read().splitlines()
            old_pid = int(lines[0])
            old_view = lines[1] if len(lines) > 1 else ""

        os.kill(old_pid, 0)
        os.kill(old_pid, 9)
        os.remove(PID_FILE)
        
        # If clicking the SAME active tab, toggle OFF and exit
        if old_view == TARGET_VIEW:
            sys.exit(0)
    except Exception:
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

with open(PID_FILE, 'w') as f:
    f.write(f"{os.getpid()}\n{TARGET_VIEW}\n")

def get_stats():
    # 1. Memory stats
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

    swap_total = meminfo.get('SwapTotal', 0)
    swap_free = meminfo.get('SwapFree', 0)
    swap_used = max(0, swap_total - swap_free)
    swap_pct = int((swap_used / swap_total) * 100) if swap_total > 0 else 0

    # 2. CPU stats
    load_str = "1.00 1.00 1.00"
    load1 = 0.0
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
            load1 = float(parts[0])
            load_str = f"{parts[0]} {parts[1]} {parts[2]}"
    except Exception:
        pass
    
    cpu_count = os.cpu_count() or 4
    pressure_pct = min(100, int((load1 / cpu_count) * 100))

    # CPU Frequency
    cpu_freq = "2.40"
    try:
        with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq', 'r') as f:
            khz = int(f.read().strip())
            cpu_freq = f"{khz / 1000000:.2f}"
    except Exception:
        pass

    # CPU Temperature
    cpu_temp = "48"
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            milli = int(f.read().strip())
            cpu_temp = str(int(milli / 1000))
    except Exception:
        pass

    # Uptime
    uptime_str = "0d 16h"
    try:
        with open('/proc/uptime', 'r') as f:
            up_sec = float(f.read().split()[0])
            d = int(up_sec // 86400)
            h = int((up_sec % 86400) // 3600)
            uptime_str = f"{d}d {h}h"
    except Exception:
        pass

    # GPU
    gpu_util, gpu_temp = "0", "50"
    try:
        gpu_raw = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=utilization.gpu,temperature.gpu', '--format=csv,noheader,nounits'],
            universal_newlines=True
        ).strip().split(',')
        if len(gpu_raw) >= 2:
            gpu_util = gpu_raw[0].strip()
            gpu_temp = gpu_raw[1].strip()
    except Exception:
        pass

    # 3. SSD / Disk stats
    disk_avail = "245.9 GB"
    disk_used_pct = 44
    try:
        usage = shutil.disk_usage('/')
        disk_avail = f"{usage.free / (1024**3):.1f} GB"
        disk_used_pct = int((usage.used / usage.total) * 100)
    except Exception:
        pass

    # 4. Processes
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
                        "WebExtensions": "Firefox Ext",
                        "chrome": "Google Chrome",
                        "antigravity-ide": "Antigravity IDE",
                        "language_server": "Language Server",
                        "claude": "Claude Code",
                        "node": "Node Server",
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
        "initial_tab": TARGET_VIEW,
        "pressure_pct": pressure_pct,
        "mem_pct": mem_pct,
        "app_mem": fmt_gb(app_mem),
        "wired_mem": fmt_gb(wired_mem),
        "compressed_mem": fmt_gb(compressed_mem),
        "free_mem": fmt_gb(available),
        "swap_used": fmt_mb(swap_used) if swap_total > 0 else "0 MB",
        "swap_total": fmt_gb(swap_total) if swap_total > 0 else "0 GB",
        "swap_pct": swap_pct,
        "cpu": {
            "freq": cpu_freq,
            "temp": cpu_temp,
            "user": "8",
            "system": "6",
            "load": load_str,
            "uptime": uptime_str,
            "gpu": {
                "util": gpu_util,
                "temp": gpu_temp
            }
        },
        "ssd": {
            "used_pct": disk_used_pct,
            "available": disk_avail,
            "read_speed": "116 KB/s",
            "write_speed": "3.8 MB/s"
        },
        "processes": processes
    }

class IStatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        
        title_suffix = TARGET_VIEW.upper()
        self.set_title(f"iStat Menus - {title_suffix}")
        self.set_role(f"istat_popup_{TARGET_VIEW}")
        self.set_default_size(320, 395)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Transparent GTK CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            window {
                background-color: transparent;
                background: none;
            }
        """)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

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
        GLib.timeout_add(250, self.update_data)

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
    app = IStatWindow()
    Gtk.main()
