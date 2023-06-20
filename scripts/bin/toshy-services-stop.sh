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


echo -e "\nStopping Toshy systemd services..."

/usr/bin/systemctl --user stop toshy-kde-dbus.service
sleep 0.5
/usr/bin/systemctl --user stop toshy-session-monitor.service
sleep 0.5
/usr/bin/systemctl --user stop toshy-config.service

echo -e "\nToshy systemd services stopped.\n"
sleep 0.5
