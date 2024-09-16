#!/usr/bin/env python3

# Script to get and print out the versions of various Toshy components. 

# Version info in modules is updated sporadically when relatively large
# changes are made to a component. 

import os
import sys

home_dir                = os.path.expanduser('~')
toshy_dir_path          = os.path.join(home_dir, '.config', 'toshy')
lib_dir_path            = os.path.join(toshy_dir_path, 'lib')

if not os.path.exists(toshy_dir_path):
    print(f"Looks like you haven't installed Toshy yet. This won't work.")
    sys.exit(0)

this_file_path          = os.path.realpath(__file__)
this_file_dir           = os.path.dirname(this_file_path)
this_file_name          = os.path.basename(__file__)
parent_folder_path      = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

home_local_bin          = os.path.join(home_dir, '.local', 'bin')
run_tmp_dir             = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'

sys.path.insert(0, toshy_dir_path)
sys.path.insert(0, lib_dir_path)
# print(sys.path)


# Files to parse for version info:

# ~/.config/toshy/toshy_config.py
# ~/.config/toshy/toshy_gui.py
# ~/.config/toshy/toshy_tray.py

# ~/.config/toshy/lib/env_context.py
# ~/.config/toshy/lib/notification_manager.py
# ~/.config/toshy/lib/settings_class.py


file_paths = [
    os.path.join(toshy_dir_path, 'toshy_config.py'),
    os.path.join(toshy_dir_path, 'toshy_gui.py'),
    os.path.join(toshy_dir_path, 'toshy_tray.py'),

    os.path.join(lib_dir_path, 'env_context.py'),
    os.path.join(lib_dir_path, 'notification_manager.py'),
    os.path.join(lib_dir_path, 'settings_class.py'),
]


# Helper function to extract version from file content
def extract_version(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"').strip("'")
    except Exception as e:
        return f"Error reading file: {str(e)}"


# Calculate max file name length for formatting
max_file_name_length = max(len(os.path.basename(path)) for path in file_paths)

# Print header
print(f"{'File Name'.ljust(max_file_name_length + 4)}Version")
print('-' * (max_file_name_length + 14))

# Print version information
for path in file_paths:
    file_name = os.path.basename(path)
    version = extract_version(path)
    if version:
        print(f"{file_name.ljust(max_file_name_length + 4)}{version}")
    else:
        print(f"{file_name.ljust(max_file_name_length + 4)}No version found or error reading file.")

print()
