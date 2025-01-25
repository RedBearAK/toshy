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


# Set the process name for the Toshy services log process
echo "toshy-svcs-log" > /proc/$$/comm


# Check if stdbuf is available and set the appropriate command
# Hopefully this may stop certain terminals from holding back journal
# output and showing new output in large bursts.
if command -v stdbuf >/dev/null 2>&1; then
    STDBUF_CMD="stdbuf -oL"
else
    STDBUF_CMD=""
fi

# -b flag to only show messages since last boot
# -f flag to follow new journal output
# -n100 to show the last 100 lines (max) of existing log output
# journalctl --user -n100 -b -f -u toshy-config -u toshy-session-monitor -u toshy-kde-dbus
# newer(?) syntax to do the same thing? 
# ${STDBUF_CMD} journalctl -n100 -b -f --user-unit 'toshy-*'

# Had trouble with Tumbleweed not wanting to show any output at all when using the wildcard, so...

# Start building the command with the basic parameters
cmd_base="${STDBUF_CMD} journalctl -n200 -b -f"

# First get all the Toshy service names into an array
# Backslashes not required inside parentheses in bash?
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

# Add each service to the base command
cmd_units=""
for service in "${toshy_services[@]}"; do
    cmd_units+=" --user-unit $service"
done

# Combine and execute
full_cmd="${cmd_base}${cmd_units}"
# echo "Executing: $full_cmd"
eval "$full_cmd"
