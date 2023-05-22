#!/usr/bin/env bash


# Start the config service, then the session monitor service

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


echo -e "\nStarting Toshy systemd services..."

/usr/bin/systemctl --user start toshy-config.service
sleep 0.5
/usr/bin/systemctl --user start toshy-session-monitor.service

echo -e "\nToshy systemd services started.\n\nRemember to tap a modifier key before trying shortcuts!\n"
sleep 1
