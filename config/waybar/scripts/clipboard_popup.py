#!/usr/bin/env python3
import os
import sys
import json
import base64
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.1')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, WebKit2, GLib

PID_FILE = "/tmp/clipboard_popup.pid"
PINS_FILE = os.path.expanduser("~/.cache/clipboard_pins.json")
TENOR_KEY_FILE = os.path.expanduser("~/.config/waybar/scripts/tenor_key.txt")

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


def load_pins():
    try:
        with open(PINS_FILE, 'r') as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_pins(pins):
    try:
        os.makedirs(os.path.dirname(PINS_FILE), exist_ok=True)
        with open(PINS_FILE, 'w') as f:
            json.dump(sorted(pins), f)
    except Exception:
        pass


def read_tenor_key():
    try:
        with open(TENOR_KEY_FILE, 'r') as f:
            return f.read().strip()
    except Exception:
        return ""


def parse_binary_marker(content):
    # e.g. "[[ binary data 1013 KiB png 3106x1621 ]]"
    try:
        inner = content.strip().strip('[]').strip()
        parts = inner.split()
        # parts: data <size> <unit> <fmt> <dims>
        size = parts[1] + " " + parts[2]
        fmt = parts[3]
        dims = parts[4]
        return size, fmt, dims
    except Exception:
        return "", "", ""


def get_clip_items(limit=300):
    items = []
    pins = load_pins()
    try:
        out = subprocess.check_output(["cliphist", "list"], universal_newlines=True)
        lines = out.strip().split('\n') if out.strip() else []
        for line in lines[:limit]:
            if '\t' not in line:
                continue
            cid, content = line.split('\t', 1)
            cid = cid.strip()
            content = content.strip()
            is_image = content.startswith('[[ binary data')
            entry = {
                "id": cid,
                "content": content,
                "type": "image" if is_image else "text",
                "pinned": cid in pins,
            }
            if is_image:
                size, fmt, dims = parse_binary_marker(content)
                entry["size"] = size
                entry["fmt"] = fmt
                entry["dims"] = dims
            items.append(entry)
    except Exception:
        pass
    # pinned first, preserving relative order within each group
    items.sort(key=lambda it: 0 if it["pinned"] else 1)
    return items


def make_thumbnail_dataurl(cid, max_dim=160):
    try:
        raw = subprocess.check_output(["cliphist", "decode", cid])
        loader = GdkPixbuf.PixbufLoader()
        loader.write(raw)
        loader.close()
        pixbuf = loader.get_pixbuf()
        if pixbuf is None:
            return None
        w, h = pixbuf.get_width(), pixbuf.get_height()
        scale = min(1.0, max_dim / max(w, h))
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        scaled = pixbuf.scale_simple(nw, nh, GdkPixbuf.InterpType.BILINEAR)
        ok, buf = scaled.save_to_bufferv("png", [], [])
        if not ok:
            return None
        b64 = base64.b64encode(bytes(buf)).decode('ascii')
        return f"data:image/png;base64,{b64}"
    except Exception:
        return None


class ClipboardWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus - Clipboard")
        self.set_role("clipboard_popup")
        self.set_default_size(520, 650)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

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
        self.webview.connect("load-changed", self.on_load_changed)

        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.add(self.webview)
        self.show_all()

        GLib.timeout_add(40, self.position_at_cursor)

    def position_at_cursor(self, width=520, height=650):
        try:
            pos = json.loads(subprocess.check_output(["hyprctl", "-j", "cursorpos"]))
            cx, cy = pos["x"], pos["y"]
            x, y = cx - width // 2, cy - height // 2
            try:
                monitors = json.loads(subprocess.check_output(["hyprctl", "-j", "monitors"]))
                mon = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
                if mon:
                    mx, my = mon["x"], mon["y"]
                    mw, mh = mon["width"], mon["height"]
                    x = max(mx, min(x, mx + mw - width))
                    y = max(my, min(y, my + mh - height))
            except Exception:
                pass
            subprocess.run(["hyprctl", "dispatch", f"hl.dsp.window.move({{ x = {x}, y = {y} }})"])
        except Exception:
            pass
        return False

    def on_load_changed(self, webview, event):
        if event == WebKit2.LoadEvent.FINISHED:
            GLib.timeout_add(50, self.send_init)

    def eval_js(self, script):
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)

    def send_init(self):
        items = get_clip_items()
        payload = json.dumps({"items": items, "tenorKey": read_tenor_key()})
        self.eval_js(f"if (window.updateStats) {{ window.updateStats({payload}); }}")
        return False

    def on_js_action(self, content_manager, js_result):
        try:
            val = js_result.get_js_value().to_string()
            if val == "close":
                self.destroy()
            elif val.startswith("copy_item:"):
                cid = val.split(":", 1)[1]
                try:
                    content = subprocess.check_output(["cliphist", "decode", cid])
                    p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                    p.communicate(input=content)
                    p_pri = subprocess.Popen(["wl-copy", "--primary"], stdin=subprocess.PIPE)
                    p_pri.communicate(input=content)
                except Exception:
                    pass
                GLib.timeout_add(120, self.destroy)
            elif val.startswith("copy_raw:"):
                b64 = val.split(":", 1)[1]
                try:
                    text = base64.b64decode(b64).decode('utf-8')
                    p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
                    p.communicate(input=text.encode('utf-8'))
                    p_pri = subprocess.Popen(["wl-copy", "--primary"], stdin=subprocess.PIPE)
                    p_pri.communicate(input=text.encode('utf-8'))
                except Exception:
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
                pins = load_pins()
                if cid in pins:
                    pins.discard(cid)
                    save_pins(pins)
                GLib.timeout_add(150, self.send_init)
            elif val.startswith("toggle_pin:"):
                cid = val.split(":", 1)[1]
                pins = load_pins()
                if cid in pins:
                    pins.discard(cid)
                else:
                    pins.add(cid)
                save_pins(pins)
                GLib.timeout_add(50, self.send_init)
            elif val.startswith("get_thumb:"):
                cid = val.split(":", 1)[1]
                dataurl = make_thumbnail_dataurl(cid)
                if dataurl:
                    safe_id = json.dumps(cid)
                    safe_url = json.dumps(dataurl)
                    self.eval_js(f"if (window.setThumb) {{ window.setThumb({safe_id}, {safe_url}); }}")
            elif val == "clear_all":
                subprocess.Popen(["cliphist", "wipe"])
                save_pins(set())
                GLib.timeout_add(150, self.send_init)
        except Exception:
            pass

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
