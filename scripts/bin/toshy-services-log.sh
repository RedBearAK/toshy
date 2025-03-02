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

# Check if stdbuf is available and build the command array
if command -v stdbuf >/dev/null 2>&1; then
    cmd=(stdbuf -oL journalctl -n200 -b -f)
else
    cmd=(journalctl -n200 -b -f)
fi

# Add each service to the command array
for service in "${toshy_services[@]}"; do
    cmd+=(--user-unit "$service")
done

# Set process name before exec - this will be visible briefly, but exec will replace it
echo "toshy-svcs-log" > /proc/$$/comm

# Use exec with the -a option to set the process name
# The -a option sets the zeroth argument of the process, which is often used in process listings
if command -v stdbuf >/dev/null 2>&1; then
    exec -a "toshy-svcs-log" "${cmd[@]}"
else
    exec -a "toshy-svcs-log" journalctl -n200 -b -f "${cmd[@]:2}"
fi
