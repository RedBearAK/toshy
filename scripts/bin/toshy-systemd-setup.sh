#!/usr/bin/env bash


# Set up the Toshy systemd services (session monitor and config).

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z $USER ]] || [[ -z $HOME ]]; then
    echo "\$USER and/or \$HOME environment variables are not set. We need them."
    exit 1
fi

# Get out of here if systemctl is not available
if command -v systemctl >/dev/null 2>&1; then
    # systemd is installed, proceed
    :
else
    # no systemd found, exit (but with message for this script)
    echo "There is no 'systemctl' on this system. Nothing to do."
    exit 0
fi


DELAY=0.5

echo -e "\nSetting up Toshy service unit files in $HOME/.config/systemd/user..."

mkdir -p "$HOME/.config/systemd/user"
mkdir -p "$HOME/.config/autostart"

# Stop, disable, and remove existing unit files
eval "$(which toshy-systemd-remove)"

cp -f "$HOME/.config/toshy/systemd-user-service-units/toshy-config.service" "$HOME/.config/systemd/user/"
cp -f "$HOME/.config/toshy/systemd-user-service-units/toshy-session-monitor.service" "$HOME/.config/systemd/user/"

cp -f "$HOME/.config/toshy/desktop/Toshy_Import_Vars.desktop" "$HOME/.config/autostart/"


sleep $DELAY

echo -e "\nIssuing systemctl daemon-reload..."

/usr/bin/systemctl --user daemon-reload

# Give systemd user services access to environment variables like:
# XDG_SESSION_TYPE XDG_SESSION_DESKTOP XDG_CURRENT_DESKTOP
/usr/bin/systemctl --user import-environment XDG_SESSION_TYPE XDG_SESSION_DESKTOP XDG_CURRENT_DESKTOP


sleep $DELAY

echo -e "\nStarting Toshy systemd services..."

/usr/bin/systemctl --user reenable toshy-config.service
# /usr/bin/systemctl --user enable toshy-config.service
/usr/bin/systemctl --user start toshy-config.service

sleep $DELAY

/usr/bin/systemctl --user reenable toshy-session-monitor.service
# /usr/bin/systemctl --user enable toshy-session-monitor.service
/usr/bin/systemctl --user start toshy-session-monitor.service

sleep $DELAY

export SYSTEMD_PAGER=""

echo -e "\nDisplaying status of Toshy systemd services...\n"

/usr/bin/systemctl --user status toshy-session-monitor.service
echo ""

sleep $DELAY

/usr/bin/systemctl --user status toshy-config.service

sleep $DELAY

echo -e "\nFinished installing Toshy systemd services..."
echo -e "\nHINT: Tap any modifier key once before trying shortcuts.\n"
