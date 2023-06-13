#!/usr/bin/env bash

# Script to create a KWin event that will get the KWin script to start working

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# # Check if $USER and $HOME environment variables are not empty
# if [[ -z $USER ]] || [[ -z $HOME ]]; then
#     echo "\$USER and/or \$HOME environment variables are not set. We need them."
#     exit 1
# fi

sleep 1

message="Kickstarting the Toshy KWin script..."
timeout_s=2


if command -v zenity &> /dev/null; then
    zenity --info --text="${message}" --timeout=${timeout_s} >/dev/null 2>&1
elif command -v xmessage &> /dev/null; then
    xmessage "${message}" -timeout ${timeout_s} >/dev/null 2>&1
else
    echo "ERROR: The 'zenity' and 'xmessage' commands are not available."
    echo "ERROR: Toshy cannot kickstart the KWin script."
fi
