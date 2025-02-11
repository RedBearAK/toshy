#!/usr/bin/env bash

# Monitor whether the user's desktop session is "Active" according to loginctl.
# D-Bus event-driven version using gdbus
#
# Should handle the case of user remaining "logged in" but using "switch user"
# to let another user log in to their own desktop and use the screen. 
#
# We don't want the keymapper to interfere with any other user's input or 
# with their separate usage of this or any other keymapper. So this monitoring
# service will disable the config file service while the user's session is not
# "Active" according to loginctl.

exit_w_error() {
    local msg="$1"
    echo -e "\n(EE) ERROR: ${msg} Exiting...\n"
    exit 1
}

# Disable after testing the script works well under the target situations (switch user, logouts)
DEBUG=0

if ! command -v loginctl >/dev/null 2>&1; then
    exit_w_error "The 'loginctl' command is not available."
fi

if ! command -v systemctl >/dev/null 2>&1; then
    exit_w_error "The 'systemctl' command is not available."
fi

if ! command -v gdbus >/dev/null 2>&1; then
    exit_w_error "The 'gdbus' command is not available."
fi

# Set main process name for system tools
echo "toshy-sessmon" > /proc/$$/comm

USER="$(whoami)"

# Service arrays
TOSHY_DBUS_SVCS=(                                                   \
    "toshy-kwin-dbus.service"                                        \
    "toshy-cosmic-dbus.service"                                     \
    "toshy-wlroots-dbus.service"                                    \
)

# ALL_TOSHY_SVCS=(                                                    \
#     "toshy-config.service"                                          \
#     "${TOSHY_DBUS_SVCS[@]}"                                         \
#     "toshy-session-monitor.service"                                 \
# )

# Function to stop Toshy services
stop_toshy_services() {
    local reason="$1"
    echo "SESSMON_SVC: Stopping config service because $reason"
    [[ $DEBUG == 1 ]] && echo "(DD) Stopping config service first"

    # Stop config service first
    systemctl --user stop toshy-config.service >/dev/null 2>&1

    sleep 0.5

    # Stop all D-Bus services
    [[ $DEBUG == 1 ]] && echo "(DD) Stopping D-Bus services"
    for service in "${TOSHY_DBUS_SVCS[@]}"; do
        [[ $DEBUG == 1 ]] && echo "(DD) Stopping service: $service"
        systemctl --user stop "$service" >/dev/null 2>&1
    done

    STOPPED_BY_ME="true"
    [[ $DEBUG == 1 ]] && echo "(DD) STOPPED_BY_ME set to: $STOPPED_BY_ME"
}

# Function to start Toshy services
start_toshy_services() {
    if [[ "$STOPPED_BY_ME" == "true" ]]; then
        # Start all D-Bus services first
        [[ $DEBUG == 1 ]] && echo "(DD) Starting D-Bus services"
        for service in "${TOSHY_DBUS_SVCS[@]}"; do
            [[ $DEBUG == 1 ]] && echo "(DD) Starting service: $service"
            systemctl --user restart "$service" >/dev/null 2>&1
        done

        sleep 0.5

        # Then start the config service
        [[ $DEBUG == 1 ]] && echo "(DD) Starting config service"
        systemctl --user restart toshy-config.service >/dev/null 2>&1

        STOPPED_BY_ME="false"
        [[ $DEBUG == 1 ]] && echo "(DD) STOPPED_BY_ME set to: $STOPPED_BY_ME"
    fi
}

# Function to get current user session count from loginctl
get_session_count() {
    loginctl list-sessions -p UserName 2>/dev/null | grep -c "${USER}" || echo "0"
}

# Function to get current user session ID from loginctl
get_session_id() {
    loginctl session-status 2>/dev/null | head -n1 | cut -d' ' -f1
}

# Function to check if session is active (returns "yes" or "no")
is_session_active() {
    local session_id="$1"
    loginctl show-session "$session_id" -p Active --value 2>/dev/null || echo "no"
}

STOPPED_BY_ME="false"
LAST_STATE=""

# Main D-Bus signal monitoring loop - will restart monitoring if it fails
while true; do
    # Get session count and handle complete logout
    SESSION_COUNT=$(get_session_count)
    
    [[ $DEBUG == 1 ]] && {
        echo "(DD) Session count check:
    USER:          '$USER'
    SESSION_COUNT: '$SESSION_COUNT'"
    }
    
    if [[ "$SESSION_COUNT" -eq 0 ]]; then
        echo "SESSMON_SVC: No sessions found, stopping all services"
        [[ $DEBUG == 1 ]] && echo "(DD) Stopping all services"
        # Stop all services (session monitor last) if no sessions exist
        systemctl --user stop toshy-config.service
        for service in "${TOSHY_DBUS_SVCS[@]}"; do
            systemctl --user stop "$service"
        done
        systemctl --user stop toshy-session-monitor.service
    fi

    # Get current session ID
    SESSION_ID="$(get_session_id)"
    [[ $DEBUG == 1 ]] && echo "(DD) Got session ID: '$SESSION_ID'"
    
    if [[ -z "$SESSION_ID" ]]; then
        echo "SESSMON_SVC: No session ID found, waiting..."
        sleep 5
        continue
    fi

    # Get D-Bus path for our session
    SESSION_PATH=$(                                                 \
        gdbus call --system                                         \
          --dest org.freedesktop.login1                             \
          --object-path /org/freedesktop/login1                     \
          --method org.freedesktop.login1.Manager.ListSessions      \
          | grep -o "('$SESSION_ID',[^)]*)"                         \
          | grep -o "'/org/freedesktop/login1/session/[^']*'"       \
          | tr -d "'"                                               \
    )

    [[ $DEBUG == 1 ]] && {
        echo "(DD) D-Bus session path lookup:
    SESSION_ID: '$SESSION_ID'
    PATH:       '$SESSION_PATH'"
    }

    if [[ -z "$SESSION_PATH" ]]; then
        echo "SESSMON_SVC: Could not get session path, waiting..."
        sleep 5
        continue
    fi

    # Get initial session state
    INITIAL_STATE=$(is_session_active "$SESSION_ID")
    
    [[ $DEBUG == 1 ]] && {
        echo "(DD) Initial session state check:
    SESSION_ID:     '$SESSION_ID'
    INITIAL_STATE:  '$INITIAL_STATE'
    LAST_STATE:     '$LAST_STATE'"
    }
    
    # Process initial state
    if [[ -n "$INITIAL_STATE" ]] && [[ "$INITIAL_STATE" != "$LAST_STATE" ]]; then
        LAST_STATE="$INITIAL_STATE"
        echo "SESSMON_SVC: Initial session state: $INITIAL_STATE"
        
        if [[ "$INITIAL_STATE" == "no" ]]; then
            # Get config service status
            TOSHY_CFG_SVC_STATUS=$(systemctl --user is-active toshy-config.service)
            [[ $DEBUG == 1 ]] && echo "(DD) Config service status: '$TOSHY_CFG_SVC_STATUS'"

            if [[ "$TOSHY_CFG_SVC_STATUS" == "active" ]]; then
                stop_toshy_services "session is inactive"
            fi
        fi
    fi

    # Start monitoring D-Bus signals for session state changes
    echo "SESSMON_SVC: Starting D-Bus monitor for session $SESSION_ID"
    [[ $DEBUG == 1 ]] && {
        echo "(DD) Starting D-Bus monitor:
    SESSION_ID:   '$SESSION_ID'
    SESSION_PATH: '$SESSION_PATH'"
    }
    
    # Set monitoring process name
    echo "toshy-sessmon" > /proc/$$/comm
        
    gdbus monitor --system --dest org.freedesktop.login1            \
        | grep --line-buffered "$SESSION_PATH"                      \
        | grep --line-buffered "Active': <"                         \
        | grep --line-buffered -o "true\|false"                     \
        | while read -r STATE; do
            [[ $DEBUG == 1 ]] && {
                echo "(DD) Processing session state:
    STATE: '$STATE'
    LAST_STATE: '$LAST_STATE'"
            }

            # If session active state just changed to true, we might need to restart services
            if [[ "$STATE" != "$LAST_STATE" ]] && [[ "$STATE" == "true" ]]; then
                LAST_STATE="$STATE"
                echo "SESSMON_SVC: Session active state changed to: $STATE"

                # Get config service status
                TOSHY_CFG_SVC_STATUS=$(systemctl --user is-active toshy-config.service)
                [[ $DEBUG == 1 ]] && echo "(DD) Config service status: '$TOSHY_CFG_SVC_STATUS'"

                if [[ "$TOSHY_CFG_SVC_STATUS" == "inactive" ]]; then
                    [[ $DEBUG == 1 ]] && echo "(DD) Starting services due to session active"
                    start_toshy_services
                fi
            fi

            # Always check for logout when session active state is false
            if [[ "$STATE" == "false" ]]; then
                LAST_STATE="$STATE"
                
                # First stop the regular services right away
                TOSHY_CFG_SVC_STATUS=$(systemctl --user is-active toshy-config.service)
                [[ $DEBUG == 1 ]] && echo "(DD) Config service status: '$TOSHY_CFG_SVC_STATUS'"

                if [[ "$TOSHY_CFG_SVC_STATUS" == "active" ]]; then
                    [[ $DEBUG == 1 ]] && echo "(DD) Stopping services due to session inactive"
                    stop_toshy_services "session is inactive"
                fi

                # Then start watching for either complete logout or session reactivation
                echo "SESSMON_SVC: Starting logout monitor..."
                while true; do
                    # First check if the session became active again
                    CURRENT_STATE=$(is_session_active "$SESSION_ID")
                    if [[ "$CURRENT_STATE" == "yes" ]]; then
                        [[ $DEBUG == 1 ]] && echo "(DD) Session became active again, ending logout monitor"
                        break
                    fi

                    # If still inactive, check for complete logout
                    SESSION_COUNT=$(get_session_count)
                    [[ $DEBUG == 1 ]] && echo "(DD) Checking session count during inactive state: $SESSION_COUNT"

                    if [[ "$SESSION_COUNT" -eq 0 ]]; then
                        echo "SESSMON_SVC: No sessions found, stopping session monitor"
                        systemctl --user stop toshy-session-monitor.service
                        break
                    fi
                    sleep 3
                done
            fi
        done

    # If monitor exits, wait before restarting
    echo "SESSMON_SVC: Monitor exited, restarting in 5 seconds..."
    sleep 5
done

# Final comment line to make sure last line of "code" ends with a new line character.
