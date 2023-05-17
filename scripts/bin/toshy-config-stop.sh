#!/usr/bin/env bash


# Stop the Toshy manual scripts. First stop session monitor script so that it 
# doesn't try to restart the config script. Then stop config script. 

# Check if the script is being run as root
if [[ $EUID -eq 0 ]]; then
    echo "This script must not be run as root"
    exit 1
fi

# Check if $USER and $HOME environment variables are not empty
if [[ -z $USER ]] || [[ -z $HOME ]]; then
    echo "\$USER and/or \$HOME environment variables are not set. We need them."
    exit 1
fi

echo -e "Stopping Toshy services/script...\n"

toshy-services-stop

/usr/bin/pkill -f "bin/keyszer"
/usr/bin/pkill -f "toshy-config-start"
