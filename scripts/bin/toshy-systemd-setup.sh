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

LOCAL_BIN_PATH="$HOME/.local/bin"
USER_SYSD_PATH="$HOME/.config/systemd/user"
TOSHY_CFG_PATH="$HOME/.config/toshy"
SYSD_UNIT_PATH="$TOSHY_CFG_PATH/systemd-user-service-units"

DELAY=0.5

export PATH="$LOCAL_BIN_PATH:$PATH"

echo -e "\nSetting up Toshy service unit files in $USER_SYSD_PATH..."

mkdir -p "$USER_SYSD_PATH"
mkdir -p "$HOME/.config/autostart"

# Stop, disable, and remove existing unit files
eval "$LOCAL_BIN_PATH/toshy-systemd-remove"

cp -f "$SYSD_UNIT_PATH/toshy-kde-dbus.service"              "$USER_SYSD_PATH/"
cp -f "$SYSD_UNIT_PATH/toshy-config.service"                "$USER_SYSD_PATH/"
cp -f "$SYSD_UNIT_PATH/toshy-session-monitor.service"       "$USER_SYSD_PATH/"

cp -f "$TOSHY_CFG_PATH/desktop/Toshy_Import_Vars.desktop"   "$HOME/.config/autostart/"


sleep $DELAY

# Give systemd user services access to environment variables like:
# XDG_SESSION_TYPE XDG_SESSION_DESKTOP XDG_CURRENT_DESKTOP
# Do this BEFORE daemon-reload? Maybe not necessary. 
# But silence errors (e.g., "XDG_SESSION_DESKTOP not set, ignoring")
vars_to_import="XDG_SESSION_TYPE XDG_SESSION_DESKTOP XDG_CURRENT_DESKTOP"
# shellcheck disable=SC2086
/usr/bin/systemctl --user import-environment $vars_to_import >/dev/null 2>&1

echo -e "\nIssuing systemctl daemon-reload..."

/usr/bin/systemctl --user daemon-reload

sleep $DELAY

echo -e "\nStarting Toshy systemd services..."

service_names=(
    "toshy-kde-dbus.service"
    "toshy-config.service"
    "toshy-session-monitor.service"
)

for service_name in "${service_names[@]}"; do
    /usr/bin/systemctl --user reenable "$service_name"
    /usr/bin/systemctl --user start "$service_name"
    sleep "$DELAY"
done

# /usr/bin/systemctl --user reenable toshy-kde-dbus.service
# /usr/bin/systemctl --user start toshy-kde-dbus.service

# sleep $DELAY

# /usr/bin/systemctl --user reenable toshy-config.service
# /usr/bin/systemctl --user start toshy-config.service

# sleep $DELAY

# /usr/bin/systemctl --user reenable toshy-session-monitor.service
# /usr/bin/systemctl --user start toshy-session-monitor.service

# sleep $DELAY

export SYSTEMD_PAGER=""

echo -e "\nDisplaying status of Toshy systemd services...\n"

/usr/bin/systemctl --user status toshy-session-monitor.service
echo ""

sleep $DELAY

/usr/bin/systemctl --user status toshy-config.service

sleep $DELAY

echo -e "\nFinished installing Toshy systemd services..."
echo -e "\nHINT: Tap any modifier key once before trying shortcuts.\n"
