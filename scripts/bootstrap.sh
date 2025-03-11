#!/bin/bash

# Improved Toshy Installation Bootstrap Script
# https://github.com/RedBearAK/toshy

set -e  # Exit on error

# Force unbuffered output
exec > >(cat) 2>&1

# Store the original directory
ORIGINAL_DIR="$(pwd)"

# Default branch
DEFAULT_BRANCH="main"
SUGGESTED_BRANCH="dev_beta"

# Function to ensure echoes are visible
echo_unbuffered() {
    echo "$@" >&2
}

# Get branch from user input
get_branch() {
    local branch
    
    # Force output to stderr to ensure it's visible when piped
    echo_unbuffered
    echo_unbuffered "Which branch would you like to install from?"
    echo_unbuffered "1) $DEFAULT_BRANCH (default/stable)"
    echo_unbuffered "2) $SUGGESTED_BRANCH (development/beta)"
    echo_unbuffered "3) Enter custom branch name"
    echo_unbuffered
    
    # Make sure output is flushed before prompt
    sleep 0.1
    
    # Use /dev/tty for interactive input when possible
    if [ -t 0 ]; then
        read -r -p "Enter choice [1-3, default=1]: " choice
    else
        read -r -p "Enter choice [1-3, default=1]: " choice </dev/tty
    fi
    
    case "$choice" in
        "" | "1")
            branch="$DEFAULT_BRANCH"
            ;;
        "2")
            branch="$SUGGESTED_BRANCH"
            ;;
        "3")
            if [ -t 0 ]; then
                read -r -p "Enter custom branch name: " custom_branch
            else
                read -r -p "Enter custom branch name: " custom_branch </dev/tty
            fi
            branch="${custom_branch:-$DEFAULT_BRANCH}"
            ;;
        *)
            echo_unbuffered "Invalid choice, using default ($DEFAULT_BRANCH)"
            branch="$DEFAULT_BRANCH"
            ;;
    esac
    
    echo_unbuffered
    echo_unbuffered "Selected branch: $branch"
    echo_unbuffered
    echo "$branch"
}

# Create a unique folder name with timestamp
FILE_NAME="toshy_$(date +%Y%m%d_%H%M)"
DOWNLOAD_DIR="$HOME/Downloads"

# Get branch selection
echo_unbuffered
echo_unbuffered
echo_unbuffered "Starting Toshy branch selection..."
BRANCH=$(get_branch)

URL="https://github.com/RedBearAK/toshy/archive/refs/heads/$BRANCH.zip"
TOSHY_DIR="$DOWNLOAD_DIR/$FILE_NAME/toshy-$BRANCH"

echo_unbuffered "Starting Toshy download process..."
echo_unbuffered "Using branch: $BRANCH"

# Create the Downloads directory if it doesn't exist
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

# Download the zip file using curl or wget
echo_unbuffered "Downloading Toshy from GitHub..."
echo_unbuffered
if ! (curl -L "$URL" -o "$FILE_NAME.zip" || wget "$URL" -O "$FILE_NAME.zip"); then
    echo_unbuffered "Download failed. Please check your internet connection or verify the branch name exists."
    exit 1
fi

# Create directory and extract the zip file
echo_unbuffered
echo_unbuffered "Extracting files..."
echo_unbuffered
mkdir -p "$FILE_NAME"
if ! unzip -o "$FILE_NAME.zip" -d "$FILE_NAME"; then
    echo_unbuffered "Extraction failed. Please make sure 'unzip' is installed."
    exit 1
fi

# Navigate to the setup directory
cd "$FILE_NAME/toshy-$BRANCH"

# Ask if additional options should be passed to the setup script
echo_unbuffered
sleep 0.1

# Use /dev/tty for interactive input when possible
if [ -t 0 ]; then
    read -r -p "Would you like to specify additional options for the setup script? [y/N]: " ADD_OPTIONS
else
    read -r -p "Would you like to specify additional options for the setup script? [y/N]: " ADD_OPTIONS </dev/tty
fi

ADD_OPTIONS=$(echo "$ADD_OPTIONS" | tr '[:upper:]' '[:lower:]')

INSTALL_ARGS="install"

show_install_options() {
    echo_unbuffered
    echo_unbuffered "Available install options:"
    echo_unbuffered "  --override-distro=DISTRO  Override auto-detection of distro"
    echo_unbuffered "  --barebones-config        Install with mostly empty/blank keymapper config file"
    echo_unbuffered "  --skip-native             Skip the install of native packages"
    echo_unbuffered "  --no-dbus-python          Avoid installing dbus-python pip package"
    echo_unbuffered "  --dev-keymapper[=BRANCH]  Install the development branch of the keymapper"
    echo_unbuffered "  --fancy-pants             See README for more info on this option"
    echo_unbuffered
}

if [[ "$ADD_OPTIONS" == "y" || "$ADD_OPTIONS" == "yes" ]]; then
    show_install_options
    sleep 0.1
    
    if [ -t 0 ]; then
        read -r -p "Enter options (separated by spaces): " USER_OPTIONS
    else
        read -r -p "Enter options (separated by spaces): " USER_OPTIONS </dev/tty
    fi
    
    INSTALL_ARGS="install $USER_OPTIONS"
fi

# Define the Ctrl+C trap function
ctrl_c() {
    echo_unbuffered
    echo_unbuffered "Installation paused."
    echo_unbuffered
    echo_unbuffered "To navigate to the Toshy directory and run the setup manually, use:"
    echo_unbuffered "  cd \"$TOSHY_DIR\""
    echo_unbuffered
    exit 0
}

# Set up the trap before the countdown
trap ctrl_c INT

echo_unbuffered
echo_unbuffered "==================================================================="
echo_unbuffered "Toshy has been downloaded and extracted to:"
echo_unbuffered "  $TOSHY_DIR"
echo_unbuffered
echo_unbuffered "Setup will run with command:"
echo_unbuffered "  ./setup_toshy.py $INSTALL_ARGS"
echo_unbuffered
echo_unbuffered "Other commands are also available in the full setup script:"
echo_unbuffered "  ./setup_toshy.py --help           (to see all available commands)"
echo_unbuffered "==================================================================="
echo_unbuffered

# Display command and confirmation prompt
echo_unbuffered "Ready to execute:"
echo_unbuffered "  ./setup_toshy.py $INSTALL_ARGS"
echo_unbuffered
echo_unbuffered "Options:"
echo_unbuffered "  Y - Continue with installation (default)"
echo_unbuffered "  e - Edit installation options"
echo_unbuffered "  q - Quit without installing"
echo_unbuffered

# Simple confirmation prompt
while true; do
    if [ -t 0 ]; then
        read -r -p "Continue? [Y/e/q]: " confirm
    else
        read -r -p "Continue? [Y/e/q]: " confirm </dev/tty
    fi
    
    # Convert to lowercase
    confirm=$(echo "$confirm" | tr '[:upper:]' '[:lower:]')
    
    # Default to yes if empty
    if [ -z "$confirm" ] || [ "$confirm" = "y" ]; then
        echo_unbuffered "Executing installation now..."
        break
    elif [ "$confirm" = "e" ]; then
        show_install_options
        
        # Clear previous options and get new ones
        if [ -t 0 ]; then
            read -r -p "Enter options (separated by spaces): " USER_OPTIONS
        else
            read -r -p "Enter options (separated by spaces): " USER_OPTIONS </dev/tty
        fi
        
        INSTALL_ARGS="install $USER_OPTIONS"
        echo_unbuffered
        echo_unbuffered "Updated command:"
        echo_unbuffered "  ./setup_toshy.py $INSTALL_ARGS"
        echo_unbuffered
    elif [ "$confirm" = "q" ]; then
        echo_unbuffered "Installation cancelled."
        echo_unbuffered
        echo_unbuffered "To navigate to the Toshy directory and run the setup manually, use:"
        echo_unbuffered "  cd \"$TOSHY_DIR\""
        echo_unbuffered
        exit 0
    else
        echo_unbuffered "Invalid option. Please enter Y, e, or q."
    fi
done

echo_unbuffered

# Run the setup script with collected arguments
if ! ./setup_toshy.py $INSTALL_ARGS; then
    echo_unbuffered "Setup script execution failed."
    exit 1
fi

echo_unbuffered
echo_unbuffered "Toshy bootstrap-based installation completed successfully!"
echo_unbuffered

# Return to original directory
cd "$ORIGINAL_DIR"
