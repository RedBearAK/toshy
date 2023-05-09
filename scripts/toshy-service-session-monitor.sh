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


USER="$(whoami)"
STOPPED_BY_ME="false"


# give the session info and config service a bit of time to stabilize
sleep 2

while true
    do

        sleep 3

        # get the current session ID (number)
        SESSION_ID="$(/usr/bin/loginctl session-status | head -n1 | cut -d' ' -f1)"

        # check the loginctl show-session metadata to see if it's "Active" (yes/no)
        SESSION_IS_ACTIVE="$(/usr/bin/loginctl show-session "$SESSION_ID" -p Active --value)"

        # check the status of Toshy Config service
        SERVICE_STATUS="$(/usr/bin/systemctl --user is-active toshy-config.service)"

        # if session is active, try to start Toshy Config service (only if inactive)
        if [[ "$SESSION_IS_ACTIVE" == "yes" ]]
            then
                # echo "Session for user $USER is active right now. $(date +%F_%H%M%S)" | tee -a /tmp/user-$USER.txt
                if [[ "$SERVICE_STATUS" == "inactive" ]]
                    then
                        # only start Toshy Config service if we stopped it due to inactive session (below)
                        if [[ "$STOPPED_BY_ME" == "true" ]]
                            then
                                /usr/bin/systemctl --user start toshy-config.service > /dev/null 2>&1
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
                        echo "SESSMON: Stopping config service because session is inactive."
                        /usr/bin/systemctl --user stop toshy-config.service > /dev/null 2>&1
                        STOPPED_BY_ME="true"
                fi
        fi

        sleep 3 # no need to check too frequently

done
