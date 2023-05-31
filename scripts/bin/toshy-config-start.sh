#!/usr/bin/env bash


# Start the Toshy manual script

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

# shellcheck disable=SC1091
source "$HOME/.config/toshy/.venv/bin/activate"

keyszer -w -c "$HOME/.config/toshy/toshy_config.py"
