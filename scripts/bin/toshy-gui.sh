#!/usr/bin/env bash


# Start Toshy GUI app after activating venv
# shellcheck disable=SC1091
source "$HOME/.config/toshy/.venv/bin/activate"

/usr/bin/python3 "$HOME/.config/toshy/toshy_gui.py"

deactivate
