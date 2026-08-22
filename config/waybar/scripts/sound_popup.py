#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/sound_popup.pid"

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

def get_sound_stats():
    # 1. Master Sink Volume
    master = {"volume": 80, "muted": False}
    try:
        out = subprocess.check_output(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], universal_newlines=True).strip()
        parts = out.split()
        if len(parts) >= 2:
            master["volume"] = int(float(parts[1]) * 100)
            master["muted"] = ('[MUTED]' in out)
    except Exception:
        pass

    # 2. Microphone Volume
    mic = {"volume": 80, "muted": False}
    try:
        out = subprocess.check_output(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SOURCE@'], universal_newlines=True).strip()
        parts = out.split()
        if len(parts) >= 2:
            mic["volume"] = int(float(parts[1]) * 100)
            mic["muted"] = ('[MUTED]' in out)
    except Exception:
        pass

    # 3. Sinks List (Output Devices)
    sinks = []
    try:
        out = subprocess.check_output(['wpctl', 'status'], universal_newlines=True)
        in_sinks = False
        for line in out.split('\n'):
            if 'Sinks:' in line:
                in_sinks = True
                continue
            if in_sinks:
                if 'Sources:' in line or 'Sink endpoints:' in line or not line.strip() or '├─' in line and 'Devices:' in line:
                    in_sinks = False
                    break
                line_clean = line.replace('│', '').strip()
                if not line_clean or line_clean.startswith('─'):
                    continue
                
                is_default = '*' in line_clean
                parts = line_clean.replace('*', '').strip().split('.', 1)
                if len(parts) == 2:
                    sink_id = parts[0].strip()
                    sink_desc = parts[1].split('[vol:')[0].strip()
                    
                    # Clean friendly device names
                    clean_name = sink_desc
                    if 'Speaker' in sink_desc:
                        clean_name = "Laptop Built-in Speakers"
                    elif 'Headset' in sink_desc or 'AB13X' in sink_desc:
                        clean_name = "AB13X Headset / Earphones"
                    elif 'HDMI' in sink_desc:
                        clean_name = "HDMI / DisplayPort Audio"
                    
                    sinks.append({
                        "id": sink_id,
                        "name": clean_name,
                        "is_default": is_default
                    })
    except Exception:
        pass

    # 4. Active Per-App Voice Streams (Sink Inputs)
    apps = []
    try:
        out = subprocess.check_output(['pactl', 'list', 'sink-inputs'], universal_newlines=True)
        blocks = out.split('Sink Input #')
        for block in blocks[1:]:
            lines = block.split('\n')
            input_id = lines[0].strip()
            app_name = "Application Audio"
            app_vol = 100
            app_muted = False

            for l in lines:
                l_s = l.strip()
                if l_s.startswith('application.name = '):
                    app_name = l_s.split('=', 1)[1].replace('"', '').strip()
                elif l_s.startswith('Volume:'):
                    # e.g. front-left: 65536 / 100% / 0.00 dB
                    if '/' in l_s:
                        try:
                            pct_str = l_s.split('/')[1].replace('%', '').strip()
                            app_vol = int(pct_str)
                        except Exception:
                            pass
                elif l_s.startswith('Mute:'):
                    app_muted = ('yes' in l_s.lower())

            apps.append({
                "id": input_id,
                "name": app_name,
                "volume": app_vol,
                "muted": app_muted
            })
    except Exception:
        pass

    return {
        "master": master,
        "mic": mic,
        "sinks": sinks,
        "apps": apps
    }

class SoundWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus - Sound")
        self.set_role("sound_popup")
        self.set_default_size(320, 480)
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

        html_path = os.path.expanduser("~/.config/waybar/scripts/sound.html")
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
            elif val == "toggle_master_mute":
                subprocess.Popen(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
                GLib.timeout_add(150, self.update_data)
            elif val == "toggle_mic_mute":
                subprocess.Popen(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
                GLib.timeout_add(150, self.update_data)
            elif val.startswith("set_master_volume:"):
                vol = int(val.split(":")[1])
                subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol/100:.2f}"])
            elif val.startswith("set_mic_volume:"):
                vol = int(val.split(":")[1])
                subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", f"{vol/100:.2f}"])
            elif val.startswith("switch_sink:"):
                sink_id = val.split(":")[1]
                subprocess.Popen(["wpctl", "set-default", sink_id])
                GLib.timeout_add(200, self.update_data)
            elif val.startswith("set_app_volume:"):
                parts = val.split(":")
                app_id, vol = parts[1], parts[2]
                subprocess.Popen(["pactl", "set-sink-input-volume", app_id, f"{vol}%"])
            elif val.startswith("toggle_app_mute:"):
                app_id = val.split(":")[1]
                subprocess.Popen(["pactl", "set-sink-input-mute", app_id, "toggle"])
                GLib.timeout_add(150, self.update_data)
            elif val == "pavucontrol":
                subprocess.Popen(["pavucontrol"])
                self.destroy()
        except Exception:
            pass

    def update_data(self):
        stats = get_sound_stats()
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
    app = SoundWindow()
    Gtk.main()
