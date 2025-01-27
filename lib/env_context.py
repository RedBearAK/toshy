#!/usr/bin/env python3

import re
import os
import time
import shutil
import subprocess

from typing import Dict

# ENV_CONTEXT module version:
__version__ = '20250126'

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


class EnvironmentInfo:
    def __init__(self):
        self.DISTRO_ID                      = None
        self.DISTRO_VER                     = None
        self.VARIANT_ID                     = None
        self.SESSION_TYPE                   = None
        self.DESKTOP_ENV                    = None
        self.DE_MAJ_VER                     = None
        self.WINDOW_MGR                     = None
        # self.WDW_MGR_VER                    = None        # Just in case we need it later

        self.env_info_dct: Dict[str, str]   = {}
        self.release_files: Dict[str, str]  = self.read_release_files()

    def get_env_info(self):
        """Primary method to get complete environment info"""

        # Call methods to populate the instance variables with info.
        # As of 2024-09-04 there are seven different bits of info to generate. 
        self.get_distro_id()
        self.get_distro_version()
        self.get_variant_id()
        self.get_session_type()
        self.get_desktop_environment()
        self.get_desktop_env_version()
        self.get_window_manager()
        # self.get_window_manager_version()                 # Just in case we need it later

        # Collect all info into a dictionary
        self.env_info_dct = {
            'DISTRO_ID':        self.DISTRO_ID,
            'DISTRO_VER':       self.DISTRO_VER,
            'VARIANT_ID':       self.VARIANT_ID,
            'SESSION_TYPE':     self.SESSION_TYPE,
            'DESKTOP_ENV':      self.DESKTOP_ENV,
            'DE_MAJ_VER':       self.DE_MAJ_VER,
            'WINDOW_MGR':       self.WINDOW_MGR,
            # 'WDW_MGR_VER':      self.WDW_MGR_VER,         # Just in case we need it later
        }
        return self.env_info_dct

    def read_release_files(self) -> Dict[str, str]:
        paths = [
            '/etc/os-release', '/etc/lsb-release', '/etc/arch-release'
        ]
        contents = {}
        for path in paths:
            if os.path.isfile(path):
                with open(path, 'r', encoding='UTF-8') as file:
                    contents[path] = file.read().splitlines()
        return contents

    def is_process_running(self, process_name):
        """Utility function to check if process is running, case-insensitive where supported"""
        cmd = ['pgrep', '-x', '-i', process_name]
        if self.DISTRO_ID == "centos" and self.DISTRO_VER == "7":
            # CentOS 7 complains about "-i" being invalid option, so remove it
            cmd = ['pgrep', '-x', process_name]
        try:
            subprocess.check_output(cmd)
            return True
        except subprocess.CalledProcessError:
            return False

####################################################################################################
##                                                                                                ##
##                ██████  ██ ███████ ████████ ██████   ██████      ██ ██████                      ##
##                ██   ██ ██ ██         ██    ██   ██ ██    ██     ██ ██   ██                     ##
##                ██   ██ ██ ███████    ██    ██████  ██    ██     ██ ██   ██                     ##
##                ██   ██ ██      ██    ██    ██   ██ ██    ██     ██ ██   ██                     ##
##                ██████  ██ ███████    ██    ██   ██  ██████      ██ ██████                      ##
##                                                                                                ##
####################################################################################################

    def get_distro_id(self):
        """logic to set self.DISTRO_ID"""
        _distro_id          = ""

        if _distro_id == "" and self.release_files['/etc/os-release']:
            for prefix in ['ID=', 'NAME=', 'PRETTY_NAME=']:
                for line in self.release_files['/etc/os-release']:
                    if line.startswith(prefix):
                        _distro_id = line.split('=')[1].strip().strip('"')
                        break
                if _distro_id != "":
                    break

        if _distro_id == "" and self.release_files['/etc/lsb-release']:
            for prefix in ['DISTRIB_ID=', 'DISTRIB_DESCRIPTION=']:
                for line in self.release_files['/etc/lsb-release']:
                    if line.startswith(prefix):
                        _distro_id = line.split('=')[1].strip().strip('"')
                        break
                if _distro_id != "":
                    break

        if _distro_id == "" and self.release_files['/etc/arch-release']:
            _distro_id = 'arch'

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
            if re.search(k, _distro_id, re.I):
                self.DISTRO_ID = v
                break

        # If distro name not found in list, just show original name
        if not self.DISTRO_ID:
            self.DISTRO_ID = _distro_id

        # filter distro name to lower case if string (not `None`)
        if isinstance(self.DISTRO_ID, str):
            self.DISTRO_ID = self.DISTRO_ID.casefold()

####################################################################################################
##                                                                                                ##
##           ██████  ██ ███████ ████████ ██████   ██████      ██    ██ ███████ ██████             ##
##           ██   ██ ██ ██         ██    ██   ██ ██    ██     ██    ██ ██      ██   ██            ##
##           ██   ██ ██ ███████    ██    ██████  ██    ██     ██    ██ █████   ██████             ##
##           ██   ██ ██      ██    ██    ██   ██ ██    ██      ██  ██  ██      ██   ██            ##
##           ██████  ██ ███████    ██    ██   ██  ██████        ████   ███████ ██   ██            ##
##                                                                                                ##
####################################################################################################

    def get_distro_version(self):
        """logic to set self.DISTRO_VER"""

        if self.release_files['/etc/os-release']:
            for line in self.release_files['/etc/os-release']:
                line: str
                if line.startswith('VERSION_ID='):
                    self.DISTRO_VER = line.split('=')[1].strip().strip('"')
                    break
        elif self.release_files['/etc/lsb-release']:
            for line in self.release_files['/etc/lsb-release']:
                line: str
                if line.startswith('DISTRIB_RELEASE='):
                    self.DISTRO_VER = line.split('=')[1].strip().strip('"')
                    break

        arch_distros = [
            'arch',
            'arcolinux',
            'endeavouros',
            'garuda',
            'manjaro',
        ]

        if not self.DISTRO_VER:
            if self.DISTRO_ID in arch_distros:
                self.DISTRO_VER = 'arch_btw'
            else:
                self.DISTRO_VER = 'notfound'

####################################################################################################
##                                                                                                ##
##             ██    ██  █████  ██████  ██  █████  ███    ██ ████████     ██ ██████               ##
##             ██    ██ ██   ██ ██   ██ ██ ██   ██ ████   ██    ██        ██ ██   ██              ##
##             ██    ██ ███████ ██████  ██ ███████ ██ ██  ██    ██        ██ ██   ██              ##
##              ██  ██  ██   ██ ██   ██ ██ ██   ██ ██  ██ ██    ██        ██ ██   ██              ##
##               ████   ██   ██ ██   ██ ██ ██   ██ ██   ████    ██        ██ ██████               ##
##                                                                                                ##
####################################################################################################

    def get_variant_id(self):
        """logic to set self.VARIANT_ID, if variant info available"""

        if self.release_files['/etc/os-release']:
            for line in self.release_files['/etc/os-release']:
                line: str
                if line.startswith('VARIANT_ID='):
                    self.VARIANT_ID = line.split('=')[1].strip().strip('"')
                    break
        elif self.release_files['/etc/lsb-release']:
            for line in self.release_files['/etc/lsb-release']:
                line: str
                if line.startswith('DISTRIB_DESCRIPTION='):
                    self.VARIANT_ID = line.split('=')[1].strip().strip('"')
                    break

        if not self.VARIANT_ID:
            self.VARIANT_ID = 'notfound'

####################################################################################################
##                                                                                                ##
##  ███████ ███████ ███████ ███████ ██  ██████  ███    ██     ████████ ██    ██ ██████  ███████   ##
##  ██      ██      ██      ██      ██ ██    ██ ████   ██        ██     ██  ██  ██   ██ ██        ##
##  ███████ █████   ███████ ███████ ██ ██    ██ ██ ██  ██        ██      ████   ██████  █████     ##
##       ██ ██           ██      ██ ██ ██    ██ ██  ██ ██        ██       ██    ██      ██        ##
##  ███████ ███████ ███████ ███████ ██  ██████  ██   ████        ██       ██    ██      ███████   ##
##                                                                                                ##
####################################################################################################

    def get_session_type(self):
        """logic to set self.SESSION_TYPE"""
        valid_session_types = ['x11', 'wayland']
        self.SESSION_TYPE   = os.environ.get("XDG_SESSION_TYPE") or None

        if not self.SESSION_TYPE:  # Why isn't XDG_SESSION_TYPE set? This shouldn't happen.
            error(f'ENV: XDG_SESSION_TYPE should really be set. Not a graphical environment?')

        if self.SESSION_TYPE not in valid_session_types or self.SESSION_TYPE == 'tty':
            # This is seen sometimes in situations like starting a window manager
            # or desktop environment session from a TTY, without using a login
            # manager like GDM or SDDM. This is not good. Treat as error. 
            error(f"ENV: XDG_SESSION_TYPE is 'tty' for some reason. Why?")

            # We need to check in some other way whether we are in Wayland or X11
            # Usually for Wayland there will be: WAYLAND_DISPLAY=wayland-[number]
            wayland_display = os.environ.get('WAYLAND_DISPLAY')
            if wayland_display and wayland_display.startswith('wayland'):
                self.SESSION_TYPE = 'wayland'

            # If the Wayland display variable was not set or not 'wayland*', 
            # then check for the usual X11 display variable.
            elif os.environ.get('DISPLAY'):
                self.SESSION_TYPE = 'x11'

        if self.SESSION_TYPE not in valid_session_types:
            # Deal with archaic distros like antiX that fail to set XDG_SESSION_TYPE
            time.sleep(3)

            xorg_check_p1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
            xorg_check_p2 = subprocess.Popen(
                                        ['grep', '-i', '-c', 'xorg'], 
                                        stdin=xorg_check_p1.stdout, 
                                        stdout=subprocess.PIPE)
            xorg_check_p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            xorg_check_output = xorg_check_p2.communicate()[0]
            xorg_count = int(xorg_check_output.decode()) - 1

            if xorg_count:
                self.SESSION_TYPE = 'x11'

            wayland_check_p1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
            wayland_check_p2 = subprocess.Popen(
                                            ['grep', '-i', '-c', 'wayland'], 
                                            stdin=wayland_check_p1.stdout, 
                                            stdout=subprocess.PIPE)
            wayland_check_p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
            wayland_check_output = wayland_check_p2.communicate()[0]
            wayland_count = int(wayland_check_output.decode()) - 1

            if wayland_count:
                self.SESSION_TYPE = 'wayland'

        if self.SESSION_TYPE is None:
            raise EnvironmentError(
                f'\n\nENV: Detecting session type failed.\n')

        if isinstance(self.SESSION_TYPE, str):
            self.SESSION_TYPE = self.SESSION_TYPE.casefold()

        if self.SESSION_TYPE not in valid_session_types:
            error(f'\n\nENV: Unknown session type: {self.SESSION_TYPE}.\n')

####################################################################################################
##                                                                                                ##
##    ██████  ███████ ███████ ██   ██ ████████  ██████  ██████      ███████ ███    ██ ██    ██    ##
##    ██   ██ ██      ██      ██  ██     ██    ██    ██ ██   ██     ██      ████   ██ ██    ██    ##
##    ██   ██ █████   ███████ █████      ██    ██    ██ ██████      █████   ██ ██  ██ ██    ██    ##
##    ██   ██ ██           ██ ██  ██     ██    ██    ██ ██          ██      ██  ██ ██  ██  ██     ##
##    ██████  ███████ ███████ ██   ██    ██     ██████  ██          ███████ ██   ████   ████      ##
##                                                                                                ##
####################################################################################################

    def get_desktop_environment(self):
        """logic to set self.DESKTOP_ENV and self.DE_MAJ_VER"""
        _desktop_env        = ""

        _desktop_env = (
            os.environ.get("XDG_CURRENT_DESKTOP") or
            os.environ.get("XDG_SESSION_DESKTOP") or
            os.environ.get("DESKTOP_SESSION")
        )

        # If it's a colon-separated list in XDG_CURRENT_DESKTOP,
        # the first entry is the primary desktop environment
        if _desktop_env and ':' in _desktop_env:
            _desktop_env = _desktop_env.split(':')[0]

        # Check for Qtile if the environment variables were not set/empty
        if not _desktop_env and self.is_qtile_running():
            _desktop_env = 'qtile'

        if not _desktop_env:
            _desktop_env = None
            error("ERR: DE not found in XDG_SESSION_DESKTOP, XDG_CURRENT_DESKTOP or DESKTOP_SESSION.")
            error("ERR: Config file may not be able to adapt automatically to Desktop Environment.")

        # Protect '.lower()' method from NoneType error
        if _desktop_env and 'unity' in _desktop_env.lower():
            self.DESKTOP_ENV = 'unity'

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
            'Miracle-WM':               'miracle-wm',
            'miracle-wm:mir':           'miracle-wm',
            'Miriway':                  'miriway',
            'Niri':                     'niri',
            'Pantheon':                 'pantheon',
            'Plasma':                   'kde',
            'qtile:wlroots':            'qtile',
            'Qtile':                    'qtile',
            'qtilewaylan':              'qtile',    # actual value in real life (typo in Qtile code?)
            'qtilewayland':             'qtile',    # might appear if they fix the typo
            'qtilex11':                 'qtile',
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

        if not self.DESKTOP_ENV:
            for k, v in desktop_env_names.items():
                # debug(f'{k = :<10} {v = :<10}')
                if _desktop_env is None: break  # watch out for NoneType here
                if re.search(k, _desktop_env, re.I):
                    self.DESKTOP_ENV = v
                if self.DESKTOP_ENV:
                    break

        # say DE should be added to list only if it it isn't None
        if not self.DESKTOP_ENV and _desktop_env is not None:
            error(f'DE or window manager not in desktop_env_names list! Should fix this.'
                    f'\n\t{_desktop_env}')
            self.DESKTOP_ENV = _desktop_env

        # do this only if DESKTOP_ENV is still None after the above step
        if not self.DESKTOP_ENV:
            # Doublecheck the desktop environment by checking for identifiable running processes
            def check_process(names, desktop_env):
                # nonlocal DESKTOP_ENV
                for name in names:
                    command = f"pgrep -x {name}"
                    try:
                        subprocess.check_output(command, shell=True)
                        if self.DESKTOP_ENV != desktop_env:
                            error(  f"Desktop may be misidentified: '{self.DESKTOP_ENV}'\n"
                                    f"'{desktop_env}' was detected and will be used instead.")
                            self.DESKTOP_ENV = desktop_env
                        break  # Stop checking if any of the processes are found
                    except subprocess.CalledProcessError:
                        pass

            processes = {
                'kde':          ['plasmashell', 'kwin_ft', 'kwin_wayland', 'kwin_x11', 'kwin'],
                'gnome':        ['gnome-shell'],
                'miracle-wm':   ['miracle-wm'],
                'sway':         ['sway', 'swaywm'],
                'hyprland':     ['hyprland'],
            }

            for desktop_env, process_names in processes.items():
                if check_process(process_names, desktop_env):
                    break   # Stop this loop when some process is found by exact match

    def is_qtile_running(self):
        """Utility function to detect Qtile if the usual environment vars are not set/empty"""
        xdg_cache_home      = os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache'))
        display             = os.environ.get('DISPLAY')
        wayland_display     = os.environ.get('WAYLAND_DISPLAY')
        desktop_session     = os.environ.get('DESKTOP_SESSION')

        socket_paths = []
        
        if display:
            socket_paths.append(os.path.join(xdg_cache_home, f'qtile/qtilesocket.{display}'))
        
        if wayland_display:
            socket_paths.append(os.path.join(xdg_cache_home, f'qtile/qtilesocket.{wayland_display}'))

        if desktop_session and 'qtile' in desktop_session:
            return True

        for socket_path in socket_paths:
            if os.path.exists(socket_path):
                return True

        return False

####################################################################################################
##                                                                                                ##
##          ██████  ███████     ██    ██ ███████ ██████  ███████ ██  ██████  ███    ██            ##
##          ██   ██ ██          ██    ██ ██      ██   ██ ██      ██ ██    ██ ████   ██            ##
##          ██   ██ █████       ██    ██ █████   ██████  ███████ ██ ██    ██ ██ ██  ██            ##
##          ██   ██ ██           ██  ██  ██      ██   ██      ██ ██ ██    ██ ██  ██ ██            ##
##          ██████  ███████       ████   ███████ ██   ██ ███████ ██  ██████  ██   ████            ##
##                                                                                                ##
####################################################################################################

    def get_desktop_env_version(self):
        """logic to set self.DE_MAJ_VER"""
        # Desktop environments for which we need the major version:
        # - GNOME
        # - KDE Plasma

        if self.DESKTOP_ENV == 'gnome':
            self.DE_MAJ_VER = self.get_gnome_version()
        elif self.DESKTOP_ENV == 'kde':
            self.DE_MAJ_VER = self.get_kde_version()
        elif self.DESKTOP_ENV == 'lxqt':
            self.DE_MAJ_VER = self.get_lxqt_version()

        if not self.DE_MAJ_VER:
            self.DE_MAJ_VER = 'no_logic_for_DE'

    def get_gnome_version(self):
            try:
                # Run the gnome-shell command to get the version
                output = subprocess.check_output(["gnome-shell", "--version"]).decode().strip()
                # Use regular expression to extract the major version number
                match = re.search(r"GNOME Shell (\d+)\.", output)
                if match:
                    return match.group(1)
            except subprocess.CalledProcessError as proc_err:
                error(f"Error obtaining GNOME version: {proc_err}")
                return 'gnome_ver_check_err'

    def get_kde_version(self):
        KDE_session_ver = os.environ.get('KDE_SESSION_VERSION')
        if KDE_session_ver is None:
            error(f"KDE_SESSION_VERSION was not set.")
        elif KDE_session_ver in ['3', '4', '5', '6']:
            return KDE_session_ver
        else:
            error(f"KDE_SESSION_VERSION contains unrecognized value: '{KDE_session_ver}'")
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

    def get_lxqt_version(self):
        try:
            output = subprocess.check_output(["lxqt-session", "--version"]).decode().strip()
            match = re.search(r"lxqt-session (\d+\.\d+\.\d+)", output)
            if match:
                major_version = match.group(1).split('.')[0]
                return major_version
        except subprocess.CalledProcessError:
            return 'lxqt_ver_check_err'

####################################################################################################
##                                                                                                ##
##       ██     ██ ██ ███    ██ ██████   ██████  ██     ██     ███    ███  ██████  ██████         ##
##       ██     ██ ██ ████   ██ ██   ██ ██    ██ ██     ██     ████  ████ ██       ██   ██        ##
##       ██  █  ██ ██ ██ ██  ██ ██   ██ ██    ██ ██  █  ██     ██ ████ ██ ██   ███ ██████         ##
##       ██ ███ ██ ██ ██  ██ ██ ██   ██ ██    ██ ██ ███ ██     ██  ██  ██ ██    ██ ██   ██        ##
##        ███ ███  ██ ██   ████ ██████   ██████   ███ ███      ██      ██  ██████  ██   ██        ##
##                                                                                                ##
####################################################################################################

    def get_window_manager(self):
        """
        logic to set self.WINDOW_MGR
        Useful in environments like LXQt that can have various window managers.
        """

        # Common "desktop environments" mapped to likely actual "window manager" process names
        de_wm_map = {

            # Older KDE may just use 'kwin' process name
            'kde': [
                'kwin_wayland',
                'kwin_x11', 
                'kwin', 
            ],

            # Older GNOME may have 'mutter' integrated into 'gnome-shell' process
            'gnome': [
                'mutter',
                'gnome-shell',
            ],

            # LXQt often uses OpenBox, but can use a number of different WMs in X11 or Wayland
            'lxqt': [
                'openbox',          # X11/Xorg window manager
                'labwc',            # Wayland compositor
                'sway',             # Wayland compositor
                'hyprland',         # Wayland compositor
                'kwin_wayland',     # Wayland compositor
                'wayfire',          # Wayland compositor
                'river',            # Wayland compositor
                'niri',             # Wayland compositor
                'miriway',          # Wayland compositor
                'miriway-shell',    # Wayland compositor (actual process name?)
            ],

            'awesome':          'awesome',
            'cinnamon':         'cinnamon',
            'cosmic':           'cosmic-comp',
            'dwm':              'dwm',
            'hyprland':         'Hyprland',     # the process name is capitalized (this is unusual)
            'i3':               'i3',
            'i3-gaps':          'i3',
            'miracle-wm':       'miracle-wm',
            'openbox':          'openbox',
            'pantheon':         'gala',
            'sway':             'sway',
            'xfce':             'xfwm4',

        }

        # First try to limit search for window managers associated with desktop environment
        if self.DESKTOP_ENV and self.DESKTOP_ENV in de_wm_map:
            possible_wms = de_wm_map[self.DESKTOP_ENV]
            for wm in possible_wms:
                if self.is_process_running(wm):
                    self.WINDOW_MGR = wm
                    return

        if self.DESKTOP_ENV and self.DESKTOP_ENV == 'lxqt' and not self.WINDOW_MGR:
            self.get_lxqt_window_manager()
            if self.WINDOW_MGR:
                return

        # Iterate through whole dictionary if desktop environment not found in de_wm_map
        for DE, process_names in de_wm_map.items():
            if not isinstance(process_names, list):
                process_names = [process_names]  # Ensure we can iterate
            for process_name in process_names:
                if self.is_process_running(process_name):
                    self.WINDOW_MGR = process_name
                    return

        # If nothing found, set a default value
        if not self.WINDOW_MGR:
            self.WINDOW_MGR = 'WM_unidentified_by_logic'

    def get_lxqt_window_manager(self):
        """Further steps to identify possible LXQt window manager"""
        # If DE is LXQt and WM still not found after above search, try checking its config file:
        # cat ~/.config/lxqt/session.conf | grep WindowManager
        config_path = os.path.expanduser('~/.config/lxqt/session.conf')
        try:
            with open(config_path, 'r') as config_file:
                for line in config_file:
                    if line.startswith('window_manager=') or line.startswith('compositor='):
                        # Typically the line would be like "window_manager=openbox\n"
                        wm_name = os.path.basename(line.strip().split('=')[1])
                        if wm_name == 'miriway' and self.is_process_running('miriway-shell'):
                            self.WINDOW_MGR = 'miriway-shell'
                            return
                        elif self.is_process_running(wm_name):
                            self.WINDOW_MGR = wm_name
                            return
                        else:
                            # Fallback to checking other known WMs in case config is outdated
                            break
        except FileNotFoundError:
            # Handle cases where the config file does not exist
            print(f"Could not find LXQt config file at: {config_path}")

####################################################################################################
##                                                                                                ##
##    ██     ██ ██████  ██     ██     ███    ███  ██████  ██████      ██    ██ ███████ ██████     ##
##    ██     ██ ██   ██ ██     ██     ████  ████ ██       ██   ██     ██    ██ ██      ██   ██    ##
##    ██  █  ██ ██   ██ ██  █  ██     ██ ████ ██ ██   ███ ██████      ██    ██ █████   ██████     ##
##    ██ ███ ██ ██   ██ ██ ███ ██     ██  ██  ██ ██    ██ ██   ██      ██  ██  ██      ██   ██    ##
##     ███ ███  ██████   ███ ███      ██      ██  ██████  ██   ██       ████   ███████ ██   ██    ##
##                                                                                                ##
####################################################################################################

    def get_window_manager_version(self):
        """Login to set self.WDW_MGR_VER, if ever necessary"""
        if not self.WDW_MGR_VER:
            self.WDW_MGR_VER = 'no_logic_for_wdw_mgr'


if __name__ == "__main__":
    env_info_getter = EnvironmentInfo()
    _env_info = env_info_getter.get_env_info()
    print('')
    debug(  f'Toshy env_info module sees this environment:'
            f'\n\t\t DISTRO_ID       = \'{_env_info["DISTRO_ID"]}\''
            f'\n\t\t DISTRO_VER      = \'{_env_info["DISTRO_VER"]}\''
            f'\n\t\t VARIANT_ID      = \'{_env_info["VARIANT_ID"]}\''
            f'\n\t\t SESSION_TYPE    = \'{_env_info["SESSION_TYPE"]}\''
            f'\n\t\t DESKTOP_ENV     = \'{_env_info["DESKTOP_ENV"]}\''
            f'\n\t\t DE_MAJ_VER      = \'{_env_info["DE_MAJ_VER"]}\''
            f'\n\t\t WINDOW_MGR      = \'{_env_info["WINDOW_MGR"]}\''
            # f'\n\t\t WDW_MGR_VER     = \'{_env_info["WDW_MGR_VER"]}\''
            f'\n', ctx="EV")
