#!/usr/bin/env bash

# Script to make task switcher in KDE Plasma act more like macOS/GNOME task switchers.
# - Use large icons for app switching, instead of window thumbnails
# - Show only one icon per "app", not one per window (makes no sense with "Large Icons")
# - Don't flash the selected window while Tabbing through task switcher icons (annoying)
# - Use alternative UI (thumbnail grid) for switching windows of current app
# These task switcher fixes should be paired with "Application Switcher" KWin script.


KDE_ver="$KDE_SESSION_VERSION"


if [ -z "$KDE_ver" ]; then
    echo "KDE_SESSION_VERSION is not set or is empty. Not in KDE? Exiting."
    exit 1
else
    # Single quotes inside double quotes do not block variable expansion
    echo "Detected KDE_SESSION_VERSION: '${KDE_ver}'"
    kwriteconfig_cmd="kwriteconfig${KDE_ver}"
fi


if ! command -v "$kwriteconfig_cmd" > /dev/null 2>&1; then
    echo "The necessary '$kwriteconfig_cmd' is missing. Cannot fix Plasma task switcher."
    exit 1
fi


"$kwriteconfig_cmd" --file kwinrc --group TabBox --key ApplicationsMode '1'
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key HighlightWindows 'false'
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key LayoutName 'big_icons'

"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key HighlightWindows 'false'
"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key LayoutName 'thumbnail_grid'
	
"$kwriteconfig_cmd" --file kglobalshortcutsrc --group kwin --key \
'Walk Through Windows of Current Application' \
'none,none,Walk Through Windows of Current Application'

"$kwriteconfig_cmd" --file kglobalshortcutsrc --group kwin --key \
'Walk Through Windows of Current Application (Reverse)' \
'none,none,Walk Through Windows of Current Application (Reverse)'

"$kwriteconfig_cmd" --file kglobalshortcutsrc --group kwin --key \
'Walk Through Windows of Current Application Alternative' \
'Alt+`,none,Walk Through Windows of Current Application Alternative'

"$kwriteconfig_cmd" --file kglobalshortcutsrc --group kwin --key \
'Walk Through Windows of Current Application Alternative (Reverse)' \
'Alt+~,none,Walk Through Windows of Current Application Alternative (Reverse)'


# Give a little time to make sure files are actually written and 
# available for KWin reconfigure and restarting kglobalaccel.
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


# Unquoted 'true' and 'false' are built-in commands in bash, returning 0 or 1 exit status
# so they can sort of be treated like Python's 'True' or 'False' in 'if' conditions.
dbus_cmd_found=false


# Iterate through the dbus_commands array
for cmd in "${dbus_commands[@]}"; do
    if command -v "${cmd}" &> /dev/null; then
        # Call the corresponding function based on the command
        dbus_cmd_found=true
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


if ! $dbus_cmd_found; then
    echo "No suitable DBus utility found. KWin configuration may need manual reloading."
fi


kglobalaccel_cmd="kglobalaccel${KDE_ver}"
kstart_cmd="kstart${KDE_ver}"


if command -v "$kglobalaccel_cmd" >/dev/null 2>&1; then

    if ! command -v "$kstart_cmd" >/dev/null 2>&1; then
        if ! command -v "kstart" > /dev/null 2>&1; then
            kstart_cmd_not_found=true
        else
            kstart_cmd_not_found=false
            kstart_cmd="kstart"
        fi
    fi

    if ! $kstart_cmd_not_found && killall "$kglobalaccel_cmd" > /dev/null 2>&1; then
        echo "Successfully killed ${kglobalaccel_cmd}."
        sleep 2
        "$kstart_cmd" "$kglobalaccel_cmd"
        echo "Restarted ${kglobalaccel_cmd}. If global shortcuts do not work, log out."
    else
        echo "Failed to kill ${kglobalaccel_cmd}. You may need to log out."
    fi

else
    echo "ERROR: The ${kglobalaccel_cmd} is not available."
    echo "       You must log out to activate modified shortcuts."
fi

echo "Finished fixing Plasma task switcher to act more like macOS/GNOME."
