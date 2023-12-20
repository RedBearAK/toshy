#!/usr/bin/env bash

# script to process and launch items in the XDG Autostart user location (~/.config/autostart)

for entry in ~/.config/autostart/*; do
    if [[ -f "$entry" ]]; then
        # Check if the file is a desktop entry
        if [[ $(file --mime-type -b "$entry") == "application/x-desktop" ]]; then
            # Extract the Exec command from the desktop entry and execute it
            grep '^Exec=' "$entry" | sed 's/^Exec=//' | sh
        else
            # Execute the file directly (useful for scripts but may not be valid in the XDG spec)
            sh "$entry"
        fi
    fi
done
