#!/usr/bin/env bash


# Start the Toshy manual script, with verbose output

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

"$HOME/.local/bin/toshy-services-stop"

pkill -f "bin/keyszer"
# systemctl stop xkeysnail.service
pkill -f "bin/xkeysnail"

# start KDE D-Bus service in case we are in Wayland+KDE (it will stop itself if not)
nohup "${HOME}/.local/bin/toshy-kde-dbus-service" >/dev/null 2>&1 &

# shellcheck disable=SC1091
source "$HOME/.config/toshy/.venv/bin/activate"

# Start keyszer with verbose flag [-v] and anti-buffering flag [--flush]
keyszer --flush -w -v -c "$HOME/.config/toshy/toshy_config.py"
