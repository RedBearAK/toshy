#!/usr/bin/env bash

# Script to make task switcher in KDE Plasma act more like macOS/GNOME task switchers.
# 
# - Use large icons for app switching, instead of window thumbnails
# - Show only one icon per "app", not one per window (makes no sense with "Large Icons")
# - Don't flash the selected window while Tabbing through task switcher icons (annoying)
# - Use alternative UI (thumbnail grid) for switching windows of current app
# 
# These task switcher fixes should be paired with the "Application Switcher" KWin script,
# otherwise they won't make that much sense (single icon per "application" when doing 
# non-grouped window switching is not sensible).


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
    echo "The necessary '$kwriteconfig_cmd' is missing. Cannot fix Plasma task switcher."
    exit 1
fi

echo "Making Plasma task switcher behave like macOS/GNOME."


# In "Main" tab:

# Enable "Only one window per application" (makes only a single icon appear for each "application")
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key ApplicationsMode 1

# Disable "Show selected window" (stops flashing each window on the screen as you Alt+Tab)
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key HighlightWindows 'false'

# Set the dialog to use "Large Icons" visual UI, instead of window previews
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key LayoutName 'big_icons'

# Set the delay for showing the task switcher dialog to zero milliseconds
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key DelayTime 0

# Enable putting minimized/hidden apps at the end of the switching dialog
"$kwriteconfig_cmd" --file kwinrc --group TabBox --key OrderMinimizedMode 1

# In "Alternative" tab:

# DO NOT enable "Only one window per application"
# (we want individual window previews in current app)

# Disable "Show selected window" (stops flashing each window on the screen as you Alt+Grave)
"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key HighlightWindows 'false'

# Set the dialog to use "Thumbnail Grid" visual UI, instead of "Large Icons" (from "Main" tab)
"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key LayoutName 'thumbnail_grid'

# Set the delay for showing the task switcher dialog to zero milliseconds
"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key DelayTime 0

# Enable putting minimized/hidden apps at the end of the switching dialog
"$kwriteconfig_cmd" --file kwinrc --group TabBoxAlternative --key OrderMinimizedMode 1


# Disable the Highlight Window Desktop Effect
"$kwriteconfig_cmd" --file kwinrc --group Plugins --key highlightwindowEnabled 'false'


# Shorten some commands by putting repetetive strings in variables
sc_wtwoca="Walk Through Windows of Current Application"
alt="Alternative"
rev="(Reverse)"


# Only try to do this in KDE 5 or 6
if [ "$KDE_ver" = "5" ] || [ "$KDE_ver" = "6" ]; then

    dest="org.kde.kglobalaccel"
    obj_path="/kglobalaccel"

    # mthd_setSC="org.kde.KGlobalAccel.setShortcut"
    # ai_keys_null="[0]"                                          # To clear the keys of a shortcut
    # ai_keys_alt_grave="[134217824]"                             # Alt+``
    # ai_keys_alt_tilde="[134217854]"                             # Alt+~
    # ai_keys_ctrl_alt_grave="[201326688]"                        # Ctrl+Alt+`
    # ai_keys_ctrl_alt_tilde="[201326718]"                        # Ctrl+Alt+~

    mthd_setSCKs="org.kde.KGlobalAccel.setShortcutKeys"
    a_ai_keys_null="[([0, 0, 0, 0],)]"                          # To clear the keys of a shortcut
    a_ai_keys_alt_grave="[([134217824, 0, 0, 0],)]"             # Alt+``
    a_ai_keys_alt_tilde="[([134217854, 0, 0, 0],)]"             # Alt+~
    a_ai_keys_ctrl_alt_grave="[([201326688, 0, 0, 0],)]"        # Ctrl+Alt+`
    a_ai_keys_ctrl_alt_tilde="[([201326718, 0, 0, 0],)]"        # Ctrl+Alt+~

    NO_AUTOLOAD=4                       # Make new shortcut take effect instead of being ignored.

    # CORRECT QDBUS SYNTAX UNKNOWN AT THIS TIME (THIS DOESN'T WORK)
    # qdbus org.kde.kglobalaccel /kglobalaccel org.kde.KGlobalAccel.setShortcut "${sc_wtwoca}" 'none, NoAutoloading'

    # GDBUS SYNTAX
    # 
    # Examples that actually worked:
    # 
    # gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel --method org.kde.KGlobalAccel.setShortcut "['kwin', 'Walk Through Windows of Current Application', 'KWin', 'Walk Through Windows of Current Application']" "[201326688]" 4
    # Returns if successful, the same array of integers: ([201326688],)
    # 
    # gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel --method org.kde.KGlobalAccel.setShortcut "['kwin', 'Walk Through Windows of Current Application', 'KWin', 'Walk Through Windows of Current Application']" "[0]" 4
    # Returns: ([0],)
    # Unsets shortcut for named action, to avoid conflicts with setting something else to use
    # the shortcut that was there previously.
    # 
    # Another working example, with setShortcutKeys:
    # gdbus call --session --dest org.kde.kglobalaccel --object-path /kglobalaccel --method org.kde.KGlobalAccel.setShortcutKeys "['kwin', 'Walk Through Windows of Current Application Alternative', 'KWin', 'Walk Through Windows of Current Application Alternative']" "[([0, 0, 0, 0],)]" 4
    # Returns: ([([0, 0, 0, 0],)],)
    # 
    # setShortcutKeys wants a(ai) for the keys (array of array of integers)

    figured_out_how_to_use_dbus_calls=false

    if $figured_out_how_to_use_dbus_calls && command -v gdbus > /dev/null 2>&1; then

        # Negate the "Main" current app shortcut
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca}', 'KWin', '${sc_wtwoca}']" \
            "${a_ai_keys_null}" "$NO_AUTOLOAD"

        # Negate the "Main" current app shortcut (reverse)
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${rev}', 'KWin', '${sc_wtwoca} ${rev}']" \
            "${a_ai_keys_null}" "$NO_AUTOLOAD"

        # Negate the "Alternative" current app shortcut
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${alt}', 'KWin', '${sc_wtwoca} ${alt}']" \
            "${a_ai_keys_null}" "$NO_AUTOLOAD"

        # Negate the "Alternative" current app shortcut (reverse)
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${alt} ${rev}', 'KWin', '${sc_wtwoca} ${alt} ${rev}']" \
            "${a_ai_keys_null}" "$NO_AUTOLOAD"

        sleep 2

        # Set the "Main" current app shortcut
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca}', 'KWin', '${sc_wtwoca}']" \
            "${a_ai_keys_ctrl_alt_grave}" "$NO_AUTOLOAD"

        # Set the "Main" current app shortcut (reverse)
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${rev}', 'KWin', '${sc_wtwoca} ${rev}']" \
            "${a_ai_keys_ctrl_alt_tilde}" "$NO_AUTOLOAD"

        # Set the "Alternative" current app shortcut
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${alt}', 'KWin', '${sc_wtwoca} ${alt}']" \
            "${a_ai_keys_alt_grave}" "$NO_AUTOLOAD"

        # Set the "Alternative" current app shortcut (reverse)
        gdbus call --session --dest "${dest}" --object-path "${obj_path}" \
            --method "${mthd_setSCKs}" \
            "['kwin', '${sc_wtwoca} ${alt} ${rev}', 'KWin', '${sc_wtwoca} ${alt} ${rev}']" \
            "${a_ai_keys_alt_tilde}" "$NO_AUTOLOAD"

    else

        kgsrc="kglobalshortcutsrc"

        # Change original shortcuts in "Main" tab to disable them and
        # allow the alternative GUI instead of "Large Icons" which we
        # use for grouped "app switching" like macOS or GNOME
        "$kwriteconfig_cmd" --file "$kgsrc" --group kwin --key "${sc_wtwoca}" \
            "none,Alt+\`,${sc_wtwoca}"
        "$kwriteconfig_cmd" --file "$kgsrc" --group kwin --key "${sc_wtwoca} ${rev}" \
            "none,Alt+~,${sc_wtwoca} ${rev}"

        # Set the same shortcuts from "Main" tab in the "Alternative" tab to
        # enable the alternate GUI and see thumbnails for windows of the current app.
        "$kwriteconfig_cmd" --file "$kgsrc" --group kwin --key "${sc_wtwoca} ${alt}" \
            "Alt+\`,none,${sc_wtwoca} ${alt}"
        "$kwriteconfig_cmd" --file "$kgsrc" --group kwin --key "${sc_wtwoca} ${alt} ${rev}" \
            "Alt+~,none,${sc_wtwoca} ${alt} ${rev}"

        # Allow a little time for RC files to be written and available for 'kglobalaccel' restart.
        sleep 0.5

        kglobalaccel_cmd="kglobalaccel${KDE_ver}"
        kstart_cmd_not_found=false
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
            echo "The ${kglobalaccel_cmd}  command is not available."
            echo "You must log out to activate modified shortcuts."
        fi

    fi

else
    echo "KDE version is not recognized. Avoiding change of keyboard shortcuts."
    exit 1
fi


# Give a little time to make sure files are actually written and 
# available for KWin reconfigure.
sleep 0.5


# We need to gracefully cascade through common D-Bus utils to 
# find one that is available to use for the KWin reconfigure 
# command. Sometimes 'qdbus' is not available. Start with 'gdbus'.

dbus_commands=("gdbus" "qdbus6" "qdbus-qt6" "qdbus-qt5" "qdbus" "dbus-send")

# Functions to handle reconfiguration with different dbus utilities
reconfigure_kwin() {
    case "$1" in
        gdbus)
            gdbus call --session --dest org.kde.KWin --object-path /KWin --method org.kde.KWin.reconfigure
            ;;
        qdbus6 | qdbus-qt6 | qdbus-qt5 | qdbus)
            "$1" org.kde.KWin /KWin reconfigure
            ;;
        dbus-send)
            dbus-send --session --type=method_call --dest=org.kde.KWin /KWin org.kde.KWin.reconfigure
            ;;
        *)
            echo "Unsupported DBus utility: $1" >&2
            return 1
            ;;
    esac
}

# Unquoted 'true' and 'false' values are built-in commands in bash, 
# returning 0 or 1 exit status.
# So they can sort of be treated like Python's 'True' or 'False' in 
# simple 'if' conditionals.
dbus_cmd_found=false

# Iterate through the dbus_commands array
for cmd in "${dbus_commands[@]}"; do
    if command -v "${cmd}" &> /dev/null; then
        dbus_cmd_found=true
        echo "Refreshing KWin configuration using $cmd."
        reconfigure_kwin "${cmd}" &> /dev/null
        sleep 0.5
        # Break out of the loop once a command is found and executed
        break
    fi
done

if ! $dbus_cmd_found; then
    echo "No suitable DBus utility found. KWin configuration may need manual reloading."
fi


echo "Finished fixing Plasma task switcher to act more like macOS/GNOME."
