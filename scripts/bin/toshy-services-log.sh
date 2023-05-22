#!/usr/bin/env bash


# Show the journalctl output of the Toshy systemd services (session monitor and config).

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


echo "Showing systemd journal messages for Toshy services (since last boot):"

# -b flag to only show messages since last boot
/usr/bin/journalctl --user -n300 -b -f -u toshy-config -u toshy-session-monitor
