#!/usr/bin/env bash


# Remove the Toshy desktop entry files and icon files


exit_w_error() {
    local msg="$1"
    echo -e "\nERROR: ${msg} Exiting...\n"
    exit 1
}


# Check if the script is being run as root
if [[ ${EUID} -eq 0 ]]; then
    exit_w_error "This script must not be run as root"
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z ${USER} ]] || [[ -z ${HOME} ]]; then
    exit_w_error "\$USER and/or \$HOME environment variables are not set. We need them."
fi


LOCAL_SHARE="${HOME}/.local/share"


echo -e "\nRemoving Toshy Preferences and Tray Icon app launchers..."

rm -f "${LOCAL_SHARE}/applications/Toshy_GUI.desktop" || \
    exit_w_error "Problem while removing the Toshy_GUI.desktop file."

rm -f "${LOCAL_SHARE}/applications/Toshy_Tray.desktop" || \
    exit_w_error "Problem while removing the Toshy_Tray.desktop file."

rm -f "${LOCAL_SHARE}/icons/toshy_app_icon_*.svg" || \
    exit_w_error "Problem while removing the Toshy icon files."

echo ""
echo "Finished removing Toshy Preferences and Tray Icon app launchers:"
echo ""
echo "- Toshy_GUI.desktop"
echo "- Toshy_Tray.desktop"
echo ""
