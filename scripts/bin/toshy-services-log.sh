#!/usr/bin/env bash

# Show the journalctl output of the Toshy systemd services (session monitor and config).

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if systemd is actually the init system
if [[ $(ps -p 1 -o comm=) == "systemd" ]]; then
    # systemd is the init system, proceed
    :
else
    # systemd is NOT the init system, exit with message
    echo "Init system is not 'systemd'..."
    exit 0
fi

# Get out of here if systemctl is not available
if command -v systemctl >/dev/null 2>&1; then
    # systemctl is installed, proceed
    :
else
    # no systemctl found, exit silently
    exit 0
fi

clean_exit() {
    echo "Caught Interrupt signal. Exiting..."
    # Add your clean-up commands here

    # Exit the script
    exit 0
}

# Trap the interrupt signal
trap 'clean_exit' SIGINT

echo "Showing systemd journal messages for Toshy services (since last boot):"

# Set the process name for the Toshy services log process.
# We can do this here because this is just a direct launcher script.
# This trick seems to confuse systemd as it tries to track "child" processes. 
echo "toshy-svcs-log" > /proc/$$/comm

# First get all the Toshy service names into an array
if systemctl --user list-unit-files &>/dev/null; then
    mapfile -t toshy_services < <(
        systemctl --user list-unit-files |
        grep -i toshy |
        grep -v generated |
        awk '{print $1}'
    )
else
    # Handle systems without user service support (e.g., CentOS 7)
    echo "ERROR: Systemd user services are probably not supported here."
    echo
    exit 1
fi

# Check if any services were found
if [ ${#toshy_services[@]} -eq 0 ]; then
    echo "No Toshy services found. Exiting."
    exit 0
fi

# Check if stdbuf is available and set the appropriate command
if command -v stdbuf >/dev/null 2>&1; then
    STDBUF_CMD="stdbuf -oL"
else
    STDBUF_CMD=""
fi

# Start building the command with the basic parameters
cmd_base="${STDBUF_CMD} journalctl -n200 -b -f"

# Add each service to the base command
cmd_units=""
for service in "${toshy_services[@]}"; do
    cmd_units+=" --user-unit $service"
done

# Combine and execute the command (no exec, keep the renamed shell)
full_cmd="${cmd_base}${cmd_units}"
eval "$full_cmd"
