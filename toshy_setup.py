#!/usr/bin/env python3


from enum import auto
import os
import sys
import pwd
import grp
import json
import signal
import shutil
import zipfile
import argparse
import datetime
import platform
import textwrap
import subprocess
import configparser

from argparse import Namespace
from typing import Any
# local import
import lib.env as env
from lib.logger import debug, error


if os.name == 'posix' and os.geteuid() == 0:
    print("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        print(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
    signal.signal(signal.SIGHUP,    signal_handler)
    signal.signal(signal.SIGUSR1,   signal_handler)
    signal.signal(signal.SIGUSR2,   signal_handler)
else:
    signal.signal(signal.SIGINT,    signal_handler)
    print(f'This is only meant to run on Linux. Exiting...')
    sys.exit(1)



class InstallerSettings:
    """set up variables for necessary information to be used by all functions"""
    def __init__(self) -> None:
        self.separator          = '============================================='
        self.env_info_dct       = None
        self.override_distro    = None
        self.DISTRO_NAME        = None
        self.DISTRO_VER         = None
        self.SESSION_TYPE       = None
        self.DESKTOP_ENV        = None
        
        self.systemctl_present  = shutil.which('systemctl') is not None
        self.init_system        = None

        self.pkgs_json_dct      = None
        self.pkgs_for_distro    = None
        self.pip_pkgs           = None

        self.home_dir_path      = os.path.abspath(os.path.expanduser('~'))
        self.toshy_dir_path     = os.path.join(self.home_dir_path, '.config', 'toshy')
        self.backup_succeeded   = None
        self.venv_path          = os.path.join(self.toshy_dir_path, '.venv')

        self.keyszer_tmp_path   = os.path.join('.', 'keyszer-temp')

        # keyszer_branch          = 'env_and_adapt_to_capslock'
        # keyszer_branch          = 'environ_api'
        self.keyszer_branch     = 'environ_api_kde'
        self.keyszer_url        = 'https://github.com/RedBearAK/keyszer.git'
        self.keyszer_clone_cmd  = f'git clone -b {self.keyszer_branch} {self.keyszer_url}'

        self.input_group_name   = 'input'
        self.user_name          = pwd.getpwuid(os.getuid()).pw_name

        self.should_reboot      = None
        self.reboot_tmp_file    = "/tmp/toshy_installer_says_reboot"
        self.reboot_ascii_art   = textwrap.dedent("""
                ██████      ███████     ██████       ██████       ██████      ████████     ██ 
                ██   ██     ██          ██   ██     ██    ██     ██    ██        ██        ██ 
                ██████      █████       ██████      ██    ██     ██    ██        ██        ██ 
                ██   ██     ██          ██   ██     ██    ██     ██    ██        ██           
                ██   ██     ███████     ██████       ██████       ██████         ██        ██ 
                """)


def get_environment_info():
    """get back the distro name, distro version, session type and 
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

    print('')   # blank line after init system message

    cnfg.env_info_dct   = env.get_env_info()

    # Avoid casefold() errors by converting all to strings
    if cnfg.override_distro:
        cnfg.DISTRO_NAME    = str(cnfg.override_distro).casefold()
    else:
        cnfg.DISTRO_NAME    = str(cnfg.env_info_dct.get('DISTRO_NAME',  'keymissing')).casefold()

    cnfg.DISTRO_VER     = str(cnfg.env_info_dct.get('DISTRO_VER',   'keymissing')).casefold()
    cnfg.SESSION_TYPE   = str(cnfg.env_info_dct.get('SESSION_TYPE', 'keymissing')).casefold()
    cnfg.DESKTOP_ENV    = str(cnfg.env_info_dct.get('DESKTOP_ENV',  'keymissing')).casefold()
    # This syntax fails on anything older than Python 3.8
    print(  f'Toshy installer sees this environment:'
            f'\n\t{cnfg.DISTRO_NAME     = }'
            f'\n\t{cnfg.DISTRO_VER      = }'
            f'\n\t{cnfg.SESSION_TYPE    = }'
            f'\n\t{cnfg.DESKTOP_ENV     = }'
            f'\n')


def call_attention_to_password_prompt():
    try:
        subprocess.run( ['sudo', '-n', 'true'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=True)
    except subprocess.CalledProcessError:
        # sudo requires a password
        print('')
        print('-- PASSWORD REQUIRED --')
        print('')


def prompt_for_reboot():
    cnfg.should_reboot = True
    if not os.path.exists(cnfg.reboot_tmp_file):
        os.mknod(cnfg.reboot_tmp_file)


def load_uinput_module():
    """Check to see if `uinput` kernel module is loaded"""

    print(f'\n\n§  Checking status of "uinput" kernel module...\n{cnfg.separator}')

    try:
        subprocess.check_output("lsmod | grep uinput", shell=True)
        print('"uinput" module is already loaded')
    except subprocess.CalledProcessError:
        print('"uinput" module is not loaded, loading now...')
        call_attention_to_password_prompt()
        subprocess.run(f'sudo modprobe uinput', shell=True, check=True)

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
                print(f"Failed to create /etc/modules-load.d/uinput.conf: {proc_error}")
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
                        print(f"ERROR: Failed to append 'uinput' to /etc/modules: {proc_error}")


def reload_udev_rules():
    try:
        call_attention_to_password_prompt()
        subprocess.run(
            "sudo udevadm control --reload-rules && sudo udevadm trigger",
            shell=True, check=True)
        print('"udev" rules reloaded successfully.')
    except subprocess.CalledProcessError as proc_error:
        print(f'Failed to reload "udev" rules: {proc_error}')
        prompt_for_reboot()


def install_udev_rules():
    """set up udev rules file to give user/keyszer access to uinput"""
    print(f'\n\n§  Installing "udev" rules file for keymapper...\n{cnfg.separator}')
    rules_file_path = '/etc/udev/rules.d/90-toshy-keymapper-input.rules'
    rule_content = (
        'SUBSYSTEM=="input", GROUP="input"\n'
        'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input", MODE="0660"\n'
    )
    # Only write the file if it doesn't exist or its contents are different
    if not os.path.exists(rules_file_path) or open(rules_file_path).read() != rule_content:
        command = f'sudo tee {rules_file_path}'
        try:
            call_attention_to_password_prompt()
            subprocess.run(command, input=rule_content.encode(), shell=True, check=True)
            print(f'"udev" rules file successfully installed.')
            reload_udev_rules()
        except subprocess.CalledProcessError as proc_error:
            print(f'\nERROR: Problem while installing "udev" rules file for keymapper...\n')
            err_output: bytes = proc_error.output  # Type hinting the error_output variable
            # Deal with possible 'NoneType' error output
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)
    else:
        print(f'"udev" rules file already in place.')


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
            print(f'\nERROR: Problem when trying to create "input" group...\n')
            err_output: bytes = proc_error.output  # Type hinting the error_output variable
            # Deal with possible 'NoneType' error output
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)

    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.input_group_name)
    if cnfg.user_name in group_info.gr_mem:
        print(f'User "{cnfg.user_name}" is a member of '
                f'group "{cnfg.input_group_name}", continuing...')
    else:
        # Add the user to the input group
        try:
            call_attention_to_password_prompt()
            subprocess.run(
                ['sudo', 'usermod', '-aG', cnfg.input_group_name, cnfg.user_name], check=True)
        except subprocess.CalledProcessError as proc_error:
            print(f'\nERROR: Problem when trying to add user "{cnfg.user_name}" to '
                    f'group "{cnfg.input_group_name}"...\n')
            err_output: bytes = proc_error.output  # Type hinting the error_output variable
            # Deal with possible 'NoneType' error output
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)

        print(f'User "{cnfg.user_name}" added to group "{cnfg.input_group_name}"...')
        prompt_for_reboot()


def load_package_list():
    """load package list from JSON file"""
    with open('packages.json') as f:
        cnfg.pkgs_json_dct = json.load(f)

    # cnfg.pip_pkgs = cnfg.pkgs_json_dct['pip']

    cnfg.pip_pkgs = [
            "pillow",
            "lockfile",
            "dbus-python",
            "systemd-python",
            "pygobject",
            "tk",
            "sv_ttk",
            "psutil",
            "watchdog",
            "inotify-simple",
            "evdev",
            "appdirs",
            "ordered-set",
            "python-xlib",
            "six"
    ]

    try:
        cnfg.pkgs_for_distro = cnfg.pkgs_json_dct[cnfg.DISTRO_NAME]
    except KeyError:
        print(f"\nERROR: No list of packages found for this distro: '{cnfg.DISTRO_NAME}'")
        print(f'Installation cannot proceed without a list of packages. Sorry.\n')
        sys.exit(1)


def install_distro_pkgs():
    """install needed packages from list for distro type"""
    print(f'\n\n§  Installing native packages...\n{cnfg.separator}')

    # Filter out systemd packages if not present
    cnfg.pkgs_for_distro = [
        pkg for pkg in cnfg.pkgs_for_distro 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    apt_distros = ['ubuntu', 'mint', 'lmde', 'popos', 'eos', 'neon', 'zorin', 'debian']
    dnf_distros_Fedora = ['fedora', 'fedoralinux']
    dnf_distros_RHEL = ['almalinux', 'rocky', 'rhel']
    pacman_distros = ['arch', 'endeavouros', 'manjaro']
    zypper_distros = ['opensuse']

    if cnfg.DISTRO_NAME in apt_distros:
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'apt', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in dnf_distros_Fedora:
        call_attention_to_password_prompt()
        subprocess.run(['sudo', 'dnf', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in dnf_distros_RHEL:
        call_attention_to_password_prompt()
        # for libappindicator-gtk3:
        # sudo dnf install epel-release
        subprocess.run('sudo dnf install epel-release', shell=True)
        # for gobject-introspection-devel:
        # sudo dnf config-manager --set-enabled crb
        subprocess.run('sudo dnf config-manager --set-enabled crb', shell=True)
        subprocess.run('sudo dnf update -y', shell=True)
        subprocess.run(['sudo', 'dnf', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in pacman_distros:
        print(f'\n\nNOTICE: It is ESSENTIAL to have an Arch-based system completely updated.')
        response = input('Have you run "sudo pacman -Syu" recently? [y/N]: ')

        if response in ['y', 'Y']:
            def is_package_installed(package):
                result = subprocess.run(
                                ['pacman', '-Q', package],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL
                            )
                return result.returncode == 0

            pkgs_to_install = [
                pkg
                for pkg in cnfg.pkgs_for_distro
                if not is_package_installed(pkg)
            ]
            if pkgs_to_install:
                call_attention_to_password_prompt()
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm'] + pkgs_to_install)

        else:
            print('Installer will fail with version mismatches if you have not updated recently.')
            print('Update your Arch-based system and try the Toshy installer again. Exiting.')
            sys.exit(1)
    elif cnfg.DISTRO_NAME in zypper_distros:
        # TODO: make sure this actually works!
        subprocess.run(['zypper', '--non-interactive', 'install'] + cnfg.pkgs_for_distro)

    else:
        print(f"\nERROR: Installer does not know how to handle distro: {cnfg.DISTRO_NAME}\n")
        sys.exit(1)


def clone_keyszer_branch():
    """clone the latest `keyszer` from GitHub"""
    print(f'\n\n§  Cloning keyszer branch ({cnfg.keyszer_branch})...\n{cnfg.separator}')
    
    # Check if `git` command exists. If not, exit script with error.
    has_git = shutil.which('git')
    if not has_git:
        print(f'ERROR: "git" is not installed, for some reason. Cannot continue.')
        sys.exit(1)

    if os.path.exists(cnfg.keyszer_tmp_path):
        # force a fresh copy of keyszer every time script is run
        shutil.rmtree(cnfg.keyszer_tmp_path, ignore_errors=True)
    subprocess.run(cnfg.keyszer_clone_cmd.split() + [cnfg.keyszer_tmp_path])


def backup_toshy_config():
    """backup existing Toshy config folder"""
    print(f'\n\n§  Backing up existing Toshy config folder...\n{cnfg.separator}')
    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_backup_dir_path = os.path.abspath(cnfg.toshy_dir_path + timestamp)
    if os.path.exists(os.path.join(os.path.expanduser('~'), '.config', 'toshy')):
        try:
            # Define the ignore function
            def ignore_venv(dirname, filenames):
                return ['.venv'] if '.venv' in filenames else []
            # Copy files recursively from source to destination
            shutil.copytree(cnfg.toshy_dir_path, toshy_backup_dir_path, ignore=ignore_venv)
        except shutil.Error as copy_error:
            print(f"Failed to copy directory: {copy_error}")
            exit(1)
        except OSError as os_error:
            print(f"Failed to create backup directory: {os_error}")
            exit(1)
        print(f'Backup completed to {toshy_backup_dir_path}')
        cnfg.backup_succeeded = True
    else:
        print(f'No existing Toshy folder to backup...')
        cnfg.backup_succeeded = True


def install_toshy_files():
    """install Toshy files"""
    print(f'\n\n§  Installing Toshy files...\n{cnfg.separator}')
    if not cnfg.backup_succeeded:
        print(f'Backup of Toshy config folder failed? Bailing out...')
        exit(1)
    script_name = os.path.basename(__file__)
    keyszer_tmp = os.path.basename(cnfg.keyszer_tmp_path)
    try:
        if os.path.exists(cnfg.toshy_dir_path):
            shutil.rmtree(cnfg.toshy_dir_path, ignore_errors=True)
        # Copy files recursively from source to destination
        shutil.copytree(
            '.', 
            cnfg.toshy_dir_path, 
            ignore=shutil.ignore_patterns(
                script_name,
                keyszer_tmp,
                'LICENSE',
                '.gitignore',
                'packages.json',
                'README.md'
            )
        )
    except shutil.Error as copy_error:
        print(f"Failed to copy directory: {copy_error}")
    except OSError as os_error:
        print(f"Failed to create backup directory: {os_error}")
    toshy_default_cfg = os.path.join(
        cnfg.toshy_dir_path, 'toshy-default-config', 'toshy_config.py')
    shutil.copy(toshy_default_cfg, cnfg.toshy_dir_path)
    print(f'Toshy files installed in {cnfg.toshy_dir_path}...')


def setup_virtual_env():
    """setup a virtual environment to install Python packages"""
    print(f'\n\n§  Setting up Python virtual environment...\n{cnfg.separator}')

    # Create the virtual environment if it doesn't exist
    if not os.path.exists(cnfg.venv_path):
        subprocess.run([sys.executable, '-m', 'venv', cnfg.venv_path])
    # We do not need to "activate" the venv right now, just create it
    print(f'Virtual environment setup complete.')


def install_pip_packages():
    """install `pip` packages for Python"""
    print(f'\n\n§  Installing/upgrading Python packages...\n{cnfg.separator}')
    venv_python_cmd = os.path.join(cnfg.venv_path, 'bin', 'python')
    venv_pip_cmd    = os.path.join(cnfg.venv_path, 'bin', 'pip')
    
    # Filter out systemd packages if not present
    cnfg.pip_pkgs = [
        pkg for pkg in cnfg.pip_pkgs 
        if cnfg.systemctl_present or 'systemd' not in pkg
    ]

    commands        = [
        [venv_python_cmd, '-m', 'pip', 'install', '--upgrade', 'pip'],
        [venv_pip_cmd, 'install', '--upgrade', 'wheel'],
        [venv_pip_cmd, 'install', '--upgrade', 'setuptools'],
        [venv_pip_cmd, 'install', '--upgrade'] + cnfg.pip_pkgs
    ]
    for command in commands:
        result = subprocess.run(command)
        if result.returncode != 0:
            print(f'Error installing/upgrading Python packages. Installer exiting...')
            sys.exit(1)
    if os.path.exists('./keyszer-temp'):
        result = subprocess.run([venv_pip_cmd, 'install', '--upgrade', './keyszer-temp'])
        if result.returncode != 0:
            print(f'Error installing/upgrading "keyszer".')
            sys.exit(1)
    else:
        print(f'"keyszer-temp" folder missing... Unable to install "keyszer".')
        sys.exit(1)


def install_bin_commands():
    """install the convenient scripts to manage Toshy"""
    print(f'\n\n§  Installing Toshy script commands...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-bincommands-setup.sh')
    subprocess.run([script_path])


# Replace $HOME with user home directory
def replace_home_in_file(filename):
    """utility function to replace '$HOME' in .desktop files with actual home path"""
    # Read in the file
    with open(filename, 'r') as file:
        file_data = file.read()
    # Replace the target string
    file_data = file_data.replace('$HOME', cnfg.home_dir_path)
    # Write the file out again
    with open(filename, 'w') as file:
        file.write(file_data)


def install_desktop_apps():
    """install the convenient scripts to manage Toshy"""
    print(f'\n\n§  Installing Toshy desktop apps...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-desktopapps-setup.sh')
    subprocess.run([script_path])

    desktop_files_path  = os.path.join(cnfg.home_dir_path, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    gui_desktop_file    = os.path.join(desktop_files_path, 'Toshy_GUI.desktop')

    replace_home_in_file(tray_desktop_file)
    replace_home_in_file(gui_desktop_file)


def add_kwin_script_to_kwinrc():
    """utility function to add Toshy KWin script to KWin RC file"""
    # Define path to kwinrc
    kwinrc_path = os.path.join(os.path.expanduser('~'), '.config', 'kwinrc')

    # Check if kwinrc exists and create if it does not
    if not os.path.exists(kwinrc_path):
        open(kwinrc_path, 'a').close()

    # Create a ConfigParser object and read kwinrc
    config = configparser.ConfigParser()
    config.read(kwinrc_path)

    # Check if 'Plugins' section exists and create if it does not
    if 'Plugins' not in config.sections():
        config.add_section('Plugins')

    # Check if 'toshy-dbus-notifyactivewindowEnabled' option exists in 'Plugins' section 
    # and set to 'true' if it does not
    if 'toshy-dbus-notifyactivewindowEnabled' not in config['Plugins']:
        config.set('Plugins', 'toshy-dbus-notifyactivewindowEnabled', 'true')
    elif config['Plugins'].getboolean('toshy-dbus-notifyactivewindowEnabled') is False:
        config.set('Plugins', 'toshy-dbus-notifyactivewindowEnabled', 'true')

    # Write changes back to kwinrc
    with open(kwinrc_path, 'w') as configfile:
        config.write(configfile)


def setup_kwin_script():
    """install the KWin script to notify D-Bus service about window focus changes"""
    print(f'\n\n§  Setting up the Toshy KWin script...\n{cnfg.separator}')
    kwin_script_name    = 'toshy-dbus-notifyactivewindow'
    kwin_script_path    = os.path.join( cnfg.toshy_dir_path,
                                        'kde-kwin-dbus-service',
                                        'toshy-dbus-notifyactivewindow')
    temp_file_path      = '/tmp/toshy-dbus-notifyactivewindow.kwinscript'

    # Create a zip file (overwrite if it exists)
    with zipfile.ZipFile(temp_file_path, 'w') as zipf:
        # Add main.js to the kwinscript package
        zipf.write( os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                    arcname='contents/code/main.js')
        # Add metadata.desktop to the kwinscript package
        zipf.write( os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

    base_qdbus_cmd = 'qdbus org.kde.KWin /Scripting org.kde.kwin.Scripting'
    
    # Try to unload any existing KWin script by the same name
    subprocess.run(f"{base_qdbus_cmd}.unloadScript {kwin_script_name}",
                    capture_output=True, shell=True)
    
    # Try to remove any installed KWin script entirely
    result = subprocess.run(
        ['plasmapkg2', '-t', 'kwinscript', '-r', temp_file_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        pass
        # print(f"Error removing the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully removed the KWin script.")

    # Install the script using plasmapkg2
    result = subprocess.run(
        ['plasmapkg2', '-t', 'kwinscript', '-u', temp_file_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error installing the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully installed the KWin script.")

    # Remove the temporary kwinscript file
    try:
        os.remove(temp_file_path)
    except (FileNotFoundError, PermissionError): pass

    # Try to load the KWin script by name
    subprocess.run(f"{base_qdbus_cmd}.loadScript {kwin_script_name}",
                    capture_output=True, shell=True)
    
    # Try to start the KWin script by name
    subprocess.run(f"{base_qdbus_cmd}.start {kwin_script_name}",
                    capture_output=True, shell=True)
    
    # Make sure script is added as "enabled" in ~/.config/kwinrc
    add_kwin_script_to_kwinrc()
    # Try to get KWin to notice and activate the script on its own, now that it's in RC file
    subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])



def setup_kde_dbus_service():
    """install the D-Bus service initialization script to receive window focus
    change notifications from the KWin script on KDE desktops (Wayland)"""
    print(f'\n\n§  Setting up the Toshy KDE D-Bus service...\n{cnfg.separator}')

    # need to autostart "$HOME/.local/bin/toshy-kde-dbus-service"
    user_path               = os.path.expanduser('~')
    autostart_dir_path      = os.path.join(user_path, '.config', 'autostart')
    dbus_svc_desktop_path   = os.path.join(cnfg.toshy_dir_path, 'desktop')
    dbus_svc_desktop_file   = os.path.join(dbus_svc_desktop_path, 'Toshy_KDE_DBus_Service.desktop')
    start_dbus_svc_cmd      = os.path.join(user_path, '.local', 'bin', 'toshy-kde-dbus-service')
    replace_home_in_file(dbus_svc_desktop_file)

    # ensure autostart directory exists
    try:
        os.makedirs(autostart_dir_path, exist_ok=True)
    except (PermissionError, NotADirectoryError, FileExistsError) as file_error:
        error(f"Problem trying to make sure '{autostart_dir_path}' is directory.\n\t{file_error}")
        sys.exit(1)
    shutil.copy(dbus_svc_desktop_file, autostart_dir_path)
    print(f'Toshy KDE D-Bus service should autostart at login.')

    subprocess.run('pkill -f "toshy_kde_dbus_service"', shell=True)
    subprocess.Popen(   start_dbus_svc_cmd, shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL   )
    print(f'Toshy KDE D-Bus service should be running now.')


def setup_systemd_services():
    """invoke the systemd setup script to install the systemd service units"""
    print(f'\n\n§  Setting up the Toshy systemd services...\n{cnfg.separator}')
    if cnfg.systemctl_present:
        script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'bin', 'toshy-systemd-setup.sh')
        subprocess.run([script_path])
    else:
        print(f'System does not seem to be using "systemd"')


def autostart_tray_icon():
    """set the tray icon to autostart at login"""
    print(f'\n\n§  Setting tray icon to load automatically at login...\n{cnfg.separator}')
    user_path           = os.path.expanduser('~')
    desktop_files_path  = os.path.join(user_path, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    autostart_dir_path  = os.path.join(user_path, '.config', 'autostart')
    dest_link_file      = os.path.join(autostart_dir_path, 'Toshy_Tray.desktop')

    # Need to create autostart folder if necessary
    try:
        os.makedirs(autostart_dir_path, exist_ok=True)
    except (PermissionError, NotADirectoryError, FileExistsError) as file_error:
        error(f"Problem trying to make sure '{autostart_dir_path}' is directory.\n\t{file_error}")
        sys.exit(1)
    subprocess.run(['ln', '-sf', tray_desktop_file, dest_link_file])

    print(f'Tray icon should appear in system tray at each login.')


###################################################################################################
def apply_kde_tweak():
    """Add a tweak to kwinrc file to disable Meta key opening app menu."""

    # Define path to kwinrc
    kwinrc_path = os.path.join(os.path.expanduser('~'), '.config', 'kwinrc')

    # Check if kwinrc exists and create if it does not
    if not os.path.exists(kwinrc_path):
        open(kwinrc_path, 'a').close()

    # Create a ConfigParser object and read kwinrc
    config = configparser.ConfigParser()
    config.read(kwinrc_path)

    # Check if 'ModifierOnlyShortcuts' section exists and create if it does not
    if 'ModifierOnlyShortcuts' not in config.sections():
        config.add_section('ModifierOnlyShortcuts')

    # Set 'Meta' option in 'ModifierOnlyShortcuts' section to empty
    config.set('ModifierOnlyShortcuts', 'Meta', '')

    # Write changes back to kwinrc
    with open(kwinrc_path, 'w') as configfile:
        config.write(configfile)

    # Run reconfigure command
    subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])


def remove_kde_tweak():
    """Remove the tweak to kwinrc file that disables Meta key opening app menu."""

    # Define path to kwinrc
    kwinrc_path = os.path.join(os.path.expanduser('~'), '.config', 'kwinrc')

    # Check if kwinrc exists, if not there is nothing to do
    if not os.path.exists(kwinrc_path):
        return

    # Create a ConfigParser object and read kwinrc
    config = configparser.ConfigParser()
    config.read(kwinrc_path)

    # Check if 'ModifierOnlyShortcuts' section exists, if not there is nothing to do
    if 'ModifierOnlyShortcuts' not in config.sections():
        return

    # Check if 'Meta' option exists in 'ModifierOnlyShortcuts' section, if not there is nothing to do
    if 'Meta' not in config['ModifierOnlyShortcuts']:
        return

    # Remove 'Meta' option from 'ModifierOnlyShortcuts' section
    config.remove_option('ModifierOnlyShortcuts', 'Meta')

    # Write changes back to kwinrc
    with open(kwinrc_path, 'w') as configfile:
        config.write(configfile)

    # Run reconfigure command
    subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])
###################################################################################################


def apply_desktop_tweaks():
    """
    fix things like Meta key activating overview in GNOME or KDE Plasma
    and fix the Unicode sequences in KDE Plasma
    
    TODO: These tweaks should probably be done at startup of the config
            instead of (or in addition to) here in the installer. 
    """

    tweak_applied = None
    print(f'\n\n§  Applying any known desktop environment tweaks...\n{cnfg.separator}')

    # if GNOME, disable `overlay-key`
    # gsettings set org.gnome.mutter overlay-key ''
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'set', 'org.gnome.mutter', 'overlay-key', ''])
        print(f'Disabling Super/Meta/Win/Cmd key opening the GNOME overview...')
        tweak_applied = True

        def is_extension_enabled(extension_uuid):
            output = subprocess.check_output(
                        ['gsettings', 'get', 'org.gnome.shell', 'enabled-extensions'])
            extensions = output.decode().strip().replace("'", "").split(",")
            return extension_uuid in extensions

        if is_extension_enabled("appindicatorsupport@rgcjonas.gmail.com"):
            print("AppIndicator extension is enabled. Tray icon should work.")
            # pass
        else:
            print(f"RECOMMENDATION: Install AppIndicator GNOME extension\n"
                "Easiest method: 'flatpak install extensionmanager', search for 'appindicator'")

    if cnfg.DESKTOP_ENV == 'kde':
        apply_kde_tweak()
    
    # if KDE, install `ibus` or `fcitx` and choose as input manager (ask for confirmation)
    
    if not tweak_applied:
        print(f'If nothing printed, no tweaks available for "{cnfg.DESKTOP_ENV}" yet.')


def remove_desktop_tweaks():
    """undo the relevant desktop tweaks"""

    print(f'\n\n§  Removing any applied desktop environment tweaks...\n{cnfg.separator}')

    # if GNOME, re-enable `overlay-key`
    # gsettings reset org.gnome.mutter overlay-key
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'reset', 'org.gnome.mutter', 'overlay-key'])

    if cnfg.DESKTOP_ENV == 'kde':
        remove_kde_tweak()


def uninstall_toshy():
    print("Uninstalling Toshy...")
    remove_desktop_tweaks()
    # TODO: do more uninstaller stuff...


def show_environment():
    pass


def handle_arguments():
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
        dest='override_distro',
        help='Override auto-detection of distro name/type'
    )
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Uninstall Toshy (NOT IMPLEMENTED YET)'
    )
    parser.add_argument(
        '--show-env',
        action='store_true',
        dest='show_env',
        help='Show the environment the installer detects, and exit'
    )
    parser.add_argument(
        '--apply-tweaks',
        action='store_true',
        dest='apply_tweaks',
        help='Apply desktop environment tweaks (NOT IMPLEMENTED YET)'
    )
    parser.add_argument(
        '--remove-tweaks',
        action='store_true',
        dest='remove_tweaks',
        help='Remove desktop environment tweaks (NOT IMPLEMENTED YET)'
    )

    args = parser.parse_args()

    # Check the values of arguments and perform actions accordingly
    if args.override_distro:
        cnfg.override_distro = args.override_distro
        # proceed with normal install sequence
        main(cnfg)
    elif args.show_env:
        get_environment_info()
        sys.exit(0)
    elif args.apply_tweaks:
        raise NotImplementedError
        apply_desktop_tweaks()
    elif args.remove_tweaks:
        raise NotImplementedError
        remove_desktop_tweaks()
    elif args.uninstall:
        raise NotImplementedError
        uninstall_toshy()
    else:
        # proceed with normal install sequence if no CLI args given
        main(cnfg)


def main(cnfg: InstallerSettings):
    """Main installer function"""

    get_environment_info()

    load_uinput_module()
    install_udev_rules()
    verify_user_groups()

    load_package_list()
    install_distro_pkgs()
    clone_keyszer_branch()

    backup_toshy_config()
    install_toshy_files()
    setup_virtual_env()
    install_pip_packages()
    install_bin_commands()
    install_desktop_apps()
    if cnfg.DESKTOP_ENV in ['kde', 'plasma']:
        setup_kwin_script()
        setup_kde_dbus_service()

    setup_systemd_services()

    autostart_tray_icon()
    apply_desktop_tweaks()

    if cnfg.should_reboot or os.path.exists(cnfg.reboot_tmp_file):
        cnfg.should_reboot = True
        # create reboot reminder temp file, in case installer is run again
        if not os.path.exists(cnfg.reboot_tmp_file):
            os.mknod(cnfg.reboot_tmp_file)
        print(  f'\n\n'
                f'{cnfg.separator}\n'
                f'{cnfg.reboot_ascii_art}'
                f'{cnfg.separator}\n\n'
                f'Toshy install complete. Report issues on the GitHub repo.\n'
                '>>> ALERT: Permissions changed. You MUST reboot for Toshy to work...\n'
                f'{cnfg.separator}\n'
        )

    if not cnfg.should_reboot:
        # Try to start the tray icon immediately, if reboot is not indicated
        # tray_command        = ['gtk-launch', 'Toshy_Tray']
        tray_icon_cmd = [os.path.join(cnfg.home_dir_path, '.local', 'bin', 'toshy-tray')]
        # Try to launch the tray icon in a separate process not linked to current shell
        # Also, suppress output that might confuse the user
        subprocess.Popen(
            tray_icon_cmd,
            shell=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(  f'\n\n{cnfg.separator}\n\n'
                f'Toshy install complete. Report issues on the GitHub repo.\n'
                f'Rebooting should not be necessary.\n'
                f'{cnfg.separator}\n'
        )

    print('')   # blank line to avoid crowding the prompt after install is done


if __name__ == '__main__':

    print('')   # blank line in terminal to start things off

    # Check if 'sudo' command is available
    if not shutil.which('sudo'):
        print("Error: 'sudo' not found. Installer will fail without it. Exiting.")
        sys.exit(1)

    # Invalidate any `sudo` ticket that might be hanging around
    try:
        subprocess.run("sudo -k", shell=True, check=True)
    except subprocess.CalledProcessError:
        print(f"ERROR: 'sudo' found, but 'sudo -k' did not work. Very strange.")

    cnfg = InstallerSettings()

    handle_arguments()

    # This gets called in handle_arguments() as 'else' action
    # when there are no arguments passed:
    # main(cnfg)
