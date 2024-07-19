#!/usr/bin/env bash

# Script to make 'krunner' in KDE Plasma have the settings I want

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

    echo "Setting up 'krunner' the way I like it..."

    # [General]
    # ActivateWhenTypingOnDesktop=false
    # font=Noto Sans,20,-1,5,60,0,0,0,0,0
    # historyBehavior=Disabled
    # migrated=false

    "$kwriteconfig_cmd" --file krunnerrc --group "General" --key "ActivateWhenTypingOnDesktop" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "General" --key "historyBehavior" 'Disabled'

    # [Plugins]
    # browserhistoryEnabled=false
    # browsertabsEnabled=false
    # krunner_bookmarksrunnerEnabled=false
    # krunner_recentdocumentsEnabled=false
    # krunner_webshortcutsEnabled=false
    # org.kde.activities2Enabled=false

    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "browserhistoryEnabled" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "browsertabsEnabled" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "krunner_bookmarksrunnerEnabled" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "krunner_recentdocumentsEnabled" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "krunner_webshortcutsEnabled" 'false'
    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --key "org.kde.activities2Enabled" 'false'

    # [Plugins][Favorites]
    # plugins=krunner_sessions,krunner_services,krunner_systemsettings

    "$kwriteconfig_cmd" --file krunnerrc --group "Plugins" --group "Favorites" \
        --key "plugins" 'krunner_sessions,krunner_services,krunner_systemsettings'

    echo "Finished."

fi


