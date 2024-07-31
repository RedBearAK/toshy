#!/usr/bin/env python3

import re
import os
import time
import shutil
import subprocess

# ENV module version: 2024-06-18

VERBOSE = True
FLUSH = True

def debug(*args, ctx="DD"):
    if not VERBOSE:
        return

    # allow blank lines without context
    if len(args) == 0 or (len(args) == 1 and args[0] == ""):
        print("", flush=FLUSH)
        return
    print(f"({ctx})", *args, flush=FLUSH)

def warn(*args, ctx="WW"):
    print(f"({ctx})", *args, flush=FLUSH)

def error(*args, ctx="EE"):
    print(f"({ctx})", *args, flush=FLUSH)

def log(*args, ctx="--"):
    print(f"({ctx})", *args, flush=FLUSH)

def info(*args, ctx="--"):
    log(*args, ctx=ctx)



#############################  ENVIRONMENT  ##############################
###                                                                    ###
###                                                                    ###
###      ███████ ███    ██ ██    ██ ██ ██████   ██████  ███    ██      ###
###      ██      ████   ██ ██    ██ ██ ██   ██ ██    ██ ████   ██      ###
###      █████   ██ ██  ██ ██    ██ ██ ██████  ██    ██ ██ ██  ██      ###
###      ██      ██  ██ ██  ██  ██  ██ ██   ██ ██    ██ ██  ██ ██      ###
###      ███████ ██   ████   ████   ██ ██   ██  ██████  ██   ████      ###
###                                                                    ###
###                                                                    ###
##########################################################################
# Set up some useful environment variables


def get_env_info():
    DISTRO_ID       = None
    DISTRO_VER      = None
    VARIANT_ID      = None
    SESSION_TYPE    = None
    DESKTOP_ENV     = None
    DE_MAJ_VER      = None

    env_info_dct    = {}
    _distro_name    = ""
    _desktop_env    = ""

    # Map each file path to its file object if it exists
    release_files = {
        '/etc/os-release': None,
        '/etc/lsb-release': None,
        '/etc/arch-release': None,
    }
    for path in release_files.keys():
        if os.path.isfile(path):
            with open(path, 'r', encoding='UTF-8') as f:
                release_files[path] = f.read().splitlines()

    ########################################################################
    ##  Get distro name
    if _distro_name == "" and release_files['/etc/os-release']:
        for prefix in ['ID=', 'NAME=', 'PRETTY_NAME=']:
            for line in release_files['/etc/os-release']:
                if line.startswith(prefix):
                    _distro_name = line.split('=')[1].strip().strip('"')
                    break
            if _distro_name != "":
                break
    if _distro_name == "" and release_files['/etc/lsb-release']:
        for prefix in ['DISTRIB_ID=', 'DISTRIB_DESCRIPTION=']:
            for line in release_files['/etc/lsb-release']:
                if line.startswith(prefix):
                    _distro_name = line.split('=')[1].strip().strip('"')
                    break
            if _distro_name != "":
                break
    if _distro_name == "" and release_files['/etc/arch-release']:
        _distro_name = 'arch'

    distro_names = {            # simplify distro names to an ID, if necessary
        'Debian.*':             'debian',
        # 'elementary':           'eos',
        'Fedora.*':             'fedora',
        'LMDE.*':               'lmde',
        'Manjaro':              'manjaro',
        'KDE.*Neon':            'neon',
        'Linux.*Mint':          'mint',
        'openSUSE.*Tumbleweed': 'opensuse-tumbleweed',
        'Peppermint.*':         'peppermint',
        'Pop!_OS':              'pop',
        'Red.*Hat.*':           'rhel',
        'Rocky.*':              'rocky',
        'Ubuntu':               'ubuntu',
        'Ultramarine.*Linux':   'ultramarine',
        'Zorin.*':              'zorin',
    }

    # if the regex string from dict key is in the distro name name retrieved, 
    # replace with corresponding simplified dict value for simpler matching
    for k, v in distro_names.items():
        # debug(f'{k = :<10} {v = :<10}')
        if re.search(k, _distro_name, re.I):
            DISTRO_ID = v
            break

    # If distro name not found in list, just show original name
    if not DISTRO_ID:
        DISTRO_ID = _distro_name

    # filter distro name to lower case if not `None`
    if isinstance(DISTRO_ID, str):
        DISTRO_ID = DISTRO_ID.casefold()

    env_info_dct['DISTRO_ID'] = DISTRO_ID

    ########################################################################
    ##  Get distro version
    if release_files['/etc/os-release']:
        for line in release_files['/etc/os-release']:
            line: str
            if line.startswith('VERSION_ID='):
                DISTRO_VER = line.split('=')[1].strip().strip('"')
                break
    elif release_files['/etc/lsb-release']:
        for line in release_files['/etc/lsb-release']:
            line: str
            if line.startswith('DISTRIB_RELEASE='):
                DISTRO_VER = line.split('=')[1].strip().strip('"')
                break

    if not DISTRO_VER:
        env_info_dct['DISTRO_VER'] = 'notfound'
    else:
        env_info_dct['DISTRO_VER'] = DISTRO_VER

    ########################################################################
    ##  Get distro variant if available
    if release_files['/etc/os-release']:
        for line in release_files['/etc/os-release']:
            line: str
            if line.startswith('VARIANT_ID='):
                VARIANT_ID = line.split('=')[1].strip().strip('"')
                break
    elif release_files['/etc/lsb-release']:
        for line in release_files['/etc/lsb-release']:
            line: str
            if line.startswith('DISTRIB_DESCRIPTION='):
                VARIANT_ID = line.split('=')[1].strip().strip('"')
                break

    if not VARIANT_ID:
        env_info_dct['VARIANT_ID'] = 'notfound'
    else:
        env_info_dct['VARIANT_ID'] = VARIANT_ID

    ########################################################################
    ##  Get session type
    SESSION_TYPE = os.environ.get("XDG_SESSION_TYPE") or None

    if not SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
        error(f'ENV: XDG_SESSION_TYPE should really be set. Are you in a graphical environment?')
        time.sleep(3)

        # Deal with archaic distros like antiX that fail to set XDG_SESSION_TYPE
        xorg_check_p1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
        xorg_check_p2 = subprocess.Popen(
                                    ['grep', '-i', '-c', 'xorg'], 
                                    stdin=xorg_check_p1.stdout, 
                                    stdout=subprocess.PIPE)
        xorg_check_p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        xorg_check_output = xorg_check_p2.communicate()[0]
        xorg_count = int(xorg_check_output.decode()) - 1

        if xorg_count:
            SESSION_TYPE = 'x11'

        wayland_check_p1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
        wayland_check_p2 = subprocess.Popen(
                                        ['grep', '-i', '-c', 'wayland'], 
                                        stdin=wayland_check_p1.stdout, 
                                        stdout=subprocess.PIPE)
        wayland_check_p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        wayland_check_output = wayland_check_p2.communicate()[0]
        wayland_count = int(wayland_check_output.decode()) - 1

        if wayland_count:
            SESSION_TYPE = 'wayland'

    if not SESSION_TYPE:
        SESSION_TYPE = os.environ.get("WAYLAND_DISPLAY") or None
        if not SESSION_TYPE:
            raise EnvironmentError(
                f'\n\nENV: Detecting session type failed.\n')

    if isinstance(SESSION_TYPE, str):
        SESSION_TYPE = SESSION_TYPE.casefold()

    if SESSION_TYPE not in ['x11', 'wayland']:
        raise EnvironmentError(f'\n\nENV: Unknown session type: {SESSION_TYPE}.\n')

    env_info_dct['SESSION_TYPE'] = SESSION_TYPE


    ########################################################################
    ##  Get desktop environment
    # _desktop_env = os.environ.get("XDG_SESSION_DESKTOP") or os.environ.get("XDG_CURRENT_DESKTOP")
    _desktop_env = os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("XDG_SESSION_DESKTOP")


    def is_qtile_running():
        """Utility function to detect Qtile if the usual environment vars are not set/empty"""
        xdg_cache_home = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        display = os.environ.get('DISPLAY')

        if wayland_display:
            socket_path = os.path.join(xdg_cache_home, f'qtile/qtilesocket.{wayland_display}')
        elif display:
            socket_path = os.path.join(xdg_cache_home, f'qtile/qtilesocket.{display}')
        else:
            return False

        return os.path.exists(socket_path)


    # Check for Qtile if the environment variables were not set/empty
    if not _desktop_env and is_qtile_running():
        _desktop_env = 'qtile'

    if not _desktop_env:
        _desktop_env = None
        error("ERROR: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")
        error("ERROR: Config file will not be able to adapt automatically to Desktop Environment.")

    # Protect '.lower()' method from NoneType error
    if _desktop_env and 'unity' in _desktop_env.lower():
        DESKTOP_ENV = 'unity'

    # Produce a simplified desktop environment name
    desktop_env_names = {
        'Budgie':                   'budgie',
        'Cinnamon':                 'cinnamon',
        'COSMIC':                   'cosmic',
        'Cutefish':                 'cutefish',
        'DDE':                      'dde',
        'Deepin':                   'deepin',
        'Enlightenment':            'enlightenment',
        'GNOME':                    'gnome',
        'Hyprland':                 'hyprland',
        'i3':                       'i3',
        'i3wm':                     'i3',
        'IceWM':                    'icewm',
        'KDE':                      'kde',
        'LXDE':                     'lxde',
        'LXQt':                     'lxqt',
        'MATE':                     'mate',
        'Pantheon':                 'pantheon',
        'Plasma':                   'kde',
        'Sway':                     'sway',
        'SwayWM':                   'sway',
        'Trinity':                  'trinity',
        'UKUI':                     'ukui',     # Ubuntu Kylin desktop shell
        'Unity':                    'unity',    # keep above "Ubuntu" to always catch 'unity' first
        'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
        'Wayfire':                  'wayfire',
        'WindowMaker':              'wmaker',
        'Xfce':                     'xfce',
    }

    if not DESKTOP_ENV:
        for k, v in desktop_env_names.items():
            # debug(f'{k = :<10} {v = :<10}')
            if _desktop_env is None: break  # watch out for NoneType here
            if re.search(k, _desktop_env, re.I):
                DESKTOP_ENV = v
            if DESKTOP_ENV:
                break

    # say DE should be added to list only if it it isn't None
    if not DESKTOP_ENV and _desktop_env is not None:
        error(f'DE or window manager not in desktop_env_names list! Should fix this.\n\t{_desktop_env}')
        DESKTOP_ENV = _desktop_env

    # do this only if DESKTOP_ENV is still None after the above step
    if not DESKTOP_ENV:
        # Doublecheck the desktop environment by checking for identifiable running processes
        def check_process(names, desktop_env):
            nonlocal DESKTOP_ENV
            for name in names:
                command = f"pgrep {name}"
                try:
                    subprocess.check_output(command, shell=True)
                    if DESKTOP_ENV != desktop_env:
                        error(  f"Desktop may be misidentified: '{DESKTOP_ENV}'\n"
                                f"'{desktop_env}' was detected and will be used instead.")
                        DESKTOP_ENV = desktop_env
                    break  # Stop checking if any of the processes are found
                except subprocess.CalledProcessError:
                    pass

        processes = {
            'kde':          ['plasmashell', 'kwin_ft', 'kwin_wayland', 'kwin_x11', 'kwin'],
            'gnome':        ['gnome-shell'],
            'sway':         ['sway', 'swaywm'],
            'hyprland':     ['hyprland'],
        }

        for desktop_env, process_names in processes.items():
            check_process(process_names, desktop_env)


    env_info_dct['DESKTOP_ENV'] = DESKTOP_ENV

    ########################################################################
    ##  Get desktop environment version

    def get_kde_version():
        kde_session_version = os.environ.get('KDE_SESSION_VERSION')
        if kde_session_version:
            if kde_session_version in ['3', '4', '5', '6']:
                return kde_session_version
            else:
                error(f"KDE_SESSION_VERSION contains unrecognized value: '{kde_session_version}'")
        if shutil.which("kpackagetool6"): # or shutil.which("kwriteconfig6"):
            return '6'
        elif shutil.which("kpackagetool5"): # or shutil.which("kwriteconfig5"):
            return '5'
        elif shutil.which("kpackagetool"): # or shutil.which("kwriteconfig"): 
            # In KDE 4, these tools don't have a version number in their name
            # Additional check for KDE 4 versioning can be done here if necessary
            return '4'
        # no 'kpackagetool' command in KDE 3?
        return 'kde_ver_check_err'

    if DESKTOP_ENV == 'gnome':
        try:
            # Run the gnome-shell command to get the version
            output = subprocess.check_output(["gnome-shell", "--version"]).decode().strip()
            # Use regular expression to extract the major version number
            match = re.search(r"GNOME Shell (\d+)\.", output)
            if match:
                DE_MAJ_VER = match.group(1)
        except subprocess.CalledProcessError as proc_err:
            error(f"Error obtaining GNOME version: {proc_err}")

    elif DESKTOP_ENV == 'kde':
        DE_MAJ_VER = get_kde_version()

    if not DE_MAJ_VER:
        env_info_dct['DE_MAJ_VER'] = 'no_logic_for_DE'
    else:
        env_info_dct['DE_MAJ_VER'] = DE_MAJ_VER

    return env_info_dct


if __name__ == '__main__':

    _env_info = get_env_info()
    print('')
    debug(  f'Toshy env module sees this environment:'
            f'\n\t\t DISTRO_ID       = \'{_env_info["DISTRO_ID"]}\''
            f'\n\t\t DISTRO_VER      = \'{_env_info["DISTRO_VER"]}\''
            f'\n\t\t VARIANT_ID      = \'{_env_info["VARIANT_ID"]}\''
            f'\n\t\t SESSION_TYPE    = \'{_env_info["SESSION_TYPE"]}\''
            f'\n\t\t DESKTOP_ENV     = \'{_env_info["DESKTOP_ENV"]}\''
            f'\n\t\t DE_MAJ_VER      = \'{_env_info["DE_MAJ_VER"]}\''
            f'\n', ctx="EV")
