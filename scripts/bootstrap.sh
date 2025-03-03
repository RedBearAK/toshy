#!/bin/bash

# Simple Toshy Installation Bootstrap Script
# https://github.com/RedBearAK/toshy

set -e  # Exit on error

# Store the original directory
ORIGINAL_DIR="$(pwd)"

# Create a unique folder name with timestamp
FILE_NAME="toshy_$(date +%Y%m%d_%H%M)"
DOWNLOAD_DIR="$HOME/Downloads"
URL="https://github.com/RedBearAK/toshy/archive/refs/heads/main.zip"
TOSHY_DIR="$DOWNLOAD_DIR/$FILE_NAME/toshy-main"

echo "Starting Toshy download process..."

# Create the Downloads directory if it doesn't exist
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

# Download the zip file using curl or wget
echo "Downloading Toshy from GitHub..."
if ! (curl -L "$URL" -o "$FILE_NAME.zip" || wget "$URL" -O "$FILE_NAME.zip"); then
    echo "Download failed. Please check your internet connection."
    exit 1
fi

# Create directory and extract the zip file
echo "Extracting files..."
mkdir -p "$FILE_NAME"
if ! unzip -o "$FILE_NAME.zip" -d "$FILE_NAME"; then
    echo "Extraction failed. Please make sure 'unzip' is installed."
    exit 1
fi

# Navigate to the setup directory
cd "$FILE_NAME/toshy-main"

# Define the Ctrl+C trap function
# This handles the SIGINT (Ctrl+C) signal
ctrl_c() {
    echo
    echo "Installation paused."
    echo
    echo "To navigate to the Toshy directory and run the setup manually, use:"
    echo "  cd \"$TOSHY_DIR\""
    echo
    exit 0
}

# Set up the trap before the countdown
trap ctrl_c INT

echo
echo "==================================================================="
echo "Toshy has been downloaded and extracted to:"
echo "  $TOSHY_DIR"
echo
echo "To install Toshy with default settings, run (or wait 10 sec):"
echo "  ./setup_toshy.py install"
echo
echo "Or you can use custom install flags:"
echo "  ./setup_toshy.py install --help   (to see all available options)"
echo
echo "Other commands are also available in the full setup script:"
echo "  ./setup_toshy.py --help           (to see all available commands)"
echo "==================================================================="
echo

# Countdown with option to proceed automatically
echo "The default installation will begin in 10 seconds..."
echo "Press Ctrl+C now to stop and run the setup command manually with custom flags"
echo

# Countdown timer
for i in {10..1}; do
    echo -ne "\rStarting default install with no flags in $i seconds... "
    sleep 1
done

echo -e "\rExecuting default installation now...      "
echo

# Run the setup script with default settings
if ! ./setup_toshy.py install; then
    echo "Setup script execution failed."
    exit 1
fi

echo
echo "Toshy bootstrap-based installation completed successfully!"
echo

# Return to original directory
cd "$ORIGINAL_DIR"
