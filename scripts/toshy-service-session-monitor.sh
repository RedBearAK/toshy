#!/usr/bin/env bash

# Monitor whether the user's desktop session is "Active" according to loginctl.

# Should handle the case of user remaining "logged in" but using "switch user"
# to let another user log in to their own desktop and use the screen. 
# We don't want the keymapper to interfere with the other user's input or 
# with their separate usage of this or any other keymapper. 

# Handles edge cases like login screen and session transitions

if ! command -v loginctl >/dev/null 2>&1; then
    echo "The \"loginctl\" command is not available. Toshy session monitor will not work here."
    exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
    echo "The \"systemctl\" command is not available. Toshy session monitor will not work here."
    exit 1
fi

# If XDG_RUNTIME_DIR is not set or is empty
if [ -z "${XDG_RUNTIME_DIR}" ]; then
    echo "SESSMON_SVC: XDG_RUNTIME_DIR not set. Unable to determine where to store the marker file."
else
    # Full path to the marker file
    MARKER_FILE="${XDG_RUNTIME_DIR}/toshy-service-sessmon.start"
    # Check if a marker file exists
    if [ ! -f "${MARKER_FILE}" ]; then
        # If it does not exist, wait for a certain time period
        sleep 3
        # Create the marker file to signify that the service has started once
        touch "${MARKER_FILE}"
    fi
fi


USER="$(whoami)"
STOPPED_BY_ME="false"

# Function to get current session ID safely
get_session_id() {
    # First try to get session by user
    local session_id
    session_id=$(loginctl list-sessions --no-legend | awk -v user="$USER" '$3 == user {print $1; exit}')
    
    # If that fails, try session-status (original method) but handle errors
    if [ -z "$session_id" ]; then
        session_id=$(loginctl session-status 2>/dev/null | head -n1 | cut -d' ' -f1)
    fi
    
    echo "$session_id"
}

# Function to check if session is active
check_session_active() {
    local session_id="$1"
    local is_active="no"
    
    if [ -n "$session_id" ]; then
        is_active=$(loginctl show-session "$session_id" -p Active --value 2>/dev/null || echo "no")
    fi
    
    echo "$is_active"
}

# Function to stop Toshy services
stop_toshy_services() {
    local reason="$1"
    echo "SESSMON_SVC: Stopping config service because $reason"
    systemctl --user stop toshy-config.service >/dev/null 2>&1
    sleep 0.5
    systemctl --user stop toshy-kde-dbus.service >/dev/null 2>&1
    systemctl --user stop toshy-cosmic-dbus.service >/dev/null 2>&1
    systemctl --user stop toshy-wlroots-dbus.service >/dev/null 2>&1
    STOPPED_BY_ME="true"
}

# Function to start Toshy services
start_toshy_services() {
    if [ "$STOPPED_BY_ME" = "true" ]; then
        systemctl --user restart toshy-kde-dbus.service >/dev/null 2>&1
        systemctl --user restart toshy-cosmic-dbus.service >/dev/null 2>&1
        systemctl --user restart toshy-wlroots-dbus.service >/dev/null 2>&1
        sleep 0.5
        systemctl --user restart toshy-config.service >/dev/null 2>&1
        STOPPED_BY_ME="false"
    fi
}

# give the session info and config service a bit of time to stabilize
sleep 2

while true; do
    sleep 2

    # Get session count and handle complete logout
    SESSION_COUNT=$(loginctl list-sessions -p UserName 2>/dev/null | grep -c "${USER}" || echo "0")
    
    if [ "$SESSION_COUNT" -eq 0 ]; then
        systemctl --user stop toshy-config.service
        systemctl --user stop toshy-kde-dbus.service
        systemctl --user stop toshy-cosmic-dbus.service
        systemctl --user stop toshy-wlroots-dbus.service
        # User is logged out entirely if there are no sessions, 
        # so in this case stop the session monitor too:
        systemctl --user stop toshy-session-monitor.service
        continue
    fi

    # Get current session ID
    SESSION_ID=$(get_session_id)
    
    # Check service status
    CFG_SERVICE_STATUS=$(systemctl --user is-active toshy-config.service)

    if [[ -n "$SESSION_ID" ]]; then
        # We have a valid session ID
        SESSION_IS_ACTIVE=$(check_session_active "$SESSION_ID")
        
        if [[ "$SESSION_IS_ACTIVE" == "yes" ]]; then
            # Session is active, start services if they were stopped by us
            if [[ "$CFG_SERVICE_STATUS" == "inactive" ]]; then
                start_toshy_services
            fi
        else
            # Session exists but is not active
            if [[ "$CFG_SERVICE_STATUS" == "active" ]]; then
                stop_toshy_services "session is inactive"
            fi
        fi
    else
        # No valid session ID (likely at login screen)
        if [[ "$CFG_SERVICE_STATUS" == "active" ]]; then
            stop_toshy_services "no valid session found (login screen?)"
        fi
    fi
done
