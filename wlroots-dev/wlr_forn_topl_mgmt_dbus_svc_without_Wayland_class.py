#!/usr/bin/env python3

# Reference for generating the protocol modules with pywayland scanner:
# https://github.com/flacjacket/pywayland/issues/8#issuecomment-987040284

# Protocol documentation:
# https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1

# pywayland method has a NotImplementedError for NewId argument
# (Use GitHub repo PR #64 branch or commit to install with 'pip')
# git+https://github.com/heuer/pywayland@issue_33_newid
# git+https://github.com/flacjacket/pywayland@db8fb1c3a29761a014cfbb57f84025ddf3882c3c


print("(--) Starting D-Bus service to monitor wlr-foreign-toplevel-management protocol...")

import os
import sys
import dbus
import time
import signal
import platform
import dbus.service
import dbus.mainloop.glib
import xwaykeyz.lib.logger

from pywayland.client import Display
from gi.repository import GLib
from dbus.exceptions import DBusException
from subprocess import DEVNULL
from typing import Dict
from xwaykeyz.lib.logger import debug, error

xwaykeyz.lib.logger.VERBOSE = True


# Independent module/script to create a D-Bus window context service in 
# a wlroots Wayland environment, which will be notified of window 
# focus changes by the Wayland compositor, as long as the compositor 
# implements the `zwlr_foreign_toplevel_management_unstable_v1` protocol.

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
from lib.env_context import EnvironmentInfo

from protocols.wlr_foreign_toplevel_management_unstable_v1.zwlr_foreign_toplevel_manager_v1 import (
    ZwlrForeignToplevelManagerV1,
    ZwlrForeignToplevelManagerV1Proxy,
    ZwlrForeignToplevelHandleV1
)

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser.")
    sys.exit(1)


def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        clean_shutdown()


def clean_shutdown():
    if display:  # Check if the display is globally defined and initialized
        try:
            display.disconnect()
        except Exception as e:
            error(f"Error disconnecting display: {e}")
    GLib.MainLoop().quit()  # Stop the GLib main loop if it's running
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

DISTRO_ID       = None
DISTRO_VER      = None
VARIANT_ID      = None
SESSION_TYPE    = None
DESKTOP_ENV     = None
DE_MAJ_VER      = None


def check_environment():
    """Retrieve the current environment from env module"""
    # env_info_dct   = env.get_env_info()
    env_ctxt_getter = EnvironmentInfo()
    env_info_dct   = env_ctxt_getter.get_env_info()
    global DISTRO_ID, DISTRO_VER, VARIANT_ID, SESSION_TYPE, DESKTOP_ENV, DE_MAJ_VER
    DISTRO_ID       = env_info_dct.get('DISTRO_ID')
    DISTRO_VER      = env_info_dct.get('DISTRO_VER')
    VARIANT_ID      = env_info_dct.get('VARIANT_ID')
    SESSION_TYPE    = env_info_dct.get('SESSION_TYPE')
    DESKTOP_ENV     = env_info_dct.get('DESKTOP_ENV')
    DE_MAJ_VER      = env_info_dct.get('DE_MAJ_VER')


check_environment()

# TODO: put the DE restriction back in place, find a way to identify wlroots compositors
if SESSION_TYPE == 'wayland': # and DESKTOP_ENV not in ['kde', 'plasma', 'gnome', 'cinnamon']:
    pass
else:
    debug(f'{LOG_PFX}: Probably not a wlroots environment. Exiting.')
    time.sleep(2)
    sys.exit(0)


debug("")
debug(  f'Toshy KWIN D-Bus service script sees this environment:'
        f'\n\t{DISTRO_ID        = }'
        f'\n\t{DISTRO_VER       = }'
        f'\n\t{VARIANT_ID       = }'
        f'\n\t{SESSION_TYPE     = }'
        f'\n\t{DESKTOP_ENV      = }'
        f'\n\t{DE_MAJ_VER       = }\n', ctx="CG")


TOSHY_WLR_DBUS_SVC_PATH         = '/org/toshy/Wlroots'
TOSHY_WLR_DBUS_SVC_IFACE        = 'org.toshy.Wlroots'

ERR_NO_WLR_APP_CLASS = "ERR_no_wlr_app_class"
ERR_NO_WLR_WDW_TITLE = "ERR_no_wlr_wdw_title"

wdw_handles_dct                 = {}
active_app_class                = ERR_NO_WLR_APP_CLASS
active_wdw_title                = ERR_NO_WLR_WDW_TITLE

try:
    display = Display()
    display.connect()  # Explicitly attempt to connect to the Wayland display
    wl_fd = display.get_fd()        # Get the Wayland file descriptor
    registry = display.get_registry()  # Attempt to get the registry
except ValueError as e:  # ValueError is raised if connection fails in your Display class
    print(f"Failed to connect to the Wayland display: {e}")
except RuntimeError as e:  # Catching potential runtime errors, adjust exceptions as needed
    print(f"Runtime error occurred: {e}")
    clean_shutdown()
except Exception as e:  # Generic catch-all for any other exceptions
    print(f"An unexpected error occurred: {e}")
    clean_shutdown()
else:
    print("Connection to Wayland display and registry acquisition successful.")
    # Proceed with further operations, such as setting up listeners on the registry


def handle_toplevel_event(
        toplevel_manager: ZwlrForeignToplevelManagerV1Proxy,
        toplevel_handle: ZwlrForeignToplevelHandleV1):
    # Here, you should set up event listeners for the toplevel
    toplevel_handle.dispatcher["app_id"]    = handle_app_id_change
    toplevel_handle.dispatcher["title"]     = handle_title_change
    toplevel_handle.dispatcher['closed']    = handle_window_closed
    toplevel_handle.dispatcher['state']     = handle_state_change


def handle_app_id_change(handle, app_id):
    if handle not in wdw_handles_dct:
        wdw_handles_dct[handle] = {}
    wdw_handles_dct[handle]['app_id'] = app_id
    # print(f"Title updated for window {handle}: '{app_id}'")


def handle_title_change(handle, title):
    """Update title in local state."""
    if handle not in wdw_handles_dct:
        wdw_handles_dct[handle] = {}
    wdw_handles_dct[handle]['title'] = title
    # print(f"Title updated for window {handle}: '{title}'")


def handle_window_closed(handle):
    """Remove window from local state."""
    if handle in wdw_handles_dct:
        del wdw_handles_dct[handle]
    print(f"Window {handle} has been closed.")


def handle_state_change(handle, states_bytes):
    """Track active window based on state changes."""
    states = []
    if isinstance(states_bytes, bytes):
        states = list(states_bytes)
    if ZwlrForeignToplevelHandleV1.state.activated.value in states:
        active_app_class = wdw_handles_dct[handle]['app_id']
        active_wdw_title = wdw_handles_dct[handle]['title']
        print()
        print(f"Active app class: '{active_app_class}'")
        print(f"Active window title: '{active_wdw_title}'")
        print_running_applications()  # Print the list of running applications


def print_running_applications():
    """Print a complete list of running applications."""
    print("\nList of running applications:")
    print(f"{'App ID':<30} {'Title':<50}")
    print("-" * 80)
    for handle, info in wdw_handles_dct.items():
        app_id = info.get('app_id', ERR_NO_WLR_APP_CLASS)
        title = info.get('title', ERR_NO_WLR_WDW_TITLE)
        print(f"{app_id:<30} {title:<50}")
    print()


def handle_registry_global(registry, id_, interface_name, version):
    if interface_name == 'zwlr_foreign_toplevel_manager_v1':
        toplevel_manager = registry.bind(id_, ZwlrForeignToplevelManagerV1, version)
        toplevel_manager.dispatcher["toplevel"] = handle_toplevel_event


registry.dispatcher["global"]    = handle_registry_global

display.roundtrip()


class DBUS_Object(dbus.service.Object):
    """Class to handle D-Bus interactions"""
    def __init__(self, session_bus, object_path, interface_name):
        super().__init__(session_bus, object_path)
        self.interface_name     = interface_name
        self.dbus_svc_bus_name  = dbus.service.BusName(interface_name, bus=session_bus)

    @dbus.service.method(TOSHY_WLR_DBUS_SVC_IFACE, out_signature='a{sv}')
    def GetActiveWindow(self):
        debug(f'{LOG_PFX}: GetActiveWindow() called...')
        return {'app_id':           active_app_class,
                'title':            active_wdw_title}


def wayland_event_callback(fd, condition, display):
    if condition & GLib.IO_IN:
        # display.dispatch()    # dispatch() fails to prompt new events to appear
        # dispatch() also seems to trigger the callback to get called many times in a loop,
        # but without any new useful events appearing, while roundtrip() just shows
        # the new events that I need to see, as they happen.
        display.roundtrip()     # gets new events to appear immediately
    return True


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

    # GLib.idle_add(wayland_event_callback)
    GLib.io_add_watch(wl_fd, GLib.IO_IN, wayland_event_callback, display)

    display.roundtrip() # get the event cycle started (callback never gets called without this)

    # Run the main loop
    # dbus.mainloop.glib.DBusGMainLoop().run()
    GLib.MainLoop().run()


if __name__ == "__main__":
    main()
    # After main() is done:
    clean_shutdown()
