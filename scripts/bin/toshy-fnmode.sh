#!/usr/bin/env bash


# Script to change the function keys mode of Apple keyboards that use `hid_apple` device driver


fnmode_file="/sys/module/hid_apple/parameters/fnmode"
sudo_cmd="sudo"

# Check if the script is being run as root, avoid unnecessary use of 'sudo'
if [[ $EUID -eq 0 ]]; then
    # echo "Running script as root"
    sudo_cmd=""
fi

curr_fnmode=$(cat ${fnmode_file})
curr_mode_str="The current function keys mode for the 'hid_apple' driver is:"
var_make_permanent="false"
new_fnmode=""

# echo valid choices text block to terminal
fn_show_valid_choices() {
    echo "Valid choices for function keys mode are (default mode marked with '*'):"
    echo "  0 = disabled   [F-keys are ONLY F-keys, no media/hardware functions]"
    echo "  1 = fkeyslast  [Media/hardware keys first, F-keys when Fn key is held]"
    echo "  2 = fkeysfirst [F-keys first, media/hardware keys when Fn key is held]"
    echo "  3 = auto*      [Usually defaults to acting like mode 1]"
    echo ""
}

# shellcheck disable=SC2086
fn_show_help() {
    echo ""
    echo "Usage: $(basename $0) [--option] [mode]"
    echo ""
    echo "Changes the function keys mode of Apple keyboards that use the"
    echo "'hid_apple' device driver. Interactive prompts will be shown"
    echo "if no options or arguments are provided."
    echo "Requires superuser privileges to modify the mode."
    echo ""
    echo "Options:"
    echo "  -P, --permanent  Make the mode change permanent across reboots."
    echo "  -h, --help       Show this help message and exit."
    echo ""
    echo "Arguments:"
    echo "  mode     Desired function keys mode (see below for valid modes)."
    echo ""
    fn_show_valid_choices
}

fn_update_initramfs() {
    # Get the distribution id
    local dist_id
    dist_id=$(awk -F= '/^ID=/ {print tolower($2)}' /etc/os-release)
    case "$dist_id" in
        debian|ubuntu)
            ${sudo_cmd} update-initramfs -u
            ;;
        fedora|centos|ultramarine|almalinux|rocky)
            dracut_conf_dir="/etc/dracut.conf.d"
            dracut_conf_file="${dracut_conf_dir}/hid_apple.conf"
            if [[ ! -d "$dracut_conf_dir" ]]; then
                mkdir -p "$dracut_conf_dir"
            fi
            # dracut wants spaces inserted around the " <value> " in 'install_items'
            echo 'install_items+=" /etc/modprobe.d/hid_apple.conf "' | ${sudo_cmd} tee "$dracut_conf_file" > /dev/null
            ${sudo_cmd} dracut --force
            ;;
        arch|archlinux)
            ${sudo_cmd} mkinitcpio -P
            ;;
        opensuse*)
            ${sudo_cmd} mkinitrd
            ;;
        *)
            echo "Unknown distribution ID: '$dist_id'"
            echo "Please manually update your initramfs image."
            return 1
            ;;
    esac
    return 0
}

fn_make_fnmode_permanent() {
    local new_fnmode_arg="$1"
    # If the permanent flag is true, make the change permanent
    if $var_make_permanent; then
        modprobe_dir="/etc/modprobe.d"
        conf_file="$modprobe_dir/hid_apple.conf"
        # Check if the /etc/modprobe.d directory exists
        if [[ -d "$modprobe_dir" ]]; then
            # Check if the /etc/modprobe.d/hid_apple.conf file exists, create it if not
            if [[ ! -f "$conf_file" ]]; then
                echo "" | $sudo_cmd tee "$conf_file" > /dev/null
            fi
            # Look for the options hid_apple fnmode=X line in the file
            if grep -q "^options hid_apple fnmode=[0-3]$" "$conf_file"; then
                # If found, modify the X to match the new fnmode
                $sudo_cmd sed -ri "s/^options hid_apple fnmode=[0-3]$/options hid_apple fnmode=$new_fnmode_arg/" "$conf_file"
            else
                # If not found, append the whole line to the file
                echo "options hid_apple fnmode=$new_fnmode_arg" | $sudo_cmd tee -a "$conf_file" > /dev/null
            fi
            fn_update_initramfs
            echo ""
            echo "The change has been made permanent. It will persist after reboot."
        else
            echo ""
            echo "WARNING: Could not make the change permanent because the $modprobe_dir directory does not exist."
        fi
    else
        echo ""
        echo "The change has been made on a non-permanent basis. May not persist after reboot."
    fi
}

fn_update_fnmode() {
    local new_fnmode_arg="$1"
    if [[ $new_fnmode_arg =~ ^[0-3]$ ]]; then
        if echo "${new_fnmode_arg}" | ${sudo_cmd} tee "${fnmode_file}" > /dev/null; then
            echo -e "\nFunction keys mode for 'hid_apple' has been updated to: '${new_fnmode_arg}'"
            # Make change permanent if desired
            fn_make_fnmode_permanent "${new_fnmode_arg}"
        else
            echo -e "\nFailed to update function keys mode for 'hid_apple'."
            echo ""
            exit 1
        fi
    else
        echo -e "\nInvalid input. Please enter a number from 0 to 3."
        echo ""
        exit 1
    fi
}

fn_check_preconditions() {
    # Check if the hid_apple module is loaded
    if ! lsmod | grep -q '^hid_apple'; then
        echo ""
        echo "ERROR: 'hid_apple' module is not loaded. The script cannot proceed."
        echo ""
        exit 1
    fi
    # Check if the fnmode file exists (unlikely if 'hid_apple' module is loaded)
    if [[ ! -f "$fnmode_file" ]]; then
        echo ""
        echo "ERROR: '$fnmode_file' does not exist. The script cannot proceed."
        echo ""
        exit 1
    fi
}

while (( $# )); do
    case "$1" in
        -P|--permanent)
            var_make_permanent="true"
            shift
            ;;
        -h|--help)
            fn_show_help
            exit
            ;;
        *)
            if [[ -z "$new_fnmode" && "$1" =~ ^[0-3]$ ]]; then
                new_fnmode="$1"
                fn_check_preconditions
                fn_update_fnmode "$new_fnmode"
                exit
            else
                echo "Unknown option: $1"
                fn_show_help
                exit 1
            fi
            ;;
    esac
done

# Check that a mode argument follows the use of permanent option
if [[ "$var_make_permanent" == "true" && -z "$new_fnmode" ]]; then
    echo ""
    echo "ERROR: When the permanent option is used, a mode argument must be provided."
    fn_show_help
    exit 1
fi

# Check preconditions here in the case where no arguments were passed and 
# the script is about to start showing the interactive prompts
fn_check_preconditions

# For reference, found in output of `modinfo hid_apple`:
# parm: fnmode: Mode of fn key on Apple keyboards 
# (0 = disabled, 1 = fkeyslast, 2 = fkeysfirst, [3] = auto) (uint)

if [[ $curr_fnmode -eq 0 ]]; then
    echo -e "\n${curr_mode_str} 0 (disabled)"
elif [[ $curr_fnmode -eq 1 ]]; then
    echo -e "\n${curr_mode_str} 1 (fkeyslast)"
elif [[ $curr_fnmode -eq 2 ]]; then
    echo -e "\n${curr_mode_str} 2 (fkeysfirst)"
elif [[ $curr_fnmode -eq 3 ]]; then
    echo -e "\n${curr_mode_str} 3 (auto)"
fi

echo ""
fn_show_valid_choices
read -rp "Enter your desired mode: " response_to_fnmode_prompt
fn_update_fnmode "$response_to_fnmode_prompt"
echo ""
read -rp "Make the mode change permanent? [y/N]: " response_to_permanent_prompt
if [[ "$response_to_permanent_prompt" =~ ^[yY]$ ]]; then
    var_make_permanent="true"
    fn_make_fnmode_permanent "$response_to_fnmode_prompt"
fi
echo ""
