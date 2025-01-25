#!/usr/bin/env bash


# Stop, disable, and remove the systemd service unit files

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


# This script is pointless if the system doesn't support "user" systemd services (e.g., CentOS 7)
if ! systemctl --user list-unit-files &>/dev/null; then
    echo "ERROR: Systemd user services are probably not supported here."
    echo
    exit 1
fi



LOCAL_BIN_PATH="$HOME/.local/bin"
USER_SYSD_PATH="$HOME/.config/systemd/user"
# TOSHY_CFG_PATH="$HOME/.config/toshy"
# SYSD_UNIT_PATH="$TOSHY_CFG_PATH/systemd-user-service-units"

DELAY=0.5

export PATH="$LOCAL_BIN_PATH:$PATH"

echo -e "\nRemoving Toshy systemd services...\n"

# systemctl "disable" automatically deletes all symlinks (might be bug)


service_names=(
    "toshy-cosmic-dbus.service"
    "toshy-kde-dbus.service"
    "toshy-wlroots-dbus.service"
    "toshy-config.service"
    "toshy-session-monitor.service"
)

for service_name in "${service_names[@]}"; do
    if [ -f "$USER_SYSD_PATH/$service_name" ]; then
        if systemctl --user --quiet is-active "$service_name"; then
            systemctl --user stop "$service_name"
        fi
        if systemctl --user --quiet is-enabled "$service_name"; then
            systemctl --user disable "$service_name"
        fi
        sleep "$DELAY"
        rm -f "$USER_SYSD_PATH/$service_name"
    fi
done

if [ -f "$HOME/.config/autostart/Toshy_Import_Vars.desktop" ]; then
    rm -f "$HOME/.config/autostart/Toshy_Import_Vars.desktop"
fi

sleep $DELAY

systemctl --user daemon-reload

echo -e "\nFinished removing Toshy systemd services.\n"
