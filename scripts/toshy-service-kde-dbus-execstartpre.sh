#!/bin/bash

# Function to check if KWin is responding to DBus
kwin_responding() {
    # Use qdbus to send a simple command to KWin and check the response
    if [ "$(qdbus org.kde.KWin /KWin org.kde.KWin.currentDesktop)" != "" ]; then
        return 0
    else
        return 1
    fi
}

# Wait for KWin to be ready
while true; do
    if kwin_responding; then
        sleep 1
        break
    else
        sleep 1
    fi
done
