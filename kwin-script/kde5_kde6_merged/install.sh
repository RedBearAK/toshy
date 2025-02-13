#!/usr/bin/env bash


# This script will install a KWin script structure found in the path designated in '$script_path'

exit_w_error() {
    local msg="$1"
    echo -e "\nERROR: ${msg} \nExiting...\n"
    exit 1
}

install_w_kpackagetool6() {
    if ! command -v kpackagetool6 &> /dev/null; then
        exit_w_error "The 'kpackagetool6' command was not found. Cannot install KWin script."
    fi
    echo "Installing KWin script: '${script_name}'"
    if ! kpackagetool6 --type="${script_type}" --install "${script_path}" &> /dev/null; then
        kpackagetool6 --type="${script_type}" --upgrade "${script_path}"
    fi
}

install_w_kpackagetool5() {
    if ! command -v kpackagetool5 &> /dev/null; then
        exit_w_error "The 'kpackagetool5' command was not found. Cannot install KWin script."
    fi
    echo "Installing KWin script: '${script_name}'"
    if ! kpackagetool5 --type="${script_type}" --install "${script_path}" &> /dev/null; then
        kpackagetool5 --type="${script_type}" --upgrade "${script_path}"
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


if [[ ${KDE_ver} -eq 0 ]]; then
    echo "KDE_SESSION_VERSION environment variable was not set."
    exit_w_error "Cannot install '${script_name}' KWin script."
elif [[ ${KDE_ver} -eq 6 ]]; then
    if ! install_w_kpackagetool6; then
        exit_w_error "Problem installing '${script_name}' with kpackagetool6."
    fi
    if ! command -v kwriteconfig6 &> /dev/null; then
        exit_w_error "The 'kwriteconfig6' command was not found. Cannot enable KWin script."
    fi
    kwriteconfig6 --file kwinrc --group Plugins --key "$script_name"Enabled true
elif [[ ${KDE_ver} -eq 5 ]]; then
    if ! install_w_kpackagetool5; then
        exit_w_error "Problem installing '${script_name}' with kpackagetool5."
    fi
    if ! command -v kwriteconfig5 &> /dev/null; then
        exit_w_error "The 'kwriteconfig5' command was not found. Cannot enable KWin script."
    fi
    kwriteconfig5 --file kwinrc --group Plugins --key "$script_name"Enabled true
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

echo "Finished installing KWin script: '${script_name}'"
