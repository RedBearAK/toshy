#!/bin/bash


source /etc/os-release

centos_7=false
centos_stream_8=false

# Determining CentOS version
if [[ "$VERSION_ID" == "7" ]]; then
    centos_7=true
elif [[ "$VERSION_ID" == "8" ]]; then
    centos_stream_8=true
else
    echo "Not CentOS 7 or CentOS Stream 8. Script unnecessary or incompatible."
    echo "Run the main Toshy installer script. (setup_toshy.py)"
    exit 0
fi

echo "Updating CentOS repos to use the CentOS Vault (if necessary)..."

# Define the repository directory
repo_dir="/etc/yum.repos.d"

# Updating CentOS repos to use the CentOS Vault only if necessary
echo "Checking and updating CentOS repository configurations..."

for repo_file in "${repo_dir}"/*.repo; do
    # Check and update mirror.centos.org to vault.centos.org
    if grep -q 'mirror.centos.org' "$repo_file"; then
        echo "Updating mirror to CentOS Vault in $repo_file"
        sudo sed -i 's/mirror.centos.org/vault.centos.org/g' "$repo_file"
    fi

    # Check and uncomment baseurl
    if grep -q '^#.*baseurl=http' "$repo_file"; then
        echo "Uncommenting baseurl in $repo_file"
        sudo sed -i 's/^#.*baseurl=http/baseurl=http/g' "$repo_file"
    fi

    # Check and comment out mirrorlist
    if grep -q '^mirrorlist=http' "$repo_file"; then
        echo "Commenting out mirrorlist in $repo_file"
        sudo sed -i 's/^mirrorlist=http/#&/' "$repo_file"
    fi
done

echo "Repository files checked and updated (if necessary)."

# Clearing and refreshing YUM cache
if command -v yum &> /dev/null
then
    echo "Refreshing YUM cache..."
    sudo yum clean all
    sudo yum makecache
    echo "YUM cache has been refreshed."
fi

if $centos_7; then

    echo "Detected CentOS 7. Checking for Python3 and DNF..."

    # Install python3 if not present
    if ! command -v python3 &> /dev/null; then
        echo "Installing Python3..."
        sudo yum install -y python3
    fi

    # Install dnf if not present
    if ! command -v dnf &> /dev/null; then
        echo "Installing DNF..."
        sudo yum install -y dnf
    fi

elif $centos_stream_8; then
    echo "Detected CentOS Stream 8. No other special prep necessary..."
fi

# Clearing and refreshing DNF cache
if command -v dnf &> /dev/null
then
    echo "Refreshing DNF cache..."
    sudo dnf clean all
    sudo dnf makecache
    echo "DNF cache has been refreshed."
fi

echo "Your CentOS system is fully prepped for installing Toshy."
echo "You can now run the main installer script. (setup_toshy.py)"
