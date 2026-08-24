#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/bluetooth_popup.pid"

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

def get_bt_stats():
    powered = False
    try:
        out = subprocess.check_output(['bluetoothctl', 'show'], universal_newlines=True)
        powered = 'Powered: yes' in out
    except Exception:
        pass

    connected_macs = set()
    connected_device = None
    try:
        out = subprocess.check_output(['bluetoothctl', 'devices', 'Connected'], universal_newlines=True)
        for line in out.strip().split('\n'):
            parts = line.split(maxsplit=2)
            if len(parts) >= 3:
                mac = parts[1]
                name = parts[2]
                connected_macs.add(mac)
                if not connected_device:
                    connected_device = {"mac": mac, "name": name}
    except Exception:
        pass

    devices = []
    seen_macs = set()
    try:
        out = subprocess.check_output(['bluetoothctl', 'devices'], universal_newlines=True)
        for line in out.strip().split('\n'):
            parts = line.split(maxsplit=2)
            if len(parts) >= 3:
                mac = parts[1]
                name = parts[2]
                if mac not in seen_macs:
                    seen_macs.add(mac)
                    devices.append({
                        "mac": mac,
                        "name": name,
                        "connected": mac in connected_macs
                    })
    except Exception:
        pass

    return {
        "powered": powered,
        "connected_device": connected_device,
        "devices": devices
    }

class BluetoothWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus - Bluetooth")
        self.set_role("bluetooth_popup")
        self.set_default_size(320, 420)
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

        html_path = os.path.expanduser("~/.config/waybar/scripts/bluetooth.html")
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
            elif val == "power_on":
                subprocess.Popen(["bluetoothctl", "power", "on"])
                GLib.timeout_add(800, self.update_data)
            elif val == "power_off":
                subprocess.Popen(["bluetoothctl", "power", "off"])
                GLib.timeout_add(800, self.update_data)
            elif val.startswith("connect:"):
                mac = val.split(":", 1)[1]
                subprocess.Popen(["bluetoothctl", "connect", mac])
                GLib.timeout_add(2000, self.update_data)
            elif val.startswith("disconnect:"):
                mac = val.split(":", 1)[1]
                subprocess.Popen(["bluetoothctl", "disconnect", mac])
                GLib.timeout_add(1200, self.update_data)
            elif val == "scan":
                subprocess.Popen(["bluetoothctl", "--timeout", "8", "scan", "on"])
                GLib.timeout_add(2000, self.update_data)
            elif val == "blueman":
                subprocess.Popen(["blueman-manager"])
                self.destroy()
        except Exception:
            pass

    def update_data(self):
        stats = get_bt_stats()
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
    app = BluetoothWindow()
    Gtk.main()
