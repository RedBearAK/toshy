#!/usr/bin/env bash

# Uninstalls Cinnamon shell extension to get focused window info

EXT_NAME="ToshyFocusedWindow@toshy.app"
EXT_DIR="$HOME/.local/share/cinnamon/extensions/${EXT_NAME}"

if [ -d "${EXT_DIR}" ]; then
    rm -rf "${EXT_DIR}"
fi

CIN_EXTS="org.cinnamon enabled-extensions"

if command -v gsettings &> /dev/null; then
    # shellcheck disable=SC2086
    CURRENT_EXTS=$(gsettings get ${CIN_EXTS})
    if [[ $CURRENT_EXTS == *"'${EXT_NAME}'"* ]]; then

        # Remove the extension with preceding comma and space
        UPDATED_EXTS="${CURRENT_EXTS/, \'${EXT_NAME}\'/}"
        # Remove the extension if it's the only item
        UPDATED_EXTS="${UPDATED_EXTS/\'${EXT_NAME}\'/}"

        # shellcheck disable=SC2086
        gsettings set ${CIN_EXTS} "${UPDATED_EXTS}"

    fi
else
    echo "The 'gsettings' command was not found. Is this a Cinnamon environment?"
fi

# Restart Cinnamon (optional, but recommended to apply changes)
# This is done by pressing Alt+F2, typing 'r', and pressing Enter.
# Or: cinnamon --replace &
# This will probably cause all windows to close in a Wayland session.
