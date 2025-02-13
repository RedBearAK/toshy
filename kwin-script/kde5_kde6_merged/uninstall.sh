#!/usr/bin/env bash


# This is a script to remove an installed KWin script matching a script found in the current folder

exit_w_error() {
    local msg="$1"
    echo -e "\nERROR: ${msg} \nExiting...\n"
    exit 1
}

remove_w_kpackagetool6() {
    if ! command -v kpackagetool6 &> /dev/null; then
        exit_w_error "The 'kpackagetool6' command is missing. Cannot remove KWin script."
    else
        echo "Removing '${script_name}' KWin script."
        kpackagetool6 --type=${script_type} --remove ${script_path}
    fi
}

remove_w_kpackagetool5() {
    if ! command -v kpackagetool5 &> /dev/null; then
        exit_w_error "The 'kpackagetool5' command is missing. Cannot remove KWin script."
    else
        echo "Removing '${script_name}' KWin script."
        kpackagetool5 --type=${script_type} --remove ${script_path}
    fi
}

KDE_ver=${KDE_SESSION_VERSION:-0}   # Default to zero value if environment variable not set
script_type="KWin/Script"
script_path="."


if [ -f "./metadata.json" ]; then
    script_name=$(grep -oP '"Id":\s*"[^"]*' ./metadata.json | grep -oP '[^"]*$')
elif [ -f "./metadata.desktop" ]; then
    script_name=$(grep '^X-KDE-PluginInfo-Name=' ./metadata.desktop | cut -d '=' -f2)
else
    exit_w_error "No suitable metadata file found. Unable to get script name."
fi


if [[ $KDE_ver -eq 0 ]]; then
    echo "KDE_SESSION_VERSION environment variable was not set."
    exit_w_error "Cannot remove '${script_name}' KWin script."
elif [[ $KDE_ver -eq 6 ]]; then
    if ! remove_w_kpackagetool6; then
        exit_w_error "Problem while removing '${script_name}' KWin script."
    fi
    echo "'${script_name}' KWin script removed. Refreshing KWin."
elif [[ ${KDE_ver} -eq 5 ]]; then
    if ! remove_w_kpackagetool5; then
        exit_w_error "Problem while removing '${script_name}' KWin script."
    fi
    echo "'${script_name}' KWin script removed. Refreshing KWin."
else
    exit_w_error "KDE_SESSION_VERSION had a value, but that value was unrecognized: '${KDE_ver}'"
fi


sleep 0.5

# We need to gracefully cascade through common D-Bus utils to 
# find one that is available to use for the KWin reconfigure 
# command. Sometimes 'qdbus' is not available.

# Array of command names of common D-Bus utilities
dbus_commands=("qdbus" "gdbus" "dbus-send")

reconfigure_w_qdbus() {
    qdbus org.kde.KWin /KWin reconfigure
}

reconfigure_w_gdbus() {
    gdbus call --session --dest org.kde.KWin --object-path /KWin --method org.kde.KWin.reconfigure
}

reconfigure_w_dbus_send() {
    dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure
}

# Iterate through the dbus_commands array
for cmd in "${dbus_commands[@]}"; do
    if command -v "${cmd}" &> /dev/null; then
        # Call the corresponding function based on the command
        echo "Refreshing KWin configuration."
        case "$cmd" in
            qdbus)              reconfigure_w_qdbus &> /dev/null;;
            gdbus)              reconfigure_w_gdbus &> /dev/null ;;
            dbus-send)          reconfigure_w_dbus_send &> /dev/null ;;
        esac
        sleep 0.5
        # Break out of the loop once a command is found and executed
        break
    fi
done

echo "Finished removing KWin script: '${script_name}'"
