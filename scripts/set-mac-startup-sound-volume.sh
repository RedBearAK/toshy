#!/usr/bin/env bash

echo    # blank line to start things off

# Ensure that we are root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    echo
    exit 1
fi

# Function to exit with a blank line for cleaner output
clean_exit() {
    echo
    exit "${1:-0}"  # Default to exit code 0 if not specified
}

# Check if this is an Apple system
if [ -f /sys/class/dmi/id/sys_vendor ]; then
    VENDOR=$(cat /sys/class/dmi/id/sys_vendor)
    if [[ "$VENDOR" != *"Apple"* ]]; then
        echo "Warning: This does not appear to be an Apple system."
        echo "System vendor: $VENDOR"
        echo "This script is designed for Apple computers and will have no effect on other systems."
        echo
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            clean_exit 0
        fi
    fi
fi

# Check if this is an Intel Mac (not Apple Silicon or something unknown)
if [ -f /proc/cpuinfo ] && grep -q "GenuineIntel" /proc/cpuinfo; then
    : # Intel Mac, proceed
elif [[ "$(uname -m)" == "arm64" ]] || [[ "$(uname -m)" == "aarch64" ]]; then
    echo "Warning: This appears to be an Apple Silicon Mac."
    echo "This script was designed for Intel-based Macs and likely won't work on Apple Silicon."
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        clean_exit 0
    fi
else
    echo "Warning: Unknown processor architecture: $(uname -m)"
    echo "This script was designed for Intel-based Macs and may not work on this system."
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        clean_exit 0
    fi
fi

# Function to display usage
usage() {
    SCRIPT_NAME=$(basename "$0")
    echo "Usage: "
    echo "  $SCRIPT_NAME [-d|-b|-x] <volume>"
    echo "  $SCRIPT_NAME info"
    echo "  $SCRIPT_NAME mute"
    echo "  $SCRIPT_NAME unmute"
    echo "  $SCRIPT_NAME reset"
    echo ""
    echo "Special commands:"
    echo "  info:    Display current startup volume setting"
    echo "  mute:    Set the startup volume to muted"
    echo "  unmute:  Restore previous startup volume (if preserved)"
    echo "  reset:   Delete the EFI variable (simulate NVRAM/PRAM reset)"
    echo ""
    echo "Format options:"
    echo "  -d:  Decimal format (default)"
    echo "  -b:  Binary format (e.g., 01000000)"
    echo "  -x:  Hexadecimal format (e.g., 40 or 0x40)"
    echo ""
    echo "Volume ranges:"
    echo "  Decimal:  0-127 for volume level, 128-255 to mute^"
    echo "  Binary:   00000000-01111111 for volume, 10000000-11111111 to mute^"
    echo "  Hex:      00-7F for volume level, 80-FF to mute^"
    echo ""
    echo "^ Values >128 (dec) preserve a volume level that 'unmute' will restore"
    clean_exit 1
}

# Notify user if 'efivar' command is not available
if ! command -v efivar >/dev/null 2>&1; then
    echo "There is no 'efivar' command on this system. Cannot continue."
    echo
    echo "Try installing 'efivar' package. Exiting..."
    clean_exit 0
fi

# Function to display info about current volume setting
show_info() {
    echo "SystemAudioVolume EFI Variable Information"
    echo "=========================================="
    
    # Check if the EFI variable exists
    if ! efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -p >/dev/null 2>&1; then
        echo "Status: Not found"
        echo ""
        echo "The SystemAudioVolume EFI variable is not set."
        echo "This could mean:"
        echo "  - The system is using default volume settings"
        echo "  - This is not an Apple system"
        echo "  - NVRAM/PRAM has been reset"
        clean_exit 0
    fi
    
    # Get the raw value
    RAW_VALUE=$(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null)
    
    # Extract just the last value (volume byte)
    VOLUME_DEC=$(echo "$RAW_VALUE" | awk '{print $NF}')
    
    # Convert to other formats
    VOLUME_HEX=$(printf "0x%02x" "$VOLUME_DEC")
    VOLUME_BIN=$(printf "%08d" "$(echo "obase=2; $VOLUME_DEC" | bc)")

    # Determine the meaning
    if [ "$VOLUME_DEC" -eq 128 ]; then
        STATUS="MUTED"
        PERCENTAGE="N/A"
    elif [ "$VOLUME_DEC" -gt 128 ] && [ "$VOLUME_DEC" -le 255 ]; then
        PRESERVED_VOL=$((VOLUME_DEC & 0x7F))
        STATUS="MUTED (with preserved volume: $PRESERVED_VOL)"
        PERCENTAGE="N/A"
    elif [ "$VOLUME_DEC" -ge 0 ] && [ "$VOLUME_DEC" -le 127 ]; then
        STATUS="Volume Level"
        PERCENTAGE=$(awk "BEGIN {printf \"%.1f%%\", ($VOLUME_DEC / 127.0) * 100}")
    else
        STATUS="Unknown/Invalid"
        PERCENTAGE="N/A"
    fi

    echo "Status: Found and readable"
    echo ""
    echo "Current Value:"
    echo "  Raw data: $RAW_VALUE"
    echo "  Volume byte (decimal): $VOLUME_DEC"
    echo "  Volume byte (hex):     $VOLUME_HEX"
    echo "  Volume byte (binary):  $VOLUME_BIN"
    echo ""
    echo "Interpretation:"
    echo "  Status: $STATUS"
    if [ "$PERCENTAGE" != "N/A" ]; then
        echo "  Level:  $PERCENTAGE"
    fi
    echo ""
    
    # Show the actual file path
    echo "EFI Variable Location:"
    echo "  /sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
    
    # Check immutable flag
    if lsattr "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null | grep -q "i"; then
        echo "  Immutable flag: Set (protected from modification)"
    else
        echo "  Immutable flag: Not set"
    fi
}

# Function to display "After" value with breakdown and binary representation
show_after_value() {
    local RAW_VALUE
    RAW_VALUE=$(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")

    if [[ "$RAW_VALUE" == "Not set" ]]; then
        echo "After: Not set"
    else
        local VOLUME_DEC
        local VOLUME_BIN
        local PRESERVED_VOL

        VOLUME_DEC=$(echo "$RAW_VALUE" | awk '{print $NF}')
        VOLUME_BIN=$(printf "%08d" "$(echo "obase=2; $VOLUME_DEC" | bc)")

        if [ "$VOLUME_DEC" -ge 128 ]; then
            PRESERVED_VOL=$((VOLUME_DEC & 0x7F))
            echo "After:  $VOLUME_DEC (128 + $PRESERVED_VOL)"
        else
            echo "After:  $VOLUME_DEC"
        fi
        echo "Binary: $VOLUME_BIN"
    fi
}

# Check for special commands first
if [ $# -eq 1 ]; then
    case "${1,,}" in  # Convert to lowercase for case-insensitive matching

        "info")
            show_info
            clean_exit 0
            ;;

        "mute")
            echo "Setting startup volume to: MUTED"
            echo "----------------------------------------------------------------"
            
            # Get current volume (if it exists)
            CURRENT_VALUE=$(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "7 0 0 0 64")
            CURRENT_DEC=$(echo "$CURRENT_VALUE" | awk '{print $NF}')
            
            # Extract the current volume (lower 7 bits only, removing mute bit if present)
            CURRENT_VOLUME=$((CURRENT_DEC & 0x7F))
            
            # If current volume is 0, use a reasonable default to preserve
            if [ "$CURRENT_VOLUME" -eq 0 ]; then
                CURRENT_VOLUME=64  # Default to 50%
            fi
            
            # Create muted value preserving the current volume
            MUTED_VALUE=$((128 + CURRENT_VOLUME))
            
            echo "Before: $CURRENT_VALUE"
            echo "Preserving volume level: $CURRENT_VOLUME"
            
            # Remove the immutable flag before writing
            chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null
            
            # Set to mute with preserved volume
            MUTE_HEX=$(printf "%02x" "$MUTED_VALUE")
            printf '%b' "\x07\x00\x00\x00\x${MUTE_HEX}" > "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            # Make it immutable again
            chattr +i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            # echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d)"
            show_after_value
            echo "----------------------------------------------------------------"
            clean_exit 0
            ;;

        "unmute")
            echo "Restoring previous startup volume..."
            echo "----------------------------------------------------------------"
            
            # Check if the EFI variable exists
            if ! efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -p >/dev/null 2>&1; then
                echo "SystemAudioVolume EFI variable not found."
                echo "Creating with default volume: 64 (50%)"
                PRESERVED_VOLUME=64
            else
                # Get the current value
                CURRENT_VALUE=$(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null)
                CURRENT_DEC=$(echo "$CURRENT_VALUE" | awk '{print $NF}')
                
                # Check if it's actually muted
                if [ "$CURRENT_DEC" -lt 128 ]; then
                    echo "System is not currently muted (value: $CURRENT_DEC)."
                    clean_exit 0
                fi
                
                # Extract the preserved volume (lower 7 bits)
                PRESERVED_VOLUME=$((CURRENT_DEC & 0x7F))
                
                # If the preserved volume is 0, set to a reasonable default
                if [ "$PRESERVED_VOLUME" -eq 0 ]; then
                    echo "No preserved volume found (was muted at 0)."
                    echo "Setting to default volume level: 64 (50%)"
                    PRESERVED_VOLUME=64
                fi
                
                echo "Current state: MUTED (value: $CURRENT_DEC)"
                echo "Preserved volume: $PRESERVED_VOLUME"
            fi
            
            # Remove the immutable flag before writing
            chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null
            
            # Write the preserved volume (without mute bit)
            VOLUME_HEX=$(printf "%02x" "$PRESERVED_VOLUME")
            printf '%b' "\x07\x00\x00\x00\x${VOLUME_HEX}" > "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            # Make it immutable again
            chattr +i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            # echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d)"
            show_after_value
            echo "----------------------------------------------------------------"
            echo "Volume restored to: $PRESERVED_VOLUME"
            clean_exit 0
            ;;

        "reset")
            echo "Resetting SystemAudioVolume EFI variable..."
            echo "----------------------------------------------------------------"
            echo "Before: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"
            
            # Remove the immutable flag before deleting
            chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null
            
            # Delete the EFI variable
            if rm -f "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null; then
                echo "EFI variable successfully deleted."
            else
                # Alternative method using efivar
                if efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -w < /dev/null 2>/dev/null; then
                    echo "EFI variable successfully reset using efivar."
                else
                    echo "Warning: Could not delete EFI variable. It may not exist."
                fi
            fi
            
            # echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"
            show_after_value
            echo "----------------------------------------------------------------"
            echo "Note: The system will use the default volume on next boot."
            clean_exit 0
            ;;

    esac
fi

# Default format is decimal
FORMAT="decimal"

# Parse options
while getopts "dbx" opt; do
    case $opt in
        d) FORMAT="decimal" ;;
        b) FORMAT="binary" ;;
        x) FORMAT="hex" ;;
        *) usage ;;
    esac
done

# Shift to get the volume argument
shift $((OPTIND-1))

# Check if volume argument is provided
if [ $# -ne 1 ]; then
    usage
fi

INPUT_VALUE="$1"
VOLUME=0

# Parse and validate based on format
case $FORMAT in

    decimal)
        # Check if it's a valid decimal number
        if ! [[ "$INPUT_VALUE" =~ ^[0-9]+$ ]]; then
            echo "Error: Invalid decimal format. Use only digits 0-9."
            clean_exit 1
        fi
        VOLUME=$INPUT_VALUE
        ;;

    binary)
        # Check if it's a valid binary number (only 0s and 1s)
        if ! [[ "$INPUT_VALUE" =~ ^[01]+$ ]]; then
            echo "Error: Invalid binary format. Use only 0 and 1."
            clean_exit 1
        fi
        # Check if it's not more than 8 bits
        if [ ${#INPUT_VALUE} -gt 8 ]; then
            echo "Error: Binary value must be 8 bits or less."
            clean_exit 1
        fi
        # Convert binary to decimal
        VOLUME=$((2#$INPUT_VALUE))
        ;;

    hex)
        # Remove optional 0x prefix
        HEX_VALUE="${INPUT_VALUE#0x}"
        HEX_VALUE="${HEX_VALUE#0X}"
        
        # Check if it's a valid hex number
        if ! [[ "$HEX_VALUE" =~ ^[0-9A-Fa-f]+$ ]]; then
            echo "Error: Invalid hexadecimal format. Use only 0-9, A-F, a-f."
            clean_exit 1
        fi
        # Check if it's not more than 2 hex digits (1 byte)
        if [ ${#HEX_VALUE} -gt 2 ]; then
            echo "Error: Hexadecimal value must be 2 digits or less (one byte)."
            clean_exit 1
        fi
        # Convert hex to decimal
        VOLUME=$((16#$HEX_VALUE))
        ;;

esac

# # Validate volume range
# if [ "$VOLUME" -lt 0 ] || [ "$VOLUME" -gt 128 ]; then
#     echo "Error: Volume value out of range."
#     echo "  Decimal:  0-128"
#     echo "  Binary:   00000000-10000000"
#     echo "  Hex:      00-80"
#     clean_exit 1
# fi

# Validate volume range and explain behavior for mute values
if [ "$VOLUME" -lt 0 ] || [ "$VOLUME" -gt 255 ]; then
    echo "Error: Volume value out of range."
    echo "  Valid range: 0-255 (128-255 mutes startup sound)"
    clean_exit 1
elif [ "$VOLUME" -ge 128 ]; then
    PRESERVED_VOL=$((VOLUME & 0x7F))
    echo "Note: Value $VOLUME will mute startup sound and preserve volume level $PRESERVED_VOL"
    echo "      Use 'unmute' command to restore to volume level $PRESERVED_VOL"
    echo ""
fi

# Convert to hex for writing
VOLUME_HEX=$(printf "%02x" "$VOLUME")

echo "Setting startup volume to:"
echo "  Input:    $INPUT_VALUE ($FORMAT)"
echo "  Decimal:  $VOLUME"
echo "  Hex:      $(printf "0x%02x" "$VOLUME")"
echo "  Binary:  $(printf "%08d" "$(echo "obase=2; $VOLUME" | bc)")"
echo "----------------------------------------------------------------"

# Print current value
echo "Before: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"

# Remove the immutable flag before writing
chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null

# Write the new value
# The '%b' format specifier prevents shellcheck warning SC2059 (variable directly in printf string)
printf '%b' "\x07\x00\x00\x00\x${VOLUME_HEX}" > "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"

# Make it immutable again
chattr +i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"

# echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d)"
show_after_value
echo "----------------------------------------------------------------"
clean_exit 0
