#!/usr/bin/env bash


# Start Toshy Wlroots D-Bus service, after terminating existing
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

TOSHY_CFG="${HOME}/.config/toshy"
TOSHY_WLROOTS="${TOSHY_CFG}/wlroots-dbus-service"


pkill -f "toshy_wlroots_dbus_service"

sleep 1

# run the Python interpreter from within the virtual environment
# shellcheck disable=SC1091
source "${TOSHY_CFG}/.venv/bin/activate"

# start the script that will create the D-Bus object/interface
python3 "${TOSHY_WLROOTS}/toshy_wlr_forn_topl_mgmt_dbus_svc.py"
