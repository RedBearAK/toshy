#!/usr/bin/env python3


# Reference for generating the protocol modules with pywayland scanner:
# https://github.com/flacjacket/pywayland/issues/8#issuecomment-987040284

# Protocol documentation:
# https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1

# pywayland method has a NotImplementedError for NewId argument
# (Use GitHub repo PR #64 branch or commit to install with 'pip')
# git+https://github.com/heuer/pywayland@issue_33_newid
# git+https://github.com/flacjacket/pywayland@db8fb1c3a29761a014cfbb57f84025ddf3882c3c


import sys
import select
import signal
import traceback


from protocols.wlr_foreign_toplevel_management_unstable_v1.zwlr_foreign_toplevel_manager_v1 import (
    ZwlrForeignToplevelManagerV1,
    ZwlrForeignToplevelManagerV1Proxy,
    ZwlrForeignToplevelHandleV1,
)

from pywayland.client import Display
from time import sleep

ERR_NO_WLR_APP_CLASS = "ERR_no_wlr_app_class"
ERR_NO_WLR_WDW_TITLE = "ERR_no_wlr_wdw_title"

class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        signal.signal(signal.SIGINT, self.signal_handler)
        self.display                            = None
        self.wl_fd                              = None
        self.registry                           = None
        self.forn_topl_mgr_prot_supported       = False
        self.toplevel_manager                   = None

        self.wdw_handles_dct                    = {}
        self.active_app_class                   = ERR_NO_WLR_APP_CLASS
        self.active_wdw_title                   = ERR_NO_WLR_WDW_TITLE

    def signal_handler(self, signal, frame):
        print(f"\nSignal {signal} received, shutting down.")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        if self.display is not None:
            print("Disconnecting from Wayland display...")
            self.display.disconnect()
            print("Disconnected from Wayland display.")

    def handle_toplevel_event(self, 
            toplevel_manager: ZwlrForeignToplevelManagerV1Proxy, 
            toplevel_handle: ZwlrForeignToplevelHandleV1):
        """Handle events for new toplevel windows."""
        # print(f"New toplevel window created: {toplevel_handle}")
        # Subscribe to title and app_id changes as well as close event
        toplevel_handle.dispatcher['title']             = self.handle_title_change
        toplevel_handle.dispatcher['app_id']            = self.handle_app_id_change
        toplevel_handle.dispatcher['closed']            = self.handle_window_closed
        toplevel_handle.dispatcher['state']             = self.handle_state_change

    def handle_title_change(self, handle, title):
        """Update title in local state."""
        if handle not in self.wdw_handles_dct:
            self.wdw_handles_dct[handle] = {}
        self.wdw_handles_dct[handle]['title'] = title
        # print(f"Title updated for window {handle}: '{title}'")

    def handle_app_id_change(self, handle, app_id):
        """Update app_id in local state."""
        if handle not in self.wdw_handles_dct:
            self.wdw_handles_dct[handle] = {}
        self.wdw_handles_dct[handle]['app_id'] = app_id
        # print(f"App ID updated for window {handle}: '{app_id}'")

    def handle_window_closed(self, handle):
        """Remove window from local state."""
        if handle in self.wdw_handles_dct:
            del self.wdw_handles_dct[handle]
        print(f"Window {handle} has been closed.")

    def handle_state_change(self, handle, states_bytes):
        """Track active window based on state changes."""
        states = []
        if isinstance(states_bytes, bytes):
            states = list(states_bytes)
        if ZwlrForeignToplevelHandleV1.state.activated.value in states:
            self.active_app_class = self.wdw_handles_dct[handle]['app_id']
            self.active_wdw_title = self.wdw_handles_dct[handle]['title']
            print()
            print(f"Active app class: '{self.active_app_class}'")
            print(f"Active window title: '{self.active_wdw_title}'")
            self.print_running_applications()  # Print the list of running applications

    def print_running_applications(self):
        """Print a complete list of running applications."""
        print("\nList of running applications:")
        print(f"{'App ID':<30} {'Title':<50}")
        print("-" * 80)
        for handle, info in self.wdw_handles_dct.items():
            app_id = info.get('app_id', ERR_NO_WLR_APP_CLASS)
            title = info.get('title', ERR_NO_WLR_WDW_TITLE)
            print(f"{app_id:<30} {title:<50}")
        print()

    def registry_global_handler(self, registry, id_, interface_name, version):
        """Handle registry events."""
        print(f"Registry event: id={id_}, interface={interface_name}, version={version}")
        if interface_name == 'zwlr_foreign_toplevel_manager_v1':
            print()
            print(f"Protocol '{interface_name}' version {version} is _SUPPORTED_.")
            self.forn_topl_mgr_prot_supported = True
            print(f"Creating toplevel manager...")

            # pywayland version:
            self.toplevel_manager = registry.bind(id_, ZwlrForeignToplevelManagerV1, version)

            print(f"Subscribing to 'toplevel' events from toplevel manager...")
            self.toplevel_manager.dispatcher['toplevel'] = self.handle_toplevel_event
            print()
            self.display.roundtrip()

    def run(self):
        """Run the Wayland client."""
        try:
            print("Connecting to Wayland display...")
            with Display() as self.display:
                self.display.connect()
                print("Connected to Wayland display")

                self.wl_fd = self.display.get_fd()
                print("Got Wayland file descriptor")

                print("Getting registry...")
                self.registry = self.display.get_registry()
                print("Registry obtained")

                print("Subscribing to 'global' events from registry")
                self.registry.dispatcher["global"] = self.registry_global_handler

                print("Running roundtrip to process registry events...")
                self.display.roundtrip()

                # After initial events are processed, we should know if the right
                # protocol is supported, and have a toplevel_manager object.
                if self.forn_topl_mgr_prot_supported and self.toplevel_manager:
                    print()
                    print("Protocol is supported, starting dispatch loop...")

                    # # Can't get this to stop pegging a core (or thread) without sleep()
                    # # It is as if dispatch() does not block at all
                    # # TODO: Need to properly use a lightweight event-driven loop, but how? 
                    # while self.display.dispatch() != -1:
                    #     sleep(0.05)
                    #     # seems to be necessary to trigger roundtrip() in a loop,
                    #     # or no further events will ever print out in the terminal
                    #     self.display.roundtrip()

                    while True:
                        # Wait for the Wayland file descriptor to be ready
                        rlist, wlist, xlist = select.select([self.wl_fd], [], [])

                        if self.wl_fd in rlist:
                            # self.display.dispatch()   # won't show me new events
                            self.display.roundtrip()

                else:
                    print()
                    print("Protocol 'zwlr_foreign_toplevel_manager_v1' is _NOT_ supported.")

        except Exception as e:
            print()
            print(f"An error occurred: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
