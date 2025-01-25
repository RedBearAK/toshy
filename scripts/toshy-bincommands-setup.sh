#!/usr/bin/env bash


# "Install" the bin commands as symlinks in user-local bin location.

# Check if the script is being run as root
if [[ ${EUID} -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z ${USER} ]] || [[ -z ${HOME} ]]; then
    echo "\$USER and/or \$HOME environment variables are not set. We need them."
    exit 1
fi


TOSHY_BIN="${HOME}/.config/toshy/scripts/bin"
LOCAL_BIN="${HOME}/.local/bin"

echo -e "\nInstalling Toshy terminal commands..."

mkdir -p "${LOCAL_BIN}"

ln -sf "${TOSHY_BIN}/toshy-systemd-setup.sh"            "${LOCAL_BIN}/toshy-systemd-setup"
ln -sf "${TOSHY_BIN}/toshy-systemd-remove.sh"           "${LOCAL_BIN}/toshy-systemd-remove"
ln -sf "${TOSHY_BIN}/toshy-services-status.sh"          "${LOCAL_BIN}/toshy-services-status"
ln -sf "${TOSHY_BIN}/toshy-services-disable.sh"         "${LOCAL_BIN}/toshy-services-disable"
ln -sf "${TOSHY_BIN}/toshy-services-enable.sh"          "${LOCAL_BIN}/toshy-services-enable"
ln -sf "${TOSHY_BIN}/toshy-services-restart.sh"         "${LOCAL_BIN}/toshy-services-restart"
ln -sf "${TOSHY_BIN}/toshy-services-start.sh"           "${LOCAL_BIN}/toshy-services-start"
ln -sf "${TOSHY_BIN}/toshy-services-stop.sh"            "${LOCAL_BIN}/toshy-services-stop"
ln -sf "${TOSHY_BIN}/toshy-services-log.sh"             "${LOCAL_BIN}/toshy-services-log"
ln -sf "${TOSHY_BIN}/toshy-config-start.sh"             "${LOCAL_BIN}/toshy-config-start"
ln -sf "${TOSHY_BIN}/toshy-config-stop.sh"              "${LOCAL_BIN}/toshy-config-stop"
ln -sf "${TOSHY_BIN}/toshy-config-restart.sh"           "${LOCAL_BIN}/toshy-config-restart"
ln -sf "${TOSHY_BIN}/toshy-config-start-verbose.sh"     "${LOCAL_BIN}/toshy-config-start-verbose"
ln -sf "${TOSHY_BIN}/toshy-config-start-verbose.sh"     "${LOCAL_BIN}/toshy-config-verbose-start"
ln -sf "${TOSHY_BIN}/toshy-config-start-verbose.sh"     "${LOCAL_BIN}/toshy-debug"
ln -sf "${TOSHY_BIN}/toshy-tray.sh"                     "${LOCAL_BIN}/toshy-tray"
ln -sf "${TOSHY_BIN}/toshy-gui.sh"                      "${LOCAL_BIN}/toshy-gui"
ln -sf "${TOSHY_BIN}/toshy-env.sh"                      "${LOCAL_BIN}/toshy-env"
ln -sf "${TOSHY_BIN}/toshy-venv.sh"                     "${LOCAL_BIN}/toshy-venv"
ln -sf "${TOSHY_BIN}/toshy-fnmode.sh"                   "${LOCAL_BIN}/toshy-fnmode"
ln -sf "${TOSHY_BIN}/toshy-devices.sh"                  "${LOCAL_BIN}/toshy-devices"
ln -sf "${TOSHY_BIN}/toshy-versions.sh"                 "${LOCAL_BIN}/toshy-versions"
ln -sf "${TOSHY_BIN}/toshy-machine-id.sh"               "${LOCAL_BIN}/toshy-machine-id"
ln -sf "${TOSHY_BIN}/toshy-kde-dbus-service.sh"         "${LOCAL_BIN}/toshy-kde-dbus-service"
ln -sf "${TOSHY_BIN}/toshy-cosmic-dbus-service.sh"      "${LOCAL_BIN}/toshy-cosmic-dbus-service"
ln -sf "${TOSHY_BIN}/toshy-wlroots-dbus-service.sh"     "${LOCAL_BIN}/toshy-wlroots-dbus-service"


echo ""
echo "Finished installing Toshy terminal commands:"
echo ""
echo "- toshy-systemd-setup"
echo "- toshy-systemd-remove"
echo "- toshy-services-status"
echo "- toshy-services-disable"
echo "- toshy-services-enable"
echo "- toshy-services-restart"
echo "- toshy-services-start"
echo "- toshy-services-stop"
echo "- toshy-services-log"
echo "- toshy-config-start"
echo "- toshy-config-stop"
echo "- toshy-config-restart"
echo "- toshy-config-start-verbose"
echo "- toshy-config-verbose-start"
echo "- toshy-config-debug"
echo "- toshy-tray"
echo "- toshy-gui"
echo "- toshy-env"
echo "- toshy-venv"
echo "- toshy-fnmode"
echo "- toshy-devices"
echo "- toshy-versions"
echo "- toshy-machine-id"
echo "- toshy-kde-dbus-service"
echo "- toshy-cosmic-dbus-service"
echo "- toshy-wlroots-dbus-service"
echo ""
echo "The commands may not be available until you close the current terminal, or "
echo "run 'hash -r', or source your shell RC file to refresh executable hash table."
echo ""


PROFILE="${HOME}/.profile"
LOCAL_BIN="${HOME}/.local/bin"
PATH_LINE="PATH=\"\${HOME}/.local/bin:\${PATH}\""
RUN_TMP_DIR="${XDG_RUNTIME_DIR:-/tmp}"
GOOD_PATH_TMP="${RUN_TMP_DIR}/toshy_installer_says_path_is_good"
FIX_PATH_TMP="${RUN_TMP_DIR}/toshy_installer_says_fix_path"

[ -f "${GOOD_PATH_TMP}" ] && exit 0

mkdir -p "${LOCAL_BIN}"
[ ! -f "${PROFILE}" ] && touch "${PROFILE}"

path_contains_local_bin() {
    grep -q "PATH=.*\${HOME}/.local/bin" "${PROFILE}" || \
    grep -q "PATH=.*${LOCAL_BIN}" "${PROFILE}"
}

check_rc_files() {
    local rc_files=(".bashrc" ".zshrc" ".config/fish/config.fish")
    for rc in "${rc_files[@]}"; do
        if [ -f "${HOME}/${rc}" ] && grep -q "PATH.*/.local/bin" "${HOME}/${rc}"; then
            echo "Note: Found ~/.local/bin PATH modification in ~/${rc}"
            echo "      Consider removing it to avoid duplicate PATH entries"
        fi
    done
}

if ! path_contains_local_bin; then
    if [ -f "${FIX_PATH_TMP}" ]; then
        response="y"
    else
        read -r -p "Add ~/.local/bin to PATH in ~/.profile? [Y/n] " response
    fi
    
    case $response in
        [Nn]* ) 
            echo "Skipped modifying ~/.profile"
            exit 0
            ;;
    esac

    {
        echo -e "\n# Add ~/.local/bin to PATH if not already present"
        echo "if [ -d \"\${HOME}/.local/bin\" ] && [[ \":\${PATH}:\" != *\":\${HOME}/.local/bin:\"* ]]; then"
        echo "    ${PATH_LINE}"
        echo "fi"
    } >> "${PROFILE}"
    echo "Added PATH modification to ~/.profile"
fi

check_rc_files

exit 0


# Previous code that tried to update shell RC files: 


# if [[ -n "${XDG_RUNTIME_DIR}" ]]; then
#     run_tmp_dir="${XDG_RUNTIME_DIR}"
# else
#     run_tmp_dir="/tmp"
# fi

# path_line=""
# shell_rc=""

# path_good_tmp_file="toshy_installer_says_path_is_good"
# path_good_tmp_path="${run_tmp_dir}/${path_good_tmp_file}"

# # echo "path_good_tmp_path: $path_good_tmp_path"

# if [ -f "$path_good_tmp_path" ]; then
#     exit 0
# fi

# path_fix_tmp_file="toshy_installer_says_fix_path"
# path_fix_tmp_path="${run_tmp_dir}/${path_fix_tmp_file}"

# # echo "path_fix_tmp_path: $path_fix_tmp_path"

# toshy_installer_says_fix_path=0
# if [ -f "$path_fix_tmp_path" ]; then
#     toshy_installer_says_fix_path=1
# fi


# case "${SHELL}" in
#     */bash)
#         shell_rc="${HOME}/.bashrc"
#         path_line="export PATH=\"${LOCAL_BIN}:\$PATH\""
#         ;;
#     */zsh)
#         shell_rc="${HOME}/.zshrc"
#         path_line="export PATH=\"${LOCAL_BIN}:\$PATH\""
#         ;;
#     */fish)
#         shell_rc="${HOME}/.config/fish/config.fish"
#         path_line="set -U fish_user_paths ${LOCAL_BIN} \$fish_user_paths"
#         ;;
#     *)
#         shell_rc=""
#         path_line=""
#         ;;
# esac


# if [[ ${toshy_installer_says_fix_path} -eq 1 ]]; then

#     if [[ -n "${shell_rc}" ]]; then
#         echo -e "\nFixing path because Toshy installer said so..."
#         echo -e "Appending the export path line to '${shell_rc}'..."
#         echo -e "\n${path_line}\n" >> "${shell_rc}"
#         echo -e "Done. Restart your shell or run 'source ${shell_rc}' to apply the changes."
#         exit 0
#     else
#         echo -e "\nALERT: Toshy Installer said to fix path but shell not recognized."
#         echo "Please add the appropriate line to your shell's RC file yourself."
#         exit 0
#     fi

# fi


# # Check if ~/.local/bin is in the user's PATH
# if ! echo "${PATH}" | grep -q -E "(^|:)${LOCAL_BIN}(:|$)"; then
#     echo -e "\nIt looks like '${LOCAL_BIN}' is not in your PATH."
#     echo -e "To add it permanently, append the following line to your shell RC file:"

#     case "${SHELL}" in
#         */bash)
#             echo "export PATH=\"${LOCAL_BIN}:\$PATH\""
#             ;;
#         */zsh)
#             echo "export PATH=\"${LOCAL_BIN}:\$PATH\""
#             ;;
#         */fish)
#             echo "set -U fish_user_paths ${LOCAL_BIN} \$fish_user_paths"
#             ;;
#         *)
#             echo "ALERT: Shell not recognized."
#             echo "Please add the appropriate line to your shell's RC file yourself."
#             ;;
#     esac

#     if [[ -n "${shell_rc}" ]]; then

#         # Check if the line already exists in the RC file
#         if grep -Fxq "${path_line}" "${shell_rc}"; then
#             echo "The line is already in your $shell_rc file."
#         else
#             read -r -p "Do you want to append the line to your ${shell_rc} file now? [Y/n] " yn
#             case $yn in
#                 [Nn]* )
#                     echo -e "Skipping. Please add the line to your shell RC file manually."
#                     ;;
#                 * )
#                     echo -e "\nAppending the line to ${shell_rc}..."
#                     echo -e "\n${path_line}\n" >> "${shell_rc}"
#                     echo -e "Done. Restart your shell or run 'source ${shell_rc}' to apply the changes."
#                     ;;
#             esac
#         fi

#     fi

# fi
