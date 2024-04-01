#!/usr/bin/env python3

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'     # prevent this script from creating cache files
import re
import sys
import pwd
import grp
import random
import string
import signal
import shutil
import sqlite3
import zipfile
import argparse
import builtins
import datetime
import platform
import textwrap
import subprocess

from subprocess import DEVNULL, PIPE
from typing import Dict, List, Tuple, Optional

# local import
import lib.env as env
from lib.logger import debug, error, warn, info
from lib import logger

logger.FLUSH = True

# Save the original print function
original_print = builtins.print

# Override the print function
def print(*args, **kwargs):
    kwargs['flush'] = True  # Set flush to True
#    original_print("Using custom print:", *args, **kwargs)  # Call the original print
    original_print(*args, **kwargs)  # Call the original print

# Replace the built-in print with our custom print
builtins.print = print

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser. Exiting.")
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

original_PATH_str       = os.getenv('PATH')
if original_PATH_str is None:
    print()
    error(f"ERROR: PATH variable is not set. This is abnormal. Exiting.")
    print()
    sys.exit(1)

home_dir                = os.path.expanduser('~')
trash_dir               = os.path.join(home_dir, '.local', 'share', 'Trash')
this_file_path          = os.path.realpath(__file__)
this_file_dir           = os.path.dirname(this_file_path)
this_file_name          = os.path.basename(__file__)
if trash_dir in this_file_path or '/trash/' in this_file_path.lower():
    print()
    error(f"Path to this file:\n\t{this_file_path}")
    error(f"You probably did not intend to run this from the TRASH. See path. Exiting.")
    print()
    sys.exit(1)

home_local_bin          = os.path.join(home_dir, '.local', 'bin')
run_tmp_dir             = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'

good_path_tmp_file      = 'toshy_installer_says_path_is_good'
good_path_tmp_path      = os.path.join(run_tmp_dir, good_path_tmp_file)

fix_path_tmp_file       = 'toshy_installer_says_fix_path'
fix_path_tmp_path       = os.path.join(run_tmp_dir, fix_path_tmp_file)

# set a standard path for duration of script run, to avoid issues with user customized paths
os.environ['PATH']  = '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin'

# deactivate Python virtual environment, if one is active, to avoid issues with sys.executable
if sys.prefix != sys.base_prefix:
    os.environ["VIRTUAL_ENV"] = ""
    sys.path = [p for p in sys.path if not p.startswith(sys.prefix)]
    sys.prefix = sys.base_prefix

# Check if 'sudo' command is available to user
if not shutil.which('sudo'):
    print("Error: 'sudo' not found. Installer will fail without it. Exiting.")
    sys.exit(1)

do_not_ask_about_path = None
if home_local_bin in original_PATH_str:
    with open(good_path_tmp_path, 'a') as file:
        file.write('Nothing to see here.')
    # subprocess.run(['touch', path_good_tmp_path])
    do_not_ask_about_path = True
else:
    debug("Home user local bin not part of PATH string.")
# do the 'else' of creating 'path_fix_tmp_path' later in function that prompts user

# system Python version
py_ver_mjr, py_ver_mnr  = sys.version_info[:2]
py_interp_ver_tup       = (py_ver_mjr, py_ver_mnr)
py_pkg_ver_str          = f'{py_ver_mjr}{py_ver_mnr}'


class InstallerSettings:
    """Set up variables for necessary information to be used by all functions"""
    def __init__(self) -> None:
        sep_reps                    = 80
        self.sep_char               = '='
        self.separator              = self.sep_char * sep_reps
        self.override_distro        = None
        self.DISTRO_ID            = None
        self.DISTRO_VER: str        = ""
        self.VARIANT_ID             = None
        self.SESSION_TYPE           = None
        self.DESKTOP_ENV            = None
        self.DE_MAJ_VER: str        = ""

        self.distro_mjr_ver: str    = ""
        self.distro_mnr_ver: str    = ""

        self.valid_KDE_vers         = ['6', '5', '4', '3']

        self.systemctl_present      = shutil.which('systemctl') is not None
        self.init_system            = None

        self.pkgs_for_distro        = None

        self.qdbus                  = 'qdbus-qt5' if shutil.which('qdbus-qt5') else 'qdbus'

        # current stable Python release version (TODO: update when needed):
        # 3.11 Release Date: Oct. 24, 2022
        self.curr_py_rel_ver_mjr     = 3
        self.curr_py_rel_ver_mnr     = 11
        self.curr_py_rel_ver_tup     = (self.curr_py_rel_ver_mjr, self.curr_py_rel_ver_mnr)
        self.curr_py_rel_ver_str     = f'{self.curr_py_rel_ver_mjr}.{self.curr_py_rel_ver_mnr}'

        self.py_interp_ver_str      = f'{py_ver_mjr}.{py_ver_mnr}'
        self.py_interp_path         = shutil.which('python3')

        self.toshy_dir_path         = os.path.join(home_dir, '.config', 'toshy')
        self.db_file_name           = 'toshy_user_preferences.sqlite'
        self.db_file_path           = os.path.join(self.toshy_dir_path, self.db_file_name)
        self.backup_succeeded       = None
        self.existing_cfg_data      = None
        self.existing_cfg_slices    = None
        self.venv_path              = os.path.join(self.toshy_dir_path, '.venv')

        self.keyszer_tmp_path       = os.path.join(this_file_dir, 'keyszer-temp')

        self.keyszer_branch         = 'device_grab_fix'
        # self.keyszer_branch         = 'environ_api_hyprland'
        self.keyszer_url            = 'https://github.com/RedBearAK/keyszer.git'
        self.keyszer_clone_cmd      = f'git clone -b {self.keyszer_branch} {self.keyszer_url}'

        self.input_group            = 'input'
        self.user_name              = pwd.getpwuid(os.getuid()).pw_name

        self.barebones_config       = None
        self.autostart_tray_icon    = True
        self.skip_native            = None
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


def safe_shutdown(exit_code: int):
    """do some stuff on the way out"""
    # good place to do some file cleanup?
    # 
    # invalidate the sudo ticket, don't leave system in "superuser" state
    subprocess.run(['sudo', '-k'])
    print()                         # avoid crowding the prompt on exit
    sys.exit(exit_code)


def show_reboot_prompt():
    """show the big ASCII reboot prompt"""
    print()
    print()
    print()
    print(cnfg.separator)
    print(cnfg.separator)
    print(cnfg.reboot_ascii_art)
    print(cnfg.separator)
    print(cnfg.separator)


def get_environment_info():
    """Get back the distro name (ID), distro version, session type and desktop 
        environment from `env.py` module"""
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

    env_info_dct   = env.get_env_info()

    # Avoid casefold() errors by converting all to strings
    if cnfg.override_distro:
        cnfg.DISTRO_ID    = str(cnfg.override_distro).casefold()
    else:
        cnfg.DISTRO_ID    = str(env_info_dct.get('DISTRO_ID',     'keymissing')).casefold()
    cnfg.DISTRO_VER     = str(env_info_dct.get('DISTRO_VER',    'keymissing')).casefold()
    cnfg.VARIANT_ID     = str(env_info_dct.get('VARIANT_ID',    'keymissing')).casefold()
    cnfg.SESSION_TYPE   = str(env_info_dct.get('SESSION_TYPE',  'keymissing')).casefold()
    cnfg.DESKTOP_ENV    = str(env_info_dct.get('DESKTOP_ENV',   'keymissing')).casefold()
    cnfg.DE_MAJ_VER     = str(env_info_dct.get('DE_MAJ_VER',    'keymissing')).casefold()

    # split out the major version from the minor version, if there is one
    distro_ver_parts            = cnfg.DISTRO_VER.split('.') if cnfg.DISTRO_VER else []
    cnfg.distro_mjr_ver         = distro_ver_parts[0] if distro_ver_parts else 'NO_VER'
    cnfg.distro_mnr_ver         = distro_ver_parts[1] if len(distro_ver_parts) > 1 else 'no_mnr_ver'

    debug('Toshy installer sees this environment:'
        f"\n\t DISTRO_ID        = '{cnfg.DISTRO_ID}'"
        f"\n\t DISTRO_VER       = '{cnfg.DISTRO_VER}'"
        f"\n\t VARIANT_ID       = '{cnfg.VARIANT_ID}'"
        f"\n\t SESSION_TYPE     = '{cnfg.SESSION_TYPE}'"
        f"\n\t DESKTOP_ENV      = '{cnfg.DESKTOP_ENV}'"
        f"\n\t DE_MAJ_VER       = '{cnfg.DE_MAJ_VER}'"
        # '\n', ctx='EV')
        '', ctx='EV')


def fancy_str(text, color_name, *, bold=False):
    """
    Return text wrapped in the specified color code.
    :param text: Text to be colorized.
    :param color_name: Natural name of the color.
    :param bold: Boolean to indicate if text should be bold.
    :return: Colorized string if terminal likely supports it, otherwise the original string.
    """
    color_codes = { 'red': '31', 'green': '32', 'yellow': '33', 'blue': '34', 
                    'magenta': '35', 'cyan': '36', 'white': '37', 'default': '0'}
    if os.getenv('COLORTERM') and color_name in color_codes:
        bold_code = '1;' if bold else ''
        return f"\033[{bold_code}{color_codes[color_name]}m{text}\033[0m"
    else:
        return text


def call_attn_to_pwd_prompt_if_sudo_tkt_exp():
    """Utility function to emphasize the sudo password prompt"""
    try:
        subprocess.run( ['sudo', '-n', 'true'], stdout=DEVNULL, stderr=DEVNULL, check=True)
    except subprocess.CalledProcessError:
        # sudo ticket not valid, requires a password, so get user attention
        print()
        print(fancy_str('  ----------------------------------------  ', 'blue', bold=True))
        print(fancy_str('  -- SUDO PASSWORD REQUIRED TO CONTINUE --  ', 'blue', bold=True))
        print(fancy_str('  ----------------------------------------  ', 'blue', bold=True))
        print()


def enable_prompt_for_reboot():
    """Utility function to make sure user is reminded to reboot if necessary"""
    cnfg.should_reboot = True
    if not os.path.exists(cnfg.reboot_tmp_file):
        os.mknod(cnfg.reboot_tmp_file)


def show_task_completed_msg():
    """Utility function to show a standard message after each major section completes"""
    print(fancy_str('   >> Task completed successfully <<   ', 'green', bold=True))


def dot_Xmodmap_warning():
    """Check for '.Xmodmap' file in user's home folder, show warning about mod key remaps"""

    xmodmap_file_path = os.path.join(home_dir, '.Xmodmap')

    if os.path.isfile(xmodmap_file_path):
        print()
        print(f'{cnfg.separator}')
        print(f'{cnfg.separator}')
        warn_str    = "\t WARNING: You have an '.Xmodmap' file in your home folder!!!"
        print(fancy_str(warn_str, "red"))
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
            error("Code does not match! Try the installer again after dealing with '.Xmodmap'.")
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
            with open(fix_path_tmp_path, 'a') as file:
                file.write('Nothing to see here.')


def elevate_privileges():
    """Elevate privileges early in the installer process"""
    call_attn_to_pwd_prompt_if_sudo_tkt_exp()
    subprocess.run(['sudo', 'bash', '-c', 'echo -e "\nUsing elevated privileges..."'], check=True)


#####################################################################################################
###   START OF NATIVE PACKAGE INSTALLER SECTION
#####################################################################################################


distro_groups_map: Dict[str, List[str]] = {

    # separate references for RHEL types versus Fedora types
    'fedora-based':             ["fedora", "fedoralinux", "ultramarine", "nobara"],
    'rhel-based':               ["rhel", "almalinux", "rocky", "eurolinux", "centos"],

    # separate references for Fedora immutables using rpm-ostree
    'fedora-immutables':        ["silverblue-experimental", "kinoite-experimental"],

    # separate references for Tumbleweed types versus Leap types
    'tumbleweed-based':         ["opensuse-tumbleweed"],
    'leap-based':               ["opensuse-leap"],
    'microos-based':            ["opensuse-microos", "opensuse-aeon", "opensuse-kalpa"],

    'mandriva-based':           ["openmandriva"],

    'ubuntu-based':             ["ubuntu", "mint", "pop", "elementary", "neon", "tuxedo", "zorin"],
    'debian-based':             ["deepin", "lmde", "peppermint", "debian", "kali", "q4os"],

    'arch-based':               ["arch", "arcolinux", "endeavouros", "garuda", "manjaro"],

    'solus-based':              ["solus"],

    'void-based':               ["void"],

    # 'kaos-based':               ["kaos"],
    # Add more as needed...
}

pkg_groups_map: Dict[str, List[str]] = {

    # NOTE: Do not add 'gnome-shell-extension-appindicator' to Fedora/RHELs.
    #       This will install extension but requires logging out of GNOME to activate.
    'fedora-based':        ["cairo-devel", "cairo-gobject-devel",
                            "dbus-daemon", "dbus-devel",
                            "evtest",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator-gtk3", "libnotify",
                            "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
                            "systemd-devel",
                            "wayland-devel",
                            "xset",
                            "zenity"],

    'rhel-based':          ["cairo-devel", "cairo-gobject-devel",
                            "dbus-daemon", "dbus-devel",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator-gtk3", "libnotify",
                            "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
                            "systemd-devel",
                            "xset",
                            "zenity"],

    'fedora-immutables':   ["cairo-devel", "cairo-gobject-devel",
                            "dbus-daemon", "dbus-devel",
                            "evtest",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator-gtk3", "libnotify",
                            "python3-dbus", "python3-devel", "python3-pip", "python3-tkinter",
                            "systemd-devel",
                            "xset",
                            "zenity"],

    # NOTE: for openSUSE (Tumbleweed, not applicable to Leap):
    # How to get rid of the need to use specific version numbers in packages: 
    # pkgconfig(packagename)>=N.nn (version symbols optional)
    # How to query a package to see what the equivalent pkgconfig(packagename) syntax would be:
    # rpm -q --provides packagename | grep -i pkgconfig
    'tumbleweed-based':    ["cairo-devel",
                            "dbus-1-daemon", "dbus-1-devel",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator3-devel", "libnotify-tools",
                            # f"python{py_pkg_ver_str}-dbus-python-devel",
                            "python3-dbus-python-devel",
                            # f"python{py_pkg_ver_str}-devel",
                            "python3-devel",
                            # f"python{py_pkg_ver_str}-tk",
                            "python3-tk",
                            "systemd-devel",
                            "tk", "typelib-1_0-AyatanaAppIndicator3-0_1",
                            "zenity"],

    # TODO: update Leap Python package versions as it makes newer Python available
    'leap-based':          ["cairo-devel",
                            "dbus-1-devel",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator3-devel", "libnotify-tools",
                            "python3-dbus-python-devel",
                                "python311",
                                "python311-devel",
                                "python311-tk",
                            "systemd-devel",
                            "tk", "typelib-1_0-AyatanaAppIndicator3-0_1",
                            "zenity"],

    # NOTE: This is a copy of Tumbleweed-based package list! For use with 'transactional-update'.
    # But this needs to use the versioned package names because we are checking with 'rpm -q'.
    'microos-based':       ["cairo-devel",
                            "dbus-1-daemon", "dbus-1-devel",
                            "gcc", "git", "gobject-introspection-devel",
                            "libappindicator3-devel", "libnotify-tools",
                            f"python{py_pkg_ver_str}-dbus-python-devel",
                            # "python3-dbus-python-devel",
                            f"python{py_pkg_ver_str}-devel",
                            # "python3-devel",
                            f"python{py_pkg_ver_str}-tk",
                            # "python3-tk",
                            "systemd-devel",
                            "tk", "typelib-1_0-AyatanaAppIndicator3-0_1",
                            "zenity"],

    'mandriva-based':      ["cairo-devel",
                            "dbus-daemon", "dbus-devel",
                            "git", "gobject-introspection-devel",
                            "lib64ayatana-appindicator3_1", "lib64ayatana-appindicator3-gir0.1",
                                "lib64cairo-gobject2", "lib64python-devel", "lib64systemd-devel",
                                "libnotify",
                            "python-dbus", "python-dbus-devel", "python-ensurepip", "python3-pip",
                            "task-devel", "tkinter",
                            "xset",
                            "zenity"],

    # TODO: see if this needs "dbus-daemon" added as dependency (for containers)
    'ubuntu-based':        ["curl",
                            "git", "gir1.2-ayatanaappindicator3-0.1",
                            "input-utils",
                            "libcairo2-dev", "libdbus-1-dev", "libgirepository1.0-dev",
                                "libjpeg-dev", "libnotify-bin", "libsystemd-dev", "libwayland-dev",
                            "python3-dbus", "python3-dev", "python3-pip", "python3-tk",
                                "python3-venv",
                            "zenity"],

    # TODO: see if this needs "dbus-daemon" added as dependency (for containers)
    'debian-based':        ["curl",
                            "git", "gir1.2-ayatanaappindicator3-0.1",
                            "input-utils",
                            "libcairo2-dev", "libdbus-1-dev", "libgirepository1.0-dev",
                                "libjpeg-dev", "libnotify-bin", "libsystemd-dev", "libwayland-dev",
                            "python3-dbus", "python3-dev", "python3-pip", "python3-tk",
                                "python3-venv",
                            "zenity"],

    # TODO: see if this needs "dbus-daemon" added as dependency (for containers)
    'arch-based':          ["cairo",
                            "dbus",
                            "evtest",
                            "gcc", "git", "gobject-introspection",
                            "libappindicator-gtk3", "libnotify",
                            "pkg-config", "python", "python-dbus", "python-pip",
                            "systemd",
                            "tk",
                            "zenity"],

    # TODO: see if this needs "dbus-daemon" added as dependency (for containers)
    'solus-based':         ["gcc", "git",
                            "libayatana-appindicator", "libcairo-devel", "libnotify",
                            "pip", "python3-dbus", "python3-devel", "python3-tkinter",
                                "python-dbus-devel", "python-gobject-devel",
                            "systemd-devel",
                            "zenity"],

    'void-based':          ["cairo-devel", "curl",
                            "dbus-devel",
                            "evtest",
                            "gcc", "git",
                            "libayatana-appindicator-devel", "libgirepository-devel", "libnotify",
                            "pkg-config", "python3-dbus", "python3-devel", "python3-pip",
                                "python3-pkgconfig", "python3-tkinter",
                            "wayland-devel", "wget",
                            "xset",
                            "zenity"],

    'kaos-based':          ["cairo",
                            "dbus",
                            "evtest",
                            "gcc", "git", "gobject-introspection",
                            "libappindicator-gtk3", "libnotify",
                            "pkg-config", "python", "python-dbus", "python-pip",
                            "systemd",
                            "tk",
                            "zenity"],

}

extra_pkgs_map = {
    # Add a tuple with distro name (ID), major version (or None) and packages to be added...
    # ('distro_name', '22'): ["pkg1", "pkg2", ...],
    # ('distro_name', None): ["pkg1", "pkg2", ...],
}

remove_pkgs_map = {
    # Add a tuple with distro name (ID), major version (or None) and packages to be removed...
    # ('distro_name', '22'): ["pkg1", "pkg2", ...],
    # ('distro_name', None): ["pkg1", "pkg2", ...],
    ('centos', '7'):            ['dbus-daemon', 'gnome-shell-extension-appindicator'],
    ('deepin', None):           ['input-utils'],
}


pip_pkgs   = [
    # pinning pygobject to 3.44.1 (or earlier) to get through install on RHEL 8.x and clones
    "lockfile", "dbus-python", "systemd-python", "pygobject<=3.44.1", "tk",
    "sv_ttk", "watchdog", "psutil", "hyprpy", "i3ipc", "pywayland", # "pywlroots",

    # installing 'pywlroots' will require native pkg 'libxkbcommon-devel' (Fedora)

    # TODO: Check on 'python-xlib' project by early-mid 2024 to see if this bug is fixed:
    #   [AttributeError: 'BadRRModeError' object has no attribute 'sequence_number']
    # If the bug is fixed, remove pinning to v0.31 here:

    # everything from 'inotify-simple' to 'six' is just to make `keyszer` install smoother
    "inotify-simple", "evdev", "appdirs", "ordered-set", "python-xlib==0.31", "six"
]


def get_supported_distro_ids() -> str:
    """Utility function to return list of available distro names (IDs)"""
    distro_list: List[str] = []

    for group in distro_groups_map.values():
        distro_list.extend(group)

    sorted_distro_list: List[str] = sorted(distro_list)
    prev_char: str = sorted_distro_list[0][0]
    # start index with the initial letter
    distro_index = prev_char.upper() + ": "
    line_length = len(distro_index)             # initial line length

    for distro in sorted_distro_list:
        if distro[0] != prev_char:
            distro_index = distro_index[:-2]    # remove last comma and space
            line_length -= 2
            distro_index += "\n\t" + distro[0].upper() + ": "
            line_length = len(distro[0]) + 2    # reset line length
            prev_char = distro[0]
        
        next_distro_with_comma = distro + ", "
        if line_length + len(next_distro_with_comma) > 80:
            distro_index += "\n\t    "          # insert newline and tab/spaces for continuation
            line_length = len("\t    ")         # reset line length to indent size

        distro_index += next_distro_with_comma
        line_length += len(next_distro_with_comma)

    return distro_index[:-2]  # remove the last comma and space


def exit_with_invalid_distro_error(pkg_mgr_err=None):
    """Utility function to show error message and exit when distro is not valid"""
    print()
    error(f'ERROR: Installer does not know how to handle distro: "{cnfg.DISTRO_ID}"')
    if pkg_mgr_err:
        error('ERROR: No valid package manager logic was encountered for this distro.')
    print()
    print(f'Try some options in "./{this_file_name} --help".')
    print()
    print(f'Maybe try one of these with "--override-distro" option:\n\n\t{get_supported_distro_ids()}')
    safe_shutdown(1)


class DistroQuirksHandler:
    """Object to contain methods for prepping specific distro variants that
        need some extra prep work before installing the native package list"""

    def __init__(self) -> None:
        pass

    def handle_quirks_CentOS_7(self):
        print('Doing prep/checks for CentOS 7...')

        # pin 'evdev' pip package to version 1.6.1 for CentOS 7 to
        # deal with ImportError and undefined symbol UI_GET_SYSNAME
        global pip_pkgs
        pip_pkgs = [pkg if pkg != "evdev" else "evdev==1.6.1" for pkg in pip_pkgs]

        native_pkg_installer.check_for_pkg_mgr_cmd('yum')
        yum_cmd_lst = ['sudo', 'yum', 'install', '-y']
        if py_interp_ver_tup >= (3, 8):
            print(f"Good, Python version is 3.8 or later: "
                    f"'{cnfg.py_interp_ver_str}'")
        else:
            try:
                scl_repo = ['centos-release-scl']
                subprocess.run(yum_cmd_lst + scl_repo, check=True)
                py38_pkgs = [   'rh-python38',
                                'rh-python38-python-devel',
                                'rh-python38-python-tkinter',
                                'rh-python38-python-wheel-wheel'    ]
                subprocess.run(yum_cmd_lst + py38_pkgs, check=True)
                #
                # set new Python interpreter version and path to reflect what was installed
                cnfg.py_interp_path     = '/opt/rh/rh-python38/root/usr/bin/python3.8'
                cnfg.py_interp_ver_str  = '3.8'
                # avoid using systemd packages/services for CentOS
                cnfg.systemctl_present = False
            except subprocess.CalledProcessError as proc_err:
                print()
                error(f'ERROR: (CentOS 7-specific) Problem installing/enabling Python 3.8:'
                        f'\n\t{proc_err}')
                safe_shutdown(1)
        # use yum to install dnf package manager
        try:
            subprocess.run(yum_cmd_lst + ['dnf'], check=True)
        except subprocess.CalledProcessError as proc_err:
            print()
            error(f'ERROR: Failed to install DNF package manager.\n\t{proc_err}')
            safe_shutdown(1)

    def handle_quirks_CentOS_Stream_8(self):
        print('Doing prep/checks for CentOS Stream 8...')
        min_mnr_ver = cnfg.curr_py_rel_ver_mnr - 3           # check up to 2 vers before current
        max_mnr_ver = cnfg.curr_py_rel_ver_mnr + 3           # check up to 3 vers after current
        py_minor_ver_rng = range(max_mnr_ver, min_mnr_ver, -1)
        if py_interp_ver_tup < cnfg.curr_py_rel_ver_tup:
            print(f"Checking for appropriate Python version on system...")
            for check_py_minor_ver in py_minor_ver_rng:
                if shutil.which(f'python3.{check_py_minor_ver}'):
                    cnfg.py_interp_path = shutil.which(f'python3.{check_py_minor_ver}')
                    cnfg.py_interp_ver_str = f'3.{check_py_minor_ver}'
                    print(f'Found Python version {cnfg.py_interp_ver_str} available.')
                    break
            else:
                error(  f'ERROR: Did not find any appropriate Python interpreter version.')
                safe_shutdown(1)
        try:
            # for dbus-python
            subprocess.run(['sudo', 'dnf', 'install', '-y',
                            f'python{cnfg.py_interp_ver_str}-devel'], check=True)
            # for Toshy Preferences GUI app
            subprocess.run(['sudo', 'dnf', 'install', '-y',
                            f'python{cnfg.py_interp_ver_str}-tkinter'], check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'ERROR: Problem installing necessary packages on CentOS Stream 8:'
                    f'\n\t{proc_err}')
            safe_shutdown(1)

    def handle_quirks_RHEL(self):
        print('Doing prep/checks for RHEL-type distro...')

        # for libappindicator-gtk3: sudo dnf install -y epel-release
        try:
            native_pkg_installer.check_for_pkg_mgr_cmd('dnf')
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'epel-release'], check=True)
            subprocess.run(['sudo', 'dnf', 'makecache'], check=True)
        except subprocess.CalledProcessError as proc_err:
            print()
            error(f'ERROR: Problem while adding "epel-release" repo.\n\t{proc_err}')
            safe_shutdown(1)

        # Need to do this AFTER the 'epel-release' install
        if cnfg.DISTRO_ID != 'centos' and cnfg.distro_mjr_ver in ['8']:
            # enable CRB repo on RHEL 8.x distros, but not CentOS Stream 8:
            cmd_lst = ['sudo', '/usr/bin/crb', 'enable']
            try:
                subprocess.run(cmd_lst, check=True)
            except subprocess.CalledProcessError as proc_err:
                print()
                error(f'ERROR: Problem while enabling CRB repo.\n\t{proc_err}')
                safe_shutdown(1)
            #
            # TODO: Add higher version if ever necessary (keep minimum 3.8)
            potential_versions = ['3.14', '3.13', '3.12', '3.11', '3.10', '3.9', '3.8']
            #
            for version in potential_versions:
                # check if the version is already installed
                if shutil.which(f'python{version}'):
                    cnfg.py_interp_path     = f'/usr/bin/python{version}'
                    cnfg.py_interp_ver_str  = version
                    break
                # try to install the corresponding packages
                cmd_lst = ['sudo', 'dnf', 'install', '-y']
                pkg_lst = [f'python{version}', f'python{version}-devel', f'python{version}-tkinter']
                try:
                    subprocess.run(cmd_lst + pkg_lst, check=True)
                    # if the installation succeeds, set the interpreter path and version
                    cnfg.py_interp_path     = f'/usr/bin/python{version}'
                    cnfg.py_interp_ver_str  = version
                    break
                # if the installation fails, continue with the next version
                except subprocess.CalledProcessError:
                    print(f'No match for potential Python version {version}.')
                    continue
            # this 'else' is part of the 'for' loop above, not an 'if' condition
            else:
                # if no suitable version was found, print an error message and exit
                error('ERROR: Did not find any appropriate Python interpreter version.')
                safe_shutdown(1)

        if cnfg.distro_mjr_ver in ['9']:
            #
            # enable "CodeReady Builder" repo for 'gobject-introspection-devel' only on 
            # RHEL 9.x and CentOS Stream 9 (TODO: Add v10 if it uses the same command):
            # sudo dnf config-manager --set-enabled crb
            cmd_lst = ['sudo', 'dnf', 'config-manager', '--set-enabled', 'crb']
            try:
                subprocess.run(cmd_lst, check=True)
            except subprocess.CalledProcessError as proc_err:
                print()
                error(f'ERROR: Problem while enabling CRB repo:\n\t{proc_err}')
                safe_shutdown(1)


class NativePackageInstaller:
    """Object to handle tasks related to installing native packages"""
    def __init__(self) -> None:
        pass

    def check_for_pkg_mgr_cmd(self, pkg_mgr_cmd):
        """Make sure native package installer command exists before using it, or exit"""
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
        if not shutil.which(pkg_mgr_cmd):
            print()
            error(f'Package manager command ({pkg_mgr_cmd}) not available. Unable to continue.')
            safe_shutdown(1)

    def exit_with_pkg_install_error(self, proc_err):
        """shutdown with error message if there is a problem with installing package list"""
        print()
        error(f'ERROR: Problem installing package list for distro type:\n\t{proc_err}')
        safe_shutdown(1)

    def show_pkg_install_success_msg(self):
        # Have something come out even if package list is empty (like Arch after initial run)
        print('All necessary native distro packages are installed.')

    def install_pkg_list(self, cmd_lst, pkg_lst):
        """Install packages using the given package manager command list and package list."""
        
        # Extract the package manager command to check
        pkg_mgr_cmd = next((cmd for cmd in cmd_lst if cmd != 'sudo'), None)
        # If we couldn't extract the command, exit with an error
        if not pkg_mgr_cmd:
            error(f'No valid package manager command in provided command list:\n\t{cmd_lst}')
            safe_shutdown(1)
        
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
        self.check_for_pkg_mgr_cmd(pkg_mgr_cmd)
        
        # Execute the package installation command
        try:
            subprocess.run(cmd_lst + pkg_lst, check=True)
            # self.show_pkg_install_success_msg()
        except subprocess.CalledProcessError as proc_err:
            self.exit_with_pkg_install_error(proc_err)


def install_distro_pkgs():
    """Install needed packages from list for distro type"""
    print(f'\n\n§  Installing native packages for this distro type...\n{cnfg.separator}')

    pkg_group = None
    for group, distros in distro_groups_map.items():
        if cnfg.DISTRO_ID in distros:
            pkg_group = group
            break

    if pkg_group is None:
        print()
        print(f"ERROR: No list of packages found for this distro: '{cnfg.DISTRO_ID}'")
        print(f'Installation cannot proceed without a list of packages. Sorry.')
        print(f'Try some options in "./{this_file_name} --help"')
        safe_shutdown(1)

    cnfg.pkgs_for_distro = pkg_groups_map[pkg_group]

    # Add extra packages for specific distros and versions
    for version in [cnfg.distro_mjr_ver, None]:
        distro_key = (cnfg.DISTRO_ID, version)
        if distro_key in extra_pkgs_map:
            cnfg.pkgs_for_distro.extend(extra_pkgs_map[distro_key])

    # Remove packages for specific distros and versions
    for version in [cnfg.distro_mjr_ver, None]:
        distro_key = (cnfg.DISTRO_ID, version)
        if distro_key in remove_pkgs_map:
            for pkg in remove_pkgs_map[distro_key]:
                if pkg in cnfg.pkgs_for_distro:
                    cnfg.pkgs_for_distro.remove(pkg)

    # Filter out systemd packages if if systemctl is not present
    cnfg.pkgs_for_distro = [
        pkg for pkg in cnfg.pkgs_for_distro 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    transupd_distros            = []    # 'transactional-update': openSUSE MicroOS/Aeon/Kalpa
    rpmostree_distros           = []    # 'rpm-ostree': Fedora atomic/immutables
    dnf_distros                 = []    # 'dnf': Fedora/RHEL/OpenMandriva
    zypper_distros              = []    # 'zypper': openSUSE Tumbleweed/Leap
    apt_distros                 = []    # 'apt': Debian/Ubuntu
    pacman_distros              = []    # 'pacman': Arch, BTW
    eopkg_distros               = []    # 'eopkg': Solus
    xbps_distros                = []    # 'xbps-install': Void

    # assemble specific pkg mgr distro lists

    try:
        transupd_distros        += distro_groups_map['microos-based']

        rpmostree_distros       += distro_groups_map['fedora-immutables']

        dnf_distros             += distro_groups_map['fedora-based']
        dnf_distros             += distro_groups_map['rhel-based']
        dnf_distros             += distro_groups_map['mandriva-based']

        zypper_distros          += distro_groups_map['tumbleweed-based']
        zypper_distros          += distro_groups_map['leap-based']

        apt_distros             += distro_groups_map['ubuntu-based']
        apt_distros             += distro_groups_map['debian-based']

        pacman_distros          += distro_groups_map['arch-based']

        eopkg_distros           += distro_groups_map['solus-based']

        xbps_distros            += distro_groups_map['void-based']

    except (KeyError, TypeError) as key_err:
        print()
        error(f'Problem setting up package manager distro lists:\n\t{key_err}')
        safe_shutdown(1)

    # create the quirks handler object
    quirks_handler              = DistroQuirksHandler()

    ###########################################################################
    ###  TRANSACTIONAL-UPDATE DISTROS  ########################################
    ###########################################################################
    def install_on_transupd_distro():
        """utility function that gets dispatched for distros that use Transactional-Update"""
        if cnfg.DISTRO_ID in distro_groups_map['microos-based']:
            print('Distro is openSUSE MicroOS/Aeon/Kalpa immutable. Using "transactional-update".')

            # Filter out packages that are already installed
            filtered_pkg_lst = []
            for pkg in cnfg.pkgs_for_distro:
                result = subprocess.run(["rpm", "-q", pkg], stdout=PIPE, stderr=PIPE)
                if result.returncode != 0:
                    filtered_pkg_lst.append(pkg)
                else:
                    print(fancy_str(f"Package '{pkg}' is already installed. Skipping.", "green"))

            if filtered_pkg_lst:
                print(f'Packages left to install:\n{filtered_pkg_lst}')
                cmd_lst = ['sudo', 'transactional-update', '--non-interactive', 'pkg', 'in']
                native_pkg_installer.install_pkg_list(cmd_lst, filtered_pkg_lst)
                # might as well take care of user group and udev here, if rebooting is necessary. 
                verify_user_groups()
                install_udev_rules()
                show_reboot_prompt()
                print()
                print('###############################################################################')
                print('############       WARNING: Toshy setup is NOT yet complete!       ############')
                print('###########      This distro type uses "transactional-update".      ###########')
                print('##########   You MUST reboot now to make native packages available.  ##########')
                print('#########  After REBOOTING, run the Toshy setup script a second time. #########')
                print('###############################################################################')
                safe_shutdown(0)
            else:
                print('All needed packages are already available. Continuing setup...')

    ###########################################################################
    ###  RPM-OSTREE DISTROS  ##################################################
    ###########################################################################
    def install_on_rpmostree_distro():
        """utility function that gets dispatched for distros that use RPM-OSTree"""
        if cnfg.DISTRO_ID in distro_groups_map['fedora-immutables']:
            print('Distro is Fedora-type immutable. Using "rpm-ostree" instead of DNF.')

            # Filter out packages that are already installed
            filtered_pkg_lst = []
            for pkg in cnfg.pkgs_for_distro:
                result = subprocess.run(["rpm", "-q", pkg], stdout=PIPE, stderr=PIPE)
                if result.returncode != 0:
                    filtered_pkg_lst.append(pkg)
                else:
                    print(fancy_str(f"Package '{pkg}' is already installed. Skipping.", "green"))

            if filtered_pkg_lst:
                cmd_lst = ['sudo', 'rpm-ostree', 'install', '--idempotent',
                            '--allow-inactive', '--apply-live', '-y']
                native_pkg_installer.install_pkg_list(cmd_lst, filtered_pkg_lst)

    ###########################################################################
    ###  DNF DISTROS  #########################################################
    ###########################################################################
    def install_on_dnf_distro():
        """Utility function that gets dispatched for distros that use DNF package manager."""
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()

        # Define helper functions for specific distro installations
        def install_on_mandriva_based():
            cmd_lst = ['sudo', 'dnf', 'install', '-y']
            native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

        def install_on_rhel_based():
            if cnfg.DISTRO_ID == 'centos' and cnfg.distro_mjr_ver == '7':
                quirks_handler.handle_quirks_CentOS_7()
            if cnfg.DISTRO_ID == 'centos' and cnfg.distro_mjr_ver == '8':
                quirks_handler.handle_quirks_CentOS_Stream_8()
            quirks_handler.handle_quirks_RHEL()
            cmd_lst = ['sudo', 'dnf', 'install', '-y']
            native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

        def install_on_fedora_based():
            # TODO: insert check to see if Fedora distro is actually immutable/atomic (rpm-ostree)
            cmd_lst = ['sudo', 'dnf', 'install', '-y']
            native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

        # Dispatch installation sub-function based on DNF distro type
        if cnfg.DISTRO_ID in distro_groups_map['mandriva-based']:
            install_on_mandriva_based()
        elif cnfg.DISTRO_ID in distro_groups_map['rhel-based']:
            install_on_rhel_based()
        elif cnfg.DISTRO_ID in distro_groups_map['fedora-based']:
            install_on_fedora_based()
        else:
            error(f"Distro {cnfg.DISTRO_ID} is not supported by this installation script.")
            safe_shutdown(1)

    ###########################################################################
    ###  ZYPPER DISTROS  ######################################################
    ###########################################################################
    def install_on_zypper_distro():
        """utility function that gets dispatched for distros that use Zypper package manager"""
        cmd_lst = ['sudo', 'zypper', '--non-interactive', 'install']
        native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

    ###########################################################################
    ###  APT DISTROS  #########################################################
    ###########################################################################
    def install_on_apt_distro():
        """utility function that gets dispatched for distros that use APT package manager"""
        cmd_lst = ['sudo', 'apt', 'install', '-y']
        native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

    ###########################################################################
    ###  PACMAN DISTROS  ######################################################
    ###########################################################################
    def install_on_pacman_distro():
        """utility function that gets dispatched for distros that use Pacman package manager"""
        native_pkg_installer.check_for_pkg_mgr_cmd('pacman')

        def is_pkg_installed_pacman(package):
            """utility function to help avoid 'reinstalling' existing packages on Arch"""
            result = subprocess.run(['pacman', '-Q', package], stdout=DEVNULL, stderr=DEVNULL)
            return result.returncode == 0

        pkgs_to_install = [
            pkg
            for pkg in cnfg.pkgs_for_distro
            if not is_pkg_installed_pacman(pkg)
        ]
        if pkgs_to_install:
            cmd_lst = ['sudo', 'pacman', '-S', '--noconfirm']
            native_pkg_installer.install_pkg_list(cmd_lst, pkgs_to_install)

    ###########################################################################
    ###  EOPKG DISTROS  #######################################################
    ###########################################################################
    def install_on_eopkg_distro():
        """utility function that gets dispatched for distros that use Eopkg package manager"""
        dev_cmd_lst = ['sudo', 'eopkg', 'install', '-y', '-c']
        dev_pkg_lst = ['system.devel']
        native_pkg_installer.install_pkg_list(dev_cmd_lst, dev_pkg_lst)
        cmd_lst = ['sudo', 'eopkg', 'install', '-y']
        native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

    ###########################################################################
    ###  XBPS DISTROS  ########################################################
    ###########################################################################
    def install_on_xbps_distro():
        """utility function that gets dispatched for distros that use xbps-install package manager"""
        cmd_lst = ['sudo', 'xbps-install', '-Sy']
        native_pkg_installer.install_pkg_list(cmd_lst, cnfg.pkgs_for_distro)

    ###########################################################################
    ###  PACKAGE MANAGER DISPATCHER  ##########################################
    ###########################################################################
    # map installer sub-functions to each pkg mgr distro list
    pkg_mgr_dispatch_map = {
        tuple(transupd_distros):        install_on_transupd_distro,
        tuple(rpmostree_distros):       install_on_rpmostree_distro,
        tuple(dnf_distros):             install_on_dnf_distro,
        tuple(zypper_distros):          install_on_zypper_distro,
        tuple(apt_distros):             install_on_apt_distro,
        tuple(pacman_distros):          install_on_pacman_distro,
        tuple(eopkg_distros):           install_on_eopkg_distro,
        tuple(xbps_distros):            install_on_xbps_distro,
        # add any new package manager distro lists...
    }

    # Determine the correct installation function
    for distro_list, installer_function in pkg_mgr_dispatch_map.items():
        if cnfg.DISTRO_ID in distro_list:
            installer_function()
            native_pkg_installer.show_pkg_install_success_msg()
            show_task_completed_msg()
            return
    # exit message in case there is no package manager distro list with distro name inside
    exit_with_invalid_distro_error(pkg_mgr_err=True)


#####################################################################################################
###   END OF NATIVE PACKAGE INSTALLER SECTION
#####################################################################################################


def load_uinput_module():
    """Check to see if `uinput` kernel module is loaded"""

    print(f'\n\n§  Checking status of "uinput" kernel module...\n{cnfg.separator}')

    try:
        subprocess.check_output("lsmod | grep uinput", shell=True)
        print('The "uinput" module is already loaded.')
    except subprocess.CalledProcessError:
        print('The "uinput" module is not loaded, loading now...')
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
        subprocess.run(['sudo', 'modprobe', 'uinput'], check=True)

    # Check if /etc/modules-load.d/ directory exists
    if os.path.isdir("/etc/modules-load.d/"):
        # Check if /etc/modules-load.d/uinput.conf exists
        if not os.path.exists("/etc/modules-load.d/uinput.conf"):
            # If not, create it and add "uinput"
            try:
                call_attn_to_pwd_prompt_if_sudo_tkt_exp()
                command = "echo 'uinput' | sudo tee /etc/modules-load.d/uinput.conf >/dev/null"
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as proc_err:
                error(f"Failed to create /etc/modules-load.d/uinput.conf:\n\t{proc_err}")
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
                        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
                        command = "echo 'uinput' | sudo tee -a /etc/modules >/dev/null"
                        subprocess.run(command, shell=True, check=True)
                    except subprocess.CalledProcessError as proc_err:
                        error(f"ERROR: Failed to append 'uinput' to /etc/modules:\n\t{proc_err}")
                        error(f'ERROR: Install failed.')
                        safe_shutdown(1)
    show_task_completed_msg()


def reload_udev_rules():
    """utility function to reload udev rules in case of changes to rules file"""
    try:
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
        cmd_lst_reload                 = ['sudo', 'udevadm', 'control', '--reload-rules']
        subprocess.run(cmd_lst_reload, check=True)
        cmd_lst_trigger                 = ['sudo', 'udevadm', 'trigger']
        subprocess.run(cmd_lst_trigger, check=True)
        print('Reloaded the "udev" rules successfully.')
    except subprocess.CalledProcessError as proc_err:
        print(f'Failed to reload "udev" rules:\n\t{proc_err}')
        enable_prompt_for_reboot()


def install_udev_rules():
    """Set up `udev` rules file to give user/keyszer access to uinput"""
    print(f'\n\n§  Installing "udev" rules file for keymapper...\n{cnfg.separator}')

    rules_dir                   = '/etc/udev/rules.d'

    # systemd init systems can use the 'uaccess' tag to set owner of device to current user,
    # but this also requires the rules file to be lexically earlier than '73-'. Trying '70-'.
    rules_file                  = '70-toshy-keymapper-input.rules'
    rules_file_path             = os.path.join(rules_dir, rules_file)

    # older DEPRECATED '90-' rules file name, must be removed if found
    old_rules_file              = '90-toshy-keymapper-input.rules'          # DEPRECATED
    old_rules_file_path         = os.path.join(rules_dir, old_rules_file)

    # Check if the /etc/udev/rules.d directory exists, if not, create it
    if not os.path.exists(rules_dir):
        print(f"Creating directory: '{rules_dir}'")
        try:
            call_attn_to_pwd_prompt_if_sudo_tkt_exp()
            cmd_lst = ['sudo', 'mkdir', '-p', rules_dir]
            subprocess.run(cmd_lst, check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f"Problem while creating udev rules folder:\n\t{proc_err}")
            safe_shutdown(1)

    setfacl_path                = shutil.which('setfacl')
    acl_rule                    = ''

    if setfacl_path is not None:
        acl_rule                = f', RUN+="{setfacl_path} -m g::rw /dev/uinput"'
    new_rules_content           = (
        'SUBSYSTEM=="input", GROUP="input"\n'
        # f'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660"{acl_rule}\n'
        f'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660", TAG+="uaccess"{acl_rule}\n'
    )

    def rules_file_missing_or_content_differs():
        if not os.path.exists(rules_file_path):
            return True
        try:
            with open(rules_file_path, 'r') as file:
                return file.read() != new_rules_content
        except PermissionError as perm_err:
            error(f"Permission denied when accessing '{rules_file_path}':\n\t{perm_err}")
            safe_shutdown(1)
        except IOError as io_err:
            error(f"Error reading file '{rules_file_path}':\n\t{io_err}")
            error("Rules file exists but cannot be read. File corrupted?")
            safe_shutdown(1)

    # Only write the file if it doesn't exist or its contents are different from current rule
    if rules_file_missing_or_content_differs():
        command_str             = f'sudo tee {rules_file_path}'
        try:
            call_attn_to_pwd_prompt_if_sudo_tkt_exp()
            print(f'Using these "udev" rules for "uinput" device: ')
            print()
            subprocess.run(command_str, input=new_rules_content.encode(), shell=True, check=True)
            if not rules_file_missing_or_content_differs():
                print()
                print(f'Toshy "udev" rules file successfully installed.')
                reload_udev_rules()
            else:
                error(f'Toshy "udev" rules file install failed.')
                safe_shutdown(1)
        except subprocess.CalledProcessError as proc_err:
            print()
            error(f'ERROR: Problem while installing "udev" rules file for keymapper.\n')
            err_output: bytes = proc_err.output  # Type hinting the error output variable
            # Deal with possible 'NoneType' error output
            error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print()
            error(f'ERROR: Toshy install failed.')
            safe_shutdown(1)
    else:
        print(f'Correct "udev" rules already in place.')

    # remove older '90-' rules file (cannot use 'uaccess' tag unless processed earlier than '73-')
    if os.path.exists(old_rules_file_path):
        try:
            call_attn_to_pwd_prompt_if_sudo_tkt_exp()
            print(f'Removing old udev rules file: {old_rules_file}')
            subprocess.run(['sudo', 'rm', old_rules_file_path], check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'ERROR: Problem while removing old udev rules file:\n\t{proc_err}')

    show_task_completed_msg()


def group_exists_in_etc_group(group_name):
    """Utility function to check if the group exists in /etc/group file."""
    try:
        with open('/etc/group') as f:
            return re.search(rf'^{group_name}:', f.read(), re.MULTILINE) is not None
    except FileNotFoundError:
        error(f'Warning: /etc/group file not found. Cannot add "{group_name}" group.')
        safe_shutdown(1)


def create_group(group_name):
    """Utility function to create the specified group if it does not already exist."""
    if group_exists_in_etc_group(group_name):
        print(f'Group "{group_name}" already exists.')
    else:
        print(f'Creating "{group_name}" group...')
        call_attn_to_pwd_prompt_if_sudo_tkt_exp()
        if cnfg.DISTRO_ID in distro_groups_map['fedora-immutables']:
            # Special handling for Fedora immutable distributions
            with open('/etc/group') as f:
                if not re.search(rf'^{group_name}:', f.read(), re.MULTILINE):
                    # https://docs.fedoraproject.org/en-US/fedora-silverblue/troubleshooting/
                    # Special command to make Fedora Silverblue/uBlue work, or usermod will fail: 
                    # grep -E '^input:' /usr/lib/group | sudo tee -a /etc/group
                    command = f"grep -E '^{group_name}:' /usr/lib/group | sudo tee -a /etc/group >/dev/null"
                    try:
                        subprocess.run(command, shell=True, check=True)
                        print(f"Added '{group_name}' group to system.")
                    except subprocess.CalledProcessError as proc_err:
                        error(f"Problem adding '{group_name}' group to system.\n\t{proc_err}")
                        safe_shutdown(1)
        else:
            try:
                cmd_lst = ['sudo', 'groupadd', group_name]
                subprocess.run(cmd_lst, check=True)
                print(f'Group "{group_name}" created successfully.')
            except subprocess.CalledProcessError as proc_err:
                print()
                error(f'ERROR: Problem when trying to create "input" group.\n')
                err_output: bytes = proc_err.output  # Type hinting the error output variable
                # Deal with possible 'NoneType' error output
                error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
                safe_shutdown(1)


def verify_user_groups():
    """Check if the `input` group exists and user is in group"""
    print(f'\n\n§  Checking if user is in "input" group...\n{cnfg.separator}')
    create_group(cnfg.input_group)
    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.input_group)
    if cnfg.user_name in group_info.gr_mem:
        print(f'User "{cnfg.user_name}" is a member of '
                f'group "{cnfg.input_group}".')
    else:
        # Add the user to the input group
        try:
            call_attn_to_pwd_prompt_if_sudo_tkt_exp()
            subprocess.run(
                ['sudo', 'usermod', '-aG', cnfg.input_group, cnfg.user_name], check=True)
        except subprocess.CalledProcessError as proc_err:
            print()
            error(f'ERROR: Problem when trying to add user "{cnfg.user_name}" to '
                    f'group "{cnfg.input_group}".\n')
            err_output: bytes = proc_err.output  # Type hinting the error output variable
            # Deal with possible 'NoneType' error output
            error(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print()
            error(f'ERROR: Install failed.')
            safe_shutdown(1)
        #
        print(f'User "{cnfg.user_name}" added to group "{cnfg.input_group}".')
        enable_prompt_for_reboot()
    show_task_completed_msg()


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
    try:
        subprocess.run(cnfg.keyszer_clone_cmd.split() + [cnfg.keyszer_tmp_path], check=True)
    except subprocess.CalledProcessError as proc_err:
        print()
        error(f'Problem while cloning keyszer branch from GitHub:\n\t{proc_err}')
        safe_shutdown(1)
    show_task_completed_msg()


def is_barebones_config_file() -> bool:
    """
    Determines whether the existing Toshy configuration file is of the 
    'barebones' type by reading and checking its contents.

    :param config_directory: The directory where the configuration file is located.
    :return: True if the config is of the 'barebones' type, False otherwise.
    """
    cfg_file_name               = 'toshy_config.py'
    cfg_file_path               = os.path.join(cnfg.toshy_dir_path, cfg_file_name)

    if os.path.isfile(cfg_file_path):
        try:
            with open(cfg_file_path, 'r', encoding='UTF-8') as file:
                cnfg.existing_cfg_data = file.read()
        except (FileNotFoundError, PermissionError, OSError) as file_err:
            print(f'Problem reading config file: {file_err}')
            return False

        pattern = r'###  SLICE_MARK_(?:START|END): (\w+)  ###.*'
        matches = re.findall(pattern, cnfg.existing_cfg_data)
        return 'barebones_user_cfg' in matches or any('barebones' in slice_name for slice_name in matches)
    else:
        print(f"No existing config file found at '{cfg_file_path}'.")
        return False


def extract_slices(data: str) -> Dict[str, str]:
    """Utility function to store user content slices from existing config file data"""
    slices_dct: Dict[str, str]  = {}
    pattern_start               = r'###  SLICE_MARK_START: (\w+)  ###.*'
    pattern_end                 = r'###  SLICE_MARK_END: (\w+)  ###.*'
    matches_start               = list(re.finditer(pattern_start, data))
    matches_end                 = list(re.finditer(pattern_end, data))
    if len(matches_start) != len(matches_end):
        raise ValueError(   f'Mismatched slice markers in config file:'
                            f'\n\t{matches_start}, {matches_end}')
    for begin, end in zip(matches_start, matches_end):
        slice_name = begin.group(1)
        if end.group(1) != slice_name:
            raise ValueError(f'Mismatched slice markers in config file:\n\t{slice_name}')
        slice_start             = begin.end()
        slice_end               = end.start()
        slices_dct[slice_name]  = data[slice_start:slice_end]

    # Fix some deprecated variable names here, now that slice contents are 
    # in memory, prior to merging slices back into new config file.
    # Using a List of Tuples instead of a dict to guarantee processing order.
    deprecated_object_names_ordered_LoT = [
        ('OVERRIDE_DISTRO_NAME  ', 'OVERRIDE_DISTRO_ID    '),
        ('DISTRO_NAME  ', 'DISTRO_ID    '),
        ('OVERRIDE_DISTRO_NAME', 'OVERRIDE_DISTRO_ID'),
        ('DISTRO_NAME', 'DISTRO_ID'),
    ]

    for slice_name, content in slices_dct.items():
        for deprecated_name, new_name in deprecated_object_names_ordered_LoT:
            content = content.replace(deprecated_name, new_name)
        slices_dct[slice_name] = content

    # Protect the barebones config file if a slice tagged with "barebones" found, 
    if 'barebones_user_cfg' in slices_dct or any('barebones' in key for key in slices_dct):
        cnfg.barebones_config = True
        print(f'Found "barebones" type config file. Will upgrade with same type.')
    # Confirm replacement of regular config file with barebones config if CLI option is used
    # and there is a non-barebones existing config file. 
    elif cnfg.barebones_config:
        for attempt in range(3):
            response = input(
                f'\n'
                f'ALERT:\n'
                f'Existing config file is not a barebones config, but the barebones CLI \n'
                f'option was specified. Do you want to proceed and replace the existing \n'
                f'config with a barebones config? This will discard all existing settings. \n'
                f'A timestamped backup of the existing config folder will still be made. \n'
                f'Enter "YES" to proceed or "N" to exit:'
            )
            if response.lower() not in ['n', 'yes']: continue
            if response.lower() == 'yes':
                # User confirmed to replace the existing config with a barebones config.
                # So, return an empty slices dictionary.
                return {}
            elif response.lower() == 'n':
                print(f'User chose to exit installer...')
                safe_shutdown(0)
        # If user didn't confirm after 3 attempts, exit the program.
        print('User input invalid. Exiting...')
        safe_shutdown(1)
    # 
    return slices_dct


def merge_slices(data: str, slices: Dict[str, str]) -> str:
    """Utility function to merge stored slices into new config file data"""
    pattern_start   = r'###  SLICE_MARK_START: (\w+)  ###.*'
    pattern_end     = r'###  SLICE_MARK_END: (\w+)  ###.*'
    matches_start   = list(re.finditer(pattern_start, data))
    matches_end     = list(re.finditer(pattern_end, data))
    data_slices     = []
    previous_end    = 0
    for begin, end in zip(matches_start, matches_end):
        slice_name = begin.group(1)
        if end.group(1) != slice_name:
            raise ValueError(f'Mismatched slice markers in config file:\n\t{slice_name}')
        slice_start     = begin.end()
        slice_end       = end.start()
        # add the part of the data before the slice, and the slice itself
        data_slices.extend([data[previous_end:slice_start], 
                            slices.get(slice_name, data[slice_start:slice_end])])
        previous_end = slice_end
    # add the part of the data after the last slice
    data_slices.append(data[previous_end:])
    # 
    return "".join(data_slices)


def backup_toshy_config():
    """Backup existing Toshy config folder"""
    print(f'\n\n§  Backing up existing Toshy config folder...\n{cnfg.separator}')

    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_cfg_bkups_base_dir  = os.path.join(home_dir, '.config', 'toshy_config_backups')
    toshy_cfg_bkup_timestamp_dir  = os.path.realpath(
        os.path.join(toshy_cfg_bkups_base_dir, 'toshy' + timestamp))

    if not os.path.exists(cnfg.toshy_dir_path):
        print(f'No existing Toshy folder to backup.')
        cnfg.backup_succeeded = True
    else:
        cfg_file_name           = 'toshy_config.py'
        cfg_file_path           = os.path.join(cnfg.toshy_dir_path, cfg_file_name)

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
        else:
            print(f"No existing config file found at '{cfg_file_path}'.")

        if os.path.isfile(cnfg.db_file_path):
            try:
                os.unlink(f'{cnfg.run_tmp_dir}/{cnfg.db_file_name}')
            except (FileNotFoundError, PermissionError, OSError): pass
            try:
                shutil.copy(cnfg.db_file_path, f'{cnfg.run_tmp_dir}/')
            except (FileNotFoundError, PermissionError, OSError) as file_err:
                error(f"Problem copying preferences db file to '{cnfg.run_tmp_dir}':\n\t{file_err}")
        else:
            print(f'No existing preferences db file found in {cnfg.toshy_dir_path}.')
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
    show_task_completed_msg()


def install_toshy_files():
    """Install Toshy files"""
    print(f'\n\n§  Installing Toshy files...\n{cnfg.separator}')
    if not cnfg.backup_succeeded:
        error(f'Backup of Toshy config folder failed? Bailing out.')
        safe_shutdown(1)
    keyszer_tmp_dir     = os.path.basename(cnfg.keyszer_tmp_path)
    try:
        if os.path.exists(cnfg.toshy_dir_path):
            try:
                shutil.rmtree(cnfg.toshy_dir_path)
            except (OSError, PermissionError, FileNotFoundError) as file_err:
                error(f'Problem removing existing Toshy config folder after backup:\n\t{file_err}')
        patterns_to_ignore = [
                '.git_hooks',
                '.git_hooks_install.sh',
                '.github',
                '.gitignore',
                '__pycache__',
                'CONTRIBUTING.md',
                'DO_NOT_USE_requirements.txt',
                keyszer_tmp_dir,
                'kwin-application-switcher',
                'LICENSE',
                'packages.json',
                'README.md',
                'requirements.txt',
                this_file_name,
        ]
        # must use list unpacking (*) ignore_patterns() requires individual pattern arguments
        ignore_fn = shutil.ignore_patterns(*patterns_to_ignore)
        # Copy files recursively from source to destination
        shutil.copytree(this_file_dir, cnfg.toshy_dir_path, ignore=ignore_fn)
    except shutil.Error as copy_error:
        error(f"Failed to copy directory: {copy_error}")
    except OSError as os_error:
        error(f"Failed to create backup directory: {os_error}")
    if cnfg.barebones_config is True:
        toshy_default_cfg_barebones = os.path.join(
            cnfg.toshy_dir_path, 'default-toshy-config', 'toshy_config_barebones.py')
        toshy_new_cfg = os.path.join(
            cnfg.toshy_dir_path, 'toshy_config.py')
        shutil.copy(toshy_default_cfg_barebones, toshy_new_cfg)
        print(f'Installed default "barebones" Toshy config file.')
    else:
        toshy_default_cfg = os.path.join(
            cnfg.toshy_dir_path, 'default-toshy-config', 'toshy_config.py')
        toshy_new_cfg = os.path.join(
            cnfg.toshy_dir_path, 'toshy_config.py')
        shutil.copy(toshy_default_cfg, toshy_new_cfg)
        print(f'Installed default Toshy config file.')
    print(f"Toshy files installed in '{cnfg.toshy_dir_path}'.")

    # Copy the existing user prefs database file
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
    show_task_completed_msg()


class PythonVenvQuirksHandler():
    """Object to contain methods for prepping specific distro variants that
        need some extra work while installing the Python virtual environment"""

    def __init__(self) -> None:
        pass

    def handle_quirks_Leap(self):
        print('Handling a Python virtual environment quirk in Leap...')
        # Change the Python interpreter path to use current release version from pkg list
        # if distro is openSUSE Leap type (instead of using old 3.6 Python version).
        if shutil.which(f'python{cnfg.curr_py_rel_ver_str}'):
            cnfg.py_interp_path = shutil.which(f'python{cnfg.curr_py_rel_ver_str}')
            print(f'Using Python version {cnfg.curr_py_rel_ver_str}.')
        else:
            print(  f'Current stable Python release version '
                    f'({cnfg.curr_py_rel_ver_str}) not found. ')
            safe_shutdown(1)

    def handle_quirks_OpenMandriva(self, venv_cmd_lst):
        print('Handling a Python virtual environment quirk in OpenMandriva...')
        # We need to run the exact same command twice on OpenMandriva, for unknown reasons.
        # So this instance of the command is just "prep" for the seemingly duplicate
        # command that follows it in setup_python_vir_env(). 
        subprocess.run(venv_cmd_lst, check=True)


def setup_python_vir_env():
    """Setup a virtual environment to install Python packages"""
    print(f'\n\n§  Setting up the Python virtual environment...\n{cnfg.separator}')
    venv_quirks_handler = PythonVenvQuirksHandler()
    # Create the virtual environment if it doesn't exist
    if not os.path.exists(cnfg.venv_path):
        if cnfg.DISTRO_ID in distro_groups_map['leap-based']:
            venv_quirks_handler.handle_quirks_Leap()
        else:
            print(f'Using Python version {cnfg.py_interp_ver_str}.')
        try:
            venv_cmd_lst = [cnfg.py_interp_path, '-m', 'venv', cnfg.venv_path]
            if cnfg.DISTRO_ID in ['openmandriva']:
                venv_quirks_handler.handle_quirks_OpenMandriva(venv_cmd_lst)
            subprocess.run(venv_cmd_lst, check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'ERROR: Problem creating the Python virtual environment:\n\t{proc_err}')
            safe_shutdown(1)
    # We do not need to "activate" the venv right now, just create it
    print(f'Python virtual environment setup complete.')
    print(f"Location: '{cnfg.venv_path}'")
    show_task_completed_msg()


def install_pip_packages():
    """Install `pip` packages for Python"""
    print(f'\n\n§  Installing/upgrading Python packages...\n{cnfg.separator}')
    venv_python_cmd = os.path.join(cnfg.venv_path, 'bin', 'python')
    venv_pip_cmd    = os.path.join(cnfg.venv_path, 'bin', 'pip')

    # Filter out systemd packages if no 'systemctl' present
    filtered_pip_pkgs   = [
        pkg for pkg in pip_pkgs 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    commands        = [
        [venv_python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'],
        [venv_pip_cmd, 'install', '--upgrade', 'wheel'],
        [venv_pip_cmd, 'install', '--upgrade', 'setuptools'],
        [venv_pip_cmd, 'install', '--upgrade', 'pillow'],
        [venv_pip_cmd, 'install', '--upgrade'] + filtered_pip_pkgs
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
    show_task_completed_msg()


def install_bin_commands():
    """Install the convenient terminal commands (symlinks to scripts) to manage Toshy"""
    print(f'\n\n§  Installing Toshy terminal commands...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-bincommands-setup.sh')
    try:
        subprocess.run([script_path], check=True)
    except subprocess.CalledProcessError as proc_err:
        print()
        error(f'Problem while installing terminal commands:\n\t{proc_err}')
        safe_shutdown(1)
    show_task_completed_msg()


def replace_home_in_file(filename):
    """Utility function to replace '$HOME' in .desktop files with actual home path"""
    # Read in the file
    with open(filename, 'r') as file:
        file_data = file.read()
    # Replace the target string
    file_data = file_data.replace('$HOME', home_dir)
    # Write the file out again
    with open(filename, 'w') as file:
        file.write(file_data)


def install_desktop_apps():
    """Install the convenient desktop apps to manage Toshy"""
    print(f'\n\n§  Installing Toshy desktop apps...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-desktopapps-setup.sh')

    try:
        subprocess.run([script_path], check=True)
    except subprocess.CalledProcessError as proc_err:
        print()
        error(f'Problem installing Toshy desktop apps:\n\t{proc_err}')
        safe_shutdown(1)

    desktop_files_path  = os.path.join(home_dir, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    gui_desktop_file    = os.path.join(desktop_files_path, 'Toshy_GUI.desktop')

    replace_home_in_file(tray_desktop_file)
    replace_home_in_file(gui_desktop_file)
    show_task_completed_msg()


def do_kwin_reconfigure():
    """Utility function to run the KWin reconfigure command"""

    commands = ['dbus-send', 'gdbus', cnfg.qdbus]

    for cmd in commands:
        if shutil.which(cmd):
            break
    else:
        error(f'No expected D-Bus command available. Cannot do KWin reconfigure.')
        return

    if shutil.which('dbus-send'):
        try:
            cmd_lst = [ 'dbus-send', '--type=method_call',
                        '--dest=org.kde.KWin', '/KWin',
                        'org.kde.KWin.reconfigure']
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "dbus-send" to do KWin reconfigure.\n\t{proc_err}')

    if shutil.which('gdbus'):
        try:
            cmd_lst = [ 'gdbus', 'call', '--session', 
                        '--dest', 'org.kde.KWin',
                        '--object-path', '/KWin', 
                        '--method', 'org.kde.KWin.reconfigure']
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "gdbus" to do KWin reconfigure.\n\t{proc_err}')

    if shutil.which(cnfg.qdbus):
        try:
            cmd_lst = [cnfg.qdbus, 'org.kde.KWin', '/KWin', 'reconfigure']
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "{cnfg.qdbus}" to do KWin reconfigure.\n\t{proc_err}')

    error(f'Failed to do KWin reconfigure. No available D-Bus utility worked.')


def get_kwin_script_index(script_name):
    """Utility function to get the index of a loaded KWin script"""

    kwin_dest               = "org.kde.KWin"
    kwin_script_iface       = "org.kde.kwin.Scripting"

    qdbus_idx_cmd         = ( f"qdbus {kwin_dest} /Scripting "
                                f"{kwin_script_iface}.loadScript {script_name}")
    dbus_send_idx_cmd     = ( f"dbus-send --print-reply --dest={kwin_dest} /Scripting "
                                f"{kwin_script_iface}.loadScript string:{script_name}")
    gdbus_idx_cmd         = ( f"gdbus call --session --dest {kwin_dest} --object-path /Scripting "
                                f"--method {kwin_script_iface}.loadScript {script_name}")

    try:
        if shutil.which('qdbus'):
            return subprocess.check_output(qdbus_idx_cmd, shell=True).strip().decode('utf-8')
        elif shutil.which('dbus-send'):
            return subprocess.check_output(dbus_send_idx_cmd, shell=True).strip().decode('utf-8')
        elif shutil.which('gdbus'):
            output = subprocess.check_output(gdbus_idx_cmd, shell=True).strip().decode('utf-8')
            # Extracting the numeric part from the tuple-like string
            script_index = output.strip("()").split(',')[0]
            return script_index
        else:
            error("No suitable D-Bus utility found to get script index.")
            return None
    except subprocess.CalledProcessError as proc_err:
        error(f"An error occurred while getting the script index: {proc_err}")
        return None


def run_kwin_script(script_name):
    """Utility function to run an already loaded and enabled KWin script"""

    kwin_dest               = "org.kde.KWin"
    kwin_script_iface       = "org.kde.kwin.Script"

    script_index            = get_kwin_script_index(script_name)
    if not script_index:
        error(f"Unable to run KWin script. No index returned.")
        return

    qdbus_run_cmd           = ( f"qdbus {kwin_dest} /{script_index} {kwin_script_iface}.run")
    dbus_send_run_cmd       = ( f"dbus-send --type=method_call --dest={kwin_dest} "
                            f"/{script_index} {kwin_script_iface}.run")
    gdbus_run_cmd           = ( f"gdbus call --session --dest {kwin_dest} --object-path "
                            f"/{script_index} --method {kwin_script_iface}.run")

    try:
        if shutil.which('qdbus'):
            subprocess.run(qdbus_run_cmd, shell=True, check=True)
        elif shutil.which('dbus-send'):
            subprocess.run(dbus_send_run_cmd, shell=True, check=True)
        elif shutil.which('gdbus'):
            subprocess.run(gdbus_run_cmd, shell=True, check=True)
        else:
            error("No suitable D-Bus utility found to run KWin script.")
    except subprocess.CalledProcessError as proc_err:
        error(f"An error occurred while executing the run command: {proc_err}")


def setup_kwin2dbus_script():
    """Install the KWin script to notify D-Bus service about window focus changes"""
    print(f'\n\n§  Setting up the Toshy KWin script...\n{cnfg.separator}')

    if cnfg.DESKTOP_ENV == 'kde':
        KDE_ver = cnfg.DE_MAJ_VER
    else:
        error("ERROR: Asked to install Toshy KWin script, but DE is not KDE.")
        return

    if KDE_ver not in cnfg.valid_KDE_vers:
        error("ERROR: Toshy KWin script cannot be installed.")
        error(f"KDE major version invalid: '{KDE_ver}'")
        return

    if KDE_ver in ['4', '3']:
        print(f'KDE {KDE_ver} is not Wayland compatible. Toshy KWin script unnecessary.')
        return

    kpackagetool_cmd        = f'kpackagetool{KDE_ver}'
    kwriteconfig_cmd        = f'kwriteconfig{KDE_ver}'

    kwin_script_name        = 'toshy-dbus-notifyactivewindow'
    kwin_script_path        = os.path.join( cnfg.toshy_dir_path,
                                            'kde-kwin-script',
                                            f'kde{KDE_ver}',
                                            kwin_script_name)
    kwin_script_tmp_file    = f'{cnfg.run_tmp_dir}/{kwin_script_name}.kwinscript'
    curr_script_path        = os.path.join( home_dir,
                                            '.local',
                                            'share',
                                            'kwin',
                                            'scripts',
                                            kwin_script_name)

    # Create a zip file (overwrite if it exists)
    with zipfile.ZipFile(kwin_script_tmp_file, 'w') as zipf:
        # Add main.js to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                                arcname='contents/code/main.js')
        # Add metadata.desktop to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

    # Try to remove existing KWin script, only if it exists
    if os.path.exists(curr_script_path):
        # Try to remove any installed KWin script entirely
        process = subprocess.Popen(
            [kpackagetool_cmd, '-t', 'KWin/Script', '-r', kwin_script_name],
            stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        out = out.decode('utf-8')
        err = err.decode('utf-8')
        result = subprocess.CompletedProcess(   args=process.args,
                                                returncode=process.returncode,
                                                stdout=out, stderr=err)

        if result.returncode != 0:
            error("Problem while uninstalling existing Toshy KWin script.")
            try:
                shutil.rmtree(curr_script_path)
                print(f'Removed existing Toshy KWin script folder (if any).')
            except (FileNotFoundError, PermissionError) as file_err:
                error(f'Problem removing existing KWin script folder:\n\t{file_err}')
                # safe_shutdown(1)
        else:
            print("Successfully removed existing Toshy KWin script.")

    # Install the KWin script
    cmd_lst = [kpackagetool_cmd, '-t', 'KWin/Script', '-i', kwin_script_tmp_file]
    process = subprocess.Popen(cmd_lst, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = subprocess.CompletedProcess(   args=process.args,
                                            returncode=process.returncode,
                                            stdout=out, stderr=err)

    if result.returncode != 0:
        error(f"Error installing the Toshy KWin script. The error was:\n\t{result.stderr}")
        safe_shutdown(1)
    else:
        print("Successfully installed the Toshy KWin script.")

    # Remove the temporary kwinscript file
    try:
        os.remove(kwin_script_tmp_file)
    except (FileNotFoundError, PermissionError): pass

    # Enable the KWin script
    cmd_lst = [kwriteconfig_cmd, '--file', 'kwinrc', '--group', 'Plugins', '--key',
            f'{kwin_script_name}Enabled', 'true']
    process = subprocess.Popen(cmd_lst, stdout=PIPE, stderr=PIPE)
    out, err = process.communicate()
    out = out.decode('utf-8')
    err = err.decode('utf-8')
    result = subprocess.CompletedProcess(   args=process.args,
                                            returncode=process.returncode,
                                            stdout=out, stderr=err)

    if result.returncode != 0:
        error(f"Error enabling the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully enabled the KWin script.")

    # Try to get KWin to notice and activate the script on its own, now that it's in RC file
    do_kwin_reconfigure()

    # Here we will also try to "run" the KWin script, as an alternative to the "kickstart" script
    # Did things change from Plasma 5 to 6? This doesn't seem to work. 
    # run_kwin_script(kwin_script_name)

    show_task_completed_msg()


def ensure_XDG_autostart_dir_exists():
    """Utility function to make sure XDG autostart directory exists"""
    autostart_dir_path      = os.path.join(home_dir, '.config', 'autostart')
    if not os.path.isdir(autostart_dir_path):
        try:
            os.makedirs(autostart_dir_path, exist_ok=True)
        except (PermissionError, NotADirectoryError) as file_err:
            error(f"Problem trying to make sure '{autostart_dir_path}' exists.\n\t{file_err}")
            safe_shutdown(1)


def setup_kde_dbus_service():
    """Install the D-Bus service initialization script to receive window focus
    change notifications from the KWin script on KDE desktops (needed for Wayland)"""
    print(f'\n\n§  Setting up the Toshy KDE D-Bus service...\n{cnfg.separator}')

    # need to autostart "$HOME/.local/bin/toshy-kde-dbus-service"
    autostart_dir_path      = os.path.join(home_dir, '.config', 'autostart')
    toshy_dt_files_path     = os.path.join(cnfg.toshy_dir_path, 'desktop')
    dbus_svc_desktop_file   = os.path.join(toshy_dt_files_path, 'Toshy_KDE_DBus_Service.desktop')
    start_dbus_svc_cmd      = os.path.join(home_dir, '.local', 'bin', 'toshy-kde-dbus-service')
    replace_home_in_file(dbus_svc_desktop_file)

    # Where to put the new D-Bus service file:
    # ~/.local/share/dbus-1/services/org.toshy.Toshy.service
    dbus_svcs_path          = os.path.join(home_dir, '.local', 'share', 'dbus-1', 'services')
    toshy_kde_dbus_svc_path = os.path.join(cnfg.toshy_dir_path, 'kde-kwin-dbus-service')
    kde_dbus_svc_file       = os.path.join(toshy_kde_dbus_svc_path, 'org.toshy.Toshy.service')

    if not os.path.isdir(dbus_svcs_path):
        try:
            os.makedirs(dbus_svcs_path, exist_ok=True)
        except (PermissionError, NotADirectoryError) as file_err:
            error(f"Problem trying to make sure '{dbus_svcs_path}' exists:\n\t{file_err}")
            safe_shutdown(1)

    # STOP INSTALLING THIS, IT'S NOT HELPFUL
    # if os.path.isdir(dbus_svcs_path):
    #     shutil.copy(kde_dbus_svc_file, dbus_svcs_path)
    #     print(f"Installed '{kde_dbus_svc_file}' file at path:\n\t'{dbus_svcs_path}'.")
    # else:
    #     error(f"Path '{dbus_svcs_path}' is not a directory. Cannot continue.")
    #     safe_shutdown(1)

    ensure_XDG_autostart_dir_exists()

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
    show_task_completed_msg()


def setup_systemd_services():
    """Invoke the systemd setup script to install the systemd service units"""
    print(f'\n\n§  Setting up the Toshy systemd services...\n{cnfg.separator}')
    if cnfg.systemctl_present and cnfg.init_system == 'systemd':
        script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'bin', 'toshy-systemd-setup.sh')
        subprocess.run([script_path])
        print(f'Finished setting up Toshy systemd services.')
    else:
        print(f'System does not seem to be using "systemd" as init system.')
    show_task_completed_msg()


def autostart_systemd_kickstarter():
    """Install the desktop file that will make sure the systemd services are restarted 
    after a short logout-login sequence, when systemd fails to stop the user services"""

    ensure_XDG_autostart_dir_exists()

    svcs_kick_dt_file_name  = 'Toshy_Systemd_Service_Kickstart.desktop'
    toshy_dt_files_path     = os.path.join(cnfg.toshy_dir_path, 'desktop')
    svcs_kick_dt_file       = os.path.join(toshy_dt_files_path, svcs_kick_dt_file_name)
    autostart_dir_path      = os.path.join(home_dir, '.config', 'autostart')
    dest_link_file          = os.path.join(autostart_dir_path, svcs_kick_dt_file_name)

    cmd_lst                 = ['ln', '-sf', svcs_kick_dt_file, dest_link_file]
    try:
        subprocess.run(cmd_lst, check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem while setting up systemd kickstarter:\n\t{proc_err}')
        safe_shutdown(1)


def autostart_tray_icon():
    """Set up the tray icon to autostart at login"""
    print(f'\n\n§  Setting up tray icon to load automatically at login...\n{cnfg.separator}')
    
    # Path to the database file
    toshy_cfg_dir_path          = os.path.join(home_dir, '.config', 'toshy')
    prefs_db_file_name          = 'toshy_user_preferences.sqlite'
    prefs_db_file_path          = os.path.join(toshy_cfg_dir_path, prefs_db_file_name)
    
    autostart_preference        = True  # Default to autostarting tray icon
    
    # Check if the database file exists
    if os.path.isfile(prefs_db_file_path):
        try:
            sql_query = "SELECT value FROM config_preferences WHERE name = 'autostart_tray_icon'"

            with sqlite3.connect(prefs_db_file_path) as cnxn:
                cursor = cnxn.cursor()
                cursor.execute(sql_query)
                row: Optional[Tuple[str]] = cursor.fetchone()
            
            if row is not None:
                # Convert the string value to a boolean
                autostart_preference = row[0].lower() == 'true'

        except sqlite3.Error as db_err:
            error(f"Could not read tray icon autostart preference from database:\n\t{db_err}")
            print("Defaulting to enabling autostart of tray icon.")

    if autostart_preference is True:
        tray_dt_file_name       = 'Toshy_Tray.desktop'
        home_apps_path          = os.path.join(home_dir, '.local', 'share', 'applications')
        tray_dt_file_path       = os.path.join(home_apps_path, tray_dt_file_name)
        home_autostart_path     = os.path.join(home_dir, '.config', 'autostart')
        tray_link_file_path     = os.path.join(home_autostart_path, tray_dt_file_name)
        try:
            ensure_XDG_autostart_dir_exists()
            cmd_lst                 = ['ln', '-sf', tray_dt_file_path, tray_link_file_path]
            subprocess.run(cmd_lst, check=True)
            print(f'Toshy tray icon should appear in system tray at each login.')
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem while setting up tray icon autostart:\n\t{proc_err}')
            safe_shutdown(1)
    else:
        cnfg.autostart_tray_icon = False    # to disable setup from starting the tray icon
        print("Toshy tray icon autostart is disabled by user preference. Skipping.")

    show_task_completed_msg()



###################################################################################################
##  TWEAKS UTILITY FUNCTIONS - START
###################################################################################################


def apply_tweaks_Cinnamon():
    """Utility function to add desktop tweaks to Cinnamon"""

    cmd_lst         = ['./install.sh']
    dir_path        = os.path.join(this_file_dir, 'cinnamon-extension')

    try:
        subprocess.run(cmd_lst, cwd=dir_path, check=True)
        print(f'Installed Cinnamon extension for window context.')
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem while installing Cinnamon extension:\n\t{proc_err}')


def apply_tweaks_GNOME():
    """Utility function to add desktop tweaks to GNOME"""

    # TODO: Decide if we should re-enable the toggle-overview shortcut and change default config
    # for GNOME 45 and later. Find out if toggle-overview will be dropped(!) at some point. 

    # # How to check the existing toggle-overview shortcut:
    # # gsettings get org.gnome.shell.keybindings toggle-overview
    # # Will return something like: ['<Shift><Control>space']
    # get_oview_shortcut_cmd = ['gsettings', 'get', 'org.gnome.shell.keybindings', 'toggle-overview']
    # try:
    #     # Capture the current shortcut setting
    #     curr_oview_shortcut_str = subprocess.check_output(get_oview_shortcut_cmd, text=True).strip()
    #     # Parse the JSON-formatted string into a Python list
    #     curr_oview_shortcut_lst = json.loads(curr_oview_shortcut_str)
    #     # Check if the shortcut is unset
    #     if curr_oview_shortcut_lst == ['']:
    #         # It's unset, so we define the shortcut we want to set
    #         new_oview_shortcut_str = '<Alt>F1'
    #         set_oview_shortcut_cmd = [  'gsettings', 'set', 'org.gnome.shell.keybindings',
    #                                     'toggle-overview', json.dumps([new_oview_shortcut_str])]
    #         # Set the desired shortcut
    #         subprocess.run(set_oview_shortcut_cmd, check=True)
    #         print(f"Set 'toggle-overview' shortcut to {new_oview_shortcut_str}.")
    #     else:
    #         print(f"'toggle-overview' shortcut is already set to {curr_oview_shortcut_str}.")
    # except subprocess.CalledProcessError as proc_err:
    #     error(f'Problem while checking or setting the toggle-overview shortcut.\n\t{proc_err}')

    # Stop disabling overlay-key on GNOME 45 and later (toggle-overview is no longer set)
    if cnfg.DE_MAJ_VER in ['44', '43', '42', '41', '40', '3']:
        # Disable GNOME `overlay-key` binding to Meta/Super/Win/Cmd
        # gsettings set org.gnome.mutter overlay-key ''
        cmd_lst = ['gsettings', 'set', 'org.gnome.mutter', 'overlay-key', '']
        subprocess.run(cmd_lst)
        print(f'Disabled Super key opening the GNOME overview. (Use Cmd+Space instead.)')
    else:
        print(f'NOTICE: Toshy not disabling overlay-key on GNOME 45 or later.')

    # Enable keyboard shortcut for GNOME Terminal preferences dialog
    # gsettings set org.gnome.Terminal.Legacy.Keybindings:/org/gnome/terminal/legacy/keybindings/ preferences '<Control>less'
    cmd_path = 'org.gnome.Terminal.Legacy.Keybindings:/org/gnome/terminal/legacy/keybindings/'
    prefs_binding = '<Control>comma'
    subprocess.run(['gsettings', 'set', cmd_path, 'preferences', prefs_binding])
    print(f'Set a keybinding for GNOME Terminal preferences.')

    # Enable "Expandable folders" in Nautilus
    # dconf write /org/gnome/nautilus/list-view/use-tree-view true
    cmd_path = '/org/gnome/nautilus/list-view/use-tree-view'
    subprocess.run(['dconf', 'write', cmd_path, 'true'])

    # Set default view option in Nautilus to "list-view"
    # dconf write /org/gnome/nautilus/preferences/default-folder-viewer "'list-view'"
    cmd_path = '/org/gnome/nautilus/preferences/default-folder-viewer'
    subprocess.run(['dconf', 'write', cmd_path, "'list-view'"])

    print(f'Set Nautilus default to "List" view with "Expandable folders" enabled.')


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

    if cnfg.DESKTOP_ENV == 'kde':
        KDE_ver = cnfg.DE_MAJ_VER
    else:
        error("ERROR: Asked to apply KDE tweaks, but DE is not KDE.")
        return

    # check that major release ver from env module is rational
    if KDE_ver not in cnfg.valid_KDE_vers:
        error("ERROR: Desktop tweaks for KDE cannot be applied.")
        error(f"KDE major version invalid: '{KDE_ver}'")
        return

    if KDE_ver in ['4', '3']:
        print(f'No tweaks available for KDE {KDE_ver}. Skipping.')
        return

    kstart_cmd          = f'kstart{KDE_ver}'

    if not shutil.which(kstart_cmd):
        # try just 'kstart' on KDE 6 if there is no 'kstart6'
        if shutil.which('kstart'):
            kstart_cmd          = 'kstart'
        # if no 'kstart', fall back to 'kstart5' if it exists
        elif shutil.which('kstart5'):
            kstart_cmd          = 'kstart5'

    kquitapp_cmd        = f'kquitapp{KDE_ver}'
    kwriteconfig_cmd    = f'kwriteconfig{KDE_ver}'

    # Documentation on the use of Meta key in KDE:
    # https://userbase.kde.org/Plasma/Tips#Windows.2FMeta_Key
    subprocess.run([kwriteconfig_cmd, '--file', 'kwinrc',
                    '--group', 'ModifierOnlyShortcuts',
                    '--key', 'Meta', ''], check=True)
    print(f'Disabled Meta key opening application menu. (Use Cmd+Space instead.)')

    # Run reconfigure command
    do_kwin_reconfigure()

    if cnfg.fancy_pants:
        print(f'Installing "Application Switcher" KWin script...')
        # How to install nclarius grouped "Application Switcher" KWin script:
        # git clone https://github.com/nclarius/kwin-application-switcher.git
        # cd kwin-application-switcher
        # ./install.sh
        # 
        # switcher_url        = 'https://github.com/nclarius/kwin-application-switcher.git'

        # TODO: Revert to main repo if/when patch for this is accepted.
        # Patched branch that fixes some issues with maintaining grouping:
        # 'https://github.com/RedBearAK/kwin-application-switcher/tree/grouping_fix'

        # switcher_branch     = 'grouping_fix'

        # TODO: Revert to nclarius repo if/when this branch is merged.
        # Patched branch that merges API variations for KDE 5 and 6:
        # 'https://github.com/RedBearAK/kwin-application-switcher/tree/kde6_kde5_merged'
        # (includes the fixes from 'grouping_fix' branch)

        switcher_branch     = 'kde6_kde5_merged'
        switcher_repo       = 'https://github.com/RedBearAK/kwin-application-switcher.git'

        switcher_dir_name   = 'kwin-application-switcher'
        switcher_dir_path   = os.path.join(this_file_dir, switcher_dir_name)
        switcher_title      = 'KWin Application Switcher'
        switcher_cloned     = False

        git_clone_cmd_lst   = ['git', 'clone', '--branch']
        branch_args_lst     = [switcher_branch, switcher_repo, switcher_dir_path]

        # git should be installed by this point? Not necessarily.
        if not shutil.which('git'):
            error(f"Unable to clone {switcher_title}. Install 'git' and try again.")
        else:
            if os.path.exists(switcher_dir_path):
                try:
                    shutil.rmtree(switcher_dir_path)
                except (FileNotFoundError, PermissionError, OSError) as file_err:
                    warn(f'Problem removing existing switcher clone folder:\n\t{file_err}')
            try:
                subprocess.run(git_clone_cmd_lst + branch_args_lst, check=True)
                switcher_cloned = True
            except subprocess.CalledProcessError as proc_err:
                warn(f'Problem while cloning the {switcher_title} branch:\n\t{proc_err}')
            if not switcher_cloned:
                warn(f'Unable to install {switcher_title}. Clone did not succeed.')
            else:
                try:
                    subprocess.run(["./install.sh"], cwd=switcher_dir_path, check=True) #,
                                    # stdout=DEVNULL, stderr=DEVNULL)
                    # print(f'Installed "{switcher_title}" KWin script.')
                except subprocess.CalledProcessError as proc_err:
                    warn(f'Something went wrong installing {switcher_title}.\n\t{proc_err}')

        do_kwin_reconfigure()

        # Set the LayoutName value to big_icons (shows task switcher with large icons, no previews)
        LayoutName_cmd          = [ kwriteconfig_cmd,
                                    '--file', 'kwinrc',
                                    '--group', 'TabBox',
                                    '--key', 'LayoutName', 'big_icons']
        subprocess.run(LayoutName_cmd, check=True)
        print(f'Set task switcher style to: "Large Icons"')

        # Set the HighlightWindows value to false (disables "Show selected window" option)
        HighlightWindows_cmd    = [ kwriteconfig_cmd,
                                    '--file', 'kwinrc',
                                    '--group', 'TabBox',
                                    '--key', 'HighlightWindows', 'false']
        subprocess.run(HighlightWindows_cmd, check=True)
        print(f'Disabled task switcher option: "Show selected window"')

        # Set the ApplicationsMode value to 1 (enables "Only one window per application" option)
        ApplicationsMode_cmd    = [ kwriteconfig_cmd,
                                    '--file', 'kwinrc',
                                    '--group', 'TabBox',
                                    '--key', 'ApplicationsMode', '1']
        subprocess.run(ApplicationsMode_cmd, check=True)
        print(f'Enabled task switcher option: "Only one window per application"')

        do_kwin_reconfigure()

        # Disable single click to open/launch files/folders:
        # kwriteconfig5 --file kdeglobals --group KDE --key SingleClick false
        SingleClick_cmd         = [ kwriteconfig_cmd,
                                    '--file', 'kdeglobals',
                                    '--group', 'KDE',
                                    '--key', 'SingleClick', 'false']
        subprocess.run(SingleClick_cmd, check=True)
        print('Disabled single-click to open/launch files/folders')

        # Try not restarting Plasma shell anymore. 
        # if shutil.which(kstart_cmd):
        #     plasmashell_stopped = False
        #     # Restart Plasma shell to make the new setting active
        #     # kquitapp5/6 plasmashell && kstart5/6 plasmashell
        #     try:
        #         if shutil.which(kquitapp_cmd):
        #             print('Stopping Plasma shell... ', flush=True, end='')
        #             subprocess.run([kquitapp_cmd, 'plasmashell'], check=True,
        #                             stdout=PIPE, stderr=PIPE)
        #             print('Plasma shell stopped.')
        #             plasmashell_stopped = True
        #         else:
        #             error(f'The "{kquitapp_cmd}" command is missing. Skipping plasmashell restart.')
        #     except subprocess.CalledProcessError as proc_err:
        #         err_output: bytes = proc_err.stderr             # type hint error output
        #         error(f'\nProblem while stopping Plasma shell:\n\t{err_output.decode()}')
        #     if plasmashell_stopped:
        #         print('Starting Plasma shell (backgrounded)... ')
        #         subprocess.Popen([kstart_cmd, 'plasmashell'], stdout=PIPE, stderr=PIPE)
        #     else:
        #         error('Plasma shell was not stopped. Skipping restarting Plasma shell.')
        #         print('You should probably log out or restart.')
        # else:
        #     error(f'The "{kstart_cmd}" command is missing. Skipping restarting Plasma shell.')
        #     print('You should probably log out or restart.')


def remove_tweaks_KDE():
    """Utility function to remove the tweaks applied to KDE"""

    if cnfg.DESKTOP_ENV == 'kde':
        KDE_ver = cnfg.DE_MAJ_VER
    else:
        error("ERROR: Asked to remove KDE tweaks, but DE is not KDE.")
        return

    # check that major release ver from env module is rational
    if KDE_ver not in cnfg.valid_KDE_vers:
        error("ERROR: Desktop tweaks for KDE cannot be removed.")
        error(f"KDE major version invalid: '{KDE_ver}'")
        return

    if KDE_ver in ['4', '3']:
        print('No tweaks were applied for KDE 4 or 3. Nothing to remove.')
        return

    kwriteconfig_cmd    = f'kwriteconfig{KDE_ver}'

    # Re-enable Meta key opening the application menu
    subprocess.run([kwriteconfig_cmd,
                    '--file', 'kwinrc',
                    '--group', 'ModifierOnlyShortcuts',
                    '--key', 'Meta', '--delete'],
                    check=True)
    # Disable the "Only one window per application" task switcher option
    subprocess.run([kwriteconfig_cmd,
                    '--file', 'kwinrc',
                    '--group', 'TabBox', 
                    '--key', 'ApplicationsMode', '--delete'],
                    check=True)

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

    if cnfg.barebones_config or is_barebones_config_file():
        print('Not applying tweaks due to barebones config flag or file.')
        show_task_completed_msg()
        return

    if cnfg.fancy_pants:
        print(f'Fancy-Pants install invoked. Additional steps will be taken.')

    if cnfg.DESKTOP_ENV == 'cinnamon':
        print(f'Applying Cinnamon desktop tweaks...')
        apply_tweaks_Cinnamon()
        cnfg.tweak_applied = True

    if cnfg.DESKTOP_ENV == 'gnome':
        print(f'Applying GNOME desktop tweaks...')
        apply_tweaks_GNOME()
        cnfg.tweak_applied = True

    if cnfg.DESKTOP_ENV == 'kde':
        print(f'Applying KDE Plasma desktop tweaks...')
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
            local_fonts_dir = os.path.join(home_dir, '.local', 'share', 'fonts')

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
            cnfg.tweak_applied = True

    if not cnfg.tweak_applied:
        print(f'If nothing printed, no tweaks available for "{cnfg.DESKTOP_ENV}" yet.')
    show_task_completed_msg()


def remove_desktop_tweaks():
    """Undo the relevant desktop tweaks"""

    print(f'\n\n§  Removing any applied desktop environment tweaks...\n{cnfg.separator}')

    if cnfg.barebones_config or is_barebones_config_file():
        print('Not removing tweaks due to barebones config flag or file.')
        show_task_completed_msg()
        return

    # if GNOME, re-enable `overlay-key`
    # gsettings reset org.gnome.mutter overlay-key
    if cnfg.DESKTOP_ENV == 'gnome':
        print(f'Removing GNOME desktop tweaks...')
        remove_tweaks_GNOME()

    if cnfg.DESKTOP_ENV == 'kde':
        print(f'Removing KDE Plasma desktop tweaks...')
        remove_tweaks_KDE()
        
    print('Removed known desktop tweaks applied by installer.')
    show_task_completed_msg()


def uninstall_toshy():
    print(f'\n\n§  Uninstalling Toshy...\n{cnfg.separator}')
    
    # confirm if user really wants to uninstall
    response = input("\nThis will completely uninstall Toshy. Are you sure? [y/N]: ")
    if response not in ['y', 'Y']:
        print(f"\nToshy uninstall cancelled.")
        safe_shutdown(0)
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
        KDE_ver = cnfg.DE_MAJ_VER
        try:
            cmd_lst = [f'kpackagetool{KDE_ver}', '-t', 'KWin/Script', '-r', kwin_script_name]
            subprocess.run(cmd_lst, check=True)
            print("Successfully removed the Toshy D-Bus NotifyActiveWindow KWin script.")
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem removing Toshy KWin script {kwin_script_name}:\n\t{proc_err}')

        # kill the KDE D-Bus service script
        try:
            cmd_lst = ['pkill', '-u', cnfg.user_name, '-f', 'toshy_kde_dbus_service']
            subprocess.run(cmd_lst, check=True)
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem terminating Toshy KDE D-Bus service script:\n\t{proc_err}')

    # try to remove the KDE D-Bus service autostart file
    autostart_dir_path  = os.path.join(home_dir, '.config', 'autostart')
    dbus_svc_dt_file    = os.path.join(autostart_dir_path, 'Toshy_KDE_DBus_Service.desktop')
    dbus_svc_rm_cmd     = ['rm', '-f', dbus_svc_dt_file]
    try:
        # do not pass as list (brackets) since it is already a list
        subprocess.run(dbus_svc_rm_cmd, check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy KDE D-Bus service autostart:\n\t{proc_err}')

    # try to remove the systemd services kickstart autostart file
    autostart_dir_path  = os.path.join(home_dir, '.config', 'autostart')
    svcs_kick_dt_file   = os.path.join(autostart_dir_path, 'Toshy_Systemd_Service_Kickstart.desktop')
    svcs_kick_rm_cmd    = ['rm', '-f', svcs_kick_dt_file]
    try:
        # do not pass as list (brackets) since it is already a list
        subprocess.run(svcs_kick_rm_cmd, check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f'Problem removing Toshy systemd services kickstart autostart:\n\t{proc_err}')

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
        description='Toshy Installer - commands are mutually exclusive',
        epilog=f'Check install options with "./{this_file_name} install --help"',
        allow_abbrev=False
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    subparser_install           = subparsers.add_parser(
        'install',
        help='Install Toshy (see options to modify install actions)'
    )

    subparser_install.add_argument(
        '--override-distro',
        type=str,
        help=f'Override auto-detection of distro. See "--list-distros"'
    )
    subparser_install.add_argument(
        '--barebones-config',
        action='store_true',
        help='Install with mostly empty/blank keymapper config file.'
    )
    subparser_install.add_argument(
        '--skip-native',
        action='store_true',
        help='Skip the install of native packages (for debugging installer).'
    )
    subparser_install.add_argument(
        '--fancy-pants',
        action='store_true',
        help='See README for more info on this option.'
    )

    subparser_list_distros      = subparsers.add_parser(
        'list-distros',
        help='Display list of distros to use with "--override-distro"'
    )

    subparser_show_env          = subparsers.add_parser(
        'show-env',
        help='Show the environment the installer detects, and exit'
    )

    subparser_apply_tweaks      = subparsers.add_parser(
        'apply-tweaks',
        help='Apply desktop environment tweaks only, no install'
    )

    subparser_remove_tweaks     = subparsers.add_parser(
        'remove-tweaks',
        help='Remove desktop environment tweaks only, no install'
    )

    subparser_uninstall         = subparsers.add_parser(
        'uninstall',
        help='Uninstall Toshy'
    )

    args = parser.parse_args()

    # show help output if no command given
    if args.command is None:
        parser.print_help()
        safe_shutdown(0)

    if args.command == 'install':
        if args.override_distro:
            cnfg.override_distro = args.override_distro

        if args.barebones_config:
            cnfg.barebones_config = True

        if args.skip_native:
            cnfg.skip_native = True

        if args.fancy_pants:
            cnfg.fancy_pants = True

        main(cnfg)
        safe_shutdown(0)    # redundant, but that's OK

    if args.command == 'list-distros':
        print(  f'Distros known to the Toshy installer (use with "--override-distro" arg):'
                f'\n\n\t{get_supported_distro_ids()}')
        safe_shutdown(0)

    if args.command == 'show-env':
        get_environment_info()
        safe_shutdown(0)

    if args.command == 'apply-tweaks':
        get_environment_info()
        apply_desktop_tweaks()
        if cnfg.should_reboot:
            show_reboot_prompt()
            print(f'{cnfg.sep_char * 2}  Tweaks application complete. Report issues on the GitHub repo.')
            print(f'{cnfg.sep_char * 2}  https://github.com/RedBearAK/toshy/issues/')
            print(f'{cnfg.sep_char * 2}  >>  ALERT: Something odd happened. You should probably reboot.')
            print(cnfg.separator)
            print(cnfg.separator)
            print()
        safe_shutdown(0)

    if args.command == 'remove-tweaks':
        get_environment_info()
        remove_desktop_tweaks()
        safe_shutdown(0)

    if args.command == 'uninstall':
        uninstall_toshy()
        safe_shutdown(0)


def main(cnfg: InstallerSettings):
    """Main installer function to call specific functions in proper sequence"""

    dot_Xmodmap_warning()
    ask_is_distro_updated()
    ask_add_home_local_bin()

    get_environment_info()

    if cnfg.DISTRO_ID not in get_supported_distro_ids():
        exit_with_invalid_distro_error()

    elevate_privileges()

    if not cnfg.skip_native:
        install_distro_pkgs()

    load_uinput_module()
    install_udev_rules()
    verify_user_groups()

    clone_keyszer_branch()

    backup_toshy_config()
    install_toshy_files()

    setup_python_vir_env()
    install_pip_packages()

    install_bin_commands()
    install_desktop_apps()

    # Python D-Bus service script also does this, but this will refresh if script changes
    if cnfg.DESKTOP_ENV in ['kde', 'plasma']:
        setup_kwin2dbus_script()

    setup_kde_dbus_service()

    setup_systemd_services()

    autostart_systemd_kickstarter()

    autostart_tray_icon()
    apply_desktop_tweaks()

    if cnfg.DESKTOP_ENV == 'gnome':
        print()
        def is_extension_enabled(extension_uuid):
            try:
                output = subprocess.check_output(
                            ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions'])
                extensions = output.decode().strip().replace("'", "").split(",")
            except subprocess.CalledProcessError as proc_err:
                error(f"Unable to check enabled extensions:\n\t{proc_err}")
                return False
            return extension_uuid in extensions

        if is_extension_enabled("appindicatorsupport@rgcjonas.gmail.com"):
            print("AppIndicator extension is enabled. Tray icon should work.")
        else:
            print()
            debug(f"RECOMMENDATION: Install 'AppIndicator' GNOME extension\n"
                "Easiest method: 'flatpak install extensionmanager', search for 'appindicator'\n",
                ctx="!!")

    if os.path.exists(cnfg.reboot_tmp_file):
        cnfg.should_reboot = True

    if cnfg.should_reboot:
        # create reboot reminder temp file, in case installer is run again before a reboot
        if not os.path.exists(cnfg.reboot_tmp_file):
            os.mknod(cnfg.reboot_tmp_file)
        show_reboot_prompt()
        print(f'{cnfg.sep_char * 2}  Toshy install complete. Report issues on the GitHub repo.')
        print(f'{cnfg.sep_char * 2}  https://github.com/RedBearAK/toshy/issues/')
        print(f'{cnfg.sep_char * 2}  >>  ALERT: Permissions changed. You MUST reboot for Toshy to work.')
        print(cnfg.separator)
        print(cnfg.separator)
        print()
    else:

        # Do not (re)start the tray icon here unless user preference allows it
        if cnfg.autostart_tray_icon:
            # Try to start the tray icon immediately, if reboot is not indicated
            tray_icon_cmd = [os.path.join(home_dir, '.local', 'bin', 'toshy-tray')]
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

    safe_shutdown(0)


if __name__ == '__main__':

    print()   # blank line in terminal to start things off

    # Invalidate any `sudo` ticket that might be hanging around, to maximize 
    # the length of time before `sudo` might demand the password again
    try:
        subprocess.run(['sudo', '-k'], check=True)
    except subprocess.CalledProcessError as proc_err:
        error(f"ERROR: 'sudo' found, but 'sudo -k' did not work. Very strange.\n\t{proc_err}")

    # create the configuration settings class instance
    cnfg                        = InstallerSettings()

    # create the native package installer class instance
    native_pkg_installer        = NativePackageInstaller()

    # first parse the CLI arguments
    handle_cli_arguments()
