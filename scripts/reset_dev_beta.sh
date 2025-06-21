#!/usr/bin/env bash

# Accept a repository path as an optional argument
LOCAL_REPO="${1:-$(pwd)}"
FOLDER_NAME="$(basename "$LOCAL_REPO")"

# Define the branches
DEV_BRANCH="dev_beta"
MAIN_BRANCH="main"

echo "Attempting to reset '$FOLDER_NAME' git repo '$DEV_BRANCH' to '$MAIN_BRANCH' state..."

cd "$LOCAL_REPO" || { echo "Failed to change directory to $LOCAL_REPO"; exit 1; }

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

# Check current branch
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$DEV_BRANCH" ]; then
    echo "Switching to '$DEV_BRANCH' branch..."
    git checkout $DEV_BRANCH || { echo "Failed to switch to $DEV_BRANCH. Exiting."; exit 1; }
fi

# Fetch latest changes from origin (prune branches that have been removed from remote)
git fetch origin --prune || { echo "Failed to fetch and prune changes from origin. Exiting."; exit 1; }

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
    echo "Branch '$DEV_BRANCH' is BEHIND '$MAIN_BRANCH' by $behind_count commits."
    echo "Hard resetting '$DEV_BRANCH' to match '$MAIN_BRANCH'..."
    echo ""
    echo "WARNING: This will force reset '$DEV_BRANCH' to '$MAIN_BRANCH' and push to remote."
    echo "         This cannot be undone."
    read -p "Are you sure you want to proceed? (yes/NO) " -r
    REPLY_LOWER=$(echo "$REPLY" | tr '[:upper:]' '[:lower:]')  # Convert to lowercase

    if [[ "$REPLY_LOWER" != "yes" ]]
    then
        echo ""
        echo "Hard reset not confirmed by the user. Aborting."
        exit 1
    fi

    # Perform the hard reset
    git reset --hard origin/$MAIN_BRANCH || { echo "Reset failed. Exiting."; exit 1; }

    # Push the reset to remote
    echo "Pushing changes to remote..."
    git push --force || { echo "Failed to push changes. Exiting."; exit 1; }

    echo "Reset complete."
    exit 0
else
    echo "The '$DEV_BRANCH' branch is not behind '$MAIN_BRANCH'. No reset needed."
    exit 0
fi
