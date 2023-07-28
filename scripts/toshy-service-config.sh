#!/bin/env bash


# Start the actual run of the keymapper with Toshy config, making 
# sure to stop existing processes.

# Make sure keymapper binary can be found in user-home-local "bin" location
export PATH=$HOME/.local/bin:$PATH


# If XDG_RUNTIME_DIR is not set or is empty
if [ -z "${XDG_RUNTIME_DIR}" ]; then
    echo "Toshy Config Svc: XDG_RUNTIME_DIR not set. Unable to determine where to store the marker file."
    # exit 1
else
    # Full path to the marker file
    MARKER_FILE="${XDG_RUNTIME_DIR}/toshy-service-config.start"
    # Check if a marker file exists
    if [ ! -f "${MARKER_FILE}" ]; then
        # If it does not exist, wait for a certain time period
        sleep 3
        # Create the marker file to signify that the service has started once
        touch "${MARKER_FILE}"
    fi
fi


# Activate the Python virtual environment
# shellcheck disable=SC1091
source "$HOME/.config/toshy/.venv/bin/activate"


# Check if the desktop session is X11
if [[ "$XDG_SESSION_TYPE" == "x11" ]]; then
    # Check if xset is installed
    if ! command -v xset &> /dev/null; then
        echo "Toshy Config Service: xset could not be found, please install it." >&2
        exit 1
    fi
    # Loop until the X server is ready
    while true; do
        if xset -q &>/dev/null; then
            break
        else
            echo "Toshy Config Service: X server not ready?" >&2
            # Sleep for a short period before trying again
            sleep 2
        fi
    done
elif [[ -z "$XDG_SESSION_TYPE" ]]; then
    sleep 2
    echo "Toshy Config Service: XDG_SESSION_TYPE not set. Restarting service." >&2
    exit 1
fi


if command -v keyszer >/dev/null 2>&1; then
    : # no-op operator
else
    echo -e "The \"keyszer\" command was not found in: \n$PATH."
    echo "Toshy config cannot be loaded until \"keyszer\" is installed."
    exit 1
fi


# shut down any existing keyszer (or xkeysnail) process
pkill -f "bin/keyszer"
pkill -f "bin/xkeysnail"

keyszer -w -c "$HOME/.config/toshy/toshy_config.py"
