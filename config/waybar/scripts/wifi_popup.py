#!/usr/bin/env python3
import os
import sys
import time
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/wifi_popup.pid"

# Toggle logic
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, 'r') as f:
            old_pid = int(f.read().strip())
        os.kill(old_pid, 0)
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

# Traffic state
prev_time = time.time()
prev_rx = 0
prev_tx = 0

def get_net_bytes():
    rx, tx = 0, 0
    try:
        with open('/proc/net/dev', 'r') as f:
            for line in f:
                if 'wlan0:' in line:
                    parts = line.split(':')[1].split()
                    rx = int(parts[0])
                    tx = int(parts[8])
                    break
    except Exception:
        pass
    return rx, tx

prev_rx, prev_tx = get_net_bytes()

def get_wifi_stats():
    global prev_time, prev_rx, prev_tx
    
    # 1. Wi-Fi Enabled State
    enabled = True
    try:
        out = subprocess.check_output(["nmcli", "radio", "wifi"], universal_newlines=True).strip()
        enabled = (out == "enabled")
    except Exception:
        pass

    # 2. IP Address
    ip_addr = ""
    try:
        out = subprocess.check_output(["ip", "-br", "a", "show", "wlan0"], universal_newlines=True).strip()
        parts = out.split()
        if len(parts) >= 3:
            ip_addr = parts[2].split('/')[0]
    except Exception:
        pass

    # 3. Wi-Fi Scan & Active Connection
    connected = None
    networks = []
    seen_ssids = set()

    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "active,ssid,freq,rate,signal,security", "dev", "wifi"],
            universal_newlines=True
        )
        for line in out.strip().split('\n'):
            parts = line.split(':')
            if len(parts) >= 6:
                is_active = (parts[0].lower() == 'yes')
                ssid = parts[1].strip()
                freq = parts[2].strip()
                rate = parts[3].strip()
                signal = parts[4].strip()
                security = parts[5].strip()

                if not ssid:
                    continue

                band = "5.0 GHz" if "5" in freq[:2] else "2.4 GHz"

                if is_active:
                    connected = {
                        "ssid": ssid,
                        "ip": ip_addr,
                        "signal": signal,
                        "band": band,
                        "rate": rate
                    }

                if ssid not in seen_ssids:
                    seen_ssids.add(ssid)
                    networks.append({
                        "ssid": ssid,
                        "signal": signal,
                        "security": security,
                        "band": band
                    })
    except Exception:
        pass

    # 4. Speeds Calculation
    curr_time = time.time()
    curr_rx, curr_tx = get_net_bytes()
    dt = max(0.2, curr_time - prev_time)

    down_bps = max(0, (curr_rx - prev_rx) / dt)
    up_bps = max(0, (curr_tx - prev_tx) / dt)

    prev_time, prev_rx, prev_tx = curr_time, curr_rx, curr_tx

    def fmt_speed(bps):
        if bps > 1024 * 1024:
            return f"{bps / (1024 * 1024):.1f} MB/s"
        return f"{bps / 1024:.0f} KB/s"

    return {
        "enabled": enabled,
        "connected": connected,
        "speed": {
            "down": fmt_speed(down_bps),
            "up": fmt_speed(up_bps)
        },
        "networks": networks[:15]
    }

class WifiWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus - WiFi")
        self.set_role("wifi_popup")
        self.set_default_size(320, 430)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Transparent GTK CSS
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"window { background-color: transparent; background: none; }")
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.webview = WebKit2.WebView()
        self.webview.set_background_color(Gdk.RGBA(0, 0, 0, 0))

        content_manager = self.webview.get_user_content_manager()
        content_manager.register_script_message_handler("actionHandler")
        content_manager.connect("script-message-received::actionHandler", self.on_js_action)

        html_path = os.path.expanduser("~/.config/waybar/scripts/wifi.html")
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
            elif val == "wifi_on":
                subprocess.Popen(["nmcli", "radio", "wifi", "on"])
                GLib.timeout_add(800, self.update_data)
            elif val == "wifi_off":
                subprocess.Popen(["nmcli", "radio", "wifi", "off"])
                GLib.timeout_add(800, self.update_data)
            elif val == "rescan":
                subprocess.Popen(["nmcli", "dev", "wifi", "rescan"])
                GLib.timeout_add(1200, self.update_data)
            elif val == "settings":
                subprocess.Popen(["nm-connection-editor"])
                self.destroy()
            elif val.startswith("connect:"):
                ssid = val.split(":", 1)[1]
                subprocess.Popen(["kitty", "-e", "nmcli", "dev", "wifi", "connect", ssid, "--ask"])
                self.destroy()
        except Exception:
            pass

    def update_data(self):
        stats = get_wifi_stats()
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
    app = WifiWindow()
    Gtk.main()
