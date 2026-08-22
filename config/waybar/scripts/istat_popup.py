#!/usr/bin/env python3
import os
import sys
import math
import subprocess
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Gdk, GLib, Pango, PangoCairo, cairo

PID_FILE = "/tmp/istat_popup.pid"

# Toggle logic: if already open, kill and exit
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

def get_stats():
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

    load1 = 0.0
    try:
        with open('/proc/loadavg', 'r') as f:
            load1 = float(f.read().split()[0])
    except Exception:
        pass
    
    cpu_count = os.cpu_count() or 4
    pressure_pct = min(100, int((load1 / cpu_count) * 100))

    # Segments for Memory Gauge (App=Blue, Wired=Pink, Comp=Yellow)
    segments = []
    if total > 0:
        segments.append((app_mem / total, 0.23, 0.51, 0.96))      # Blue #3b82f6
        segments.append((wired_mem / total, 0.92, 0.28, 0.60))    # Pink #ec4899
        segments.append((compressed_mem / total, 0.92, 0.70, 0.03)) # Yellow #eab308

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
                    
                    processes.append((display_name, size_str))
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
        "segments": segments,
        "app_mem": fmt_gb(app_mem),
        "wired_mem": fmt_gb(wired_mem),
        "compressed_mem": fmt_gb(compressed_mem),
        "free_mem": fmt_gb(available),
        "swap_used": fmt_mb(swap_used) if swap_total > 0 else "0 MB",
        "swap_total": fmt_gb(swap_total) if swap_total > 0 else "0 GB",
        "swap_pct": swap_pct,
        "processes": processes
    }

class GaugeWidget(Gtk.DrawingArea):
    def __init__(self, title, gauge_type):
        super().__init__()
        self.set_size_request(105, 105)
        self.title = title
        self.gauge_type = gauge_type
        self.pct = 0
        self.segments = []
        self.connect("draw", self.on_draw)

    def set_data(self, pct, segments=None):
        self.pct = pct
        self.segments = segments or []
        self.queue_draw()

    def on_draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cx = w / 2.0
        cy = h / 2.0
        r = min(cx, cy) - 10.0
        lw = 7.5

        # 1. Background circle track
        cr.set_line_width(lw)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.09)
        cr.arc(cx, cy, r, 0, 2 * math.pi)
        cr.stroke()

        # 2. Draw Progress Arc
        start_angle = -math.pi / 2.0
        cr.set_line_cap(cairo.LINE_CAP_ROUND)

        if self.gauge_type == "pressure":
            end_angle = start_angle + (max(0.01, self.pct) / 100.0) * (2 * math.pi)
            cr.set_source_rgba(0.22, 0.74, 0.97, 1.0) # Cyan #38bdf8
            cr.arc(cx, cy, r, start_angle, end_angle)
            cr.stroke()
        else:
            # Multi-segment memory arc (App=Blue, Wired=Pink, Compressed=Yellow)
            curr_angle = start_angle
            for frac, red, green, blue in self.segments:
                seg_angle = frac * (2 * math.pi)
                if seg_angle > 0.02:
                    cr.set_source_rgba(red, green, blue, 1.0)
                    cr.arc(cx, cy, r, curr_angle, curr_angle + seg_angle)
                    cr.stroke()
                    curr_angle += seg_angle

        # 3. Draw Center Percentage Number with PangoCairo
        layout = PangoCairo.create_layout(cr)
        font_desc = Pango.FontDescription("Inter Bold 17")
        layout.set_font_description(font_desc)
        
        pct_markup = f'<span font_weight="bold" color="#ffffff">{self.pct}%</span>'
        layout.set_markup(pct_markup, -1)
        ink, logical = layout.get_pixel_extents()
        cr.move_to(cx - logical.width / 2.0, cy - logical.height / 2.0 - 5)
        PangoCairo.show_layout(cr, layout)

        # 4. Draw Subtitle Label
        sub_desc = Pango.FontDescription("Inter Bold 8")
        layout.set_font_description(sub_desc)
        label_color = "#38bdf8" if self.gauge_type == "pressure" else "#f59e0b"
        lbl_markup = f'<span font_weight="bold" color="{label_color}">{self.title}</span>'
        layout.set_markup(lbl_markup, -1)
        ink, logical = layout.get_pixel_extents()
        cr.move_to(cx - logical.width / 2.0, cy + 12)
        PangoCairo.show_layout(cr, layout)

        return False

class IStatWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("iStat Menus")
        self.set_role("istat_popup")
        self.set_default_size(325, 485)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_name("istat-card")

        # RGBA visual for true glass transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Load GTK CSS
        css_provider = Gtk.CssProvider()
        css_data = b"""
            #istat-card {
                background-color: rgba(22, 27, 46, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
            }
            .title-sec {
                color: #60a5fa;
                font-weight: 700;
                font-size: 10px;
                letter-spacing: 0.8px;
            }
            .item-label {
                color: rgba(255, 255, 255, 0.85);
                font-size: 11.5px;
                font-weight: 500;
            }
            .item-val {
                color: #ffffff;
                font-size: 11.5px;
                font-weight: 600;
            }
            .swap-bar progress {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            .swap-bar progress trough {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
            }
            .swap-bar progress progress {
                background: #3b82f6;
                border-radius: 3px;
            }
            .dock-btn {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #ffffff;
                padding: 5px 12px;
                font-size: 13px;
            }
            .dock-btn:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """
        css_provider.load_from_data(css_data)
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Main Layout Box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # Gauges Box
        gauges_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        gauges_box.set_homogeneous(True)
        self.pressure_gauge = GaugeWidget("PRESSURE", "pressure")
        self.memory_gauge = GaugeWidget("MEMORY", "memory")
        gauges_box.pack_start(self.pressure_gauge, True, True, 0)
        gauges_box.pack_start(self.memory_gauge, True, True, 0)
        main_box.pack_start(gauges_box, False, False, 0)

        # Separator
        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep1, False, False, 0)

        # Memory Breakdown Rows
        self.lbl_app = Gtk.Label(label="0 GB")
        self.lbl_wired = Gtk.Label(label="0 GB")
        self.lbl_comp = Gtk.Label(label="0 GB")
        self.lbl_free = Gtk.Label(label="0 GB")

        def make_row(dot_color, name, lbl_val):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            dot = Gtk.Label(label="●")
            dot.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(*dot_color))
            lbl = Gtk.Label(label=name)
            lbl.get_style_context().add_class("item-label")
            lbl_val.get_style_context().add_class("item-val")
            row.pack_start(dot, False, False, 0)
            row.pack_start(lbl, False, False, 0)
            row.pack_end(lbl_val, False, False, 0)
            return row

        main_box.pack_start(make_row((0.23, 0.51, 0.96, 1.0), "App", self.lbl_app), False, False, 0)
        main_box.pack_start(make_row((0.92, 0.28, 0.6, 1.0), "Wired", self.lbl_wired), False, False, 0)
        main_box.pack_start(make_row((0.92, 0.7, 0.03, 1.0), "Compressed", self.lbl_comp), False, False, 0)
        main_box.pack_start(make_row((0.4, 0.45, 0.55, 1.0), "Free", self.lbl_free), False, False, 0)

        # Processes Title
        title_proc = Gtk.Label(label="PROCESSES", xalign=0)
        title_proc.get_style_context().add_class("title-sec")
        main_box.pack_start(title_proc, False, False, 0)

        # Processes Box
        self.proc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        main_box.pack_start(self.proc_box, False, False, 0)

        # Swap Box
        swap_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        swap_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_swap = Gtk.Label(label="SWAP")
        title_swap.get_style_context().add_class("title-sec")
        self.lbl_swap = Gtk.Label(label="0 MB of 0 GB")
        self.lbl_swap.get_style_context().add_class("item-label")
        swap_header.pack_start(title_swap, False, False, 0)
        swap_header.pack_end(self.lbl_swap, False, False, 0)

        self.swap_bar = Gtk.ProgressBar()
        self.swap_bar.get_style_context().add_class("swap-bar")
        self.swap_bar.set_fraction(0.1)

        swap_box.pack_start(swap_header, False, False, 0)
        swap_box.pack_start(self.swap_bar, False, False, 0)
        main_box.pack_start(swap_box, False, False, 0)

        # Bottom Actions
        dock_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        dock_box.set_homogeneous(True)
        
        btn_btop = Gtk.Button(label="📊")
        btn_btop.get_style_context().add_class("dock-btn")
        btn_btop.set_tooltip_text("Activity Monitor (btop)")
        btn_btop.connect("clicked", lambda b: (subprocess.Popen(["kitty", "-e", "btop"]), self.destroy()))

        btn_term = Gtk.Button(label="💻")
        btn_term.get_style_context().add_class("dock-btn")
        btn_term.set_tooltip_text("Terminal")
        btn_term.connect("clicked", lambda b: (subprocess.Popen(["kitty"]), self.destroy()))

        btn_clean = Gtk.Button(label="🧹")
        btn_clean.get_style_context().add_class("dock-btn")
        btn_clean.set_tooltip_text("Clean / Sync RAM")
        btn_clean.connect("clicked", lambda b: subprocess.Popen(["sync"]))

        btn_close = Gtk.Button(label="✕")
        btn_close.get_style_context().add_class("dock-btn")
        btn_close.set_tooltip_text("Close")
        btn_close.connect("clicked", lambda b: self.destroy())

        dock_box.pack_start(btn_btop, True, True, 0)
        dock_box.pack_start(btn_term, True, True, 0)
        dock_box.pack_start(btn_clean, True, True, 0)
        dock_box.pack_start(btn_close, True, True, 0)
        main_box.pack_start(dock_box, False, False, 0)

        # Key bindings & destruction
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.on_destroy)

        self.update_data()
        self.show_all()

        GLib.timeout_add(1500, self.update_data)

    def update_data(self):
        stats = get_stats()
        self.pressure_gauge.set_data(stats["pressure_pct"])
        self.memory_gauge.set_data(stats["mem_pct"], stats["segments"])

        self.lbl_app.set_text(stats["app_mem"])
        self.lbl_wired.set_text(stats["wired_mem"])
        self.lbl_comp.set_text(stats["compressed_mem"])
        self.lbl_free.set_text(stats["free_mem"])

        self.lbl_swap.set_text(f"{stats['swap_used']} of {stats['swap_total']}")
        self.swap_bar.set_fraction(stats["swap_pct"] / 100.0)

        # Update processes
        for child in self.proc_box.get_children():
            self.proc_box.remove(child)

        for name, size in stats["processes"]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            lbl_name = Gtk.Label(label=name, xalign=0)
            lbl_name.get_style_context().add_class("item-label")
            lbl_size = Gtk.Label(label=size)
            lbl_size.get_style_context().add_class("item-val")
            row.pack_start(lbl_name, True, True, 0)
            row.pack_end(lbl_size, False, False, 0)
            self.proc_box.pack_start(row, False, False, 0)

        self.proc_box.show_all()
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
