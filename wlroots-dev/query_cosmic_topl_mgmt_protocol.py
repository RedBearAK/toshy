#!/usr/bin/env python3


# Reference for generating the protocol modules with pywayland scanner:
# https://github.com/flacjacket/pywayland/issues/8#issuecomment-987040284

# Protocol documentation (original on which COSMIC variant is based):
# https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1

# COSMIC protocol specification XML files:
# https://github.com/pop-os/cosmic-protocols/blob/main/unstable/cosmic-toplevel-info-unstable-v1.xml
# https://github.com/pop-os/cosmic-protocols/blob/main/unstable/cosmic-workspace-unstable-v1.xml

# Needed for COSMIC protocol version 2:
# https://gitlab.freedesktop.org/wayland/wayland-protocols/-/raw/main/staging/ext-foreign-toplevel-list/ext-foreign-toplevel-list-v1.xml

# pywayland method had a NotImplementedError for NewId argument,
# but PR #64 was merged. 


import sys
import select
import signal
import struct
import traceback

# COSMIC-specific protocol module, using their own namespace
# XML files downloaded from `cosmic-protocols` GitHub repo, in 'unstable' folder
from protocols.cosmic_toplevel_info_unstable_v1.zcosmic_toplevel_info_v1 import (
    ZcosmicToplevelInfoV1,
    ZcosmicToplevelInfoV1Proxy,
    ZcosmicToplevelHandleV1
)

# # COSMIC protocol update has shifted to involving 'ext_foreign_toplevel_list_v1' interface.
from protocols.ext_foreign_toplevel_list_v1.ext_foreign_toplevel_list_v1 import (
    ExtForeignToplevelListV1,
    ExtForeignToplevelListV1Proxy,
    ExtForeignToplevelHandleV1
)

from pywayland.client import Display
from time import sleep

ERR_NO_COSMIC_APP_CLASS = "ERR_no_cosmic_app_class"
ERR_NO_COSMIC_WDW_TITLE = "ERR_no_cosmic_wdw_title"

# Create a mapping of state values to their names
STATE_MAP = {
    0: "maximized",
    1: "minimized",
    2: "activated",
    3: "fullscreen",
    4: "sticky"  # Since version 2
}


class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        signal.signal(signal.SIGINT, self.signal_handler)
        self.display                            = None
        self.wl_fd                              = None
        self.registry                           = None
        self.forn_topl_mgr_prot_supported       = False
        self.cosmic_protocol_ver                = None

        self.cosmic_toplvl_mgr: ZcosmicToplevelInfoV1Proxy      = None
        self.foreign_toplvl_mgr: ExtForeignToplevelListV1Proxy  = None

        self.wdw_handles_dct                    = {}
        self.cosmic_to_foreign_map              = {}
        self.active_app_class                   = ERR_NO_COSMIC_APP_CLASS
        self.active_wdw_title                   = ERR_NO_COSMIC_WDW_TITLE

    def signal_handler(self, signal, frame):
        print(f"\nSignal {signal} received, shutting down.")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        if self.display is not None:
            print("Disconnecting from Wayland display...")
            self.display.disconnect()
            print("Disconnected from Wayland display.")

    def print_running_applications(self):
        """Print a complete list of running applications."""
        print("\nFull list of running application classes (not windows):")
        print(f"{'App ID':<30} {'Title':<50}")
        print("-" * 80)
        for handle, info in self.wdw_handles_dct.items():
            app_id = info.get('app_id', ERR_NO_COSMIC_APP_CLASS)
            title  = info.get('title', ERR_NO_COSMIC_WDW_TITLE)
            # print(f"{handle}")
            print(f"{app_id:<30} {title:<50}")
        print()

    def handle_title_change(self, handle, title):
        """Update title in local state."""
        if handle not in self.wdw_handles_dct:
            self.wdw_handles_dct[handle] = {}
        self.wdw_handles_dct[handle]['title'] = title
        print(f"Title updated for window {handle}: '{title}'")

    def handle_app_id_change(self, handle, app_id):
        """Update app_id in local state."""
        if handle not in self.wdw_handles_dct:
            self.wdw_handles_dct[handle] = {}
        self.wdw_handles_dct[handle]['app_id'] = app_id
        print(f"App ID updated for window {handle}: '{app_id}'")

    def handle_window_closed(self, handle):
        """Remove window from local state."""
        foreign_handle: ExtForeignToplevelHandleV1 = None

        if self.cosmic_protocol_ver >= 2:
            if handle in self.cosmic_to_foreign_map:
                foreign_handle = self.cosmic_to_foreign_map.pop(handle, None)
            if foreign_handle and foreign_handle in self.wdw_handles_dct:
                del self.wdw_handles_dct[foreign_handle]
            print(f"Window {foreign_handle} has been closed.")

        elif self.cosmic_protocol_ver == 1:
            if handle in self.wdw_handles_dct:
                del self.wdw_handles_dct[handle]
                print(f"Window {handle} has been closed.")

    def handle_state_change(self, handle, states_bytes):
        """Track active window app class and title based on state changes."""

        # Filter out empty state updates (why do these even happen?)
        # Filter out the all-zeroes state (reset event?) before converting
        if not states_bytes or states_bytes == b'\x00\x00\x00\x00':
            print()
            print("Received empty bytes value or all-zeroes 4-byte state event, ignoring.")
            return

        # Process states_bytes as an array of 4-byte (32-bit) integers
        # Interpret 4 bytes as an integer (little-endian arrays?)
        if isinstance(states_bytes, bytes):
            state_values = list(struct.unpack(f'{len(states_bytes)//4}I', states_bytes))

        # Convert state values to their corresponding names
        state_names = [STATE_MAP.get(state, f"Unknown state: {state}") for state in state_values]

        print()
        print(f"{'State change event (bytes):':<30}",   f"{states_bytes}")
        print(f"{'State change event (values):':<30}",  f"{state_values}")
        print(f"{'State change event (names):':<30}",   f"{state_names}")

        foreign_handle: ExtForeignToplevelHandleV1 = None

        if self.cosmic_protocol_ver >= 2:
            if handle in self.cosmic_to_foreign_map:
                foreign_handle = self.cosmic_to_foreign_map[handle]
        else:
            print("Error: Foreign handle not found for the cosmic toplevel.")
            return

        if ZcosmicToplevelHandleV1.state.activated.value in state_values:

            if self.cosmic_protocol_ver >= 2:
                self.active_app_class = self.wdw_handles_dct[foreign_handle]['app_id']
                self.active_wdw_title = self.wdw_handles_dct[foreign_handle]['title']

            elif self.cosmic_protocol_ver == 1:
                self.active_app_class = self.wdw_handles_dct[handle]['app_id']
                self.active_wdw_title = self.wdw_handles_dct[handle]['title']

            self.print_running_applications()  # Print the list of running applications
            print()
            print("#" * 80)
            print(f"{'Active app class:':<30}", f"'{self.active_app_class}'")
            print(f"{'Active window title:':<30}", f"'{self.active_wdw_title}'")
            print("#" * 80)

    def handle_toplevel_event_v1(self, 
            toplevel_manager: ZcosmicToplevelInfoV1Proxy, 
            toplevel_handle: ZcosmicToplevelHandleV1):
        """Handle events for new toplevel windows in v1 COSMIC toplevel info protocol."""
        # print(f"New toplevel window created: {toplevel_handle}")
        # Subscribe to title and app_id changes as well as close event
        toplevel_handle.dispatcher['title']             = self.handle_title_change
        toplevel_handle.dispatcher['app_id']            = self.handle_app_id_change
        toplevel_handle.dispatcher['closed']            = self.handle_window_closed
        toplevel_handle.dispatcher['state']             = self.handle_state_change

    def handle_toplevel_event_v2(self,
                foreign_toplvl_mgr: ExtForeignToplevelListV1Proxy,
                foreign_toplvl_handle: ExtForeignToplevelHandleV1):
        """Request a new v2 cosmic toplevel handle for a foreign toplevel handle."""
        try:
            cosmic_toplvl_handle: ZcosmicToplevelHandleV1 = None
            cosmic_toplvl_handle = self.cosmic_toplvl_mgr.get_cosmic_toplevel(foreign_toplvl_handle)

            # Ensure the dictionary entry is initialized with the foreign handle as the primary key
            if foreign_toplvl_handle not in self.wdw_handles_dct:
                self.wdw_handles_dct[foreign_toplvl_handle] = {
                    'cosmic_handle':    cosmic_toplvl_handle,
                    'app_id':           None,
                    'title':            None,
                    'state':            None,
                    'ready':            False,  # Mark as false until all properties are received
                }

            # Store a reverse mapping from COSMIC handle to foreign handle
            # (We are dealing with two different handles for each toplevel window.)
            self.cosmic_to_foreign_map[cosmic_toplvl_handle] = foreign_toplvl_handle

            # Event listeners for the foreign toplevel handle
            # (cosmic toplevel handle will never emit these)
            foreign_toplvl_handle.dispatcher['title']       = self.handle_title_change
            foreign_toplvl_handle.dispatcher['app_id']      = self.handle_app_id_change

            # Event listeners for v2 cosmic toplevel handle
            # (foreign toplevel handle does not have these events)
            cosmic_toplvl_handle.dispatcher['closed']       = self.handle_window_closed
            cosmic_toplvl_handle.dispatcher['state']        = self.handle_state_change

            self.display.roundtrip()

        except KeyError as e:
            print(f"Error sending get_cosmic_toplevel request: {e}")

    def handle_registry_global(self, registry, id_, interface_name, version):
        """Handle registry events."""
        print(f"Registry event: id={id_}, interface={interface_name}, version={version}")

        if interface_name == 'ext_foreign_toplevel_list_v1':
            print(f"Subscribing to 'toplevel' events from foreign toplevel manager...")
            self.foreign_toplvl_mgr = registry.bind(id_, ExtForeignToplevelListV1, version)
            self.foreign_toplvl_mgr.dispatcher['toplevel'] = self.handle_toplevel_event_v2

        # COSMIC is using their own namespace instead of 'zwlr_foreign_toplevel_manager_v1'
        # interface from wlroots. 
        # But version 2 of protocol integrates 'ext_foreign_toplevel_list_v1' interface.
        if interface_name == 'zcosmic_toplevel_info_v1':
            print()
            print(f"Protocol '{interface_name}' version {version} is _SUPPORTED_.")
            self.forn_topl_mgr_prot_supported       = True
            self.cosmic_protocol_ver                = version
            print(f"Creating cosmic toplevel manager...")

            self.cosmic_toplvl_mgr = registry.bind(id_, ZcosmicToplevelInfoV1, version)

            if version == 1:
                print(f"Subscribing to 'toplevel' events from toplevel manager...")
                self.cosmic_toplvl_mgr.dispatcher['toplevel'] = self.handle_toplevel_event_v1
                print()

            elif version >= 2:
                # This updated version of the protocol will be handled when the 
                # 'ext_foreign_toplevel_list_v1' event appears and gets processed. 
                pass

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
                self.registry.dispatcher["global"] = self.handle_registry_global

                print("Running roundtrip to process registry events...")
                self.display.roundtrip()

                # After initial events are processed, we should know if the right
                # protocol is supported, and have a toplevel_manager object.
                if self.forn_topl_mgr_prot_supported and self.cosmic_toplvl_mgr:
                    print()
                    print("Protocol 'zcosmic_toplevel_info_v1' is supported, starting monitoring...")

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
                    print("Protocol 'zcosmic_toplevel_info_v1' is _NOT_ supported.")

        except Exception as e:
            print()
            print(f"An error occurred: {e}")
            print(traceback.format_exc())

if __name__ == "__main__":
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
