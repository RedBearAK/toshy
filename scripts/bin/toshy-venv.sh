#!/usr/bin/env bash

# Tell the user how to activate the Toshy Python virtual environment

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    return 1  # Use return instead of exit when script is sourced
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z $USER ]] || [[ -z $HOME ]]; then
    echo "\$USER and/or \$HOME environment variables are not set. We need them."
    return 1  # Use return instead of exit when script is sourced
fi

if [[ -z "$VIRTUAL_ENV" ]]; then
    # If the VIRTUAL_ENV variable is empty, the virtual environment is not active.
    echo -e "\n To activate the Toshy Python virtual environment, run this command: \n"
    echo -e "\t\t\t source toshy-venv \n"
    echo -e " (Ignore the text above if you've already run the command as shown.) \n"
else
    # If the VIRTUAL_ENV variable is not empty, the virtual environment is active.
    echo -e "\n The Toshy Python virtual environment is ACTIVE in this shell already.\n"
    return 0
fi

# Absolute path to the venv
VENV_PATH="$HOME/.config/toshy/.venv"

# Verify the venv directory exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Activate the venv for complete environment setup
# shellcheck disable=SC1091
source "${VENV_PATH}/bin/activate"
