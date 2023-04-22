#!/usr/bin/env bash


# Restart the Toshy services. First stop session monitor so that it doesn't 
# restart config, then restart config, then start session monitor

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


echo -e "\nRestarting Toshy systemd services..."

/usr/bin/systemctl --user stop toshy-session-monitor.service
sleep 0.5
/usr/bin/systemctl --user restart toshy-config.service
sleep 0.5
/usr/bin/systemctl --user start toshy-session-monitor.service

echo -e "\nToshy systemd services restarted.\n\nRemember to tap a modifier key before trying shortcuts!\n"
sleep 1
