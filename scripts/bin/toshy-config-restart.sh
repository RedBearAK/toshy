#!/bin/env bash


# Restart the Toshy manual script

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


"$HOME/.local/bin/toshy-config-stop"

sleep 0.5

nohup "$HOME/.local/bin/toshy-config-start" &
