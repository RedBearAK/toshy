#!/usr/bin/env python3


import os
import sys
import pwd
import grp
import json
import signal
import shutil
import argparse
import datetime
import platform
import subprocess

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
        self.separator          = '========================'
        self.env_info_dct       = None
        self.DISTRO_NAME        = None
        self.DISTRO_VER         = None
        self.SESSION_TYPE       = None
        self.DESKTOP_ENV        = None

        self.pkgs_json_dct      = None
        self.pkgs_for_distro    = None
        self.pip_pkgs           = None

        self.home_dir_path      = os.path.abspath(os.path.expanduser('~'))
        self.toshy_dir_path     = os.path.join(self.home_dir_path, '.config', 'toshy')
        self.backup_succeeded   = None
        self.venv_path          = os.path.join(self.toshy_dir_path, '.venv')

        self.keyszer_tmp_path   = os.path.join('.', 'keyszer-temp')
        self.keyszer_clone_cmd  = (
            'git clone -b adapt_to_capslock https://github.com/RedBearAK/keyszer.git'
            )

        self.input_group_name   = 'input'
        self.user_name          = pwd.getpwuid(os.getuid()).pw_name
        self.should_reboot      = None


def get_environment_info():
    """get back the distro name, distro version, session type and 
        desktop environment from `env.py` module"""
    cnfg.env_info_dct   = env.get_env_info()
    # Avoid casefold() errors by converting all to strings
    cnfg.DISTRO_NAME    = str(cnfg.env_info_dct.get('DISTRO_NAME',  'keymissing').casefold())
    cnfg.DISTRO_VER     = str(cnfg.env_info_dct.get('DISTRO_VER',   'keymissing').casefold())
    cnfg.SESSION_TYPE   = str(cnfg.env_info_dct.get('SESSION_TYPE', 'keymissing').casefold())
    cnfg.DESKTOP_ENV    = str(cnfg.env_info_dct.get('DESKTOP_ENV',  'keymissing').casefold())
    print(  f'Toshy installer sees this environment:'
            f'\n\t{cnfg.DISTRO_NAME     = }'
            f'\n\t{cnfg.DISTRO_VER      = }'
            f'\n\t{cnfg.SESSION_TYPE    = }'
            f'\n\t{cnfg.DESKTOP_ENV     = }')


def install_udev_rules():
    """set up udev rules file to give user/keyszer access to uinput"""
    print(f'\n\nInstalling "udev" rules file for keymapper...\n{cnfg.separator}')
    if not os.path.exists('/etc/udev/rules.d/90-keymapper-input.rules'):
        rule_content = (
            'SUBSYSTEM=="input", GROUP="input"\n'
            'KERNEL=="uinput", SUBSYSTEM=="misc", GROUP="input"\n'
        )
        command = 'sudo tee /etc/udev/rules.d/90-keymapper-input.rules'
        try:
            subprocess.run(command, input=rule_content.encode(), shell=True, check=True)
            print(f'"udev" rules file successfully installed.')
            cnfg.should_reboot = True
        except subprocess.CalledProcessError as e:
            print(f'\nERROR: Problem while installing "udev" rules file for keymapper...\n')
            err_output: bytes = e.output  # Type hinting the error_output variable
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)
    else:
        print(f'"udev" rules file already in place.')


def verify_user_groups():
    """Check if the `input` group exists and user is in group"""
    print(f'\n\nChecking if user is in "input" group...\n{cnfg.separator}')
    try:
        grp.getgrnam(cnfg.input_group_name)
    except KeyError:
        # The group doesn't exist, so create it
        print(f'Creating "input" group...\n{cnfg.separator}')
        try:
            subprocess.run(['sudo', 'groupadd', cnfg.input_group_name], check=True)
        except subprocess.CalledProcessError as e:
            print(f'\nERROR: Problem when trying to create "input" group...\n')
            err_output: bytes = e.output  # Type hinting the error_output variable
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)

    # Check if the user is already in the `input` group
    group_info = grp.getgrnam(cnfg.input_group_name)
    if cnfg.user_name in group_info.gr_mem:
        print(f'User "{cnfg.user_name}" is a member of '
                f'group "{cnfg.input_group_name}", continuing...\n')
    else:
        # Add the user to the input group
        try:
            subprocess.run(
                ['sudo', 'usermod', '-aG', cnfg.input_group_name, cnfg.user_name], check=True)
        except subprocess.CalledProcessError as e:
            print(f'\nERROR: Problem when trying to add user "{cnfg.user_name}" to '
                    f'group "{cnfg.input_group_name}"...\n')
            err_output: bytes = e.output  # Type hinting the error_output variable
            print(f'Command output:\n{err_output.decode() if err_output else "No error output"}')
            print(f'\nERROR: Install failed.')
            sys.exit(1)

        print(f'\nUser "{cnfg.user_name}" added to group "{cnfg.input_group_name}"...')
        cnfg.should_reboot = True


def load_package_list():
    """load package list from JSON file"""
    with open('packages.json') as f:
        cnfg.pkgs_json_dct = json.load(f)
    cnfg.pip_pkgs = cnfg.pkgs_json_dct['pip']
    cnfg.pkgs_for_distro = cnfg.pkgs_json_dct[cnfg.DISTRO_NAME]


def install_distro_pkgs():
    """install needed packages from list for distro type"""
    print(f'\n\nInstalling native packages...\n{cnfg.separator}')

    if cnfg.DISTRO_NAME in ['ubuntu', 'linux mint', 'debian']:
        subprocess.run(['sudo', 'apt', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in ['fedora', 'fedoralinux']:
        subprocess.run(['sudo', 'dnf', 'install', '-y'] + cnfg.pkgs_for_distro)

    elif cnfg.DISTRO_NAME in ['arch', 'manjaro']:
        print('NOTICE: It is ESSENTIAL to have an Arch-based system completely updated.')
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
                subprocess.run(['sudo', 'pacman', '-S', '--noconfirm'] + pkgs_to_install)

        else:
            print('Installer will fail with version mismatches if you have not updated recently.')
            print('Update your Arch-based system and try the Toshy installer again. Exiting.')
            sys.exit(1)

    else:
        print(f"Sorry, no package list available yet for distro: {cnfg.DISTRO_NAME}")
        sys.exit(1)


def clone_keyszer_branch():
    """clone the latest `keyszer` from GitHub"""
    print(f'\n\nCloning keyszer branch...\n{cnfg.separator}')
    if os.path.exists(cnfg.keyszer_tmp_path):
        # force a fresh copy of keyszer every time script is run
        shutil.rmtree(cnfg.keyszer_tmp_path, ignore_errors=True)
    subprocess.run(cnfg.keyszer_clone_cmd.split() + [cnfg.keyszer_tmp_path])


def backup_toshy_config():
    """backup existing Toshy config folder"""
    print(f'\n\nBacking up existing Toshy config folder...\n{cnfg.separator}')
    timestamp = datetime.datetime.now().strftime('_%Y%m%d_%H%M%S')
    toshy_backup_dir_path = os.path.abspath(cnfg.toshy_dir_path + timestamp)
    if os.path.exists(os.path.join(os.path.expanduser('~'), '.config', 'toshy')):
        try:
            # Define the ignore function
            def ignore_venv(dirname, filenames):
                return ['.venv'] if '.venv' in filenames else []
            # Copy files recursively from source to destination
            shutil.copytree(cnfg.toshy_dir_path, toshy_backup_dir_path, ignore=ignore_venv)
        except shutil.Error as e:
            print(f"Failed to copy directory: {e}")
            exit(1)
        except OSError as e:
            print(f"Failed to create backup directory: {e}")
            exit(1)
        print(f'Backup completed to {toshy_backup_dir_path}')
        cnfg.backup_succeeded = True
    else:
        print(f'No existing Toshy folder to backup...')
        cnfg.backup_succeeded = True


def install_toshy_files():
    """install Toshy files"""
    print(f'\n\nInstalling Toshy files...\n{cnfg.separator}')
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
                script_name, keyszer_tmp, 'LICENSE', 'packages.json', 'README.md'
            )
        )
    except shutil.Error as e:
        print(f"Failed to copy directory: {e}")
    except OSError as e:
        print(f"Failed to create backup directory: {e}")
    toshy_default_cfg = os.path.join(
        cnfg.toshy_dir_path, 'toshy-default-config', 'toshy_config.py')
    shutil.copy(toshy_default_cfg, cnfg.toshy_dir_path)
    print(f'Toshy files installed in {cnfg.toshy_dir_path}...')


def setup_virtual_env():
    """setup a virtual environment to install Python packages"""
    print(f'\n\nSetting up virtual environment...\n{cnfg.separator}')

    # Create the virtual environment if it doesn't exist
    if not os.path.exists(cnfg.venv_path):
        subprocess.run([sys.executable, '-m', 'venv', cnfg.venv_path])
    # We do not need to "activate" the venv right now, just create it
    print(f'Virtual environment setup complete.')


def install_pip_packages():
    """install `pip` packages for Python"""
    print(f'\n\nInstalling/upgrading Python packages...\n{cnfg.separator}')
    venv_python_cmd = os.path.join(cnfg.venv_path, 'bin', 'python')
    venv_pip_cmd    = os.path.join(cnfg.venv_path, 'bin', 'pip')
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
    print(f'\n\nInstalling Toshy script commands...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-bincommands-setup.sh')
    subprocess.run([script_path])


def install_desktop_apps():
    """install the convenient scripts to manage Toshy"""
    print(f'\n\nInstalling Toshy desktop apps...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'toshy-desktopapps-setup.sh')
    subprocess.run([script_path])

    # Replace $HOME with user home directory
    def replace_home_in_file(filename):
        # Read in the file
        with open(filename, 'r') as file:
            file_data = file.read()
        # Replace the target string
        file_data = file_data.replace('$HOME', cnfg.home_dir_path)
        # Write the file out again
        with open(filename, 'w') as file:
            file.write(file_data)

    desktop_files_path = os.path.join(cnfg.home_dir_path, '.local', 'share', 'applications')
    tray_desktop_file = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    gui_desktop_file = os.path.join(desktop_files_path, 'Toshy_GUI.desktop')

    replace_home_in_file(tray_desktop_file)
    replace_home_in_file(gui_desktop_file)


def setup_toshy_services():
    """invoke the setup script to install the systemd service units"""
    print(f'\n\nSetting up the Toshy systemd services...\n{cnfg.separator}')
    script_path = os.path.join(cnfg.toshy_dir_path, 'scripts', 'bin', 'toshy-systemd-setup.sh')
    subprocess.run([script_path])


def autostart_tray_icon():
    """set the tray icon to autostart at login"""
    print(f'\n\nSetting tray icon to load automatically at login...\n{cnfg.separator}')
    user_path           = os.path.expanduser('~')
    desktop_files_path  = os.path.join(user_path, '.local', 'share', 'applications')
    tray_desktop_file   = os.path.join(desktop_files_path, 'Toshy_Tray.desktop')
    autostart_dir_path  = os.path.join(user_path, '.config', 'autostart')
    dest_link_file      = os.path.join(autostart_dir_path, 'Toshy_Tray.desktop')

    # Need to create autostart folder if necessary
    os.makedirs(autostart_dir_path, exist_ok=True)
    subprocess.run(['ln', '-sf', tray_desktop_file, dest_link_file])

    print(f'Tray icon should appear in system tray at each login.')


def apply_desktop_tweaks():
    """
    fix things like Meta key activating overview in GNOME or KDE Plasma
    and fix the Unicode sequences in KDE Plasma
    
    TODO: These tweaks should probably be done at startup of the config
            instead of (or in addition to) here in the installer. 
    """
    print(f'\n\nApplying any necessary desktop tweaks...\n{cnfg.separator}')

    if cnfg.DESKTOP_ENV == 'xfce':
        print(f'Nothing to be done for Xfce yet...')

    # if GNOME, disable `overlay-key`
    # gsettings set org.gnome.mutter overlay-key ''
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'set', 'org.gnome.mutter', 'overlay-key', "''"])
        print(f'Disabling Super/Meta/Win/Cmd key opening the GNOME overview...')

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

    # if KDE Plasma, disable Meta key opening app menu
    # append this to ~/.config/kwinrc:
    # [ModifierOnlyShortcuts]
    # Meta=
    # then run command: 
    # qdbus org.kde.KWin /KWin reconfigure
    if cnfg.DESKTOP_ENV == 'kde':
        # subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])
        pass
    
    # if KDE, install `ibus` or `fcitx` and choose as input manager (ask for confirmation)


def remove_desktop_tweaks():
    """undo the relevant desktop tweaks"""

    # if GNOME, re-enable `overlay-key`
    # gsettings reset org.gnome.mutter overlay-key
    if cnfg.DESKTOP_ENV == 'gnome':
        subprocess.run(['gsettings', 'reset', 'org.gnome.mutter', 'overlay-key'])

    # if KDE Plasma, remove tweak from ~/.config/kwinrc:
    # [ModifierOnlyShortcuts]
    # Meta=
    # then run command: 
    # qdbus org.kde.KWin /KWin reconfigure
    if cnfg.DESKTOP_ENV == 'kde':
        subprocess.run(['qdbus', 'org.kde.KWin', '/KWin', 'reconfigure'])


def uninstall_toshy():
    print("Uninstalling Toshy...")


def apply_tweaks():
    print("Applying tweaks...")


def remove_tweaks():
    print("Removing tweaks...")


def handle_arguments():
    parser = argparse.ArgumentParser(
        description='Toshy Installer Script',
        epilog='Default action: Install Toshy'
    )

    parser.set_defaults(func=main)
    
    # Add arguments
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='Uninstall Toshy (not implemented yet)'
    )
    parser.add_argument(
        '--apply_tweaks',
        action='store_true',
        help='Apply desktop environment tweaks (not implemented yet)'
    )
    parser.add_argument(
        '--remove_tweaks',
        action='store_true',
        help='Remove desktop environment tweaks (not implemented yet)'
    )

    args: Namespace = parser.parse_args()

    # Check the values of arguments and perform actions accordingly
    if args.help:
        parser.print_help()
    elif args.uninstall:
        uninstall_toshy()
    elif args.apply_tweaks:
        apply_tweaks()
    elif args.remove_tweaks:
        remove_tweaks()


def main(cnfg):
    """Main installer function"""

    get_environment_info()
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
    setup_toshy_services()
    autostart_tray_icon()
    apply_desktop_tweaks()

    if cnfg.should_reboot:
        print(  f'\n\n'
                f'{cnfg.separator}\n'
                'ALERT: Permissions changed. You MUST reboot for Toshy to work...\n'
                f'{cnfg.separator}\n'
        )

    if not cnfg.should_reboot:
        # Try to start the tray icon immediately, if reboot is not indicated
        # tray_command        = ['gtk-launch', 'Toshy_Tray']
        tray_command = [os.path.join(cnfg.home_dir_path, '.local', 'bin', 'toshy-tray')]
        # Try to launch the tray icon in a separate process not linked to current shell
        # Also, suppress output that might confuse the user
        subprocess.Popen(
            tray_command,
            shell=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


if __name__ == '__main__':

    cnfg = InstallerSettings()

    handle_arguments()

    main(cnfg)
