#!/usr/bin/env bash

# Echoes the versions of various Toshy components. 

# shellcheck disable=SC1091
source "$HOME/.config/toshy/.venv/bin/activate"

python3 ~/.config/toshy/scripts/toshy_versions.py
