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

ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-restart.sh" "$HOME/.local/bin/toshy-config-restart"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-start.sh" "$HOME/.local/bin/toshy-config-start"
ln -sf "$HOME/.config/toshy/scripts/bin/toshy-config-stop.sh" "$HOME/.local/bin/toshy-config-stop"


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
echo "- toshy-config-restart"
echo "- toshy-config-start"
echo "- toshy-config-stop"
echo ""
echo "The commands will not be available until you close the current terminal, or "
echo "run 'hash -r', or source your shell RC file to refresh executable hash table."
echo ""
