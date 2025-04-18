#!/usr/bin/env bash


# Monitor whether the user's desktop session is "Active" according to loginctl.

# Should handle the case of user remaining "logged in" but using "switch user"
# to let another user log in to their own desktop and use the screen. 
# We don't want the keymapper to interfere with the other user's input or 
# with their separate usage of this or any other keymapper. 

if command -v loginctl >/dev/null 2>&1; then
    : # no-op operator
else
    echo "The \"loginctl\" command is not available. Toshy session monitor will not work here."
    exit 1
fi

if command -v systemctl >/dev/null 2>&1; then
    : # no-op operator
else
    echo "The \"systemctl\" command is not available. Toshy session monitor will not work here."
    exit 1
fi


# If XDG_RUNTIME_DIR is not set or is empty
if [ -z "${XDG_RUNTIME_DIR}" ]; then
    echo "SESSMON_SVC: XDG_RUNTIME_DIR not set. Unable to determine where to store the marker file."
    # exit 1
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


# give the session info and config service a bit of time to stabilize
sleep 2

# check that loginctl is actually going to work right now
retry=0
while true; do
    # suppress all output of command, then check exit status
    loginctl session-status >/dev/null 2>&1
    status=$?
    if [[ $status -eq 0 ]]; then
        # The command succeeded, so break out of the loop
        break
    else
        # The command failed, so wait for a bit and then try again
        sleep 2
        ((retry++))
        if [[ $retry -gt 10 ]]; then
            echo "SESSMON_SVC: Attempt to use loginctl failed after 10 attempts. Exiting."
            exit 1
        fi
    fi
done


while true
    do

        sleep 2

        # Get a count of all sessions for the user.
        # We are trying to check whether user is completely logged out.
        # Systemd user services don't automatically stop when user logs out!
        SESSION_COUNT=$(loginctl list-sessions -p UserName | grep -c "${USER}")

        # If no sessions are found, stop all the Toshy user services
        if [ "$SESSION_COUNT" -eq 0 ]
            then
                systemctl --user stop toshy-config.service
                systemctl --user stop toshy-kwin-dbus.service
                # User is logged out entirely if there are no sessions, 
                # so stop session monitor too:
                systemctl --user stop toshy-session-monitor.service
        fi

        # get the current session ID (number)
        SESSION_ID="$(loginctl session-status | head -n1 | cut -d' ' -f1)"

        # check the loginctl show-session metadata to see if it's "Active" (yes/no)
        SESSION_IS_ACTIVE="$(loginctl show-session "$SESSION_ID" -p Active --value)"

        # check the status of Toshy Config service
        SERVICE_STATUS="$(systemctl --user is-active toshy-config.service)"

        # if session is active, try to start Toshy Config service (only if inactive)
        if [[ "$SESSION_IS_ACTIVE" == "yes" ]]
            then
                # echo "Session for user $USER is active right now. $(date +%F_%H%M%S)" | tee -a /tmp/user-$USER.txt
                if [[ "$SERVICE_STATUS" == "inactive" ]]
                    then
                        # only start Toshy Config service if we stopped it due to inactive session (below)
                        if [[ "$STOPPED_BY_ME" == "true" ]]
                            then
                                # start/restart KWIN D-Bus service (adapt to switching DEs w/out reboot)
                                systemctl --user restart toshy-kwin-dbus.service > /dev/null 2>&1
                                sleep 0.5
                                systemctl --user restart toshy-config.service > /dev/null 2>&1
                                STOPPED_BY_ME="false"
                        fi
                fi
        fi

        # if session is NOT active, try to stop Toshy Config service (only if active)
        if [[ "$SESSION_IS_ACTIVE" == "no" ]]
            then
                # echo "Session for user $USER is NOT active right now. $(date +%F_%H%M%S)" | tee -a /tmp/user-$USER.txt
                if [[ "$SERVICE_STATUS" == "active" ]]
                    then
                        echo "SESSMON_SVC: Stopping config service because session is inactive."
                        systemctl --user stop toshy-config.service > /dev/null 2>&1
                        # also stop KWIN D-Bus service (unnecessary if config is not running)
                        systemctl --user stop toshy-kwin-dbus.service > /dev/null 2>&1
                        STOPPED_BY_ME="true"
                fi
        fi

done
