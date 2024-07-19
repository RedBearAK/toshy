#!/usr/bin/env bash

# This script is a simplified way to run the full gdbus call on a 
# specific D-Bus interface.

# Base gdbus command for invoking org.kde.KGlobalAccel methods
gdbus_base="gdbus call --session --dest=org.kde.kglobalaccel --object-path=/kglobalaccel --method=org.kde.KGlobalAccel."

# Separate output from previous command prompt for readability
echo

# Check for bash version for associative array support
if ((BASH_VERSINFO[0] < 4)); then
    echo "This script requires Bash version 4.0 or higher."
    exit 1
fi

safe_shutdown() {
    if [ -z "$1" ]; then
        exit_code=0
    else
        exit_code=$1
    fi
    echo
    exit "$exit_code"
}

# Declare an associative array to hold valid method names
declare -A valid_methods=(
    [actionList]=1
    [activateGlobalShortcutContext]=1
    [allActionsForComponent]=1
    [allComponents]=1
    [allMainComponents]=1
    [blockGlobalShortcuts]=1
    [defaultShortcutKeys]=1
    [doRegister]=1
    [getComponent]=1
    [globalShortcutAvailable]=1
    [globalShortcutsByKey]=1
    [setForeignShortcutKeys]=1
    [setInactive]=1
    [setShortcutKeys]=1
    [shortcutKeys]=1
    [unregister]=1
    [yourShortcutsChanged]=1
)

# Function to display help information ("here document" format)
show_help() {
    cat << EOF
Usage: $0 <KGlobalAccel_method_name> [method_args...]

Methods of org.kde.KGlobalAccel D-Bus interface (no deprecated):
NAME                           TYPE    SIGNATURE  RESULT/VALUE 
actionList                     method  (ai)       as           
activateGlobalShortcutContext  method  ss         -            
allActionsForComponent         method  as         aas          
allComponents                  method  -          ao           
allMainComponents              method  -          aas          
blockGlobalShortcuts           method  b          -            
---------------------------------------------------------------
defaultShortcutKeys            method  as         a(ai)        
doRegister                     method  as         -            
getComponent                   method  s          o            
---------------------------------------------------------------
globalShortcutAvailable        method  (ai)s      b            
globalShortcutsByKey           method  (ai)(i)    a(ssssssaiai)
---------------------------------------------------------------
setForeignShortcutKeys         method  asa(ai)    -            
setInactive                    method  as         -            
---------------------------------------------------------------
setShortcutKeys                method  asa(ai)u   a(ai)        
---------------------------------------------------------------
shortcutKeys                   method  as         a(ai)        
---------------------------------------------------------------
unregister                     method  ss         b            
---------------------------------------------------------------
yourShortcutsChanged           signal  asa(ai)    -            
EOF
}

# Check if at least one argument is provided
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

# Check if the method name is valid
method_name="$1"
method_name_lower=$(echo "$method_name" | tr '[:upper:]' '[:lower:]')
matched_methods=()

if [[ -z "${valid_methods[$method_name]}" ]]; then
    # Perform a case-insensitive substring search
    for method in "${!valid_methods[@]}"; do
        method_lower=$(echo "$method" | tr '[:upper:]' '[:lower:]')
        if [[ "$method_lower" == *"$method_name_lower"* ]]; then
            matched_methods+=("$method")
        fi
    done

    if [[ ${#matched_methods[@]} -gt 0 ]]; then
        echo "Error: Invalid exact method name '$method_name'. Deprecated or typo."
        echo
        echo "Did you mean:"
        echo
        for suggestion in "${matched_methods[@]}"; do
            # echo "  - $suggestion"
            show_help | grep "NAME\|$suggestion"
        done
    else
        echo "Error: Invalid method name '$method_name' and no similar methods found."
        show_help
    fi
    safe_shutdown 1
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
