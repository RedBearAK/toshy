#!/usr/bin/env python3

import os
import sys
import dbus
import time
import signal
import platform
import dbus.service
import dbus.mainloop.glib

from pywayland.client import Display

from gi.repository import GLib
from dbus.exceptions import DBusException
from subprocess import DEVNULL
from typing import Dict
from keyszer.lib.logger import debug, error

# Independent module/script to create a D-Bus window context service in 
# a wlroots Wayland environment, which will be notified of window 
# focus changes by the Wayland compositor, as long as the compositor 
# implements the `wlr_foreign_toplevel_management_unstable_v1` protocol.

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir            = os.path.expanduser("~")
run_tmp_dir         = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'
parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, current_folder_path)
sys.path.insert(0, parent_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{parent_folder_path}:{current_folder_path}:{existing_path}'

# local imports now that path is prepped
import lib.env as env
from .wayland_protocols.wlr_foreign_toplevel_management_unstable_v1 import ZwlrForeignToplevelManagerV1

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

LOG_PFX = 'TOSHY_WLR_DBUS_SVC'

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

if DESKTOP_ENV not in ['kde', 'plasma', 'gnome'] and SESSION_TYPE == 'wayland':
    pass
else:
    debug(f'{LOG_PFX}: Not a wlroots environment. Exiting.')
    time.sleep(2)
    sys.exit(0)


# debug("")
# debug(  f'Toshy KDE D-Bus service script sees this environment:'
#         f'\n\t{DISTRO_NAME      = }'
#         f'\n\t{DISTRO_VER       = }'
#         f'\n\t{SESSION_TYPE     = }'
#         f'\n\t{DESKTOP_ENV      = }\n', ctx="CG")


TOSHY_WLR_DBUS_SVC_PATH         = '/org/toshy/Wlroots'
TOSHY_WLR_DBUS_SVC_IFACE        = 'org.toshy.Wlroots'

wl_app_id                       = "NO_DATA"
wl_title                        = "NO_DATA"

display                         = Display()
registry                        = display.get_registry()

toplevel_manager                = None

def registry_global(event):
    if event.interface == ZwlrForeignToplevelManagerV1.interface_name:
        toplevel_manager = registry.bind(event.name, ZwlrForeignToplevelManagerV1, event.version)
        toplevel_manager.dispatcher["toplevel"] = handle_toplevel

registry.dispatcher["global"]    = registry_global


class DBUS_Object(dbus.service.Object):
    """Class to handle D-Bus interactions"""
    def __init__(self, session_bus, object_path, interface_name):
        super().__init__(session_bus, object_path)
        self.interface_name     = interface_name
        self.dbus_svc_bus_name  = dbus.service.BusName(interface_name, bus=session_bus)

    @dbus.service.method(TOSHY_WLR_DBUS_SVC_IFACE, out_signature='a{sv}')
    def GetActiveWindow(self):
        debug(f'{LOG_PFX}: GetActiveWindow() called...')
        return {'app_id':           wl_app_id,
                'title':            wl_title}


def handle_app_id(event):
    print(f"App ID changed: {event.app_id}")
    global wl_app_id
    wl_app_id   = event.app_id


def handle_title(event):
    print(f"Title changed: {event.title}")
    global wl_title
    wl_title    = event.title


def handle_toplevel(toplevel):
    # Here, you should set up event listeners for the toplevel
    toplevel.dispatcher["app_id"]   = handle_app_id
    toplevel.dispatcher["title"]    = handle_title


def wayland_event_check():
    # Check for Wayland events
    display.flush()
    display.dispatch_pending()
    return True  # Returning True keeps the callback active


def main():

    # Initialize the D-Bus main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # Connect to the session bus
    session_bus = dbus.SessionBus()

    # Create the DBUS_Object
    try:
        DBUS_Object(session_bus, TOSHY_WLR_DBUS_SVC_PATH, TOSHY_WLR_DBUS_SVC_IFACE)
    except DBusException as dbus_error:
        error(f"{LOG_PFX}: Error occurred while creating D-Bus service object:\n\t{dbus_error}")
        sys.exit(1)

    GLib.idle_add(wayland_event_check)

    # Run the main loop
    # dbus.mainloop.glib.DBusGMainLoop().run()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
