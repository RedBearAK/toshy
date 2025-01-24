#!/usr/bin/env bash


# Stop the Toshy services. First session monitor so that it doesn't try 
# to restart the config service. Then stop config service. 

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


# This script is pointless if the system doesn't support "user" systemd services (e.g., CentOS 7)
if ! systemctl --user list-unit-files &>/dev/null; then
    echo "ERROR: Systemd user services are probably not supported here."
    echo
    exit 1
fi


echo "Stopping Toshy systemd services..."

systemctl --user stop toshy-cosmic-dbus.service
sleep 0.5
systemctl --user stop toshy-kde-dbus.service
sleep 0.5
systemctl --user stop toshy-wlroots-dbus.service
sleep 0.5
systemctl --user stop toshy-session-monitor.service
sleep 0.5
systemctl --user stop toshy-config.service

echo "Toshy systemd services stopped."
sleep 0.5
