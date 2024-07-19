#!/usr/bin/env bash

# Script to make Dolphin file manager in KDE Plasma have the settings I want
# 
# - No confirmation closing windows with multiple tabs
# - Save view settings for each folder separately (GlobalViewProps=false)
# - Don't remember open tabs
# - Show full path in title bar
# - Set some default icon sizes (Details 22, Compact 32)

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

    echo "Setting up Dolphin the way I like it..."

    # [General]
    # ConfirmClosingMultipleTabs=false
    # GlobalViewProps=false
    # RememberOpenedTabs=false
    # ShowFullPathInTitlebar=true

    "$kwriteconfig_cmd" --file dolphinrc --group "General" --key "ConfirmClosingMultipleTabs" 'false'
    "$kwriteconfig_cmd" --file dolphinrc --group "General" --key "GlobalViewProps" 'false'
    "$kwriteconfig_cmd" --file dolphinrc --group "General" --key "RememberOpenedTabs" 'false'
    "$kwriteconfig_cmd" --file dolphinrc --group "General" --key "ShowFullPathInTitlebar" 'true'

    # [CompactMode]
    # PreviewSize=32

    "$kwriteconfig_cmd" --file dolphinrc --group "CompactMode" --key "PreviewSize" '32'

    # [DetailsMode]
    # PreviewSize=22

    "$kwriteconfig_cmd" --file dolphinrc --group "DetailsMode" --key "PreviewSize" '22'

    # [KFileDialog Settings]
    # Places Icons Auto-resize=false
    # Places Icons Static Size=22

    "$kwriteconfig_cmd" --file dolphinrc --group "KFileDialog Settings" --key "Places Icons Auto-resize" 'false'
    "$kwriteconfig_cmd" --file dolphinrc --group "KFileDialog Settings" --key "Places Icons Static Size" '22'

    # [MainWindow]
    # ToolBarsMovable=Disabled

    "$kwriteconfig_cmd" --file dolphinrc --group "MainWindow" --key "ToolBarsMovable" 'Disabled'

    # [PlacesPanel]
    # IconSize=22

    "$kwriteconfig_cmd" --file dolphinrc --group "PlacesPanel" --key "IconSize" '22'

    echo "Finished."

fi


