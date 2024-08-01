#!/usr/bin/env bash


# Show the journalctl output of the Toshy systemd services (session monitor and config).

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# # Check if $USER and $HOME environment variables are not empty
# if [[ -z $USER ]] || [[ -z $HOME ]]; then
#     echo "\$USER and/or \$HOME environment variables are not set. We need them."
#     exit 1
# fi


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


clean_exit() {
    echo "Caught Interrupt signal. Exiting..."
    # Add your clean-up commands here

    # Exit the script
    exit 0
}

# Trap the interrupt signal
trap 'clean_exit' SIGINT


echo "Showing systemd journal messages for Toshy services (since last boot):"


# Check if stdbuf is available and set the appropriate command
# Hopefully this may stop certain terminals from holding back journal
# output and showing new output in large bursts.
if command -v stdbuf >/dev/null 2>&1; then
    STDBUF_CMD="stdbuf -oL"
else
    STDBUF_CMD=""
fi

# -b flag to only show messages since last boot
# -f flag to follow new journal output
# -n100 to show the last 100 lines (max) of existing log output
# journalctl --user -n100 -b -f -u toshy-config -u toshy-session-monitor -u toshy-kde-dbus
# newer(?) syntax to do the same thing? 
${STDBUF_CMD} journalctl -n100 -b -f --user-unit 'toshy-*'
