#!/usr/bin/env bash


# Start Toshy KDE D-Bus service, after terminating existing
# processes and activating Python virtual environment

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

TOSHY_CFG="$HOME/.config/toshy"


pkill -f "toshy_kde_dbus_service"

sleep 1

# start the kickstart script to get KWin to give immediate update on focused window
"${TOSHY_CFG}/scripts/toshy-kwin-script-kickstart.sh" &

# shellcheck disable=SC1091
source "$TOSHY_CFG/.venv/bin/activate"

# run the Python interpreter from within the virtual environment
# and make sure it stays running when terminal is closed
nohup python3 "$TOSHY_CFG/kde-kwin-dbus-service/toshy_kde_dbus_service.py" >/dev/null 2>&1 &
