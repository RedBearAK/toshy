#!/usr/bin/env bash


# Show the status of the Toshy systemd services (session monitor and config).

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


echo -e "\nCurrent status of Toshy systemd services..."
echo "--------------------------------------------------------------------------------"

/usr/bin/systemctl --user status toshy-session-monitor.service

echo "--------------------------------------------------------------------------------"

/usr/bin/systemctl --user status toshy-config.service

echo "--------------------------------------------------------------------------------"
echo -e "Use \"toshy-systemd-setup\" to install/reinstall Toshy services...\n\
Use \"toshy-systemd-remove\" to uninstall/remove Toshy services...\n"
