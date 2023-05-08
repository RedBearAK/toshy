#!/usr/bin/env bash


# Start Toshy GUI app after activating venv
source "$HOME/.config/toshy/.venv/bin/activate"

/usr/bin/python3 "$HOME/.config/toshy/toshy_tray.py"

deactivate
