#!/usr/bin/env bash

# Script to process and launch items in the XDG Autostart user location (~/.config/autostart)


# Function to echo and log a message
log_and_echo() {
    local message="$1"
    echo "$message" | tee >(logger)
}


log_and_echo "Processing user XDG Autostart folder contents..."


for entry in ~/.config/autostart/*; do
    if [[ -f "$entry" ]]; then
        # Check if the file is a desktop entry
        if [[ $(file --mime-type -b "$entry") == "application/x-desktop" ]]; then
            # Extract the Exec command from the desktop entry and execute it
            cmd=$(grep '^Exec=' "$entry" | head -n 1 | sed 's/^Exec=//' | sed 's/%.//g')
            log_and_echo "Launching file: '$entry'"
            # shellcheck disable=SC2086
            $cmd > /dev/null 2>&1 &
        elif [[ -x "$entry" ]]; then
            # If the file is executable, run it directly
            "$entry" > /dev/null 2>&1 &
        fi
    fi
done

log_and_echo "Finished processing user XDG Autostart folder contents."
