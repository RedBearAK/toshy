#!/usr/bin/env bash


# Remove the Toshy desktop entry files and icon files


exit_w_error() {
    local msg="$1"
    echo -e "\n(EE) ERROR: ${msg} Exiting...\n"
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

# Target locations
LOCAL_SHARE="${HOME}/.local/share"
LOCAL_SHARE_APPS="${LOCAL_SHARE}/applications"
LOCAL_SHARE_ICONS="${LOCAL_SHARE}/icons/hicolor/scalable/apps"
LOCAL_SHARE_ICONS_OLD="${LOCAL_SHARE}/icons"

echo -e "\nRemoving Toshy Preferences and Tray Icon app launchers..."

# Desktop files to remove
desktop_files=(
    "Toshy_GUI.desktop"                # Old DEPRECATED GUI desktop file name, remove if present
    "app.toshy.preferences.desktop"    # New (matches app_id, makes GUI app icon work in Plasma)
    "Toshy_Tray.desktop"
)

# Icon files to remove
icon_files=(
    "toshy_app_icon_rainbow_inverse_grayscale.svg"
    "toshy_app_icon_rainbow_inverse.svg"
    "toshy_app_icon_rainbow.svg"
)


# Remove desktop files
for file in "${desktop_files[@]}"; do

    err_msg_removing_desktop_file="Problem while removing the ${file} file."
    rm -f "${LOCAL_SHARE_APPS}/${file}" || exit_w_error "$err_msg_removing_desktop_file"

done


# Remove icon files from new location (hicolor theme)
for file in "${icon_files[@]}"; do

    err_msg_removing_hicolor_icon_file="Problem removing ${file} from hicolor theme location."
    rm -f "${LOCAL_SHARE_ICONS}/${file}" || exit_w_error "$err_msg_removing_hicolor_icon_file"

done


# Remove icon files from old location (legacy)
for file in "${icon_files[@]}"; do

    err_msg_removing_legacy_icon_file="Problem removing ${file} from legacy location."
    rm -f "${LOCAL_SHARE_ICONS_OLD}/${file}" || exit_w_error "$err_msg_removing_legacy_icon_file"

done


echo ""
echo "Finished removing Toshy Preferences and Tray Icon app launchers."
echo ""
