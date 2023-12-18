#!/usr/bin/env bash

# Installs Cinnamon shell extension to get focused window info

EXT_NAME="ToshyFocusedWindow@toshy.app"
EXT_DIR="$HOME/.local/share/cinnamon/extensions/${EXT_NAME}"

mkdir -p "${EXT_DIR}"
cp ./metadata.json "${EXT_DIR}"
cp ./extension.js "${EXT_DIR}"

CIN_EXTS="org.cinnamon enabled-extensions"

if command -v gsettings &> /dev/null; then
    # shellcheck disable=SC2086
    CURRENT_EXTS=$(gsettings get ${CIN_EXTS})
    if [[ $CURRENT_EXTS != *"'${EXT_NAME}'"* ]]; then

        if [ "${CURRENT_EXTS}" == "@as []" ]; then
            # The list is empty; add the extension without leading comma and space
            UPDATED_EXTS="['${EXT_NAME}']"
        else
            # The list is not empty; add the extension with leading comma and space
            UPDATED_EXTS="${CURRENT_EXTS%]}, '${EXT_NAME}']"
        fi

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
