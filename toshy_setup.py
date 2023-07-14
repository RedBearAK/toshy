#!/usr/bin/env python3

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'     # prevent creation of cache files
import re
import sys
import pwd
import grp
import random
import string
import signal
import shutil
import zipfile
import argparse
import datetime
import platform
import textwrap
import subprocess

from subprocess import DEVNULL
from typing import Dict
# local import
import lib.env as env
from lib.logger import debug, error, warn, info

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """Handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        print('\n')
        debug(f'SIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(1)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
    signal.signal(signal.SIGHUP,    signal_handler)
    signal.signal(signal.SIGUSR1,   signal_handler)
    signal.signal(signal.SIGUSR2,   signal_handler)
else:
    signal.signal(signal.SIGINT,    signal_handler)
    error(f'This is only meant to run on Linux. Exiting.')
    sys.exit(1)

trash_dir               = os.path.expanduser("~/.local/share/Trash")
installer_file_path     = os.path.abspath(__file__)
installer_dir_path      = os.path.dirname(installer_file_path)
if trash_dir in installer_file_path or '/trash/' in installer_file_path.lower():
    print()
    error(f"Path to this file: {installer_file_path}")
    error(f"You probably did not intend to run this from the TRASH. See path. Exiting.")
    print()
    sys.exit(1)

orig_PATH_str       = os.environ['PATH']
home_local_bin      = os.path.join(os.path.expanduser('~'), '.local', 'bin')
run_tmp_dir         = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'

path_good_tmp_file  = 'toshy_installer_says_path_is_good'
path_good_tmp_path  = os.path.join(run_tmp_dir, path_good_tmp_file)

path_fix_tmp_file   = 'toshy_installer_says_fix_path'
path_fix_tmp_path   = os.path.join(run_tmp_dir, path_fix_tmp_file)

# set a standard path for duration of script run, to avoid issues with user customized paths
os.environ['PATH']  = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

# deactivate Python virtual environment, if one is active, to avoid issues with sys.executable
if sys.prefix != sys.base_prefix:
    os.environ["VIRTUAL_ENV"] = ""
    sys.path = [p for p in sys.path if not p.startswith(sys.prefix)]
    sys.prefix = sys.base_prefix

# system Python version
py_ver_major, py_ver_minor = sys.version_info[:2]
py_pkg_ver          = f'{py_ver_major}{py_ver_minor}'
py_interp_ver       = f'{py_ver_major}.{py_ver_minor}'

# current stable Python release version (update when needed):
curr_py_rel_ver_maj = 3
curr_py_rel_ver_min = 11
# 3.11 Release Date: Oct. 24, 2022
curr_py_rel_ver     = f'{curr_py_rel_ver_maj}.{curr_py_rel_ver_min}'
curr_py_rel_ver_tup = (curr_py_rel_ver_maj, curr_py_rel_ver_min)

# Check if 'sudo' command is available to user
if not shutil.which('sudo'):
    print("Error: 'sudo' not found. Installer will fail without it. Exiting.")
    sys.exit(1)

do_not_ask_about_path = None

if home_local_bin in orig_PATH_str:
    with open(path_good_tmp_path, 'a') as file:
        file.write('Nothing to see here.')
    # subprocess.run(['touch', path_good_tmp_path])
    do_not_ask_about_path = True
else:
    debug("Home user local bin not part of PATH string.")
# do the 'else' of creating 'path_fix_tmp_path' later in function that prompts user


class InstallerSettings:
    """Set up variables for necessary information to be used by all functions"""
    def __init__(self) -> None:
        sep_reps                    = 80
        self.sep_char               = '='
        self.separator              = self.sep_char * sep_reps
        self.env_info_dct           = None
        self.override_distro        = None
        self.DISTRO_NAME            = None
        self.DISTRO_VER             = None
        self.SESSION_TYPE           = None
        self.DESKTOP_ENV            = None
        
        self.systemctl_present      = shutil.which('systemctl') is not None
        self.init_system            = None

        self.pkgs_for_distro        = None
        self.pip_pkgs               = None
        self.qdbus                  = 'qdbus-qt5' if shutil.which('qdbus-qt5') else 'qdbus'
        self.py_interp_path         = shutil.which('python3')

        self.home_dir_path          = os.path.abspath(os.path.expanduser('~'))
        self.toshy_dir_path         = os.path.join(self.home_dir_path, '.config', 'toshy')
        self.db_file_name           = 'toshy_user_preferences.sqlite'
        self.db_file_path           = os.path.join(self.toshy_dir_path, self.db_file_name)
        self.backup_succeeded       = None
        self.existing_cfg_data      = None
        self.existing_cfg_slices    = None
        self.venv_path              = os.path.join(self.toshy_dir_path, '.venv')

        self.keyszer_tmp_path       = os.path.join(installer_dir_path, 'keyszer-temp')

        self.keyszer_branch         = 'environ_api_kde'
        self.keyszer_url            = 'https://github.com/RedBearAK/keyszer.git'
        self.keyszer_clone_cmd      = f'git clone -b {self.keyszer_branch} {self.keyszer_url}'

        self.input_group_name       = 'input'
        self.user_name              = pwd.getpwuid(os.getuid()).pw_name

        self.fancy_pants            = None
        self.tweak_applied          = None
        self.remind_extensions      = None

        self.should_reboot          = None
        self.run_tmp_dir            = run_tmp_dir
        self.reboot_tmp_file        = f"{self.run_tmp_dir}/toshy_installer_says_reboot"
        self.reboot_ascii_art       = textwrap.dedent("""
                ██████      ███████     ██████       ██████       ██████      ████████     ██ 
                ██   ██     ██          ██   ██     ██    ██     ██    ██        ██        ██ 
                ██████      █████       ██████      ██    ██     ██    ██        ██        ██ 
                ██   ██     ██          ██   ██     ██    ██     ██    ██        ██           
                ██   ██     ███████     ██████       ██████       ██████         ██        ██ 
                """)


def safe_shutdown(exit_code=0):
    """do some stuff on the way out"""

    # good place to do some file cleanup?

    # invalidate the sudo ticket, don't leave system in "superuser" state
    subprocess.run(['sudo', '-k'])
    sys.exit(exit_code)


def get_environment_info():
    """Get back the distro name, distro version, session type and 
        desktop environment from `env.py` module"""
    print(f'\n§  Getting environment information...\n{cnfg.separator}')

    known_init_systems = {
        'systemd':              'Systemd',
        'init':                 'SysVinit',
        'upstart':              'Upstart',
        'openrc':               'OpenRC',
        'runit':                'Runit',
        'initng':               'Initng'
    }

    try:
        with open('/proc/1/comm', 'r') as f:
            cnfg.init_system = f.read().strip()
    except (PermissionError, FileNotFoundError, OSError) as init_check_err:
        error(f'ERROR: Problem when checking init system:\n\t{init_check_err}')

    if cnfg.init_system:
        if cnfg.init_system in known_init_systems:
            init_sys_full_name = known_init_systems[cnfg.init_system]
            print(f"The active init system is: '{cnfg.init_system}' ({init_sys_full_name})")
        else:
            print(f"Init system process unknown: '{cnfg.init_system}'")
    else:
        error("ERROR: Init system (process 1) could not be determined. (See above error.)")

    print()   # blank line after init system message

    cnfg.env_info_dct   = env.get_env_info()

    # Avoid casefold() errors by converting all to strings
    if cnfg.override_distro:
        cnfg.DISTRO_NAME    = str(cnfg.override_distro).casefold()
    else:
        cnfg.DISTRO_NAME    = str(cnfg.env_info_dct.get('DISTRO_NAME',  'keymissing')).casefold()

    cnfg.DISTRO_VER     = str(cnfg.env_info_dct.get('DISTRO_VER',   'keymissing')).casefold()
    cnfg.SESSION_TYPE   = str(cnfg.env_info_dct.get('SESSION_TYPE', 'keymissing')).casefold()
    cnfg.DESKTOP_ENV    = str(cnfg.env_info_dct.get('DESKTOP_ENV',  'keymissing')).casefold()
    debug('Toshy installer sees this environment:'
        f"\n\t DISTRO_NAME  = '{cnfg.DISTRO_NAME}'"
        f"\n\t DISTRO_VER   = '{cnfg.DISTRO_VER}'"
        f"\n\t SESSION_TYPE = '{cnfg.SESSION_TYPE}'"
        f"\n\t DESKTOP_ENV  = '{cnfg.DESKTOP_ENV}'"
        '\n', ctx='EV')


def call_attention_to_password_prompt():
    """Utility function to emphasize the sudo password prompt"""
    try:
        subprocess.run( ['sudo', '-n', 'true'], stdout=DEVNULL, stderr=DEVNULL, check=True)
    except subprocess.CalledProcessError:
        # sudo requires a password
        print()
        print('  -- PASSWORD REQUIRED TO CONTINUE --  ')
        print()


def prompt_for_reboot():
    """Utility function to make sure user is reminded to reboot if necessary"""
    cnfg.should_reboot = True
    if not os.path.exists(cnfg.reboot_tmp_file):
        os.mknod(cnfg.reboot_tmp_file)


def dot_Xmodmap_warning():
    """Check for '.Xmodmap' file in user's home folder, show warning about mod key remaps"""
    xmodmap_file_path = os.path.realpath(os.path.join(os.path.expanduser('~'), '.Xmodmap'))
    if os.path.isfile(xmodmap_file_path):
        print()
        print(f'{cnfg.separator}')
        print(f'{cnfg.separator}')
        warn_str    = "\t WARNING: You have an '.Xmodmap' file in your home folder!!!"
        if os.environ['COLORTERM']:
            # Terminal supports ANSI escape sequences
            print(f"\033[1;31m{warn_str}\033[0m \n")
        else:
            # Terminal might not support ANSI escape sequences
            print(f"{warn_str} \n")
        print(f'   This can cause confusing PROBLEMS if you are remapping any modifier keys!')
        print(f'{cnfg.separator}')
        print(f'{cnfg.separator}')
        print()
        
        secret_code = ''.join(random.choice(string.ascii_letters) for _ in range(4))
        
        response = input(
            f"You must take responsibility for the issues an '.Xmodmap' file may cause."
            f"\n\n\t If you understand, enter the secret code '{secret_code}': "
        )
        
        if response == secret_code:
            print()
            info("Good code. User has taken responsibility for '.Xmodmap' file. Proceeding...\n")
        else:
            print()
            error("Code does not match! Try the installer again after dealing with '.Xmodmap'.\n")
            safe_shutdown(1)


def ask_is_distro_updated():
    """Ask user if the distro has recently been updated"""
    print()
    debug('NOTICE: It is ESSENTIAL to have your system completely updated.', ctx="!!")
    print()
    response = input('Have you updated your system recently? [y/N]: ')

    if response not in ['y', 'Y']:
        print()
        error("Try the installer again after you've done a full system update. Exiting.")
        print()
        safe_shutdown(1)


def ask_add_home_local_bin():
    """
    Check if `~/.local/bin` is in original PATH. Done earlier in script.
    Ask user if it is OK to add the `~/.local/bin` folder to the PATH permanently.
    Create temp file to allow bincommands script to bypass question.
    """
    if do_not_ask_about_path:
        pass
    else:
        print()
        response = input('The "~/.local/bin" folder is not in PATH. OK to add it? [Y/n]: ') or 'y'
        if response in ['y', 'Y']:
            # create temp file that will get script to add local bin to path without asking
            # subprocess.run(['touch', path_fix_tmp_path])
            with open(path_fix_tmp_path, 'a') as file:
                file.write('Nothing to see here.')


def elevate_privileges():
    """Elevate privileges early in the installer process"""

    call_attention_to_password_prompt()
    subprocess.run(['sudo', 'bash', '-c', 'echo -e "\nUsing elevated privileges..."'], check=True)


def do_kwin_reconfigure():
    """Utility function to run the KWin reconfigure command"""
    try:
        subprocess.run([cnfg.qdbus, 'org.kde.KWin', '/KWin', 'reconfigure'],
                        check=True, stderr=DEVNULL, stdout=DEVNULL)
    except subprocess.CalledProcessError as proc_error:
        error(f'Error while running KWin reconfigure.\n\t{proc_error}')


def load_uinput_module():
    """Check to see if `uinput` kernel module is loaded"""

    print(f'\n\n§  Checking status of "uinput" kernel module...\n{cnfg.separator}')

    try:
        subprocess.check_output("lsmod | grep uinput", shell=True)
        print('The "uinput" module is already loaded.')
    except subprocess.CalledProcessError:
        print('The "uinput" module is not loaded, loading now...')
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'modprobe', 'uinput'], check=True)

    # Check if /etc/modules-load.d/ directory exists
    if os.path.isdir("/etc/modules-load.d/"):
        # Check if /etc/modules-load.d/uinput.conf exists
        if not os.path.exists("/etc/modules-load.d/uinput.conf"):
            # If not, create it and add "uinput"
            try:
                call_attention_to_password_prompt()
                command = "echo 'uinput' | sudo tee /etc/modules-load.d/uinput.conf >/dev/null"
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as proc_error:
                error(f"Failed to create /etc/modules-load.d/uinput.conf:\n\t{proc_error}")
                error(f'ERROR: Install failed.')
                safe_shutdown(1)

    else:
        # Check if /etc/modules file exists
        if os.path.isfile("/etc/modules"):
            # If it exists, check if "uinput" is already listed in it
            with open("/etc/modules", "r") as f:
                if "uinput" not in f.read():
                    # If "uinput" is not listed, append it
                    try:
                        call_attention_to_password_prompt()
                        command = "echo 'uinput' | sudo tee -a /etc/modules >/dev/null"
                        subprocess.run(command, shell=True, check=True)
                    except subprocess.CalledProcessError as proc_error:
                        error(f"ERROR: Failed to append 'uinput' to /etc/modules:\n\t{proc_error}")
                        error(f'ERROR: Install failed.')
                        safe_shutdown(1)


def reload_udev_rules():
    try:
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'udevadm', 'control', '--reload-rules'], check=True)
        subprocess.run(['sudo', 'udevadm', 'trigger'], check=True)
        print('Reloaded the "udev" rules successfully.')
    except subprocess.CalledProcessError as proc_error:
        print(f'Failed to reload "udev" rules:\n\t{proc_error}')
        prompt_for_reboot()


def install_udev_rules():
    """Set up `udev` rules file to give user/keyszer access to uinput"""
    print(f'\n\n§  Installing "udev" rules file for keymapper...\n{cnfg.separator}')
    rules_file_path = '/etc/udev/rules.d/90-toshy-keymapper-input.rules'
    setfacl_path = shutil.which('setfacl')
    acl_rule = ''
    if setfacl_path is not None:
        acl_rule = f', RUN+="{setfacl_path} -m g::rw /dev/uinput"'
    rule_content = (
        'SUBSYSTEM=="input", GROUP="input"\n'
        f'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660"{acl_rule}\n'
    )
    # Only write the file if it doesn't exist or its contents are different
    if not os.path.exists(rules_file_path) or open(rules_file_path).read() != rule_content:
        command = f'sudo tee {rules_file_path}'
        try:
            call_attention_to_password_prompt()
            print(f'Using these "udev" rules for "uinput" device: ')
            print()
            subprocess.run(command, input=rule_content.encode(), shell=True, check=True)
            print()
            print(f'Toshy "udev" rules file successfully installed.')
            reload_udev_rules()
        except subprocess.CalledProcessError as proc_error:
            print()
            error(f'ERROR: Problem while installing "udev" rules file for keymapper.\n')
            err_output: bytes = proc_error.output  # Type hinting the error output variable
            # Deal with possible 'NoneType' error output
            error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print()
            error(f'ERROR: Install failed.')
            safe_shutdown(1)
    else:
        print(f'Correct "udev" rules already in place.')


def verify_user_groups():
    """Check if the `input` group exists and user is in group"""
    print(f'\n\n§  Checking if user is in "input" group...\n{cnfg.separator}')
    try:
        grp.getgrnam(cnfg.input_group_name)
    except KeyError:
        # The group doesn't exist, so create it
        print(f'Creating "input" group...')
        try:
            call_attention_to_password_prompt()
            subprocess.run(['sudo', 'groupadd', cnfg.input_group_name], check=True)
        except subprocess.CalledProcessError as proc_error:
            print()
            error(f'ERROR: Problem when trying to create "input" group.\n')
            err_output: bytes = proc_error.output  # Type hinting the error output variable
            # Deal with possible 'NoneType' error output
            error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print()
            error(f'ERROR: Install failed.')
            safe_shutdown(1)

    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.input_group_name)
    if cnfg.user_name in group_info.gr_mem:
        print(f'User "{cnfg.user_name}" is a member of '
                f'group "{cnfg.input_group_name}".')
    else:
        # Add the user to the input group
        try:
            call_attention_to_password_prompt()
            subprocess.run(
                ['sudo', 'usermod', '-aG', cnfg.input_group_name, cnfg.user_name], check=True)
        except subprocess.CalledProcessError as proc_error:
            print()
            error(f'ERROR: Problem when trying to add user "{cnfg.user_name}" to '
                    f'group "{cnfg.input_group_name}".\n')
            err_output: bytes = proc_error.output  # Type hinting the error output variable
            # Deal with possible 'NoneType' error output
            error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print()
            error(f'ERROR: Install failed.')
            safe_shutdown(1)

        print(f'User "{cnfg.user_name}" added to group "{cnfg.input_group_name}".')
        prompt_for_reboot()


distro_groups_map = {
    # TODO: remove this distro group if the change to RHEL/Fedora works out
    # 'redhat-based':    ["fedora", "fedoralinux", "ultramarine", "nobara",
    #                     "rhel", "almalinux", "rocky", "eurolinux"],

    # separate references for RHEL types versus Fedora types
    'fedora-based':    ["fedora", "fedoralinux", "ultramarine", "nobara"],
    'rhel-based':      ["rhel", "almalinux", "rocky", "eurolinux"],

    'tumbleweed-based':["opensuse-tumbleweed"],
    'leap-based':      ["opensuse-leap"],
    'ubuntu-based':    ["ubuntu", "mint", "popos", "eos", "neon", "tuxedo", "zorin"],
    'debian-based':    ["lmde", "peppermint", "debian"],
    'arch-based':      ["arch", "arcolinux", "endeavouros", "manjaro"],
    # Add more as needed...
}

pkg_groups_map = {
    # TODO: remove this package group if the change to RHEL/Fedora works out
    # 'redhat-based':    ["gcc", "git", "cairo-devel", "cairo-gobject-devel", "dbus-devel",
    #                     "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
    #                     "gobject-introspection-devel", "libappindicator-gtk3", "xset",
    #                     "libnotify", "systemd-devel", "zenity"],

    'fedora-based':    ["gcc", "git", "cairo-devel", "cairo-gobject-devel", "dbus-devel",
                        "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
                        "gobject-introspection-devel", "libappindicator-gtk3", "xset",
                        "libnotify", "systemd-devel", "zenity", "evtest"],

    'rhel-based':      ["gcc", "git", "cairo-devel", "cairo-gobject-devel", "dbus-devel",
                        "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
                        "gobject-introspection-devel", "libappindicator-gtk3", "xset",
                        "libnotify", "systemd-devel", "zenity"],

    # opensuse-tumbleweed
    'tumbleweed-based':["gcc", "git", "cairo-devel",  "dbus-1-devel", f"python{py_pkg_ver}-tk",
                        f"python{py_pkg_ver}-dbus-python-devel", f"python{py_pkg_ver}-devel",
                        "gobject-introspection-devel", "libappindicator3-devel", "tk",
                        "libnotify-tools", "typelib-1_0-AyatanaAppIndicator3-0_1",
                        "systemd-devel", "zenity"],

    'leap-based':      ["gcc", "git", "cairo-devel",  "dbus-1-devel", "python311-tk",
                        "python3-dbus-python-devel", "python311-devel", "python311",
                        "gobject-introspection-devel", "libappindicator3-devel", "tk",
                        "libnotify-tools", "typelib-1_0-AyatanaAppIndicator3-0_1",
                        "systemd-devel", "zenity"],

    'ubuntu-based':    ["curl", "git", "input-utils", "libcairo2-dev", "libnotify-bin",
                        "python3-dbus", "python3-dev", "python3-pip", "python3-venv",
                        "python3-tk", "libdbus-1-dev", "libgirepository1.0-dev",
                        "gir1.2-appindicator3-0.1", "libsystemd-dev", "zenity"],

    'debian-based':    ["curl", "git", "input-utils", "libcairo2-dev", "libnotify-bin", 
                        "python3-dbus", "python3-dev", "python3-pip", "python3-venv",
                        "python3-tk", "libdbus-1-dev", "libgirepository1.0-dev", 
                        "gir1.2-ayatanaappindicator3-0.1", "libsystemd-dev", "zenity"],

    'arch-based':      ["cairo", "dbus", "evtest", "git", "gobject-introspection", "tk",
                        "libappindicator-gtk3", "pkg-config", "python-dbus", "python-pip",
                        "python", "libnotify", "systemd", "zenity"],
}

extra_pkgs_map = {
    # Add a distro name and its additional packages here as needed
    # 'distro_name': ["pkg1", "pkg2", ...],
    # TODO: remove the lines below if the updated RHEL/Fedora distro groups works out
    # 'fedora':          ["evtest"],
    # 'fedoralinux':     ["evtest"],
    # 'ultramarine':     ["evtest"],
}


def install_distro_pkgs():
    """Install needed packages from list for distro type"""
    print(f'\n\n§  Installing native packages for this distro type...\n{cnfg.separator}')

    pkg_group = None
    for group, distros in distro_groups_map.items():
        if cnfg.DISTRO_NAME in distros:
            pkg_group = group
            break

    if pkg_group is None:
        print()
        print(f"ERROR: No list of packages found for this distro: '{cnfg.DISTRO_NAME}'")
        print(f'Installation cannot proceed without a list of packages. Sorry.')
        print(f'Try some options in "./toshy_setup.py --help"\n')
        safe_shutdown(1)

    cnfg.pkgs_for_distro = pkg_groups_map[pkg_group]

    # Add extra packages for specific distros
    if cnfg.DISTRO_NAME in extra_pkgs_map:
        cnfg.pkgs_for_distro.extend(extra_pkgs_map[cnfg.DISTRO_NAME])

    # Filter out systemd packages if not present
    cnfg.pkgs_for_distro = [
        pkg for pkg in cnfg.pkgs_for_distro 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    dnf_distros     = distro_groups_map['fedora-based'] + distro_groups_map['rhel-based']
    zypper_distros  = distro_groups_map['tumbleweed-based'] + distro_groups_map['leap-based']
    apt_distros     = distro_groups_map['ubuntu-based'] + distro_groups_map['debian-based']
    pacman_distros  = distro_groups_map['arch-based']

    def check_for_pkg_mgr_cmd(command):
        pkg_mgr_cmd = command
        if not shutil.which(pkg_mgr_cmd):
            print()
            error(f'Package manager command ({pkg_mgr_cmd}) not available. Unable to continue.')
            safe_shutdown(1)

    if cnfg.DISTRO_NAME in dnf_distros:
        check_for_pkg_mgr_cmd('dnf')
        # do extra stuff only if distro is a RHEL type (not Fedora type)
        if cnfg.DISTRO_NAME in distro_groups_map['rhel-based']:
            call_attention_to_password_prompt()
            # for gobject-introspection-devel: sudo dnf config-manager --set-enabled crb
            subprocess.run(['sudo', 'dnf', 'config-manager', '--set-enabled', 'crb'])
            # for libappindicator-gtk3: sudo dnf install -y epel-release
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'epel-release'])
            subprocess.run(['sudo', 'dnf', 'update', '-y'])
        # now do the install of the list of packages
        subprocess.run(['sudo', 'dnf', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in zypper_distros:
        check_for_pkg_mgr_cmd('zypper')
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'zypper', '--non-interactive', 'install'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in apt_distros:
        check_for_pkg_mgr_cmd('apt')
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'apt', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in pacman_distros:
        check_for_pkg_mgr_cmd('pacman')

        def is_pkg_installed_pacman(package):
            result = subprocess.run(['pacman', '-Q', package], stdout=DEVNULL, stderr=DEVNULL)
            return result.returncode == 0

        pkgs_to_install = [
            pkg
            for pkg in cnfg.pkgs_for_distro
            if not is_pkg_installed_pacman(pkg)
        ]
        if pkgs_to_install:
            call_attention_to_password_prompt()
            subprocess.run(['sudo', 'pacman', '-S', '--noconfirm'] + pkgs_to_install)

    else:
        print()
        error(f"ERROR: Installer does not know how to handle distro: {cnfg.DISTRO_NAME}\n")
        safe_shutdown(1)

    # Have something come out even if package list is empty (like Arch after initial run)
    print(f'All necessary native distro packages are installed.')


def get_distro_names():
    """Utility function to return list of available distro names"""

    distro_list = []
    for group in distro_groups_map.values():
        distro_list.extend(group)

    sorted_distro_list = sorted(distro_list)
    distros = ",\n\t".join(sorted_distro_list)
    return distros


def clone_keyszer_branch():
    """Clone the designated `keyszer` branch from GitHub"""
    print(f'\n\n§  Cloning keyszer branch ({cnfg.keyszer_branch})...\n{cnfg.separator}')
    
    # Check if `git` command exists. If not, exit script with error.
    has_git = shutil.which('git')
    if not has_git:
        print(f'ERROR: "git" is not installed, for some reason. Cannot continue.')
        safe_shutdown(1)

    if os.path.exists(cnfg.keyszer_tmp_path):
        # force a fresh copy of keyszer every time script is run
        try:
            shutil.rmtree(cnfg.keyszer_tmp_path)
        except (OSError, PermissionError, FileNotFoundError) as file_err:
            error(f"Problem removing existing '{cnfg.keyszer_tmp_path}' folder:\n\t{file_err}")
    subprocess.run(cnfg.keyszer_clone_cmd.split() + [cnfg.keyszer_tmp_path])


def extract_slices(data: str) -> Dict[str, str]:
    """Utility function to store user content slices from existing config file data"""
    slices = {}
    pattern_start       = r'###  SLICE_MARK_START: (\w+)  ###.*'
    pattern_end         = r'###  SLICE_MARK_END: (\w+)  ###.*'
    matches_start       = list(re.finditer(pattern_start, data))
    matches_end         = list(re.finditer(pattern_end, data))
    if len(matches_start) != len(matches_end):
        raise ValueError(   f'Mismatched slice markers in config file:'
                            f'\n\t{matches_start}, {matches_end}')
    for begin, end in zip(matches_start, matches_end):
        slice_name = begin.group(1)
        if end.group(1) != slice_name:
            raise ValueError(f'Mismatched slice markers in config file:\n\t{slice_name}')
        slice_start     = begin.end()
        slice_end       = end.start()
        slices[slice_name] = data[slice_start:slice_end]
    
    return slices


def merge_slices(data: str, slices: Dict[str, str]) -> str:
    """Utility function to merge stored slices into new config file data"""
    pattern_start = r'###  SLICE_MARK_START: (\w+)  ###.*'
    pattern_end = r'###  SLICE_MARK_END: (\w+)  ###.*'
    matches_start = list(re.finditer(pattern_start, data))
    matches_end = list(re.finditer(pattern_end, data))
    data_slices = []
    previous_end = 0
    for begin, end in zip(matches_start, matches_end):
        slice_name = begin.group(1)
        if end.group(1) != slice_name:
            raise ValueError(f'Mismatched slice markers in config file:\n\t{slice_name}')
        slice_start = begin.end()
        slice_end = end.start()
        # add the part of the data before the slice, and the slice itself
        data_slices.extend([data[previous_end:slice_start], 
                            slices.get(slice_name, data[slice_start:slice_end])])
        previous_end = slice_end
    # add the part of the data after the last slice
    data_slices.append(data[previous_end:])

    return "".join(data_slices)


def backup_toshy_config():
    """Backup existing Toshy config folder"""
    print(f'\n\n§  Backing up existing Toshy config folder...\n{cnfg.separator}')

    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_cfg_bkups_base_dir  = os.path.join(
        os.path.expanduser('~'), '.config', 'toshy_config_backups')
    toshy_cfg_bkup_timestamp_dir  = os.path.abspath(
        os.path.join(toshy_cfg_bkups_base_dir, 'toshy' + timestamp))

    if not os.path.exists(cnfg.toshy_dir_path):
        print(f'No existing Toshy folder to backup.')
        cnfg.backup_succeeded = True
    else:
        cfg_file_path   = os.path.join(cnfg.toshy_dir_path, 'toshy_config.py')

        if os.path.isfile(cfg_file_path):
            try:
                with open(cfg_file_path, 'r', encoding='UTF-8') as file:
                    cnfg.existing_cfg_data = file.read()
                print(f'Prepared existing config file data for merging into new config.')
            except (FileNotFoundError, PermissionError, OSError) as file_err:
                cnfg.existing_cfg_data = None
                error(f'Problem reading existing config file contents.\n\t{file_err}')
            if cnfg.existing_cfg_data is not None:
                try:
                    cnfg.existing_cfg_slices = extract_slices(cnfg.existing_cfg_data)
                except ValueError as value_err:
                    error(f'Problem extracting marked slices from existing config.\n\t{value_err}')

        if os.path.isfile(cnfg.db_file_path):
            try:
                os.unlink(f'{cnfg.run_tmp_dir}/{cnfg.db_file_name}')
            except (FileNotFoundError, PermissionError, OSError): pass
            try:
                shutil.copy(cnfg.db_file_path, f'{cnfg.run_tmp_dir}/')
            except (FileNotFoundError, PermissionError, OSError) as file_err:
                error(f"Problem copying preferences db file to '{cnfg.run_tmp_dir}':\n\t{file_err}")
        try:
            # Define the ignore function
            def ignore_venv(dirname, filenames):
                return ['.venv'] if '.venv' in filenames else []
            # Copy files recursively from source to destination
            shutil.copytree(cnfg.toshy_dir_path, toshy_cfg_bkup_timestamp_dir, ignore=ignore_venv)
        except shutil.Error as copy_error:
            print(f"Failed to copy directory: {copy_error}")
            safe_shutdown(1)
        except OSError as os_error:
            print(f"Failed to copy directory: {os_error}")
            safe_shutdown(1)
        print(f"Backup completed to '{toshy_cfg_bkup_timestamp_dir}'")
        cnfg.backup_succeeded = True


def install_toshy_files():
    """Install Toshy files"""
    print(f'\n\n§  Installing Toshy files...\n{cnfg.separator}')
    if not cnfg.backup_succeeded:
        print(f'Backup of Toshy config folder failed? Bailing out.')
        safe_shutdown(1)
    keyszer_tmp_dir     = os.path.basename(cnfg.keyszer_tmp_path)
    script_file_name    = os.path.basename(__file__)
    try:
        if os.path.exists(cnfg.toshy_dir_path):
            try:
                shutil.rmtree(cnfg.toshy_dir_path) # , ignore_errors=True)
            except (OSError, PermissionError, FileNotFoundError) as file_err:
                error(f'Problem removing existing Toshy config folder after backup:\n\t{file_err}')
        # Copy files recursively from source to destination
        shutil.copytree(
            installer_dir_path, 
            cnfg.toshy_dir_path, 
            ignore=shutil.ignore_patterns(
                '__pycache__',
                '.github',
                '.gitignore',
                keyszer_tmp_dir,
                'kwin-application-switcher',
                'LICENSE',
                'packages.json',
                'README.md',
                script_file_name
            )
        )
    except shutil.Error as copy_error:
        print(f"Failed to copy directory: {copy_error}")
    except OSError as os_error:
        print(f"Failed to create backup directory: {os_error}")
    toshy_default_cfg = os.path.join(
        cnfg.toshy_dir_path, 'toshy-default-config', 'toshy_config.py')
    shutil.copy(toshy_default_cfg, cnfg.toshy_dir_path)
    print(f"Toshy files installed in '{cnfg.toshy_dir_path}'.")

    if os.path.isfile(f'{cnfg.run_tmp_dir}/{cnfg.db_file_name}'):
        try:
            shutil.copy(f'{cnfg.run_tmp_dir}/{cnfg.db_file_name}', cnfg.toshy_dir_path)
            print(f'Copied preferences db file from existing config folder.')
        except (FileExistsError, FileNotFoundError, PermissionError, OSError) as file_err:
            error(f"Problem copying preferences db file from '{cnfg.run_tmp_dir}':\n\t{file_err}")

    # Apply user customizations to the new config file.
    new_cfg_file = os.path.join(cnfg.toshy_dir_path, 'toshy_config.py')
    if cnfg.existing_cfg_slices is not None:
        try:
            with open(new_cfg_file, 'r', encoding='UTF-8') as file:
                new_cfg_data = file.read()
        except (FileNotFoundError, PermissionError, OSError) as file_err:
            error(f'Problem reading new config file:\n\t{file_err}')
            safe_shutdown(1)
        merged_cfg_data = None
        try:
            merged_cfg_data = merge_slices(new_cfg_data, cnfg.existing_cfg_slices)
        except ValueError as value_err:
            error(f'Problem when merging user customizations with new config file:\n\t{value_err}')
        if merged_cfg_data is not None:
            try:
                with open(new_cfg_file, 'w', encoding='UTF-8') as file:
                    file.write(merged_cfg_data)
            except (FileNotFoundError, PermissionError, OSError) as file_err:
                error(f'Problem writing to new config file:\n\t{file_err}')
                safe_shutdown(1)
            print(f"Existing user customizations applied to the new config file.")


def setup_python_virt_env():
    """Setup a virtual environment to install Python packages"""
    print(f'\n\n§  Setting up the Python virtual environment...\n{cnfg.separator}')

    # Create the virtual environment if it doesn't exist
    if not os.path.exists(cnfg.venv_path):
        # change the Python interpreter path to user current release version 
        # if distro is openSUSE Leap type (instead of old 3.6 version)
        if cnfg.DISTRO_NAME in distro_groups_map['leap-based']:
            if shutil.which(f'python{curr_py_rel_ver}'):
                cnfg.py_interp_path     = shutil.which(f'python{curr_py_rel_ver}')
                print(f'Using Python version {curr_py_rel_ver}.')
            else:
                print(  f'Current stable Python release version '
                        f'({curr_py_rel_ver}) not found. ')
        else:
            print(f'Using Python version {py_interp_ver}.')
        subprocess.run([cnfg.py_interp_path, '-m', 'venv', cnfg.venv_path])

    # We do not need to "activate" the venv right now, just create it
    print(f'Python virtual environment setup complete.')


def install_pip_packages():
    """Install `pip` packages for Python"""
    print(f'\n\n§  Installing/upgrading Python packages...\n{cnfg.separator}')
    venv_python_cmd = os.path.join(cnfg.venv_path, 'bin', 'python')
    venv_pip_cmd    = os.path.join(cnfg.venv_path, 'bin', 'pip')
    
    # everything from 'inotify-simple' to 'six' is just to make `keyszer` install smoother
    cnfg.pip_pkgs   = [
        "lockfile", "dbus-python", "systemd-python", "pygobject", "tk", "sv_ttk", "psutil",
        "watchdog", "inotify-simple", "evdev", "appdirs", "ordered-set", "python-xlib", "six"
    ]

    # Filter out systemd packages if no 'systemctl' present
    cnfg.pip_pkgs   = [
        pkg for pkg in cnfg.pip_pkgs 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    commands        = [
        [venv_python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'],
        [venv_pip_cmd, 'install', '--upgrade', 'wheel'],
        [venv_pip_cmd, 'install', '--upgrade', 'setuptools'],
        [venv_pip_cmd, 'install', '--upgrade', 'pillow'],
        [venv_pip_cmd, 'install', '--upgrade'] + cnfg.pip_pkgs
    ]
    for command in commands:
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f'Error installing/upgrading Python packages. Installer exiting.')
            safe_shutdown(1)
    if os.path.exists(cnfg.keyszer_tmp_path):
        result = subprocess.run([venv_pip_cmd, 'install', '--upgrade', cnfg.keyszer_tmp_path])
        if result.returncode != 0:
            print(f'Error installing/upgrading "keyszer".')
            safe_shutdown(1)
    else:
        print(f'Temporary "keyszer" clone folder missing. Unable to install "keyszer".')
        safe_shutdown(1)


def install_bin_commands():
    """Install the convenient terminal commands (symlinks to scripts) to manage Toshy"""
    print(f'\n\n§  Installing Toshy terminal commands...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-bincommands-setup.sh')
    subprocess.run([script_path])


def replace_home_in_file(filename):
    """Utility function to replace '$HOME' in .desktop files with actual home path"""
    # Read in the file
    with open(filename, 'r') as file:
        file_data = file.read()
    # Replace the target string
    file_data = file_data.replace('$HOME', cnfg.home_dir_path)
    # Write the file out again
    with open(filename, 'w') as file:
        file.write(file_data)


def install_desktop_apps():
    """Install the convenient scripts to manage Toshy"""
    print(f'\n\n§  Installing Toshy desktop apps...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-desktopapps-setup.sh')
    subprocess.run([script_path])

    desktop_files_path  = os.path.join(cnfg.home_dir_path, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    gui_desktop_file    = os.path.join(desktop_files_path, 'Toshy_GUI.desktop')

    replace_home_in_file(tray_desktop_file)
    replace_home_in_file(gui_desktop_file)


def setup_kwin2dbus_script():
    """Install the KWin script to notify D-Bus service about window focus changes"""
    print(f'\n\n§  Setting up the Toshy KWin script...\n{cnfg.separator}')
    kwin_script_name    = 'toshy-dbus-notifyactivewindow'
    kwin_script_path    = os.path.join( cnfg.toshy_dir_path,
                                        'kde-kwin-dbus-service', kwin_script_name)
    script_tmp_file     = f'{cnfg.run_tmp_dir}/{kwin_script_name}.kwinscript'

    # Create a zip file (overwrite if it exists)
    with zipfile.ZipFile(script_tmp_file, 'w') as zipf:
        # Add main.js to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                                arcname='contents/code/main.js')
        # Add metadata.desktop to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

    # Try to remove any installed KWin script entirely
    process = subprocess.Popen(
        ['kpackagetool5', '-t', 'KWin/Script', '-r', kwin_script_name],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = subprocess.CompletedProcess(args=process.args, returncode=process.returncode,
                                            stdout=out, stderr=err)

    # NOT COMPATIBLE WITH PYTHON 3.6
    # result = subprocess.run(
    #     ['kpackagetool5', '-t', 'KWin/Script', '-r', kwin_script_name],
    #     capture_output=True, text=True)

    if result.returncode != 0:
        pass
    else:
        print("Successfully removed existing KWin script.")

    # Install the KWin script
    process = subprocess.Popen(
        ['kpackagetool5', '-t', 'KWin/Script', '-i', script_tmp_file],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = subprocess.CompletedProcess(args=process.args, returncode=process.returncode,
                                            stdout=out, stderr=err)

    # NOT COMPATIBLE WITH PYTHON 3.6
    # result = subprocess.run(
    #     ['kpackagetool5', '-t', 'KWin/Script', '-i', script_tmp_file],
    #     capture_output=True, text=True)

    if result.returncode != 0:
        error(f"Error installing the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully installed the KWin script.")

    # Remove the temporary kwinscript file
    try:
        os.remove(script_tmp_file)
    except (FileNotFoundError, PermissionError): pass

    # Enable the script using kwriteconfig5
    process = subprocess.Popen(
        [   'kwriteconfig5', '--file', 'kwinrc', '--group', 'Plugins', '--key',
            f'{kwin_script_name}Enabled', 'true'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = subprocess.CompletedProcess(args=process.args, returncode=process.returncode,
                                            stdout=out, stderr=err)

    # NOT COMPATIBLE WITH PYTHON 3.6
    # result = subprocess.run(
    #     [   'kwriteconfig5', '--file', 'kwinrc', '--group', 'Plugins', '--key',
    #         f'{kwin_script_name}Enabled', 'true'],
    #     capture_output=True, text=True)

    if result.returncode != 0:
        error(f"Error enabling the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully enabled the KWin script.")

    # Try to get KWin to notice and activate the script on its own, now that it's in RC file
    do_kwin_reconfigure()


def setup_kde_dbus_service():
    """Install the D-Bus service initialization script to receive window focus
    change notifications from the KWin script on KDE desktops (needed for Wayland)"""
    print(f'\n\n§  Setting up the Toshy KDE D-Bus service...\n{cnfg.separator}')

    # need to autostart "$HOME/.local/bin/toshy-kde-dbus-service"
    user_path               = os.path.expanduser('~')
    autostart_dir_path      = os.path.join(user_path, '.config', 'autostart')
    dbus_svc_dt_file_path   = os.path.join(cnfg.toshy_dir_path, 'desktop')
    dbus_svc_desktop_file   = os.path.join(dbus_svc_dt_file_path, 'Toshy_KDE_DBus_Service.desktop')
    start_dbus_svc_cmd      = os.path.join(user_path, '.local', 'bin', 'toshy-kde-dbus-service')
    replace_home_in_file(dbus_svc_desktop_file)

    # Where to put the new D-Bus service file:
    # ~/.local/share/dbus-1/services/org.toshy.Toshy.service
    dbus_svcs_path          = os.path.join(user_path, '.local', 'share', 'dbus-1', 'services')
    toshy_kde_dbus_svc_path = os.path.join(cnfg.toshy_dir_path, 'kde-kwin-dbus-service')
    kde_dbus_svc_file       = os.path.join(toshy_kde_dbus_svc_path, 'org.toshy.Toshy.service')

    if not os.path.isdir(dbus_svcs_path):
        try:
            os.makedirs(dbus_svcs_path, exist_ok=True)
        except (PermissionError, NotADirectoryError) as file_err:
            error(f"Problem trying to make sure '{dbus_svcs_path}' is a directory:\n\t{file_err}")
            safe_shutdown(1)

    # STOP INSTALLING THIS, IT'S NOT HELPFUL
    # if os.path.isdir(dbus_svcs_path):
    #     shutil.copy(kde_dbus_svc_file, dbus_svcs_path)
    #     print(f"Installed '{kde_dbus_svc_file}' file at path:\n\t'{dbus_svcs_path}'.")
    # else:
    #     error(f"Path '{dbus_svcs_path}' is not a directory. Cannot continue.")
    #     safe_shutdown(1)

    # ensure autostart directory exists
    if not os.path.isdir(autostart_dir_path):
        try:
            os.makedirs(autostart_dir_path, exist_ok=True)
        except (PermissionError, NotADirectoryError) as file_err:
            error(f"Problem trying to make sure '{autostart_dir_path}' is directory.\n\t{file_err}")
            safe_shutdown(1)

    # try to delete old desktop entry file that would have been installed by code below
    autostart_dbus_dt_file = os.path.join(autostart_dir_path, 'Toshy_KDE_DBus_Service.desktop')
    if os.path.isfile(autostart_dbus_dt_file):
        try:
            os.unlink(autostart_dbus_dt_file)
            print(f'Removed older KDE D-Bus desktop entry autostart.')
        except subprocess.CalledProcessError as proc_err:
            debug(f'Problem removing old D-Bus service desktop entry autostart:\n\t{proc_err}')

    # # STOP DOING THIS, IN FAVOR OF SYSTEMD SERVICE, INSTALLED BY BASH SCRIPT
    # shutil.copy(dbus_svc_desktop_file, autostart_dir_path)
    # print(f'Toshy KDE D-Bus service should autostart at login.')
    # subprocess.run(['pkill', '-u', cnfg.user_name, '-f', 'toshy_kde_dbus_service'])
    # subprocess.Popen([start_dbus_svc_cmd], stdout=DEVNULL, stderr=DEVNULL)
    
    # # DON'T DO THIS HERE, IT'S IN THE KDE D-BUS SERVICE PYTHON SCRIPT NOW
    # # Try to kickstart the KWin script so that it can start sending focused window info
    # kickstart_script    = 'toshy-kwin-script-kickstart.sh'
    # kickstart_cmd       = os.path.join(cnfg.toshy_dir_path, 'scripts', kickstart_script)
    # subprocess.Popen([kickstart_cmd])

    print(f'Toshy KDE D-Bus service should automatically start when needed.')


def setup_systemd_services():
    """Invoke the systemd setup script to install the systemd service units"""
    print(f'\n\n§  Setting up the Toshy systemd services...\n{cnfg.separator}')
    if cnfg.systemctl_present and cnfg.init_system == 'systemd':
        script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'bin', 'toshy-systemd-setup.sh')
        subprocess.run([script_path])
        print(f'Finished setting up Toshy "systemd" services.')
    else:
        print(f'System does not seem to be using "systemd" as init system.')


def autostart_tray_icon():
    """Set up the tray icon to autostart at login"""
    print(f'\n\n§  Setting up tray icon to load automatically at login...\n{cnfg.separator}')
    user_path           = os.path.expanduser('~')
    desktop_files_path  = os.path.join(user_path, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    autostart_dir_path  = os.path.join(user_path, '.config', 'autostart')
    dest_link_file      = os.path.join(autostart_dir_path, 'Toshy_Tray.desktop')

    # Need to create autostart folder if necessary
    try:
        os.makedirs(autostart_dir_path, exist_ok=True)
    except (PermissionError, NotADirectoryError) as file_err:
        error(f"Problem trying to make sure '{autostart_dir_path}' is directory.\n\t{file_err}")
        safe_shutdown(1)
    subprocess.run(['ln', '-sf', tray_desktop_file, dest_link_file])

    print(f'Toshy tray icon should appear in system tray at each login.')


###################################################################################################
##  TWEAKS UTILITY FUNCTIONS - START
###################################################################################################


def apply_tweaks_GNOME():
    """Utility function to add desktop tweaks to GNOME"""
    # Disable GNOME `overlay-key` binding to Meta/Super/Win/Cmd
    # gsettings set org.gnome.mutter overlay-key ''
    subprocess.run(['gsettings', 'set', 'org.gnome.mutter', 'overlay-key', ''])
    print(f'Disabled Super key opening the GNOME overview. (Use Cmd+Space instead.)')

    # Set the keyboard shortcut for "Switch applications" to "Alt+Tab"
    # gsettings set org.gnome.desktop.wm.keybindings switch-applications "['<Alt>Tab']"
    subprocess.run(['gsettings', 'set', 'org.gnome.desktop.wm.keybindings',
                    'switch-applications', "['<Alt>Tab']"])
    # Set the keyboard shortcut for "Switch windows of an application" to "Alt+`" (Alt+Grave)
    # gsettings set org.gnome.desktop.wm.keybindings switch-group "['<Alt>grave']"
    subprocess.run(['gsettings', 'set', 'org.gnome.desktop.wm.keybindings',
                    'switch-group', "['<Alt>grave']"])
    print(f'Enabled "Switch applications" Mac-like task switching.')
    
    # Enable keyboard shortcut for GNOME Terminal preferences dialog
    # gsettings set org.gnome.Terminal.Legacy.Keybindings:/org/gnome/terminal/legacy/keybindings/ preferences '<Control>less'
    cmd_path = 'org.gnome.Terminal.Legacy.Keybindings:/org/gnome/terminal/legacy/keybindings/'
    prefs_binding = '<Control>less'
    subprocess.run(['gsettings', 'set', cmd_path, 'preferences', prefs_binding])
    print(f'Set a keybinding for GNOME Terminal preferences.')
    
    # Enable "Expandable folders" in Nautilus
    # dconf write /org/gnome/nautilus/list-view/use-tree-view true
    subprocess.run(['dconf', 'write', '/org/gnome/nautilus/list-view/use-tree-view', 'true'])
    
    # Set default view option in Nautilus to "list-view"
    # dconf write /org/gnome/nautilus/preferences/default-folder-viewer "'list-view'"
    subprocess.run(['dconf', 'write', '/org/gnome/nautilus/preferences/default-folder-viewer',
                    "'list-view'"])
    print(f'Set Nautilus to "List" view with "Expandable folders" enabled.')


def remove_tweaks_GNOME():
    """Utility function to remove the tweaks applied to GNOME"""
    subprocess.run(['gsettings', 'reset', 'org.gnome.mutter', 'overlay-key'])
    print(f'Removed tweak to disable GNOME "overlay-key" binding to Meta/Super.')
    
    # gsettings reset org.gnome.desktop.wm.keybindings switch-applications
    subprocess.run(['gsettings', 'reset', 'org.gnome.desktop.wm.keybindings',
                    'switch-applications'])
    # gsettings reset org.gnome.desktop.wm.keybindings switch-group
    subprocess.run(['gsettings', 'reset', 'org.gnome.desktop.wm.keybindings', 'switch-group'])
    print(f'Removed tweak to enable more Mac-like task switching')


def apply_tweaks_KDE():
    """Utility function to add desktop tweaks to KDE"""

    # Documentation on the use of Meta key in KDE:
    # https://userbase.kde.org/Plasma/Tips#Windows.2FMeta_Key
    subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group',
                    'ModifierOnlyShortcuts', '--key', 'Meta', ''], check=True)

    # Run reconfigure command
    do_kwin_reconfigure()
    print(f'Disabled Meta key opening application menu. (Use Cmd+Space instead.)')
    
    if cnfg.fancy_pants:

        print(f'Installing "Application Switcher" KWin script...')
        # How to install nclarius grouped "Application Switcher" KWin script:
        # git clone https://github.com/nclarius/kwin-application-switcher.git
        # cd kwin-application-switcher
        # ./install.sh
        switcher_url        = 'https://github.com/nclarius/kwin-application-switcher.git'
        switcher_dir        = 'kwin-application-switcher'
        script_path         = os.path.dirname(os.path.realpath(__file__))
        switcher_dir_path   = os.path.join(script_path, switcher_dir)
        # git should be installed by this point? Not necessarily.
        if shutil.which('git'):
            try:
                if os.path.exists(switcher_dir_path):
                    try:
                        shutil.rmtree(switcher_dir_path)
                    except (FileNotFoundError, PermissionError, OSError) as file_err:
                        print(f'Problem removing existing switcher clone folder:\n\t{file_err}')
                subprocess.run(["git", "clone", switcher_url, switcher_dir_path], check=True,
                                stdout=DEVNULL, stderr=DEVNULL)
                command_dir     = os.path.join(script_path, switcher_dir)
                subprocess.run(["./install.sh"], cwd=command_dir, check=True,
                                stdout=DEVNULL, stderr=DEVNULL)
                print(f'Installed "Application Switcher" KWin script.')
            except subprocess.CalledProcessError as proc_error:
                print(f'Something went wrong installing KWin Application Switcher.\n\t{proc_error}')
        else:
            print(f"ERROR: Unable to clone KWin Application Switcher. 'git' not installed.")

        # Run reconfigure command
        do_kwin_reconfigure()

        # Set the LayoutName value to big_icons (shows task switcher with large icons, no previews)
        subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group', 'TabBox',
                        '--key', 'LayoutName', 'big_icons'], check=True)
        # Set the HighlightWindows value to false (disables "Show selected window" option)
        subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group', 'TabBox',
                        '--key', 'HighlightWindows', 'false'], check=True)
        # Set the ApplicationsMode value to 1 (enables "Only one window per application" option)
        subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group', 'TabBox',
                        '--key', 'ApplicationsMode', '1'], check=True)

        # Run reconfigure command
        do_kwin_reconfigure()
        print(f'Set task switcher to "Large Icons", disabled "Show selected window" option.')


def remove_tweaks_KDE():
    """Utility function to remove the tweaks applied to KDE"""

    # Re-enable Meta key opening the application menu
    subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group',
                    'ModifierOnlyShortcuts', '--key', 'Meta', '--delete'], check=True)
    # Disable the "Only one window per application" task switcher option
    subprocess.run(['kwriteconfig5', '--file', 'kwinrc', '--group', 'TabBox', 
                    '--key', 'ApplicationsMode', '--delete'], check=True)

    # Run reconfigure command
    do_kwin_reconfigure()
    print(f'Re-enabled Meta key opening application menu.')
    print(f'Disabled "Only one window per application" task switcher option.')


###################################################################################################
##  TWEAKS UTILITY FUNCTIONS - END
###################################################################################################


def apply_desktop_tweaks():
    """
    Fix things like Meta key activating overview in GNOME or KDE Plasma
    and fix the Unicode sequences in KDE Plasma
    
    TODO: These tweaks should probably be done at startup of the config
            instead of (or in addition to) here in the installer. 
    """

    print(f'\n\n§  Applying any known desktop environment tweaks...\n{cnfg.separator}')

    if cnfg.DESKTOP_ENV == 'gnome':
        apply_tweaks_GNOME()
        cnfg.tweak_applied = True

    if cnfg.DESKTOP_ENV == 'kde':
        apply_tweaks_KDE()
        cnfg.tweak_applied = True

    # General (not DE specific) "fancy pants" additions:
    if cnfg.fancy_pants:
        
        print(f'Installing font: ', end='', flush=True)

        # install Fantasque Sans Mono NoLig (no ligatures) from GitHub fork
        font_file   = 'FantasqueSansMono-LargeLineHeight-NoLoopK-NameSuffix.zip'
        font_url    = 'https://github.com/spinda/fantasque-sans-ligatures/releases/download/v1.8.1'
        font_link   = f'{font_url}/{font_file}'

        print(f'Downloading… ', end='', flush=True)

        zip_path    = f'{cnfg.run_tmp_dir}/{font_file}'
        
        if shutil.which('curl'):
            subprocess.run(['curl', '-Lo', zip_path, font_link], 
                        stdout=DEVNULL, stderr=DEVNULL)
        elif shutil.which('wget'):
            subprocess.run(['wget', '-O', zip_path, font_link],
                        stdout=DEVNULL, stderr=DEVNULL)
        else:
            print("\nERROR: Neither 'curl' nor 'wget' is available. Can't install font.")

        if os.path.isfile(zip_path):
            folder_name = font_file.rsplit('.', 1)[0]
            extract_dir = f'{cnfg.run_tmp_dir}/'

            print(f'Unzipping… ', end='', flush=True)

            # Open the zip file and check if it has a top-level directory
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Get the first part of each path in the zip file
                top_dirs = {name.split('/')[0] for name in zip_ref.namelist()}
                
                # If the zip doesn't have a consistent top-level directory, create one and adjust extract_dir
                if len(top_dirs) > 1:
                    extract_dir = os.path.join(extract_dir, folder_name)
                    os.makedirs(extract_dir, exist_ok=True)
                
                zip_ref.extractall(extract_dir)

            # use TTF instead of OTF to try and minimize "stem darkening" effect in KDE
            font_dir        = f'{extract_dir}/TTF/'
            local_fonts_dir = os.path.realpath(os.path.expanduser('~/.local/share/fonts'))

            os.makedirs(local_fonts_dir, exist_ok=True)

            print(f'Moving… ', end='', flush=True)

            for file in os.listdir(font_dir):
                if file.endswith('.ttf'):
                    src_path = os.path.join(font_dir, file)
                    dest_path = os.path.join(local_fonts_dir, file)
                    shutil.move(src_path, dest_path)

            print(f'Refreshing font cache… ', end='', flush=True)

            # Update the font cache
            subprocess.run(['fc-cache', '-f', '-v'],
                            stdout=DEVNULL, stderr=DEVNULL)
            print(f'Done.', flush=True)

            print(f"Installed font: '{folder_name}'")

    if not cnfg.tweak_applied:
        print(f'If nothing printed, no tweaks available for "{cnfg.DESKTOP_ENV}" yet.')


def remove_desktop_tweaks():
    """Undo the relevant desktop tweaks"""

    print(f'\n\n§  Removing any applied desktop environment tweaks...\n{cnfg.separator}')

    # if GNOME, re-enable `overlay-key`
    # gsettings reset org.gnome.mutter overlay-key
    if cnfg.DESKTOP_ENV == 'gnome':
        remove_tweaks_GNOME()

    if cnfg.DESKTOP_ENV == 'kde':
        remove_tweaks_KDE()
        
    print('Removed known desktop tweaks applied by installer.')


def uninstall_toshy():
    print(f'\n\n§  Uninstalling Toshy...\n{cnfg.separator}')
    
    # confirm if user really wants to uninstall
    response = input("\nThis will completely uninstall Toshy. Are you sure? [y/N]: ")
    if response not in ['y', 'Y']:
        print(f"\nToshy uninstall cancelled.\n")
        safe_shutdown()
    else:
        print(f'\nToshy uninstall proceeding...\n')
    
    get_environment_info()
    
    remove_desktop_tweaks()
    
    # stop Toshy manual script if it is running
    toshy_cfg_stop_cmd = os.path.join(home_local_bin, 'toshy-config-stop')
    subprocess.run([toshy_cfg_stop_cmd])
    
    if cnfg.systemctl_present and cnfg.init_system == 'systemd':
        # stop Toshy systemd services if they are running
        toshy_svcs_stop_cmd = os.path.join(home_local_bin, 'toshy-services-stop')
        subprocess.run([toshy_svcs_stop_cmd])
        # run the systemd-remove script
        sysd_rm_cmd = os.path.join(cnfg.toshy_dir_path, 'scripts', 'bin', 'toshy-systemd-remove.sh')
        subprocess.run([sysd_rm_cmd])
    else:
        print(f'System does not seem to be using "systemd". Skipping removal of services.')

    if cnfg.DESKTOP_ENV in ['kde', 'plasma']:
        # unload/uninstall/remove KWin script(s)
        kwin_script_name = 'toshy-dbus-notifyactivewindow'
        try:
            subprocess.run(['kpackagetool5', '-t', 'KWin/Script', '-r', kwin_script_name], check=True)
            print("Successfully removed the KWin script.")
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem removing Toshy KWin script {kwin_script_name}:\n\t{proc_err}')

        # kill the KDE D-Bus service script
        try:
            subprocess.run(['pkill', '-u', cnfg.user_name, '-f', 'toshy_kde_dbus_service'], check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem terminating Toshy KDE D-Bus service script:\n\t{proc_err}')

    # try to remove the KDE D-Bus service autostart file
    user_path           = os.path.expanduser('~')
    autostart_dir_path  = os.path.join(user_path, '.config', 'autostart')
    dbus_svc_dt_file    = os.path.join(autostart_dir_path, 'Toshy_KDE_DBus_Service.desktop')

    dbus_svc_rm_cmd = ['rm', '-f', dbus_svc_dt_file]
    try:
        # do not pass as list (brackets) since it is already a list
        subprocess.run(dbus_svc_rm_cmd, check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy KDE D-Bus service autostart:\n\t{proc_err}')

    # terminate the tray icon process
    stop_tray_cmd = ['pkill', '-u', cnfg.user_name, '-f', 'toshy_tray']
    try:
        # do not pass as list (brackets) since it is already a list
        subprocess.run(stop_tray_cmd, check=True)
    except subprocess.CalledProcessError as proc_err:
        print(f'Problem stopping the tray icon process:\n\t{proc_err}')
    # remove the tray icon autostart file
    tray_autostart_file = os.path.join(autostart_dir_path, 'Toshy_Tray.desktop')

    tray_autostart_rm_cmd = ['rm', '-f', tray_autostart_file]
    try:
        # do not pass as list (brackets) since it is already a list
        subprocess.run(tray_autostart_rm_cmd, check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy tray icon autostart:\n\t{proc_err}')

    # run the desktopapps-remove script
    apps_rm_cmd = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-desktopapps-remove.sh')
    try:
        subprocess.run([apps_rm_cmd], check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy desktop apps:\n\t{proc_err}')

    # run the bincommands-remove script
    bin_rm_cmd = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-bincommands-remove.sh')
    try:
        subprocess.run([bin_rm_cmd], check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy bin commands apps:\n\t{proc_err}')

    response_rm_udev_rules = input('Remove the Toshy "udev/uinput" rules file? [y/N]: ')
    if response_rm_udev_rules.lower() == 'y':
        elevate_privileges()
        # define the udev rules file path
        udev_rules_file = '/etc/udev/rules.d/90-toshy-keymapper-input.rules'
        # remove the 'udev' rules file
        try:
            subprocess.run(['sudo', 'rm', '-f', udev_rules_file], check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem removing Toshy udev rules file:\n\t{proc_err}')
        # refresh the active 'udev' rules
        reload_udev_rules()

    print()
    print()
    print(cnfg.separator)
    print(f'Toshy uninstall complete. Reboot if indicated above with ASCII banner.')
    print(f"The '~/.config/toshy' folder with your settings has NOT been removed.")
    print(f'Please report any problems or leftover files/commands on the GitHub repo:')
    print(f'https://github.com/RedBearAK/toshy/issues/')
    print(cnfg.separator)
    print()


def handle_cli_arguments():
    """Deal with CLI arguments given to installer script"""
    parser = argparse.ArgumentParser(
        description='Toshy Installer - options are mutually exclusive',
        epilog='Default action: Install Toshy'
    )

    # This would require a 'lambda' to be able to pass 'cnfg' object to 'main()':
    # parser.set_defaults(func=main)
    
    # Add arguments
    parser.add_argument(
        '--override-distro',
        type=str,
        # dest='override_distro',
        help=f'Override auto-detection of distro name/type. See --list-distros'
    )
    parser.add_argument(
        '--list-distros',
        action='store_true',
        help='Display list of distro names to use with --override-distro'
    )
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Uninstall Toshy'
    )
    parser.add_argument(
        '--show-env',
        action='store_true',
        help='Show the environment the installer detects, and exit'
    )
    parser.add_argument(
        '--apply-tweaks',
        action='store_true',
        help='Apply desktop environment tweaks only, no install'
    )
    parser.add_argument(
        '--remove-tweaks',
        action='store_true',
        help='Remove desktop environment tweaks only, no install'
    )
    parser.add_argument(
        '--fancy-pants',
        action='store_true',
        help='Optional: install font, KDE task switcher, etc...'
    )

    args = parser.parse_args()

    # Check the values of arguments and perform actions accordingly
    if args.override_distro:
        cnfg.override_distro = args.override_distro
        # proceed with normal install sequence
        main(cnfg)
        safe_shutdown(0)
    elif args.list_distros:
        print(  f'Distro names known to the Toshy installer (to use with --override-distro):'
                f'\n\n\t{get_distro_names()}\n')
        safe_shutdown(0)
    elif args.show_env:
        get_environment_info()
        safe_shutdown(0)
    elif args.apply_tweaks:
        apply_desktop_tweaks()
        safe_shutdown(0)
    elif args.remove_tweaks:
        remove_desktop_tweaks()
        safe_shutdown(0)
    elif args.uninstall:
        uninstall_toshy()
    elif args.fancy_pants:
        cnfg.fancy_pants = True
        main(cnfg)
    else:
        # proceed with normal install sequence if no CLI args given
        main(cnfg)


def main(cnfg: InstallerSettings):
    """Main installer function to call specific functions in proper sequence"""

    dot_Xmodmap_warning()
    ask_is_distro_updated()
    ask_add_home_local_bin()

    get_environment_info()

    valid_distro_names = get_distro_names()
    if cnfg.DISTRO_NAME not in valid_distro_names:
        print()
        print(f"Installer does not know how to deal with distro '{cnfg.DISTRO_NAME}'\n")
        print(f'Maybe try one of these with "--override-distro" option:\n\t{valid_distro_names}')
        safe_shutdown(1)

    elevate_privileges()

    load_uinput_module()
    install_udev_rules()
    verify_user_groups()

    install_distro_pkgs()

    clone_keyszer_branch()

    backup_toshy_config()
    install_toshy_files()

    setup_python_virt_env()
    install_pip_packages()

    install_bin_commands()
    install_desktop_apps()

    # Python D-Bus service script also does this, but this will refresh if script changes
    if cnfg.DESKTOP_ENV in ['kde', 'plasma']:
        setup_kwin2dbus_script()

    setup_kde_dbus_service()

    setup_systemd_services()

    autostart_tray_icon()
    apply_desktop_tweaks()

    if cnfg.DESKTOP_ENV == 'gnome':
        def is_extension_enabled(extension_uuid):
            output = subprocess.check_output(
                        ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions'])
            extensions = output.decode().strip().replace("'", "").split(",")
            return extension_uuid in extensions

        if is_extension_enabled("appindicatorsupport@rgcjonas.gmail.com"):
            print("AppIndicator extension is enabled. Tray icon should work.")
            # pass
        else:
            print()
            debug(f"RECOMMENDATION: Install 'AppIndicator' GNOME extension\n"
                "Easiest method: 'flatpak install extensionmanager', search for 'appindicator'\n",
                ctx="!!")

    if cnfg.should_reboot or os.path.exists(cnfg.reboot_tmp_file):
        cnfg.should_reboot = True
        # create reboot reminder temp file, in case installer is run again
        if not os.path.exists(cnfg.reboot_tmp_file):
            os.mknod(cnfg.reboot_tmp_file)
        print()
        print()
        print()
        print(cnfg.separator)
        print(cnfg.separator)
        print(cnfg.reboot_ascii_art)
        print(cnfg.separator)
        print(cnfg.separator)
        print(f'{cnfg.sep_char * 2}  Toshy install complete. Report issues on the GitHub repo.')
        print(f'{cnfg.sep_char * 2}  https://github.com/RedBearAK/toshy/issues/')
        print(f'{cnfg.sep_char * 2}  >>  ALERT: Permissions changed. You MUST reboot for Toshy to work.')
        print(cnfg.separator)
        print(cnfg.separator)
        print()
    else:
        # Try to start the tray icon immediately, if reboot is not indicated
        tray_icon_cmd = [os.path.join(cnfg.home_dir_path, '.local', 'bin', 'toshy-tray')]
        # Try to launch the tray icon in a separate process not linked to current shell
        # Also, suppress output that might confuse the user
        subprocess.Popen(tray_icon_cmd, close_fds=True, stdout=DEVNULL, stderr=DEVNULL)
        print()
        print()
        print()
        print(cnfg.separator)
        print(cnfg.separator)
        print(f'{cnfg.sep_char * 2}  Toshy install complete. Rebooting should not be necessary.')
        print(f'{cnfg.sep_char * 2}  Report issues on the GitHub repo.')
        print(f'{cnfg.sep_char * 2}  https://github.com/RedBearAK/toshy/issues/')
        print(cnfg.separator)
        print(cnfg.separator)
        print()
        if cnfg.SESSION_TYPE == 'wayland' and cnfg.DESKTOP_ENV == 'kde':
            print(f'Switch to a different window ONCE to get KWin script to start working!')

    if cnfg.remind_extensions or (cnfg.DESKTOP_ENV == 'gnome' and cnfg.SESSION_TYPE == 'wayland'):
        print(f'You MUST install GNOME EXTENSIONS if using Wayland+GNOME! See Toshy README.')

    print()   # blank line to avoid crowding the prompt after install is done
    safe_shutdown()


if __name__ == '__main__':

    print()   # blank line in terminal to start things off

    # Invalidate any `sudo` ticket that might be hanging around, to maximize 
    # the length of time before `sudo` might demand the password again
    try:
        subprocess.run(['sudo', '-k'], check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f"ERROR: 'sudo' found, but 'sudo -k' did not work. Very strange.\n\t{proc_err}")

    cnfg = InstallerSettings()

    handle_cli_arguments()
