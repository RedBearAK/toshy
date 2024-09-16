#!/usr/bin/env bash

# Script to make Konsole terminal emulator in KDE Plasma have the settings I want


KDE_ver="$KDE_SESSION_VERSION"

# Check if we're actually in KDE
if [ -z "$KDE_ver" ]; then
    echo "KDE_SESSION_VERSION is not set or is empty. Not in KDE? Exiting."
    exit 1
else
    # Single quotes inside double quotes do not block variable expansion
    echo "Detected KDE_SESSION_VERSION: '${KDE_ver}'"
    kwriteconfig_cmd="kwriteconfig${KDE_ver}"
fi

# See if the relevant 'kwriteconfig' command variation is available
if ! command -v "$kwriteconfig_cmd" > /dev/null 2>&1; then
    echo "The necessary '$kwriteconfig_cmd' is missing."
    exit 1
fi

# Only try to do this in KDE 5 or 6
if [ "$KDE_ver" = "5" ] || [ "$KDE_ver" = "6" ]; then

    echo "Setting up Konsole the way I like it..."

    # [TabBar]
    # ExpandTabWidth=true
    # TabBarPosition=Bottom

    "$kwriteconfig_cmd" --file konsolerc --group "TabBar" --key "ExpandTabWidth" 'true'
    "$kwriteconfig_cmd" --file konsolerc --group "TabBar" --key "TabBarPosition" 'Bottom'

    echo "Finished."

fi
