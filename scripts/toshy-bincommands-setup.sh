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

echo -e "\nInstalling Toshy bin commands..."

mkdir -p "$HOME/.local/bin"

ln -sf "$HOME/.config/toshy/scripts/bin/toshy-systemd-setup.sh" "$HOME/.local/bin/toshy-systemd-setup"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-systemd-remove.sh" "$HOME/.local/bin/toshy-systemd-remove"

ln -sf "$HOME/.config/toshy/scripts/bin/toshy-services-status.sh" "$HOME/.local/bin/toshy-services-status"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-services-restart.sh" "$HOME/.local/bin/toshy-services-restart"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-services-start.sh" "$HOME/.local/bin/toshy-services-start"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-services-stop.sh" "$HOME/.local/bin/toshy-services-stop"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-services-log.sh" "$HOME/.local/bin/toshy-services-log"

ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-start.sh" "$HOME/.local/bin/toshy-config-start"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-start-verbose.sh" "$HOME/.local/bin/toshy-config-start-verbose"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-restart.sh" "$HOME/.local/bin/toshy-config-restart"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-stop.sh" "$HOME/.local/bin/toshy-config-stop"

ln -sf "$HOME/.config/toshy/scripts/bin/toshy-tray.sh" "$HOME/.local/bin/toshy-tray"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-gui.sh" "$HOME/.local/bin/toshy-gui"


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
echo ""
echo "The commands will not be available until you close the current terminal, or "
echo "run 'hash -r', or source your shell RC file to refresh executable hash table."
echo ""


# Check if ~/.local/bin is in the user's PATH
if ! echo "$PATH" | grep -q -E "(^|:)$HOME/.local/bin(:|$)"; then
    echo -e "\nIt looks like ~/.local/bin is not in your PATH. To add it permanently, append the following line to your shell RC file:"

    # shellcheck disable=SC2016
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

    if [[ -n "$shell_rc" ]]; then
        read -r -p "Do you want to append the line to your $shell_rc file now? [Y/n] " yn

        # shellcheck disable=SC2016
        case $yn in
            [Nn]* )
                echo -e "Skipping. Please add the line to your shell RC file manually."
                ;;
            * )
                echo -e "\nAppending the line to $shell_rc..."
                if [[ "$SHELL" == */fish ]]; then
                    echo 'set -U fish_user_paths $HOME/.local/bin $fish_user_paths' >> "$shell_rc"
                else
                    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$shell_rc"
                fi
                echo -e "Done. Restart your shell or run 'source $shell_rc' to apply the changes."
                ;;
        esac
    fi

fi
