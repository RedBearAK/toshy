#!/usr/bin/env bash


# Remove the Toshy bin command symlinks from user-local bin location.

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

LOCAL_BIN="${HOME}/.local/bin"


echo -e "\nRemoving Toshy terminal commands..."

/usr/bin/rm -f "${LOCAL_BIN}/toshy-systemd-setup"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-systemd-remove"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-services-status"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-services-restart"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-services-start"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-services-stop"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-services-log"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-config-start"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-config-start-verbose"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-config-verbose-start"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-config-restart"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-config-stop"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-tray"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-gui"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-env"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-venv"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-fnmode"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-devices"
/usr/bin/rm -f "${LOCAL_BIN}/toshy-kde-dbus-service"


echo ""
echo "Finished removing Toshy terminal commands:"
echo ""
echo "- toshy-systemd-setup"
echo "- toshy-systemd-remove"
echo "- toshy-services-status"
echo "- toshy-services-start"
echo "- toshy-services-restart"
echo "- toshy-services-stop"
echo "- toshy-services-log"
echo "- toshy-config-start"
echo "- toshy-config-start-verbose"
echo "- toshy-config-verbose-start"
echo "- toshy-config-restart"
echo "- toshy-config-stop"
echo "- toshy-tray"
echo "- toshy-gui"
echo "- toshy-env"
echo "- toshy-venv"
echo "- toshy-fnmode"
echo "- toshy-devices"
echo "- toshy-kde-dbus-service"
echo ""
echo "The commands will still be available until you close the current terminal, or "
echo "run 'hash -r', or source your shell RC file to refresh executable hash table."
echo ""
