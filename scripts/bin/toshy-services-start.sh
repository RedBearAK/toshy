#!/usr/bin/env bash


# Start the config service, then the session monitor service

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


echo -e "\nStarting Toshy systemd services..."

systemctl --user start toshy-cosmic-dbus.service
sleep 0.5
systemctl --user start toshy-kde-dbus.service
sleep 0.5
systemctl --user start toshy-wlroots-dbus.service
sleep 0.5
systemctl --user start toshy-config.service
sleep 0.5
systemctl --user start toshy-session-monitor.service

echo -e "\nToshy systemd services started.\n\nRemember to tap a modifier key before trying shortcuts!\n"
sleep 1
