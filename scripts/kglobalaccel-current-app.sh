#!/usr/bin/env bash

# The purpose of this script is to check for the possibly localized strings
# composing the 'actionId' array of strings for the shortcuts for switching
# between the windows of the focused "application" in KDE Plasma 6. And then
# use those localized arrays of strings to either reset or swap the "Main"
# and "Alternative" in-app task switching shortcuts. So that in-app shortcuts
# can utilize a different UI choice (e.g. "Thumbnail Grid" vs "Large Icons").

# WARNING: Currently the D-Bus commands cause the in-app shortcuts to 
# malfunction a bit, until Shortuts settings or Task Switcher settings
# are used to "Apply" some change (any change). This seems to "reset"
# something and get the new shortcut reassignments to work correctly. 


# blank line before any output, for readability in the terminal
echo

safe_shutdown() {
    if [ -z "$1" ]; then
        exit_code=0
    else
        exit_code=$1
    fi
    echo
    exit "$exit_code"
}


if [[ "$1" == "--help" || "$1" == "-h" || "$1" == "" ]]; then
    echo "Swap Main/Alternative task switching in-app shortcuts in Plasma 6"
    echo "Usage: $0 [reset]"
    echo "       swap       - set in-app shortcuts to Alternative task switching UI"
    echo "       reset      - reset in-app shortcuts to Main task switching UI"
    safe_shutdown 0
fi


if [ -z "$KDE_SESSION_VERSION" ]; then
    echo "Cannot identify KDE session version. Not in KDE?"
    safe_shutdown 1
elif ! [ "$KDE_SESSION_VERSION" = "6" ]; then
    echo "This script is meant to operate only in Plasma 6."
    safe_shutdown 1
fi

# Check for bash version for associative array support
if ((BASH_VERSINFO[0] < 4)); then
    echo "This script requires Bash version 4.0 or higher."
    exit 1
fi


run_tmp_dir="/tmp"
if [ -z "$XDG_RUNTIME_DIR" ]; then
    :
else
    run_tmp_dir="$XDG_RUNTIME_DIR"
fi

temp_file="$run_tmp_dir/plasma_current_app_actions_$(date +%Y%m%d_%H%M%S).txt"


# Getting 'actionId' arrays of strings for shortcuts using custom 'kglobalaccel-dbus.sh' script:
# This command should produce arrays of strings of all shortcuts in 'kwin' to send to a temporary file.
# File will have one 4-element array of strings in brackets "[]" on each line of the resulting file.
# 1st and 2nd elements should be the Unique Component ID and Unique Name ID of each keyboard shortcut.
# May have localized/translated strings in 3rd and 4th elements of each array, on non-English systems.

#./kglobalaccel-dbus.sh allActionsForComponent "['kwin']" | sed -e 's/\[\[/\[/g' -e 's/\]\]/\]/g' -e 's/\], /\]\n/g'

# To filter the above command for only the in-app shortcuts:

# ./kglobalaccel-dbus.sh allActionsForComponent "['kwin']" |\
#     sed -e 's/\[\[/\[/g' -e 's/\]\]/\]/g' -e 's/\], /\]\n/g' |\
#     grep "Current Application" > "$temp_file"

# The filtered command should show only four shortcuts as output (if the system language is US English): 
# ['kwin', 'Walk Through Windows of Current Application Alternative (Reverse)', 'System Settings', 'Walk Through Windows of Current Application Alternative (Reverse)']
# ['kwin', 'Walk Through Windows of Current Application', 'System Settings', 'Walk Through Windows of Current Application']
# ['kwin', 'Walk Through Windows of Current Application Alternative', 'System Settings', 'Walk Through Windows of Current Application Alternative']
# ['kwin', 'Walk Through Windows of Current Application (Reverse)', 'System Settings', 'Walk Through Windows of Current Application (Reverse)']


fetch_and_process_shortcuts() {
    local temp_file=$1  # Pass the temp file path as a parameter

    # Run the pipeline and return its exit status directly
    ./kglobalaccel-dbus.sh allActionsForComponent "['kwin']" | \
    sed -e 's/\[\[/\[/g' -e 's/\]\]/\]/g' -e 's/\], /\]\n/g' | \
    grep "Current Application" > "$temp_file"
}


# Fetch and process shortcuts
if ! fetch_and_process_shortcuts "$temp_file"; then
    echo "Failed to fetch or process shortcut data."
    safe_shutdown 1
fi


# Using built-in true/false like Python bools
reset_to_defaults=false
swap_alt_with_main=false
if [ "$1" = "reset" ]; then
    reset_to_defaults=true
elif [ "$1" = "swap" ]; then
    swap_alt_with_main=true
fi

sc_wtwoca="Walk Through Windows of Current Application"

# Array of ints argument to disable a shortcut
ai_disable_sc="([0, 0, 0, 0],)"

ai_Alt_Grave="([134217824, 0, 0, 0],)"
ai_Alt_Tilde="([134217854, 0, 0, 0],)"

# shellcheck disable=SC2034
ai_Meta_Ctrl_Alt_Grave="([469762144, 0, 0, 0],)"
# shellcheck disable=SC2034
ai_Meta_Ctrl_Alt_Tilde="([469762174, 0, 0, 0],)"


# Define unique action IDs in associative arrays

# Variable is used as custom function argument, which doesn't satisfy shellcheck.
# shellcheck disable=SC2034
declare -A actions_taskswitch_disable_alt=(
    ["kwin,$sc_wtwoca Alternative"]="$ai_disable_sc"
    ["kwin,$sc_wtwoca Alternative (Reverse)"]="$ai_disable_sc"
)

# Variable is used as custom function argument, which doesn't satisfy shellcheck.
# shellcheck disable=SC2034
declare -A actions_taskswitch_enable_main=(
    ["kwin,$sc_wtwoca"]="$ai_Alt_Grave"
    ["kwin,$sc_wtwoca (Reverse)"]="$ai_Alt_Tilde"
)

# Variable is used as custom function argument, which doesn't satisfy shellcheck.
# shellcheck disable=SC2034
declare -A actions_taskswitch_disable_main=(
    ["kwin,$sc_wtwoca"]="$ai_disable_sc"
    ["kwin,$sc_wtwoca (Reverse)"]="$ai_disable_sc"
)

# Variable is used as custom function argument, which doesn't satisfy SC2034 error.
# shellcheck disable=SC2034
declare -A actions_taskswitch_enable_alt=(
    # ["kwin,$sc_wtwoca Alternative"]="$ai_Alt_Grave"
    # ["kwin,$sc_wtwoca Alternative (Reverse)"]="$ai_Alt_Tilde"
    ["kwin,$sc_wtwoca Alternative"]="$ai_Alt_Grave"
    ["kwin,$sc_wtwoca Alternative (Reverse)"]="$ai_Alt_Tilde"
)


process_file() {
    local file=$1
    local mode=$2  # pass 'main' or 'alt' as 2nd function argument

    local mode_disable=""
    if [ "$mode" = "alt" ]; then
        mode_disable="main"
    else
        mode_disable="alt"
    fi

    local disable_group="actions_taskswitch_disable_${mode_disable}"

    echo
    echo "Disabling $mode_disable-tab in-app task switching shortcuts..."
    while IFS= read -r line; do
        process_line "$line" "$disable_group"
    done < "$file"

    local enable_group="actions_taskswitch_enable_${mode}"

    echo
    echo "Enabling $mode-tab in-app task switching shortcuts..."
    while IFS= read -r line; do
        process_line "$line" "$enable_group"
    done < "$file"

    rm "$file"
}

process_line() {
    local line=$1
    local action_group=$2
    declare -n actions=$action_group

    # Don't declare a local variable and also assign command output to it on the same line.
    # Triggers a shellcheck error (SC2155).
    local clean_line
    clean_line=$(echo "$line" | sed -e "s/\['//;s/'\]//;s/', '/,/g" | cut -d ',' -f 1-2)
    local component action
    IFS=',' read -r component action <<< "$clean_line"
    local unique_action_ids="${component},${action}"

    if [[ ${actions["$unique_action_ids"]} ]]; then
        local shortcut_keys_int_array=${actions["$unique_action_ids"]}
        echo "Match found: $line"
        echo "Associated shortcut integer array(s): $shortcut_keys_int_array"
        # Example of using the setShortcutKeys method
        # ./kglobalaccel-dbus.sh setShortcutKeys "$line" "[$shortcut_keys_int_array]" 4
        ./kglobalaccel-dbus.sh setShortcutKeys "$line" "[$shortcut_keys_int_array]" 4
    fi
}

# Main script logic
if $swap_alt_with_main; then
    process_file "$temp_file" "alt"
elif $reset_to_defaults; then
    process_file "$temp_file" "main"
fi

# Separate from next command prompt for readability
echo 
