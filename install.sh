#!/bin/bash
# Bootstraps this Hyprland rice onto an Arch/EndeavourOS machine.
# Safe to re-run: existing ~/.config targets are backed up once, not clobbered.
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_SRC="$DOTFILES_DIR/config"
BACKUP_DIR="$HOME/.config-backup-$(date +%Y%m%d-%H%M%S)"

OFFICIAL_PKGS=(
    hyprland hyprlock hyprpaper hyprpolkitagent hypridle
    waybar wofi mako
    kitty neovim zsh starship ttf-jetbrains-mono-nerd
    thunar thunar-volman gvfs
    grim slurp swappy wf-recorder brightnessctl playerctl wob
    cliphist wl-clipboard
    blueman bluez bluez-utils
    quickshell jq socat
    yad networkmanager pavucontrol
    papirus-icon-theme
    mpv imv rclone python
)
AUR_PKGS=(supergfxctl wlogout catppuccin-gtk-theme-mocha catppuccin-cursors-mocha)

echo "==> Installing official-repo packages"
sudo pacman -S --needed "${OFFICIAL_PKGS[@]}"

if ! command -v yay >/dev/null; then
    echo "==> yay not found — install an AUR helper first, then re-run for: ${AUR_PKGS[*]}"
else
    echo "==> Installing AUR packages"
    yay -S --needed "${AUR_PKGS[@]}"
fi

echo "==> Linking configs into ~/.config (backing up existing ones to $BACKUP_DIR)"
mkdir -p "$BACKUP_DIR"

link_config() {
    local name="$1"
    local target="$HOME/.config/$name"
    if [ -e "$target" ] || [ -L "$target" ]; then
        mkdir -p "$(dirname "$BACKUP_DIR/$name")"
        mv "$target" "$BACKUP_DIR/$name"
    fi
    mkdir -p "$(dirname "$target")"
    ln -s "$CONFIG_SRC/$name" "$target"
    echo "  linked $name"
}

for name in hypr waybar kitty wofi mako quickshell wlogout wob nvim swappy systemd; do
    [ -d "$CONFIG_SRC/$name" ] && link_config "$name"
done

# Copy local binaries/scripts
mkdir -p "$HOME/.local/bin" "$HOME/Linux_Back_Ups" "$HOME/.config/gtk-3.0"
if [ -d "$DOTFILES_DIR/local_bin" ]; then
    cp -rf "$DOTFILES_DIR/local_bin/"* "$HOME/.local/bin/"
    chmod +x "$HOME/.local/bin/"*
fi

# Add Thunar Sidebar Bookmark for Linux_Back_Ups
BOOKMARK_LINE="file://$HOME/Linux_Back_Ups Linux Back_Ups"
if [ -f "$HOME/.config/gtk-3.0/bookmarks" ]; then
    if ! grep -Fxq "$BOOKMARK_LINE" "$HOME/.config/gtk-3.0/bookmarks"; then
        echo "$BOOKMARK_LINE" >> "$HOME/.config/gtk-3.0/bookmarks"
    fi
else
    echo "$BOOKMARK_LINE" > "$HOME/.config/gtk-3.0/bookmarks"
fi

if [ -e "$HOME/.config/starship.toml" ] || [ -L "$HOME/.config/starship.toml" ]; then
    mv "$HOME/.config/starship.toml" "$BACKUP_DIR/starship.toml"
fi
ln -s "$CONFIG_SRC/starship.toml" "$HOME/.config/starship.toml"
echo "  linked starship.toml"

if [ -e "$HOME/.zshrc" ] || [ -L "$HOME/.zshrc" ]; then
    mv "$HOME/.zshrc" "$BACKUP_DIR/zshrc"
fi
ln -s "$DOTFILES_DIR/zshrc" "$HOME/.zshrc"
echo "  linked .zshrc"

if [ -e "$HOME/.config/mimeapps.list" ] || [ -L "$HOME/.config/mimeapps.list" ]; then
    mv "$HOME/.config/mimeapps.list" "$BACKUP_DIR/mimeapps.list"
fi
ln -s "$CONFIG_SRC/mimeapps.list" "$HOME/.config/mimeapps.list"
echo "  linked mimeapps.list (mpv for video, imv for images)"

echo "==> Enabling required system services"
sudo systemctl enable --now bluetooth
if pacman -Q supergfxctl >/dev/null 2>&1; then
    sudo systemctl enable --now supergfxd
fi
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable --now gdrive-watcher.service 2>/dev/null || true


echo "==> Setting zsh as default shell (if not already)"
if [ "$SHELL" != "$(command -v zsh)" ]; then
    chsh -s "$(command -v zsh)"
fi

echo "==> Applying GTK theme/icons/cursor (Catppuccin Mocha blue + Papirus-Dark)"
gsettings set org.gnome.desktop.interface gtk-theme "catppuccin-mocha-blue-standard+default"
gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark"
gsettings set org.gnome.desktop.interface cursor-theme "catppuccin-mocha-blue-cursors"
gsettings set org.gnome.desktop.interface cursor-size 24
gsettings set org.gnome.desktop.interface color-scheme "prefer-dark"

echo "==> Done. Anything that existed before was moved to $BACKUP_DIR"
echo "    Log out and back into Hyprland (or reboot) to pick everything up."
echo "    Neovim plugins install automatically the first time you launch nvim."
