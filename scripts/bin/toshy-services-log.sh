#!/usr/bin/env bash

# Show the journalctl output of the Toshy systemd services (session monitor and config).

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if systemd is actually the init system
if [[ $(ps -p 1 -o comm=) == "systemd" ]]; then
    # systemd is the init system, proceed
    :
else
    # systemd is NOT the init system, exit with message
    echo "Init system is not 'systemd'..."
    exit 0
fi

# Get out of here if systemctl is not available
if command -v systemctl >/dev/null 2>&1; then
    # systemctl is installed, proceed
    :
else
    # no systemctl found, exit silently
    exit 0
fi

# Use the XDG_RUNTIME_DIR if available, otherwise fall back to /tmp
if [ -n "$XDG_RUNTIME_DIR" ] && [ -d "$XDG_RUNTIME_DIR" ]; then
    RUNTIME_DIR="$XDG_RUNTIME_DIR"
else
    RUNTIME_DIR="/tmp"
fi

# Create a toshy-specific directory in the runtime directory
TEMP_DIR="$RUNTIME_DIR/toshy-logs"
mkdir -p "$TEMP_DIR"
TEMP_SYMLINK="$TEMP_DIR/toshy-svcs-log"

clean_exit() {
    echo "Caught Interrupt signal. Exiting..."
    # Clean up our temporary files
    rm -rf "$TEMP_DIR"
    # Exit the script
    exit 0
}

# Trap the interrupt signal
trap 'clean_exit' SIGINT

echo "Showing systemd journal messages for Toshy services (since last boot):"

# First get all the Toshy service names into an array
if systemctl --user list-unit-files &>/dev/null; then
    mapfile -t toshy_services < <(
        systemctl --user list-unit-files |
        grep -i toshy |
        grep -v generated |
        awk '{print $1}'
    )
else
    # Handle systems without user service support (e.g., CentOS 7)
    echo "ERROR: Systemd user services are probably not supported here."
    echo
    exit 1
fi

# Check if any services were found
if [ ${#toshy_services[@]} -eq 0 ]; then
    echo "No Toshy services found. Exiting."
    exit 0
fi

# Check if stdbuf is available
USE_STDBUF=0
if command -v stdbuf >/dev/null 2>&1; then
    USE_STDBUF=1
fi

# Prepare the command arguments
ARGS=(-n200 -b -f)

# Add each service to the arguments
for service in "${toshy_services[@]}"; do
    ARGS+=(--user-unit "$service")
done

# Create the appropriate symlink based on whether stdbuf is used
if [ $USE_STDBUF -eq 1 ]; then
    # Create a special wrapper script that calls stdbuf with journalctl
    cat > "$TEMP_SYMLINK" << 'EOF'
#!/bin/sh
exec stdbuf -oL journalctl "$@"
EOF
    chmod +x "$TEMP_SYMLINK"
else
    # Create a symlink to journalctl with our custom name
    JOURNALCTL_PATH=$(command -v journalctl)
    ln -sf "$JOURNALCTL_PATH" "$TEMP_SYMLINK"
fi

# Execute the command through our renamed symlink or wrapper
# The PATH manipulation ensures our renamed command is found first
PATH="$TEMP_DIR:$PATH" exec toshy-svcs-log "${ARGS[@]}"
