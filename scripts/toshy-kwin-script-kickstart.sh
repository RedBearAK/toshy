#!/usr/bin/env bash

# Script to create a KWin event that will get the KWin script to start working

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

sleep 3
# check that there is a valid display, otherwise wait a bit longer before showing dialog
if [[ -z "${DISPLAY}" && -z "${WAYLAND_DISPLAY}" ]]; then
    sleep 6
fi

title="Toshy"
icon_file="${HOME}/.local/share/icons/toshy_app_icon_rainbow.svg"
icon_name="toshy_app_icon_rainbow"
time1_s=2
time2_s=3
message="Kickstarting Toshy window context."


if command -v timeout &> /dev/null; then
    timeout_cmd="timeout -k ${time2_s}s -s SIGTERM ${time1_s}s "
else
    timeout_cmd=""
fi

if command -v zenity &> /dev/null; then
    if zenity --help-info | grep -q -- '--icon='; then
        ${timeout_cmd} zenity --info --no-wrap --title="${title}" --icon="${icon_name}" \
            --text="${message}" --timeout=${time2_s} >/dev/null 2>&1
    elif zenity --help-info | grep -q -- '--icon-name='; then
        ${timeout_cmd} zenity --info --no-wrap --title="${title}" --icon-name="${icon_name}" \
            --text="${message}" --timeout=${time2_s} >/dev/null 2>&1
    else
        ${timeout_cmd} zenity --info --no-wrap --title="${title}" \
            --text="${message}" --timeout=${time2_s} >/dev/null 2>&1
    fi
    exit 0
elif command -v kdialog &> /dev/null; then
    ${timeout_cmd} kdialog --title="${title}" --icon "${icon_file}" \
        --msgbox "${message}" >/dev/null 2>&1
    exit 0
elif command -v xmessage &> /dev/null; then
    ${timeout_cmd} xmessage "${message}" -timeout ${time2_s} >/dev/null 2>&1
    exit 0
else
    echo "ERROR: Toshy cannot kickstart the KWin script. Dialog utilities unavailable."
fi
