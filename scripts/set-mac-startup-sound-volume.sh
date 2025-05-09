#!/usr/bin/env bash

# Ensure that we are root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Function to display usage
usage() {
    echo "Usage: $0 [-d|-b|-x] <volume>"
    echo "       $0 mute"
    echo "       $0 reset"
    echo "       $0 info"
    echo ""
    echo "Special commands:"
    echo "  info:  Display current startup volume setting"
    echo "  mute:  Set the startup volume to muted"
    echo "  reset: Delete the EFI variable (simulate NVRAM/PRAM reset)"
    echo ""
    echo "Format options:"
    echo "  -d: Decimal format (default)"
    echo "  -b: Binary format (e.g., 01000000)"
    echo "  -x: Hexadecimal format (e.g., 40 or 0x40)"
    echo ""
    echo "Volume ranges:"
    echo "  Decimal: 0-127 for volume levels, 128 to mute"
    echo "  Binary: 00000000-01111111 for volume, 10000000 to mute"
    echo "  Hex: 00-7F for volume, 80 to mute"
    exit 1
}

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
        exit 0
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

# Check for special commands first
if [ $# -eq 1 ]; then
    case "${1,,}" in  # Convert to lowercase for case-insensitive matching
        "info")
            show_info
            exit 0
            ;;
            
        "mute")
            echo "Setting startup volume to: MUTED"
            echo "----------------------------------------------------------------"
            echo "Before: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"
            
            # Remove the immutable flag before writing
            chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null
            
            # Set to mute (128)
            printf "\x07\x00\x00\x00\x80" > "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            # Make it immutable again
            chattr +i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"
            
            echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d)"
            echo "----------------------------------------------------------------"
            exit 0
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
            
            echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"
            echo "----------------------------------------------------------------"
            echo "Note: The system will use the default volume on next boot."
            exit 0
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
            exit 1
        fi
        VOLUME=$INPUT_VALUE
        ;;
    
    binary)
        # Check if it's a valid binary number (only 0s and 1s)
        if ! [[ "$INPUT_VALUE" =~ ^[01]+$ ]]; then
            echo "Error: Invalid binary format. Use only 0 and 1."
            exit 1
        fi
        # Check if it's not more than 8 bits
        if [ ${#INPUT_VALUE} -gt 8 ]; then
            echo "Error: Binary value must be 8 bits or less."
            exit 1
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
            exit 1
        fi
        # Check if it's not more than 2 hex digits (1 byte)
        if [ ${#HEX_VALUE} -gt 2 ]; then
            echo "Error: Hexadecimal value must be 2 digits or less (one byte)."
            exit 1
        fi
        # Convert hex to decimal
        VOLUME=$((16#$HEX_VALUE))
        ;;
esac

# Validate volume range
if [ "$VOLUME" -lt 0 ] || [ "$VOLUME" -gt 128 ]; then
    echo "Error: Volume value out of range."
    echo "  Decimal: 0-128"
    echo "  Binary: 00000000-10000000"
    echo "  Hex: 00-80"
    exit 1
fi

# Convert to hex for writing
VOLUME_HEX=$(printf "\\x%02x" "$VOLUME")

echo "Setting startup volume to:"
echo "  Input: $INPUT_VALUE ($FORMAT)"
echo "  Decimal: $VOLUME"
echo "  Hex: $(printf "0x%02x" "$VOLUME")"
echo "  Binary: $(printf "%08d" "$(echo "obase=2; $VOLUME" | bc)")"
echo "----------------------------------------------------------------"

# Print current value
echo "Before: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d 2>/dev/null || echo "Not set")"

# Remove the immutable flag before writing
chattr -i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82" 2>/dev/null

# Write the new value
# The '%b' format specifier prevents shellcheck warning SC2059 (variable directly in printf string)
printf '%b' "\x07\x00\x00\x00${VOLUME_HEX}" > "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"

# Make it immutable again
chattr +i "/sys/firmware/efi/efivars/SystemAudioVolume-7c436110-ab2a-4bbb-a880-fe41995c9f82"

echo "After: $(efivar -n "7c436110-ab2a-4bbb-a880-fe41995c9f82-SystemAudioVolume" -d)"
echo "----------------------------------------------------------------"
