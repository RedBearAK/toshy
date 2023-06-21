#!/usr/bin/env python3

import os
import sys
import dbus
import time
import shutil
import signal
import zipfile
import platform
import subprocess
import dbus.service
import dbus.mainloop.glib

from gi.repository import GLib
from dbus.exceptions import DBusException
from subprocess import DEVNULL
# from dbus.service import method
from typing import Dict, List, Union
from keyszer.lib.logger import debug, error, warn, info, log

# Independent module/script to create a D-Bus window context
# service in a KDE Plasma environment, which will be notified
# of window focus changes by the Toshy KWin script

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir            = os.path.expanduser("~")
run_tmp_dir         = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'
parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, current_folder_path)
sys.path.insert(0, parent_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{parent_folder_path}:{current_folder_path}:{existing_path}'

# local imports
# from ..lib.env import get_env_info
import lib.env as env

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
else:
    error(f'This is only meant to run on Linux. Exiting...')
    sys.exit(1)

sep_reps        = 80
sep_char        = '='
separator       = sep_char * sep_reps

LOG_PFX = 'TOSHY_KDE_DBUS_SVC'

DISTRO_NAME     = None
DISTRO_VER      = None
SESSION_TYPE    = None
DESKTOP_ENV     = None


def check_environment():
    """Retrieve the current environment from env module"""
    env_info: Dict[str, str] = env.get_env_info()   # Returns a dict
    global DISTRO_NAME, DISTRO_VER, SESSION_TYPE, DESKTOP_ENV
    DISTRO_NAME     = env_info.get('DISTRO_NAME')
    DISTRO_VER      = env_info.get('DISTRO_VER')
    SESSION_TYPE    = env_info.get('SESSION_TYPE')
    DESKTOP_ENV     = env_info.get('DESKTOP_ENV')


check_environment()

if DESKTOP_ENV in ['kde', 'plasma'] and SESSION_TYPE == 'wayland':
    pass
else:
    debug(f'{LOG_PFX}: Not a Wayland+KDE environment. Exiting.')
    time.sleep(2)
    sys.exit(1)

# loop_delay = 2
# while True:
#     if loop_delay > 8:
#         debug(f'{LOG_PFX}: Not a Wayland+KDE environment. Exiting.')
#         sys.exit(0)
#     if DESKTOP_ENV in ['kde', 'plasma'] and SESSION_TYPE == 'wayland':
#         break
#     else:
#         time.sleep(loop_delay)
#         loop_delay += 2
#         check_environment()

qdbus_cmd = None

if shutil.which('qdbus'):
    qdbus_cmd = 'qdbus'
elif shutil.which('qdbus-qt5'):
    qdbus_cmd = 'qdbus-qt5'

toshy_kwin_script_name = 'toshy-dbus-notifyactivewindow'
toshy_kwin_script_is_loaded = False
kwin_scripting_obj = 'org.kde.KWin'
kwin_scripting_path = '/Scripting'
kwin_scripting_iface = 'org.kde.kwin.Scripting'

def do_kwin_reconfigure():
    """Utility function to run the KWin reconfigure command"""
    try:
        subprocess.run([qdbus_cmd, 'org.kde.KWin', '/KWin', 'reconfigure'],
                        check=True, stderr=DEVNULL, stdout=DEVNULL)
        time.sleep(1)
    except subprocess.CalledProcessError as proc_error:
        error(f'Error while running KWin reconfigure.\n\t{proc_error}')


def is_kwin_script_loaded():
    try:
        output = subprocess.check_output([  qdbus_cmd,
                                            kwin_scripting_obj,
                                            kwin_scripting_path,
                                            f'{kwin_scripting_iface}.isScriptLoaded',
                                            toshy_kwin_script_name    ])
        # output is bytes object, not string!
        output: bytes
        return output.decode().strip() == 'true'
    except subprocess.CalledProcessError as e:
        print(f"Error checking if KWin script is loaded:\n\t{e}")
        return False


def load_kwin_script():
    try:
        subprocess.run([qdbus_cmd,
                        kwin_scripting_obj,
                        kwin_scripting_path,
                        f'{kwin_scripting_iface}.loadScript',
                        toshy_kwin_script_name    ],
                        check=True,
                        stderr=DEVNULL,
                        stdout=DEVNULL)
        print(f'Successfully loaded KWin script.')
    except subprocess.CalledProcessError as e:
        print(f"Error checking if KWin script is loaded:\n\t{e}")
        return False


if qdbus_cmd is not None:
    toshy_kwin_script_is_loaded = is_kwin_script_loaded()
    print(f"Script '{toshy_kwin_script_name}' loaded: {toshy_kwin_script_is_loaded}")
else:
    error(f"Cannot find 'qdbus' or 'qdbus-qt5'. Cannot check KWin script status.")


def setup_kwin2dbus_script():
    """Install the KWin script to notify D-Bus service about window focus changes"""
    print(f'\n\n§  Setting up the Toshy KWin script...\n{separator}')
    kwin_script_name    = 'toshy-dbus-notifyactivewindow'
    kwin_script_path    = os.path.join( parent_folder_path,
                                        'kde-kwin-dbus-service', kwin_script_name)
    script_tmp_file     = f'{run_tmp_dir}/{kwin_script_name}.kwinscript'

    # Create a zip file (overwrite if it exists)
    with zipfile.ZipFile(script_tmp_file, 'w') as zipf:
        # Add main.js to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                                arcname='contents/code/main.js')
        # Add metadata.desktop to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

    # Try to remove any installed KWin script entirely
    result = subprocess.run(
        ['kpackagetool5', '-t', 'KWin/Script', '-r', kwin_script_name],
        capture_output=True, text=True)

    if result.returncode != 0:
        pass
    else:
        print("Successfully removed existing KWin script.")

    # Install the KWin script
    result = subprocess.run(
        ['kpackagetool5', '-t', 'KWin/Script', '-i', script_tmp_file], capture_output=True, text=True)

    if result.returncode != 0:
        error(f"Error installing the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully installed the KWin script.")

    do_kwin_reconfigure()
    
    # Remove the temporary kwinscript file
    try:
        os.remove(script_tmp_file)
    except (FileNotFoundError, PermissionError): pass

    # # Load the script using qdbus_cmd
    # load_kwin_script()

    # Try to get KWin to load the script (probably won't activate until enabled later)
    do_kwin_reconfigure()

    # Keep the script enabled the script using kwriteconfig5
    result = subprocess.run(
        [   'kwriteconfig5', '--file', 'kwinrc', '--group', 'Plugins', '--key',
            f'{kwin_script_name}Enabled', 'true'],
        capture_output=True, text=True)
    if result.returncode != 0:
        error(f"Error enabling the KWin script. The error was:\n\t{result.stderr}")
    else:
        print("Successfully enabled the KWin script.")

    # Try to get KWin to activate the script
    do_kwin_reconfigure()

if toshy_kwin_script_is_loaded is not True:
    setup_kwin2dbus_script()

# loop above breaks if environment is suitable (Wayland+KDE), so run the kickstart 
# script here to generate a KWin event (hopefully)
kickstart_script    = 'toshy-kwin-script-kickstart.sh'
kickstart_cmd       = os.path.join(home_dir, '.config', 'toshy', 'scripts', kickstart_script)
subprocess.Popen([kickstart_cmd], stderr=DEVNULL, stdout=DEVNULL)

# debug("")
# debug(  f'Toshy KDE D-Bus service script sees this environment:'
#         f'\n\t{DISTRO_NAME      = }'
#         f'\n\t{DISTRO_VER       = }'
#         f'\n\t{SESSION_TYPE     = }'
#         f'\n\t{DESKTOP_ENV      = }\n', ctx="CG")


TOSHY_KDE_DBUS_SVC_PATH         = '/org/toshy/Toshy'
TOSHY_KDE_DBUS_SVC_IFACE        = 'org.toshy.Toshy'


class DBUS_Object(dbus.service.Object):
    """Class to handle D-Bus interactions"""
    def __init__(self, session_bus, object_path, interface_name):
        super().__init__(session_bus, object_path)
        self.interface_name     = interface_name
        self.dbus_svc_bus_name  = dbus.service.BusName(interface_name, bus=session_bus)
        self.caption            = "NO_DATA"
        self.resource_class     = "NO_DATA"
        self.resource_name      = "NO_DATA"

    @dbus.service.method(TOSHY_KDE_DBUS_SVC_IFACE, in_signature='sss')
    def NotifyActiveWindow(self, caption, resource_class, resource_name):
        debug(f'{LOG_PFX}: NotifyActiveWindow() called...')
        self.caption            = str(caption)
        self.resource_class     = str(resource_class)
        self.resource_name      = str(resource_name)
        debug(f'{LOG_PFX}: Active window attributes:'
                f"\n\t caption        = '{self.caption}'"
                f"\n\t resource_class = '{self.resource_class}'"
                f"\n\t resource_name  = '{self.resource_name}'"
        )

    @dbus.service.method(TOSHY_KDE_DBUS_SVC_IFACE, out_signature='a{sv}')
    def GetActiveWindow(self):
        debug(f'{LOG_PFX}: GetActiveWindow() called...')
        return {    'caption':          self.caption,
                    'resource_class':   self.resource_class,
                    'resource_name':    self.resource_name }


def main():
    # Initialize the D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Connect to the session bus
    session_bus = dbus.SessionBus()

    # Create the DBUS_Object
    try:
        DBUS_Object(session_bus, TOSHY_KDE_DBUS_SVC_PATH, TOSHY_KDE_DBUS_SVC_IFACE)
    except DBusException as dbus_error:
        error(f"{LOG_PFX}: Error occurred while creating D-Bus service object:\n\t{dbus_error}")
        sys.exit(1)

    # Run the main loop
    # dbus.mainloop.glib.DBusGMainLoop().run()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
