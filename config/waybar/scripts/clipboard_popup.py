#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib

PID_FILE = "/tmp/clipboard_popup.pid"

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

def get_clip_items():
    items = []
    try:
        out = subprocess.check_output(["cliphist", "list"], universal_newlines=True)
        for line in out.strip().split('\n'):
            if '\t' in line:
                cid, content = line.split('\t', 1)
                items.append({
                    "id": cid.strip(),
                    "content": content.strip()
                })
    except Exception:
        pass
    return items[:100]

class ClipboardWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus - Clipboard")
        self.set_role("clipboard_popup")
        self.set_default_size(380, 520)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

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

        html_path = os.path.expanduser("~/.config/waybar/scripts/clipboard.html")
        self.webview.load_uri(f"file://{html_path}")

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.add(self.webview)
        self.show_all()

        GLib.timeout_add(100, self.update_data)

    def on_js_action(self, content_manager, js_result):
        try:
            val = js_result.get_js_value().to_string()
            if val == "close":
                self.destroy()
            elif val.startswith("copy_item:"):
                cid = val.split(":", 1)[1]
                try:
                    content = subprocess.check_output(["cliphist", "decode", cid])
                    # Copy to both standard Wayland clipboard and primary selection
                    p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                    p.communicate(input=content)
                    p_pri = subprocess.Popen(["wl-copy", "--primary"], stdin=subprocess.PIPE)
                    p_pri.communicate(input=content)
                except Exception as e:
                    pass
                GLib.timeout_add(120, self.destroy)
            elif val.startswith("delete_item:"):
                cid = val.split(":", 1)[1]
                try:
                    content = subprocess.check_output(["cliphist", "decode", cid])
                    p = subprocess.Popen(["cliphist", "delete"], stdin=subprocess.PIPE)
                    p.communicate(input=content)
                except Exception:
                    pass
                GLib.timeout_add(150, self.update_data)
            elif val == "clear_all":
                subprocess.Popen(["cliphist", "wipe"])
                GLib.timeout_add(150, self.update_data)
        except Exception:
            pass

    def update_data(self):
        items = get_clip_items()
        json_data = json.dumps({"items": items})
        script = f"if (window.updateStats) {{ window.updateStats({json_data}); }}"
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
        return False

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
    app = ClipboardWindow()
    Gtk.main()
