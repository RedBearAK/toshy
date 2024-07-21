#!/usr/bin/env python3


# Reference for creating the protocols with pywayland scanner:
# https://github.com/flacjacket/pywayland/issues/8#issuecomment-987040284

# Protocol documentation:
# https://wayland.app/protocols/wlr-foreign-toplevel-management-unstable-v1


import sys
import signal
import traceback

from protocols.wlr_foreign_toplevel_management_unstable_v1 import (
    ZwlrForeignToplevelManagerV1,
    ZwlrForeignToplevelHandleV1
)

from pywayland.client import Display
from protocols.wayland import WlOutput, WlSeat
from typing import Optional


class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        signal.signal(signal.SIGINT, self.signal_handler)
        self.display: Optional[Display] = None
        self.registry = None
        self.toplevel_manager: Optional[ZwlrForeignToplevelManagerV1] = None
        self.forn_topl_mgr_prot_supported = False
        self.window_handles_dct = {}
        self.active_window_handle = None
        self.outputs = {}

    def signal_handler(self, signal, frame):
        print("\nSignal received, shutting down.")
        self.cleanup()
        sys.exit(0)

    def cleanup(self):
        if self.display is not None:
            print("Disconnecting from Wayland display...")
            self.display.disconnect()
            print("Disconnected from Wayland display.")

    def registry_global_handler(self, registry, id_, interface_name, version):
        """Handle registry events."""
        print(f"Registry event: id={id_}, interface={interface_name}, version={version}")
        if interface_name == 'zwlr_foreign_toplevel_manager_v1':
            print()
            print(f"Protocol '{interface_name}' version {version} is SUPPORTED.")
            self.forn_topl_mgr_prot_supported = True
            print(f"Creating toplevel manager by binding protocol to registry")
            self.toplevel_manager = registry.bind(id_, ZwlrForeignToplevelManagerV1, version)
            print(f"Subscribing to 'toplevel' events from toplevel manager")
            self.toplevel_manager.dispatcher['toplevel'] = self.handle_toplevel_event
            print()
        elif interface_name == 'wl_seat':
            print(f"Binding to wl_seat interface.")
            seat = registry.bind(id_, WlSeat, version)
            seat.dispatcher['capabilities'] = self.handle_seat_capabilities
            seat.dispatcher['name'] = self.handle_seat_name
        elif interface_name == 'wl_output':
            print(f"Binding to wl_output interface.")
            output = registry.bind(id_, WlOutput, version)
            self.outputs[id_] = output
            output.dispatcher['geometry'] = self.handle_output_geometry
            output.dispatcher['mode'] = self.handle_output_mode
            output.dispatcher['done'] = self.handle_output_done
            output.dispatcher['scale'] = self.handle_output_scale


    def handle_seat_capabilities(self, seat, capabilities):
        print(f"Seat {seat} capabilities changed: {capabilities}")

    def handle_seat_name(self, seat, name):
        print(f"Seat {seat} name set to: {name}")


    def handle_output_geometry(self, output, x, y, physical_width, physical_height, subpixel, make, model, transform):
        print(f"Output {output} geometry updated: {make} {model}, {physical_width}x{physical_height}")

    def handle_output_mode(self, output, flags, width, height, refresh):
        print(f"Output {output} mode changed: {width}x{height}@{refresh/1000}Hz")

    def handle_output_done(self, output):
        print(f"Output {output} configuration done.")

    def handle_output_scale(self, output, factor):
        print(f"Output {output} scale set to {factor}.")


    def handle_toplevel_event(self, toplevel_handle: ZwlrForeignToplevelHandleV1):
        """Handle events for new toplevel windows."""
        print(f"New toplevel window created: {toplevel_handle}")
        
        # Subscribe to title and app_id changes as well as close event
        toplevel_handle.dispatcher['title']             = self.handle_title_change
        toplevel_handle.dispatcher['app_id']            = self.handle_app_id_change
        toplevel_handle.dispatcher['closed']            = self.handle_window_closed
        toplevel_handle.dispatcher['state']             = self.handle_state_change

    def handle_title_change(self, handle, title):
        """Update title in local state."""
        if handle.id not in self.window_handles_dct:
            self.window_handles_dct[handle.id] = {}
        self.window_handles_dct[handle.id]['title'] = title
        print(f"Title updated for window {handle.id}: {title}")

    def handle_app_id_change(self, handle, app_id):
        """Update app_id in local state."""
        if handle.id not in self.window_handles_dct:
            self.window_handles_dct[handle.id] = {}
        self.window_handles_dct[handle.id]['app_id'] = app_id
        print(f"App ID updated for window {handle.id}: {app_id}")

    def handle_window_closed(self, handle):
        """Remove window from local state."""
        if handle.id in self.window_handles_dct:
            del self.window_handles_dct[handle.id]
        print(f"Window {handle.id} has been closed.")

    def handle_state_change(self, handle, states):
        """Track active window based on state changes."""
        if 'activated' in states:
            if self.active_window is not None and self.active_window != handle.id:
                print(f"Window {self.active_window} is no longer active.")
            self.active_window = handle.id
            print(f"Window {handle.id} is now active.")
        elif self.active_window == handle.id:
            # If the currently active window reports any state change that might imply it is no longer active,
            # you would handle that here. Since there's no 'deactivated' state, this part might adjust based on your app's logic.
            print(f"Window {handle.id} is no longer active.")
            self.active_window = None

    def run(self):
        """Run the Wayland client."""
        try:
            print("Connecting to Wayland display...")
            self.display = Display()
            self.display.connect()
            print("Connected to Wayland display")

            print("Getting registry...")
            self.registry = self.display.get_registry()
            print("Registry obtained")

            print("Subscribing to 'global' events from registry")
            self.registry.dispatcher["global"] = self.registry_global_handler

            print("Running roundtrip to process registry events...")
            self.display.roundtrip()        # this is what causes initial events to come out...

            if self.forn_topl_mgr_prot_supported and self.toplevel_manager:
                print()
                print("Protocol is supported, waiting for events...")
                while True:
                    self.display.dispatch()   # Using 'block=True' causes NotImplementedError
            else:
                print()
                print("Protocol 'zwlr_foreign_toplevel_manager_v1' is NOT supported.")

        except Exception as e:
            print()
            print(f"An error occurred: {e}")
            print(traceback.format_exc())
        finally:
            if self.display is not None:
                self.cleanup()

if __name__ == "__main__":
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
