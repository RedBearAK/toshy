#!/bin/env bash

# Do this in ExecStartPre to help the config service script


# shellcheck disable=SC2034
for _ in {1..10}; do
    if systemctl --quiet is-active graphical-session.target; then
        break
    elif [ -f "${XDG_RUNTIME_DIR}/toshy-service-config.start" ]; then
        break
    elif [ -n "$XDG_SESSION_TYPE" ]; then
        break
    fi
    sleep 0.5
done
