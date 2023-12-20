#!/usr/bin/env bash

# Script to process and launch items in the XDG Autostart user location (~/.config/autostart)

for entry in ~/.config/autostart/*; do
    if [[ -f "$entry" ]]; then
        # Check if the file is a desktop entry
        if [[ $(file --mime-type -b "$entry") == "application/x-desktop" ]]; then
            # Extract the Exec command from the desktop entry and execute it
            cmd=$(grep '^Exec=' "$entry" | head -n 1 | sed 's/^Exec=//' | cut -d ' ' -f 1)
            # Execute the command using nohup
            # shellcheck disable=SC2086
            nohup $cmd > /dev/null 2>&1 &
        elif [[ -x "$entry" ]]; then
            # If the file is executable, run it directly
            nohup "$entry" > /dev/null 2>&1 &
        fi
    fi
done
