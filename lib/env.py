#!/usr/bin/env python3

import re
import os
import time
import subprocess

# ENV module version: 2023-05-22

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
    DISTRO_NAME     = None
    DISTRO_VER      = None
    SESSION_TYPE    = None
    DESKTOP_ENV     = None

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

    distro_names = {            # simplify distro names
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
            DISTRO_NAME = v
            break

    # If distro name not found in list, just show original name
    if not DISTRO_NAME:
        DISTRO_NAME = _distro_name

    # filter distro name to lower case if not `None`
    if isinstance(DISTRO_NAME, str):
        DISTRO_NAME = DISTRO_NAME.casefold()

    env_info_dct['DISTRO_NAME'] = DISTRO_NAME

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

    if not _desktop_env:
        _desktop_env = None
        error("ERROR: Desktop Environment not found in XDG_SESSION_DESKTOP or XDG_CURRENT_DESKTOP.")
        error("ERROR: Config file will not be able to adapt automatically to Desktop Environment.")

    # Produce a simplified desktop environment name
    desktop_env_names = {
        'Budgie':                   'budgie',
        'Cinnamon':                 'cinnamon',
        'Cutefish':                 'cutefish',
        'Deepin':                   'deepin',
        'Enlightenment':            'enlightenment',
        'GNOME':                    'gnome',
        'Hyprland':                 'hyprland',
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
        'Ubuntu':                   'gnome',    # "Ubuntu" in XDG_CURRENT_DESKTOP, but DE is GNOME
        'Unity':                    'unity',
        'Xfce':                     'xfce',
    }

    for k, v in desktop_env_names.items():
        # debug(f'{k = :<10} {v = :<10}')
        if _desktop_env is None: break  # watch out for NoneType here
        if re.search(k, _desktop_env, re.I):
            DESKTOP_ENV = v
        if DESKTOP_ENV:
            break

    # say DE should be added to list only if it it isn't None
    if not DESKTOP_ENV and _desktop_env is not None:
        error(f'Desktop Environment not in de_names list! Should fix this.\n\t{_desktop_env}')
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
            'kde':          ['plasmashell', 'kwin_ft', 'kwin_wayland', 'kwin_x11'],
            'gnome':        ['gnome-shell'],
            'sway':         ['sway', 'swaywm'],
            'hyprland':     ['hyprland'],
        }

        for desktop_env, process_names in processes.items():
            check_process(process_names, desktop_env)


    env_info_dct['DESKTOP_ENV'] = DESKTOP_ENV
    
    return env_info_dct


if __name__ == '__main__':

    _env_info = get_env_info()
    print('')
    debug(  f'Toshy env module sees this environment:'
            f'\n\t\t DISTRO_NAME     = \'{_env_info["DISTRO_NAME"]}\''
            f'\n\t\t DISTRO_VER      = \'{_env_info["DISTRO_VER"]}\''
            f'\n\t\t SESSION_TYPE    = \'{_env_info["SESSION_TYPE"]}\''
            f'\n\t\t DESKTOP_ENV     = \'{_env_info["DESKTOP_ENV"]}\''
            f'\n', ctx="EV")
