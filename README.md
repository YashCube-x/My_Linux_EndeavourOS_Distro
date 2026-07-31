# My Linux EndeavourOS Distro — Hyprland Calm-Slate Rice

A complete Hyprland desktop setup: Hyprland (native Lua config) + Waybar (with
Quickshell as an on-demand alternate shell) + Kitty + Wofi + Mako + Neovim +
zsh/Starship, all on one consistent "calm slate" color palette — plus
`hypridle`/`hyprlock`, a wallpaper picker, screenshot annotation, screen
recording, GTK theming, and 80+ keybindings (press `SUPER+H` any time for the
full list).

There are two ways to set this up: **do it yourself step by step**, or
**hand it to an AI CLI (Claude Code / Gemini CLI) and let it do the work**.

---

## Color scheme — "calm slate"

Base/neutral colors (bar background, workspace pills, window title):

| Color | Hex | Used for |
|---|---|---|
| Crust | `#12141d` | Bar/lock-screen background |
| Separator | `#2a2d3a` | Dividers, borders |
| Muted | `#7a8296` | Inactive text, muted labels |
| Slate blue | `#8fb0e8` | Active workspace, Hyprland active border (gradient end) |
| Mauve | `#cba6f7` | Hyprland active border (gradient start) |

Each waybar/wlogout module gets its own accent — background + a dark
foreground (`#0d1f14`–`#241505` range) for contrast:

| Module | Background | Where else it's used |
|---|---|---|
| Launcher / clock | `#c9b8ff` (light purple) | wlogout logout button |
| RAM / disk | `#5ecb8a` (sage green) | — |
| CPU | `#f0a93e` (amber) | wlogout reboot button |
| Brightness | `#f0c65e` (yellow) | — |
| WiFi | `#a48ff0` (purple) | — |
| Bluetooth | `#5edfe8` (cyan) | — |
| Volume | `#7ea6f0` (blue) | wlogout sleep button |
| Battery / power | `#f08a94` (rose) | wlogout shutdown button |

Kitty, wofi, hyprlock, and mako use the standard
[Catppuccin Mocha](https://github.com/catppuccin/catppuccin) palette rather
than these custom accents — close in spirit (same dark-base philosophy) but
not pixel-matched to the table above. GTK apps (Thunar, blueman-manager,
yad) use `catppuccin-gtk-theme-mocha` with a blue accent, applied via
`gsettings` (see Known Limitations below for why they're not pixel-matched
either).

All the exact values live in `config/waybar/style.css` (`@define-color`
block at the top) and `config/hypr/hyprland.lua` (`col.active_border` /
`col.inactive_border` in the `general` section) if you want to retheme
anything.

---

## Option A: Do it yourself

### Step 1 — Install EndeavourOS

Download the ISO from [endeavouros.com](https://endeavouros.com/), flash it
to a USB drive (`dd`, or [Rufus](https://rufus.ie/) on Windows), boot from
it, and go through the installer. Pick any desktop option during install
(or "No Desktop") — this repo replaces whatever it sets up.

*(Using plain Arch instead? Follow the
[Arch install guide](https://wiki.archlinux.org/title/Installation_guide),
then install an AUR helper yourself before Step 3:)*
```bash
sudo pacman -S --needed base-devel git
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si
```

### Step 2 — Pull this repo

Once you're booted in and logged into a terminal, with internet working:

```bash
git clone https://github.com/YashCube-x/My_Linux_EndourOS_Distro.git ~/dotfiles
```

### Step 3 — Run the Interactive Setup Wizard

```bash
cd ~/dotfiles
./setup.sh
```

*(This opens an interactive GUI menu where you can toggle which features to install, auto-detects your RAM/GPU hardware, and configures everything automatically!)*

This installs every package the setup needs (via `pacman` and `yay`),
symlinks all the configs into `~/.config/`, enables the required system
services, and applies the GTK theme. Reboot (or log out and back in) once
it finishes.

---

## Option B: Let an AI CLI do it for you

If you have (or are willing to install) **Claude Code** or **Gemini CLI**,
you can skip doing this by hand — install whichever one, open a terminal in
your home directory, run it, and paste the prompt below. It will clone the
repo, read this README, run the installer, and — unlike a plain script —
actually troubleshoot anything that goes wrong (missing packages, `sudo`
password prompts it can't answer itself, a config that doesn't apply
cleanly, etc.) instead of just failing silently.

**Install one of these first:**
- Claude Code: `npm install -g @anthropic-ai/claude-code` (needs Node.js:
  `sudo pacman -S nodejs npm` first if you don't have it), then run `claude`
- Gemini CLI: `npm install -g @google/gemini-cli`, then run `gemini`

**Then paste this prompt:**

```
Clone https://github.com/YashCube-x/My_Linux_EndourOS_Distro.git into
~/dotfiles (skip if it's already there), read its README.md for context,
then run ./install.sh to set up this Hyprland desktop environment.

Rules for you to follow while doing this:
- You almost certainly can't run `sudo` interactively yourself (no real
  TTY for password prompts). When a command needs sudo, tell me the exact
  command and ask me to run it in my own terminal, then wait for me to
  confirm before continuing.
- After I say a step is "done", verify it actually happened yourself
  (check the package is installed, check the service is running, etc.)
  rather than just trusting my word — I might be wrong about what
  finished.
- If something errors, don't just retry blindly — read the actual error,
  explain what's wrong in plain terms, and fix the root cause.
- If a step is destructive or affects things outside this setup, ask me
  before doing it.
- Once install.sh finishes, reload/restart the relevant services and
  actually confirm the desktop looks right (e.g. screenshot the bar,
  check hyprctl for config errors) instead of assuming it worked.
- Ask me before installing anything not already listed in this repo's
  install.sh or README.
```

---

## What's in here

| Path | What it is |
|---|---|
| `config/hypr/` | `hyprland.lua` (compositor config, 80+ keybinds, animations, blur, tiling controls), `hyprlock.conf`, `hyprpaper.conf`, `hypridle.conf` (auto lock/dim/suspend), `scripts/` (smart volume/brightness/menu/powermenu wrappers, wallpaper picker, keybind cheat-sheet, battery warning, screen-record toggle), `wallpaper/` (switch with `SUPER+W`) |
| `config/waybar/` | Bar config + calm-slate `style.css` + `scripts/` (volume/brightness sliders via `yad`, WiFi popup via `nmcli`+`wofi`, Bluetooth popup via `bluetoothctl`+`wofi`, clipboard picker via `cliphist`, notification toggle) |
| `config/kitty/` | Terminal config, Catppuccin Mocha colors, JetBrains Mono Nerd Font |
| `config/wofi/` | App launcher styling |
| `config/mako/` | Notification daemon styling |
| `config/quickshell/` | Alternate native shell (QML) — control center, OSD, GPU switcher, clipboard manager. Toggle with `SUPER+SHIFT+Q`. Adapted from [matteogini/dotfiles](https://github.com/matteogini/dotfiles). |
| `config/wlogout/` | Centered 4-option power menu (shutdown/restart/sleep/logout) |
| `config/wob/` | Volume/brightness OSD bar used when Quickshell isn't running |
| `config/swappy/` | Screenshot annotation (crop/draw/copy) — `Print`/`SUPER+Print` |
| `config/nvim/` | Neovim config: `lazy.nvim`, LSP via `mason.nvim`, `nvim-cmp` autocomplete, `nvim-tree`, Catppuccin Mocha theme |
| `config/starship.toml` | Shell prompt |
| `config/mimeapps.list` | `mpv` for video, `imv` for images |
| `zshrc` | `.zshrc` |
| `bashrc` | `.bashrc` |
| `local_bin/` | Utility CLI binaries (`copy-screenshot.sh`, `setup_zram.sh`, `antigravity-ide`, `flameshot-hypr`) |
| `install.sh` | Installs every package below and symlinks everything into place |

---

## ⚡ Recent Desktop Enhancements & Features

- **Wofi Top-Left Zero-Gap Application Menu**: Positioned at top-left attached directly under Waybar (`move = {0, 27}`), with sharp 90-degree corners, thin 1px border, and compact dimensions (`250x300`). Triggered via **`SUPER+SPACE`** or Waybar **"e"** logo.
- **YouTube Picture-in-Picture**: Pinned across ALL workspaces (`pin = true`, `float = true`) with interactive mouse border drag resizing (`resize_on_border = true`).
- **Dropdown Scratchpad Terminal**: Instant floating Kitty terminal toggle using **`SUPER+S`**.
- **Workspace Switcher**: Fast workspace navigation using **`ALT+TAB`** (next workspace `e+1`) and **`ALT+SHIFT+TAB`** (previous workspace `e-1`).
- **Auto-Copy Screenshots & Click-to-Open Notifications**: **`Print`** / **`SUPER+Print`** automatically captures region, saves to `~/Pictures/Screenshots/`, and copies `image/png` to clipboard for instant **`CTRL+V`** pasting. Left-clicking the Mako notification popup opens the image in `imv`.
- **Clipboard History Picker**: Browse and paste past text/image snippets via **`SUPER+ALT+V`**.
- **Interactive Terminal History Search**: Fuzzy search command history using **`CTRL+R`** in Zsh via `fzf`.
- **zRAM Memory Compression**: Active 3.7GB `zstd` compressed RAM swap (`/dev/zram0` at Priority 100) allowing 8GB RAM systems to perform smoothly like 12GB.
- **Sleep & Suspend Stabilization**: Eliminated DPMS signal drops and crashed lockscreen screens (`hypridle`/`hyprlock`) with clean PAM handle refresh on wake-up.
- **Antigravity IDE & Shell Aliases**: SimpleDialog enabled for 100% click responsiveness; added `ide` & `agy-ide` terminal commands.

---

## ⌨️ Keybindings Reference

| Keybinding | Function / Action |
|---|---|
| `SUPER` + `SPACE` | Open Wofi Application Launcher (Top-Left under Waybar, 0px gap) |
| `SUPER` + `RETURN` / `SUPER` + `Q` | Open Kitty Terminal |
| `SUPER` + `E` | Open Thunar File Manager |
| `SUPER` + `SHIFT` + `B` | Open Firefox Web Browser |
| `SUPER` + `C` | Close Active Window |
| `SUPER` + `M` | Exit / Logout Hyprland Session |
| `SUPER` + `V` | Toggle Window Floating State |
| `SUPER` + `P` | Toggle Dwindle Pseudo-Tiling Mode |
| `SUPER` + `J` | Toggle Dwindle Split Direction (Horizontal / Vertical) |
| `SUPER` + `F` | Toggle Fullscreen Mode |
| `SUPER` + `SHIFT` + `F` | Toggle Maximized Window Mode |
| `SUPER` + `S` | Toggle Dropdown Scratchpad Terminal (Floating Kitty) |
| `SUPER` + `ALT` + `V` | Open Clipboard History Picker (Browse & paste past text/code/screenshots) |
| `ALT` + `TAB` | Switch to Next Workspace (`e+1`) |
| `ALT` + `SHIFT` + `TAB` | Switch to Previous Workspace (`e-1`) |
| `SUPER` + `SHIFT` + `P` | Pin / Unpin Floating Window across all workspaces |
| `SUPER` + `W` | Open Interactive Wallpaper Picker |
| `SUPER` + `H` | Open Interactive Keybinding Cheatsheet |
| `SUPER` + `ESCAPE` | Open Power & Logout Menu (Lock, Suspend, Logout, Reboot, Shutdown) |
| `PRINT` / `SUPER` + `PRINT` | Capture Screenshot → Auto-copy to clipboard + Click notification to open in `imv` |
| `CTRL` + `R` (in Zsh Terminal) | Interactive Fuzzy Command History Search (`fzf`) |
| `SUPER` + Left Mouse Drag | Move Window anywhere on screen |
| `SUPER` + Right Mouse Drag | Resize Window dynamically |
| Mouse Border Drag | Drag window borders/corners directly to resize (e.g. YouTube PiP window) |




Because configs are **symlinked** by `install.sh`, editing a file under
`~/.config/...` afterward is the same as editing it in
`~/dotfiles/config/...` — commit from either place.

## Known limitations / before reusing on a different machine or username

- Four files hardcode the absolute path `/home/suyash/...`: `config/hypr/hyprpaper.conf` and three `config/quickshell/*.qml` files (`AppLauncher.qml`, `ThemeSwitcher.qml`, `shell.qml`). If you restore this under a **different username**, run this before symlinking:
  ```bash
  grep -rl '/home/suyash' ~/dotfiles/config | xargs sed -i 's#/home/suyash#'"$HOME"'#g'
  ```
- `hyprpaper.conf` targets a specific monitor name (`eDP-1`). On different hardware, check `hyprctl monitors` and adjust.
- Neovim plugins (via `lazy.nvim`) aren't vendored here — they install automatically the first time you launch `nvim` (needs internet).
- Bluetooth requires the `bluetooth` service (handled by `install.sh`); the GPU switcher needs `supergfxd` (also handled) **and** actual hybrid Intel/Nvidia graphics to do anything useful.
- GTK apps (Thunar, blueman-manager, yad, pavucontrol) use Catppuccin Mocha (blue accent) + Papirus-Dark icons + matching cursor, applied via `gsettings`. Not pixel-matched to the custom calm-slate hex palette used in the bar/lock-screen/power-menu, but dark and cohesive rather than the default light GTK theme. Quickshell draws its own UI in QML, so it isn't affected either way.

## Package list

**Official repo:** `hyprland hyprlock hyprpaper hyprpolkitagent hypridle waybar wofi mako kitty neovim zsh starship ttf-jetbrains-mono-nerd thunar thunar-volman gvfs grim slurp swappy wf-recorder brightnessctl playerctl wob cliphist wl-clipboard blueman bluez bluez-utils quickshell jq socat yad networkmanager pavucontrol papirus-icon-theme mpv imv`

**AUR:** `supergfxctl wlogout catppuccin-gtk-theme-mocha catppuccin-cursors-mocha`
