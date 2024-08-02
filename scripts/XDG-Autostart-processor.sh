#!/usr/bin/env bash

# Script to process and launch items in the XDG Autostart user location (~/.config/autostart)


# Function to echo and log a message
log_and_echo() {
    local message="$1"
    echo "$message" | tee >(logger -p user.info)
}


log_and_echo "Processing user XDG Autostart folder contents..."

# Let the environment be established for a bit before loading autostart items,
# in case anything here needs to grab environment variables that may not be
# set immediately upon login. 
sleep 5


for entry in ~/.config/autostart/*.desktop; do
    if [[ -f "$entry" ]]; then
        # Extract the Exec command from the desktop entry and execute it
        cmd=$(grep '^Exec=' "$entry" | head -n 1 | sed 's/^Exec=//' | sed 's/%.//g')
        log_and_echo "Launching desktop entry file: '$entry'"
        # shellcheck disable=SC2086
        $cmd > /dev/null 2>&1 &
    elif [[ -x "$entry" ]]; then
        # If the file is executable, run it directly
        log_and_echo "Launching executable file: '$entry'"
        "$entry" > /dev/null 2>&1 &
    fi
done

log_and_echo "Finished processing user XDG Autostart folder contents."
