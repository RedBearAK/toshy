#!/usr/bin/env bash
#
# Toshy Environment Information Collection Script
# ----------------------------------------------
# This script collects system environment information to help diagnose issues with
# environment detection in the Toshy keymapper. The collected information is packaged
# into a timestamped zip file that users can attach to GitHub issues.
#
# The script only collects system configuration and environment data, not personal files.

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Create base name and timestamp for both temp dir and output file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ENV_DUMP_NAME="toshy_env_dump_${TIMESTAMP}"

# Determine temp directory location (XDG_RUNTIME_DIR if available, otherwise /tmp)
if [ -n "$XDG_RUNTIME_DIR" ] && [ -d "$XDG_RUNTIME_DIR" ]; then
    TEMP_BASE_DIR="$XDG_RUNTIME_DIR"
else
    TEMP_BASE_DIR="/tmp"
fi

# Determine output location (Downloads folder if available, otherwise home directory)
if [ -d "$HOME/Downloads" ]; then
    OUTPUT_DIR="$HOME/Downloads"
else
    OUTPUT_DIR="$HOME"
fi

TEMP_DIR="${TEMP_BASE_DIR}/${ENV_DUMP_NAME}"
OUTPUT_FILE="${OUTPUT_DIR}/${ENV_DUMP_NAME}.zip"

# Introduction and explanation
echo -e "${BOLD}${BLUE}Toshy Environment Information Collection Script${RESET}"
echo
echo -e "This script will collect raw system environment information to help diagnose"
echo -e "issues with environment detection in the Toshy keymapper."
echo
echo -e "The following information will be collected:"
echo -e "  ${GREEN}•${RESET} System release files (/etc/os-release, /etc/lsb-release, etc.)"
echo -e "  ${GREEN}•${RESET} Environment variables (with HOME, USER, and password-related entries filtered)"
echo -e "  ${GREEN}•${RESET} Process list (filtered to focus on important processes)"
echo -e "  ${GREEN}•${RESET} Output from various system information commands"
echo -e "  ${GREEN}•${RESET} D-Bus service information"
echo
echo -e "${YELLOW}The information will be saved to:${RESET} ${BOLD}$OUTPUT_FILE${RESET}"
echo -e "${YELLOW}No private configuration files, passwords, or SSH keys will be collected.${RESET}"
echo

# Ask for confirmation
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Operation canceled.${RESET}"
    exit 1
fi

# Create temporary directory
mkdir -p "$TEMP_DIR"
echo -e "${BLUE}Creating temporary directory at $TEMP_DIR...${RESET}"

# Function to copy system release files
collect_release_files() {
    echo -e "${BLUE}Collecting system release files...${RESET}"
    
    mkdir -p "$TEMP_DIR/release_files"
    
    # Copy release files if they exist
    for file in /etc/os-release /etc/lsb-release /etc/arch-release /etc/fedora-release /etc/debian_version /etc/redhat-release; do
        if [ -f "$file" ]; then
            cp "$file" "$TEMP_DIR/release_files/" 2>/dev/null || echo "Could not copy $file" > "$TEMP_DIR/release_files/$(basename $file).error"
        fi
    done
}

# Collect raw environment variables output
collect_env_vars() {
    echo -e "${BLUE}Collecting environment variables...${RESET}"
    
    # Raw env output (with minimal filtering for security)
    env | grep -v -E "(PASSWORD|SECRET|PASS|KEY|AUTH|SSH|HOME|USER)" > "$TEMP_DIR/environment_variables.txt"
}

# Collect raw process list
collect_process_list() {
    echo -e "${BLUE}Collecting process information...${RESET}"
    
    # Full process list (with usernames redacted for privacy)
    # Only filtering out kernel threads (commands in square brackets)
    ps aux 2>/dev/null | 
        sed -E 's/^([a-zA-Z0-9_\-]+)[ \t]+/USER /' | 
        grep -v -E '\[.*\]$' > "$TEMP_DIR/process_list.txt" || 
        echo "Could not create process list" > "$TEMP_DIR/process_list.txt"
    
    # Create tree-views of processes to better show parent-child relationships
    if command -v pstree >/dev/null 2>&1; then
        # Create a simplified process tree (1 level deep)
        # Different versions of pstree use different options for depth limiting
        # Explicitly start from PID 1 (systemd/init) to avoid kernel threads
        pstree -p 1 --level 1 > "$TEMP_DIR/process_tree_collapsed.txt" 2>/dev/null || \
        pstree -p 1 -n 1 > "$TEMP_DIR/process_tree_collapsed.txt" 2>/dev/null || \
        pstree -p 1 -l 1 > "$TEMP_DIR/process_tree_collapsed.txt" 2>/dev/null || \
        pstree 1 > "$TEMP_DIR/process_tree_collapsed.txt" 2>/dev/null || \
        echo "Could not create collapsed process tree" > "$TEMP_DIR/process_tree_collapsed.txt"
        
        # Also create a full process tree for reference, also starting from PID 1
        pstree -p 1 > "$TEMP_DIR/process_tree_full.txt" 2>/dev/null || \
        pstree 1 > "$TEMP_DIR/process_tree_full.txt" 2>/dev/null || \
        echo "Could not create full process tree" > "$TEMP_DIR/process_tree_full.txt"
    else
        echo "pstree command not available" > "$TEMP_DIR/process_tree_collapsed.txt"
        echo "pstree command not available" > "$TEMP_DIR/process_tree_full.txt"
    fi
    
    # # Create a focused list of likely window manager and session-related processes
    # {
    #     echo "=== Window Manager Related Processes ==="
    #     echo

    #     # Find all processes that might be window managers or compositors
    #     ps aux 2>/dev/null | 
    #     grep -v -E '\[.*\]$' | 
    #     grep -E "gnome-shell|mutter|kwin|plasmashell|sway|wayfire|river|weston|hyprland|labwc|niri|cosmic-comp|qtile|i3|bspw|awesome|xfwm|openbox|fluxbox|compton|picom|marco|gala|budgie|cinnamon|fvwm|enlightenment|miriway|dwm|xmonad" | 
    #     grep -v grep | 
    #     sed -E 's/^([a-zA-Z0-9_\-]+)[ \t]+/USER /' || 
    #     echo "No window manager processes found"
        
    # } > "$TEMP_DIR/window_manager_processes.txt"
    
    # Alternative process listing that shows parent-child relationships
    # Only filtering out kernel threads
    ps -ef 2>/dev/null | 
        sed -E 's/^([a-zA-Z0-9_\-]+)[ \t]+/USER /' | 
        grep -v -E '\[.*\]$' > "$TEMP_DIR/process_list_with_ppid.txt" || 
        echo "Could not create process list with PPIDs" > "$TEMP_DIR/process_list_with_ppid.txt"
}

# Collect system command outputs
collect_command_outputs() {
    echo -e "${BLUE}Collecting system command outputs...${RESET}"
    
    mkdir -p "$TEMP_DIR/command_outputs"
    
    # System information
    uname -a > "$TEMP_DIR/command_outputs/uname.txt" 2>&1 || true
    
    # Display server information
    echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE" > "$TEMP_DIR/command_outputs/session_type.txt"
    
    # X11 specific commands
    if [ "$XDG_SESSION_TYPE" = "x11" ] || [ -n "$DISPLAY" ]; then
        xrandr > "$TEMP_DIR/command_outputs/xrandr.txt" 2>&1 || true
        xdpyinfo > "$TEMP_DIR/command_outputs/xdpyinfo.txt" 2>&1 || true
        xprop -root > "$TEMP_DIR/command_outputs/xprop_root.txt" 2>&1 || true
        wmctrl -m > "$TEMP_DIR/command_outputs/wmctrl_m.txt" 2>&1 || true
    fi
    
    # Wayland specific commands
    if [ "$XDG_SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
        echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY" > "$TEMP_DIR/command_outputs/wayland_display.txt"
    fi
    
    # Input devices
    if command -v libinput >/dev/null 2>&1; then
        libinput list-devices > "$TEMP_DIR/command_outputs/libinput_list_devices.txt" 2>&1 || true
    fi
    
    xinput list > "$TEMP_DIR/command_outputs/xinput_list.txt" 2>&1 || true
    
    # Copy input devices file
    cp /proc/bus/input/devices "$TEMP_DIR/command_outputs/proc_input_devices.txt" 2>&1 || true
    
    # systemd services (window manager related)
    systemctl --user list-units '*session*' '*display*' '*x11*' '*wayland*' '*wm*' '*compositor*' '*desktop*' '*window*' --no-pager > "$TEMP_DIR/command_outputs/systemctl_user_display_units.txt" 2>&1 || true
}

# Collect D-Bus information
collect_dbus_info() {
    echo -e "${BLUE}Collecting D-Bus information...${RESET}"
    
    mkdir -p "$TEMP_DIR/dbus_info"
    
    # List all D-Bus services (system and session)
    if command -v busctl >/dev/null 2>&1; then
        busctl list --user > "$TEMP_DIR/dbus_info/busctl_user.txt" 2>&1 || true
        busctl list --system > "$TEMP_DIR/dbus_info/busctl_system.txt" 2>&1 || true
    fi
    
    if command -v dbus-send >/dev/null 2>&1; then
        dbus-send --session --dest=org.freedesktop.DBus --type=method_call --print-reply /org/freedesktop/DBus org.freedesktop.DBus.ListNames > "$TEMP_DIR/dbus_info/dbus_session_names.txt" 2>&1 || true
    fi
}

# Create README file
create_readme() {
    echo -e "${BLUE}Creating README file...${RESET}"
    
    {
        echo "=== Toshy Environment Information Collection ==="
        echo "Collection date: $(date)"
        echo "Collection script version: 1.0.0"
        echo
        echo "This archive contains raw system environment information to help troubleshoot"
        echo "environment detection issues in the Toshy keymapper."
        echo
        echo "--- Key Environment Variables ---"
        echo "Session type: $XDG_SESSION_TYPE"
        echo "DISPLAY: $DISPLAY"
        echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
        echo "XDG_CURRENT_DESKTOP: $XDG_CURRENT_DESKTOP"
        echo "XDG_SESSION_DESKTOP: $XDG_SESSION_DESKTOP"
        echo "DESKTOP_SESSION: $DESKTOP_SESSION"
        
        # Add DE-specific env vars if they exist
        if [ -n "$KDE_SESSION_VERSION" ]; then
            echo "KDE_SESSION_VERSION: $KDE_SESSION_VERSION"
        fi
        
        if [ -n "$GNOME_SHELL_SESSION_MODE" ]; then
            echo "GNOME_SHELL_SESSION_MODE: $GNOME_SHELL_SESSION_MODE"
        fi
        
        if [ -n "$HYPRLAND_INSTANCE_SIGNATURE" ]; then
            echo "HYPRLAND_INSTANCE_SIGNATURE: $HYPRLAND_INSTANCE_SIGNATURE"
        fi
        
        echo
        echo "Folder structure:"
        echo "- command_outputs/: Raw output from various system commands"
        echo "- dbus_info/: D-Bus service information"
        echo "- release_files/: System release information files"
        echo "- environment_variables.txt: Environment variables"
        echo "- process_list.txt: Process list (no kernel threads)"
        echo "- process_list_with_ppid.txt: Process list with parent PIDs (no kernel threads)"
        echo "- process_tree_collapsed.txt: Simplified tree view of processes (1 level deep)"
        echo "- process_tree_full.txt: Complete tree view of processes"
        echo "- window_manager_processes.txt: Focused list of window manager processes"
        echo
        echo "Please attach this file to your GitHub issue."
    } > "$TEMP_DIR/README.txt"
}

# Run all collection functions
echo -e "${BLUE}Starting data collection...${RESET}"
collect_release_files || echo -e "${RED}Error during release file collection${RESET}"
collect_env_vars || echo -e "${RED}Error during environment variable collection${RESET}"
collect_process_list || echo -e "${RED}Error during process collection${RESET}"
collect_command_outputs || echo -e "${RED}Error during command output collection${RESET}"
collect_dbus_info || echo -e "${RED}Error during D-Bus info collection${RESET}"
create_readme || echo -e "${RED}Error creating README${RESET}"

# Create zip archive
echo -e "${BLUE}Creating zip archive at $OUTPUT_FILE...${RESET}"

# Simple and reliable zip method
current_dir=$(pwd)
cd "$TEMP_BASE_DIR" || exit 1
zip -r "$OUTPUT_FILE" "$(basename "$TEMP_DIR")" > /dev/null
zip_status=$?
cd "$current_dir" || exit 1

if [ $zip_status -ne 0 ]; then
    echo -e "${RED}Error creating zip file. Files remain in $TEMP_DIR${RESET}"
    echo -e "${RED}Please manually zip the directory and attach it to your issue.${RESET}"
    exit 1
fi

# Clean up temporary directory
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Done!${RESET}"
echo -e "Information collected and saved to: ${BOLD}$OUTPUT_FILE${RESET}"
echo -e "Please attach this file to your GitHub issue."
echo -e "Thank you for helping improve Toshy!"
