#!/usr/bin/env bash


# "Install" the bin commands as symlinks in user-local bin location.

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


TOSHY_CFG="$HOME/.config/toshy"
LOCAL_BIN="$HOME/.local/bin"

echo -e "\nInstalling Toshy bin commands..."

mkdir -p "$HOME/.local/bin"

ln -sf "$TOSHY_CFG/scripts/bin/toshy-systemd-setup.sh"         "$LOCAL_BIN/toshy-systemd-setup"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-systemd-remove.sh"        "$LOCAL_BIN/toshy-systemd-remove"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-services-status.sh"       "$LOCAL_BIN/toshy-services-status"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-services-restart.sh"      "$LOCAL_BIN/toshy-services-restart"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-services-start.sh"        "$LOCAL_BIN/toshy-services-start"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-services-stop.sh"         "$LOCAL_BIN/toshy-services-stop"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-services-log.sh"          "$LOCAL_BIN/toshy-services-log"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-config-start.sh"          "$LOCAL_BIN/toshy-config-start"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-config-start-verbose.sh"  "$LOCAL_BIN/toshy-config-start-verbose"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-config-restart.sh"        "$LOCAL_BIN/toshy-config-restart"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-config-stop.sh"           "$LOCAL_BIN/toshy-config-stop"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-tray.sh"                  "$LOCAL_BIN/toshy-tray"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-gui.sh"                   "$LOCAL_BIN/toshy-gui"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-env.sh"                   "$LOCAL_BIN/toshy-env"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-venv.sh"                  "$LOCAL_BIN/toshy-venv"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-devices.sh"               "$LOCAL_BIN/toshy-devices"
ln -sf "$TOSHY_CFG/scripts/bin/toshy-kde-dbus-service.sh"      "$LOCAL_BIN/toshy-kde-dbus-service"


echo ""
echo "Finished installing Toshy bin commands:"
echo ""
echo "- toshy-systemd-setup"
echo "- toshy-systemd-remove"
echo "- toshy-services-status"
echo "- toshy-services-restart"
echo "- toshy-services-start"
echo "- toshy-services-stop"
echo "- toshy-services-log"
echo "- toshy-config-start"
echo "- toshy-config-start-verbose"
echo "- toshy-config-restart"
echo "- toshy-config-stop"
echo "- toshy-tray"
echo "- toshy-gui"
echo "- toshy-env"
echo "- toshy-venv"
echo "- toshy-devices"
echo "- toshy-kde-dbus-service"
echo ""
echo "The commands may not be available until you close the current terminal, or "
echo "run 'hash -r', or source your shell RC file to refresh executable hash table."
echo ""


if [[ -n "$XDG_RUNTIME_DIR" ]]; then
    run_tmp_dir="$XDG_RUNTIME_DIR"
else
    run_tmp_dir="/tmp"
fi

path_good_tmp_file="toshy_installer_says_path_is_good"
path_good_tmp_path="$run_tmp_dir/$path_good_tmp_file"

if [ -f "$path_good_tmp_path" ]; then
    exit 0
fi

path_fix_tmp_file="toshy_installer_says_fix_path"
path_fix_tmp_path="$run_tmp_dir/$path_fix_tmp_file"

if [ -f "$path_fix_tmp_path" ]; then
    toshy_installer_says_fix_path=1
fi


# Check if ~/.local/bin is in the user's PATH
# shellcheck disable=SC2016
if ! echo "$PATH" | grep -q -E "(^|:)$HOME/.local/bin(:|$)" || [ -f "$path_fix_tmp_path" ]; then

    if [ ! "$toshy_installer_says_fix_path" -eq 1 ]; then

        echo -e "\nIt looks like '~/.local/bin' is not in your PATH."
        echo -e "To add it permanently, append the following line to your shell RC file:"

        case "$SHELL" in
            */bash)
                shell_rc="$HOME/.bashrc"
                echo 'export PATH="$HOME/.local/bin:$PATH"'
                ;;
            */zsh)
                shell_rc="$HOME/.zshrc"
                echo 'export PATH="$HOME/.local/bin:$PATH"'
                ;;
            */fish)
                shell_rc="$HOME/.config/fish/config.fish"
                echo 'set -U fish_user_paths $HOME/.local/bin $fish_user_paths'
                ;;
            *)
                echo "ALERT: Shell not recognized."
                echo "Please add the appropriate line to your shell's RC file yourself."
                shell_rc=""
                ;;
        esac

    fi

    if [[ -n "${shell_rc}" ]]; then

        if [[ "${SHELL}" == */fish ]]; then
            path_line='set -U fish_user_paths $HOME/.local/bin $fish_user_paths'
        else
            path_line='export PATH="$HOME/.local/bin:$PATH"'
        fi

        # Check if the line already exists in the RC file
        if grep -Fxq "$path_line" "${shell_rc}"
        then
            echo "The line is already in your $shell_rc file."
        else

            if [ "$toshy_installer_says_fix_path" -eq 1 ]; then
                echo -e "\nAppending the line to $shell_rc..."
                echo -e "\n$path_line" >> "${shell_rc}"
                echo -e "Done. Restart your shell or run 'source $shell_rc' to apply the changes."
                exit 0
            fi

            read -r -p "Do you want to append the line to your $shell_rc file now? [Y/n] " yn

            case $yn in
                [Nn]* )
                    echo -e "Skipping. Please add the line to your shell RC file manually."
                    ;;
                * )
                    echo -e "\nAppending the line to $shell_rc..."
                    echo -e "\n$path_line" >> "${shell_rc}"
                    echo -e "Done. Restart your shell or run 'source $shell_rc' to apply the changes."
                    ;;
            esac

        fi

    fi

fi
