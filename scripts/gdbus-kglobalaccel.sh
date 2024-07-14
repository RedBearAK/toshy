#!/usr/bin/env bash

# Base gdbus command for invoking org.kde.KGlobalAccel methods
gdbus_base="gdbus call --session --dest=org.kde.kglobalaccel --object-path=/kglobalaccel --method=org.kde.KGlobalAccel."

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <KGlobalAccel_method_name> [method_args...]"
    exit 1
fi

# Extract the method name and shift the arguments
method_name=$1
shift

# Build the complete gdbus command
command="${gdbus_base}${method_name}"

# Add each remaining CLI argument to the command
for arg in "$@"; do
    # Append each argument correctly quoted
    # shellcheck disable=SC2001
    command+=" \"$(echo "$arg" | sed 's/"/\\"/g')\""
done

# Use 'eval' to correctly interpret the constructed command string 
# with preserved internal quotes.
# Use 'sed' on result to strip excess (result,) formatting from 
# 'gdbus' to make result easier to use as args to other methods.
result=$(eval "$command" | sed -e 's/^(\(.*\),)$/\1/')
echo "$result"
