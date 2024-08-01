#!/usr/bin/env bash


# Show the status of the Toshy systemd services (session monitor and config).

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


export SYSTEMD_PAGER=""

echo -e "\nCurrent status of Toshy systemd services..."
echo "--------------------------------------------------------------------------------"

systemctl --user status toshy-cosmic-dbus.service

echo "--------------------------------------------------------------------------------"

systemctl --user status toshy-kde-dbus.service

echo "--------------------------------------------------------------------------------"

systemctl --user status toshy-wlroots-dbus.service

echo "--------------------------------------------------------------------------------"

systemctl --user status toshy-session-monitor.service

echo "--------------------------------------------------------------------------------"

systemctl --user status toshy-config.service

echo "--------------------------------------------------------------------------------"

cat <<EOF
Use 'toshy-services-disable' to disable Toshy services autostart at login.
Use 'toshy-services-enable' to (re)enable Toshy services autostart at login.
Use 'toshy-systemd-remove' to uninstall/remove Toshy services.
Use 'toshy-systemd-setup' to install/reinstall Toshy services.

EOF
