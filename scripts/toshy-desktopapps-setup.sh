#!/usr/bin/env bash


# "Install" the Toshy dekstop entry files so that app launchers and menus can 
# "see" them and launch them.

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

LOCAL_SHARE="$HOME/.local/share"
TOSHY_CFG="$HOME/.config/toshy"


echo -e "\nInstalling Toshy Preferences and Tray Icon app launchers..."

mkdir -p "$LOCAL_SHARE/applications"
mkdir -p "$LOCAL_SHARE/icons"

cp -f "$TOSHY_CFG/desktop/Toshy_GUI.desktop"            "$LOCAL_SHARE/applications"
cp -f "$TOSHY_CFG/desktop/Toshy_Tray.desktop"           "$LOCAL_SHARE/applications"
cp -f "$TOSHY_CFG/assets/toshy_app_icon_rainbow.svg"    "$LOCAL_SHARE/icons"


echo -e "\nFinished installing Toshy Preferences and Tray Icon app launchers:"
echo ""
echo "- Toshy Preferences"
echo "- Toshy Tray Icon"
echo ""
echo "The applications should appear quickly in most app launchers."
echo ""
