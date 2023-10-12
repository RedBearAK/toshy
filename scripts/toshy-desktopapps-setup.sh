#!/usr/bin/env bash


# "Install" the Toshy desktop entry files and icon files, so that app launchers, 
# notification dialogs and menus can "see" them and use them.


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
TOSHY_CFG_DIR="${HOME}/.config/toshy"


echo -e "\nInstalling Toshy Preferences and Tray Icon app launchers..."

mkdir -p "${LOCAL_SHARE}/applications" || \
    exit_w_error "Failed to create \"${LOCAL_SHARE}/applications\" folder."

mkdir -p "${LOCAL_SHARE}/icons" || \
    exit_w_error "Failed to create \"${LOCAL_SHARE}/icons\" folder."

cp -f "${TOSHY_CFG_DIR}/desktop/Toshy_GUI.desktop"          "${LOCAL_SHARE}/applications" || \
    exit_w_error "Problem copying Toshy_GUI.desktop file."

cp -f "${TOSHY_CFG_DIR}/desktop/Toshy_Tray.desktop"         "${LOCAL_SHARE}/applications" || \
    exit_w_error "Problem copying Toshy_Tray.desktop file."

cp -f "${TOSHY_CFG_DIR}/assets/toshy_app_icon_*.svg"        "${LOCAL_SHARE}/icons" || \
    exit_w_error "Problem copying Toshy icon files."


echo -e "\nFinished installing Toshy Preferences and Tray Icon app launchers:"
echo ""
echo "- Toshy Preferences"
echo "- Toshy Tray Icon"
echo ""
echo "The applications should appear quickly in most app launchers."
echo ""
