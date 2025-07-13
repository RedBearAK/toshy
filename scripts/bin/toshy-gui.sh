#!/usr/bin/env bash


# Start Toshy GUI app after activating venv

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


# Set the process name for the Toshy Preferences GUI app launcher process
# echo "toshy-pref-stub" > /proc/$$/comm
# REMOVING: This seems to confuse systemd and cause error messages in the journal

# Absolute path to the venv
VENV_PATH="$HOME/.config/toshy/.venv"

# Verify the venv directory exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Activate the venv for complete environment setup (technically not needed for this app!)
# shellcheck disable=SC1091
source "${VENV_PATH}/bin/activate"

# Original exec command before modularising toshy_gui app package:
# exec "${VENV_PATH}/bin/python" "$HOME/.config/toshy/toshy_gui.py"

# Launch GUI app as a Python "module":
export PYTHONPATH="${HOME}/.config/toshy:${PYTHONPATH}"
exec "${VENV_PATH}/bin/python" -m toshy_gui "$@"
