#!/usr/bin/env bash


# Restart the Toshy services. First stop session monitor so that it doesn't 
# restart config, then restart config, then start session monitor

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

show_progress() {
    echo -n "  ."
}

echo -e "\nRestarting Toshy systemd services..."

systemctl --user stop toshy-cosmic-dbus.service
show_progress
systemctl --user stop toshy-kwin-dbus.service
show_progress
systemctl --user stop toshy-wlroots-dbus.service
show_progress

sleep 0.1

systemctl --user start toshy-cosmic-dbus.service
show_progress
systemctl --user start toshy-kwin-dbus.service
show_progress
systemctl --user start toshy-wlroots-dbus.service
show_progress

sleep 0.1

systemctl --user stop toshy-session-monitor.service
show_progress

sleep 0.1

systemctl --user stop toshy-config.service
show_progress

sleep 0.3

systemctl --user start toshy-config.service
show_progress

sleep 0.1

systemctl --user start toshy-session-monitor.service
show_progress

# The keymapper's problem with ignoring the first modifier key press after startup
# was fixed in 'xwaykeyz' 1.5.4, so we don't need to have these reminders anymore!
# echo -e "\nToshy systemd services restarted.\n\nRemember to tap a modifier key before trying shortcuts!\n"
echo -e "  done.\nToshy systemd services restarted.\n"
sleep 0.1
