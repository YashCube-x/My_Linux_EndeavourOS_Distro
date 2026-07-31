#!/usr/bin/env bash
# ==============================================================================
#  EndeavourOS / Arch Linux Hyprland Interactive Setup Wizard
# ==============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Detecting System Hardware & Compatibility ===${NC}"

# 1. Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$NAME
else
    OS_NAME="Linux"
fi
echo -e "OS Detected: ${GREEN}$OS_NAME${NC}"

# 2. Detect Total RAM
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
ZRAM_SIZE_GB=$((TOTAL_RAM_GB / 2))
[ $ZRAM_SIZE_GB -lt 2 ] && ZRAM_SIZE_GB=2
echo -e "RAM Detected: ${GREEN}${TOTAL_RAM_GB} GB${NC} (Recommended zRAM: ${ZRAM_SIZE_GB} GB)"

# 3. Detect GPU
GPU_INFO=$(lspci 2>/dev/null | grep -i 'vga\|3d\|display' || true)
HAS_NVIDIA=$(echo "$GPU_INFO" | grep -i "nvidia" || true)
HAS_INTEL=$(echo "$GPU_INFO" | grep -i "intel" || true)
HAS_AMD=$(echo "$GPU_INFO" | grep -i "amd" || true)

if [ -n "$HAS_NVIDIA" ]; then
    echo -e "GPU Detected: ${YELLOW}NVIDIA Graphics${NC}"
elif [ -n "$HAS_AMD" ]; then
    echo -e "GPU Detected: ${GREEN}AMD Radeon Graphics${NC}"
else
    echo -e "GPU Detected: ${BLUE}Intel Graphics${NC}"
fi

# 4. Check for TUI tool (whiptail)
if ! command -v whiptail &>/dev/null; then
    echo "Installing whiptail for interactive setup menu..."
    sudo pacman -S --noconfirm libnewt || true
fi

# ==============================================================================
# Interactive TUI Menu Selection
# ==============================================================================

CHOICES=$(whiptail --title "EndeavourOS / Hyprland Desktop Setup Wizard" \
  --checklist "Select features to install/configure (Use Spacebar to toggle, Enter to proceed):" 20 78 8 \
  "HYPRLAND_CONFIG" "Hyprland, Waybar, Wofi (Top-Left 0px, PiP rules)" ON \
  "SCRATCHPAD_TERM" "Dropdown Scratchpad Terminal (Super + S)" ON \
  "SCREENSHOT_SYS"  "Auto-Copy Screenshots & Click-to-Open Popup" ON \
  "WORKSPACE_SW"    "Workspace Switcher (Alt + Tab / Alt + Shift + Tab)" ON \
  "ZRAM_OPTIMIZE"   "zRAM Memory Compression (${ZRAM_SIZE_GB}GB zstd Swap)" ON \
  "CLI_SHELL"       "Zsh Productivity Aliases (ide, update, fzf Ctrl+R)" ON \
  "SLEEP_STABILITY" "Hypridle & Hyprlock Stabilization (No sleep crash)" ON 3>&1 1>&2 2>&3)

if [ $? -ne 0 ]; then
    echo "Setup cancelled by user."
    exit 0
fi

echo -e "\n${BLUE}=== Installing & Configuring Selected Features ===${NC}\n"

# Directory references
DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="$HOME/.config"
mkdir -p "$CONFIG_DIR" "$HOME/.local/bin"

# ------------------------------------------------------------------------------
# Feature 1: Hyprland & UI Configs
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"HYPRLAND_CONFIG"* ]]; then
    echo -e "${GREEN}[+] Configuring Hyprland, Waybar & Wofi...${NC}"
    mkdir -p "$CONFIG_DIR/hypr" "$CONFIG_DIR/waybar" "$CONFIG_DIR/wofi" "$CONFIG_DIR/mako"
    
    cp -rf "$DOTFILES_DIR/config/hypr/"* "$CONFIG_DIR/hypr/" 2>/dev/null || true
    cp -rf "$DOTFILES_DIR/config/waybar/"* "$CONFIG_DIR/waybar/" 2>/dev/null || true
    cp -rf "$DOTFILES_DIR/config/wofi/"* "$CONFIG_DIR/wofi/" 2>/dev/null || true
    cp -rf "$DOTFILES_DIR/config/mako/"* "$CONFIG_DIR/mako/" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# Feature 2: Dropdown Scratchpad Terminal
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"SCRATCHPAD_TERM"* ]]; then
    echo -e "${GREEN}[+] Setting up Dropdown Scratchpad Terminal (Super + S)...${NC}"
    mkdir -p "$CONFIG_DIR/hypr/scripts"
    cp -f "$DOTFILES_DIR/config/hypr/scripts/toggle_scratchpad.sh" "$CONFIG_DIR/hypr/scripts/" 2>/dev/null || true
    chmod +x "$CONFIG_DIR/hypr/scripts/toggle_scratchpad.sh" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# Feature 3: Screenshot Auto-Copy & Click Popup
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"SCREENSHOT_SYS"* ]]; then
    echo -e "${GREEN}[+] Configuring Screenshot Auto-Copy & Click-to-Open Notifications...${NC}"
    cp -f "$DOTFILES_DIR/local_bin/copy-screenshot.sh" "$HOME/.local/bin/" 2>/dev/null || true
    chmod +x "$HOME/.local/bin/copy-screenshot.sh" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# Feature 4: zRAM Memory Compression
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"ZRAM_OPTIMIZE"* ]]; then
    echo -e "${GREEN}[+] Configuring zRAM ${ZRAM_SIZE_GB}GB Memory Compression...${NC}"
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm zram-generator 2>/dev/null || true
        sudo sh -c "printf '[zram0]\nzram-size = ram / 2\ncompression-algorithm = zstd\n' > /etc/systemd/zram-generator.conf" 2>/dev/null || true
        sudo systemctl daemon-reload 2>/dev/null || true
        sudo systemctl restart systemd-zram-setup@zram0 2>/dev/null || true
    fi
fi

# ------------------------------------------------------------------------------
# Feature 5: Zsh Productivity Aliases & FZF
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"CLI_SHELL"* ]]; then
    echo -e "${GREEN}[+] Configuring Zsh Aliases & fzf History Search...${NC}"
    [ -f "$DOTFILES_DIR/zshrc" ] && cp -f "$DOTFILES_DIR/zshrc" "$HOME/.zshrc" || true
    [ -f "$DOTFILES_DIR/bashrc" ] && cp -f "$DOTFILES_DIR/bashrc" "$HOME/.bashrc" || true
    cp -f "$DOTFILES_DIR/local_bin/antigravity-ide" "$HOME/.local/bin/" 2>/dev/null || true
    chmod +x "$HOME/.local/bin/antigravity-ide" 2>/dev/null || true
fi

# ------------------------------------------------------------------------------
# Feature 6: Hypridle & Hyprlock Stabilization
# ------------------------------------------------------------------------------
if [[ "$CHOICES" == *"SLEEP_STABILITY"* ]]; then
    echo -e "${GREEN}[+] Stabilizing Hypridle & Hyprlock Sleep System...${NC}"
    cp -f "$DOTFILES_DIR/config/hypr/hypridle.conf" "$CONFIG_DIR/hypr/" 2>/dev/null || true
    cp -f "$DOTFILES_DIR/config/hypr/hyprlock.conf" "$CONFIG_DIR/hypr/" 2>/dev/null || true
fi

# Apply reloads
echo -e "\n${BLUE}=== Reloading Hyprland & Desktop Services ===${NC}"
hyprctl reload 2>/dev/null || true
makoctl reload 2>/dev/null || true

echo -e "\n${GREEN}✔ Setup Completed Successfully! Enjoy your custom Hyprland desktop!${NC}\n"
