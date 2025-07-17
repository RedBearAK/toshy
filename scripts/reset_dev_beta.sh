#!/usr/bin/env bash

# Version="20250717"

# Accept expected commit hash as argument
EXPECTED_MAIN_HASH="${1}"
# LOCAL_REPO="$(pwd)"
# FOLDER_NAME="$(basename "$LOCAL_REPO")"

# Define the branches
DEV_BRANCH="dev_beta"
MAIN_BRANCH="main"

# Check if expected hash was provided, if not prompt for it
if [ -z "$EXPECTED_MAIN_HASH" ]; then
    echo ""
    echo "=== SAFE RESET: dev_beta → main ==="
    echo ""
    echo "To prevent code loss due to GitHub replication delays, this script"
    echo "requires the expected commit hash from the GitHub web UI."
    echo ""
    echo "Steps:"
    echo "  1. Go to your GitHub repo main branch"
    echo "  2. Copy the latest commit hash (full or first 7+ characters)"
    echo "  3. Enter it below"
    echo ""
    # shellcheck disable=SC2162     # The '-r' argument is not relevant
    read -p "Enter expected main branch commit hash: " EXPECTED_MAIN_HASH
    
    if [ -z "$EXPECTED_MAIN_HASH" ]; then
        echo "No commit hash provided. Exiting."
        exit 1
    fi
fi

# Trim whitespace and validate hash format
EXPECTED_MAIN_HASH=$(echo "$EXPECTED_MAIN_HASH" | tr -d '[:space:]')
if ! [[ "$EXPECTED_MAIN_HASH" =~ ^[a-fA-F0-9]{7,40}$ ]]; then
    echo ""
    echo "ERROR: Invalid commit hash format."
    echo "       Expected: 7-40 hexadecimal characters"
    echo "       Got: '$EXPECTED_MAIN_HASH'"
    exit 1
fi

echo "Attempting to reset '$DEV_BRANCH' to '$MAIN_BRANCH' state..."
echo "Expected main commit: $EXPECTED_MAIN_HASH"

# Already in the correct directory (current working directory)

# Check that folder is a git repo
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "The specified directory is not a git repository."
    exit 1
fi

# Check that repo has branches matching main and dev branch variables
if ! git show-ref --verify --quiet "refs/heads/$MAIN_BRANCH"; then
    echo "The repository does not have a branch named '$MAIN_BRANCH'."
    exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/$DEV_BRANCH"; then
    echo "The repository does not have a branch named '$DEV_BRANCH'."
    exit 1
fi

# Check current branch - script must be run from dev_beta
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$DEV_BRANCH" ]; then
    echo ""
    echo "ERROR: This script is designed to be run from the '$DEV_BRANCH' branch only."
    echo "       Current branch: $current_branch"
    echo "       Please checkout '$DEV_BRANCH' first and run again."
    echo ""
    exit 1
fi

# Fetch latest changes from origin (prune branches that have been removed from remote)
echo "Fetching latest changes from origin..."
if ! git fetch origin --prune; then
    echo ""
    echo "ERROR: Failed to fetch from origin. Check your network connection."
    echo "       Make sure you can access GitHub and try again."
    exit 1
fi

# Switch to main and pull to get latest
echo "Checking out main branch and pulling latest changes..."
git checkout $MAIN_BRANCH || { echo "Failed to checkout $MAIN_BRANCH. Exiting."; exit 1; }
git pull origin $MAIN_BRANCH || { echo "Failed to pull latest changes to $MAIN_BRANCH. Exiting."; exit 1; }

# Verify main branch has the expected commit hash
current_main_hash=$(git rev-parse HEAD)
current_main_short=$(git rev-parse --short HEAD)
expected_short=$(echo "$EXPECTED_MAIN_HASH" | cut -c1-7)

echo ""
echo "=== COMMIT HASH VERIFICATION ==="
echo "Expected: $EXPECTED_MAIN_HASH"
echo "Current:  $current_main_hash"

if [[ ! "$current_main_hash" == "$EXPECTED_MAIN_HASH"* ]]; then
    echo ""
    echo "❌ ERROR: Main branch commit hash mismatch!"
    echo "   Expected: $expected_short..."
    echo "   Got:      $current_main_short"
    echo ""
    echo "This indicates GitHub replication delay or you provided the wrong hash."
    echo "Solutions:"
    echo "  1. Wait 30-60 seconds and try again"
    echo "  2. Verify the expected hash from GitHub web UI"
    echo "  3. Check if someone else pushed to main"
    echo ""
    echo "Latest commits in main:"
    git log --oneline -5
    exit 1
fi

echo "✅ Commit hash verified! Main branch is at expected state."

# Switch back to dev_beta
git checkout $DEV_BRANCH || { echo "Failed to switch back to $DEV_BRANCH. Exiting."; exit 1; }

# Check for any local changes or uncommitted files
if ! git diff-index --quiet HEAD --; then
    echo ""
    echo "There are uncommitted changes. Please commit or stash them before running this script."
    exit 1
fi

# Check if DEV_BRANCH is ahead of MAIN_BRANCH
ahead_count=$(git rev-list --count origin/$MAIN_BRANCH..$DEV_BRANCH)

if [ "$ahead_count" -ne 0 ]; then
    echo ""
    echo "The '$DEV_BRANCH' branch is AHEAD of '$MAIN_BRANCH' by $ahead_count commits."
    echo "Current uncommitted/unmerged changes will be LOST if branch is reset."
    echo "Consider reviewing these changes before resetting."
    exit 1
fi

# Check that DEV_BRANCH is behind MAIN_BRANCH
behind_count=$(git rev-list --count $DEV_BRANCH..origin/$MAIN_BRANCH)

if [ "$behind_count" -gt 0 ]; then
    echo ""
    echo "=== RESET CONFIRMATION ==="
    echo "Branch '$DEV_BRANCH' is BEHIND '$MAIN_BRANCH' by $behind_count commits."
    echo ""
    echo "This will:"
    echo "  • Hard reset '$DEV_BRANCH' to match '$MAIN_BRANCH' (commit $expected_short)"
    echo "  • Force push to origin/$DEV_BRANCH"
    echo "  • PERMANENTLY DELETE any commits in '$DEV_BRANCH' not in '$MAIN_BRANCH'"
    echo ""
    echo "Lost commits:"
    git log --oneline $MAIN_BRANCH..$DEV_BRANCH
    echo ""
    echo "WARNING: This operation cannot be undone!"
    read -p "Type 'DELETE' to confirm you want to proceed: " -r

    if [[ "$REPLY" != "DELETE" ]]; then
        echo ""
        echo "Reset cancelled by user."
        exit 1
    fi

    # Perform the hard reset
    echo ""
    echo "Performing hard reset..."
    git reset --hard origin/$MAIN_BRANCH || { echo "Reset failed. Exiting."; exit 1; }

    # Push the reset to remote
    echo "Force pushing to origin..."
    git push --force || { echo "Failed to push changes. Exiting."; exit 1; }

    # Verify the reset worked
    final_hash=$(git rev-parse HEAD)
    if [[ "$final_hash" == "$current_main_hash"* ]]; then
        echo ""
        echo "✅ Reset complete and verified!"
        echo "   '$DEV_BRANCH' now matches '$MAIN_BRANCH' at commit $expected_short"
    else
        echo ""
        echo "⚠️  Reset completed but verification failed."
        echo "   Please check the branch state manually."
        echo ""
        echo "Recovery options if something went wrong:"
        echo "  • Check 'git reflog' to find previous commit"
        echo "  • Use 'git reset --hard <previous_commit>' to restore"
        echo "  • Contact support if you need help recovering"
    fi
    exit 0
else
    echo "The '$DEV_BRANCH' branch is not behind '$MAIN_BRANCH'. No reset needed."
    exit 0
fi
