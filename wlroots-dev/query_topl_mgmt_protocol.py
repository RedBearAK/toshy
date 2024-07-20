#!/usr/bin/env python3


from wlroots.wlr_types.foreign_toplevel_management_v1 import (
    ForeignToplevelManagerV1, ForeignToplevelHandleV1
)
from pywayland.client import Display
from pywayland.protocol.wayland import WlRegistry, wl_display, wl_registry
import traceback
from typing import Optional

from pywayland.protocol_core import Interface


class ZwlrForeignToplevelManagerV1Interface(Interface):
    name = "zwlr_foreign_toplevel_manager_v1"
    version = 3


class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        self.display: Optional[Display] = None
        self.also_display = None
        self.registry: Optional[WlRegistry] = None
        self.also_registry = None
        self.topl_mgmt: Optional[ForeignToplevelManagerV1] = None
        self.topl_mgmt_prot_supported = False

    def registry_handler(self, registry, name, interface, version):
        """Handle registry events."""
        print(f"Registry event: name={name}, interface={interface}, version={version}")
        if interface == 'zwlr_foreign_toplevel_manager_v1':
            self.topl_mgmt_prot_supported = True
            self.topl_mgmt = self.also_registry.bind(name, ZwlrForeignToplevelManagerV1Interface, version)
            self.topl_mgmt.add_listener(self.handle_toplevel_event)
            print(f"Protocol '{interface}' version '{version}' is SUPPORTED.")

    def handle_toplevel_event(self, toplevel, event, *args):
        """Handle toplevel events."""
        if event == 'title':
            print(f"Toplevel handle title: {args[0]}")
        elif event == 'app_id':
            print(f"Toplevel handle app_id: {args[0]}")

    def run(self):
        """Run the Wayland client."""
        try:
            print("Connecting to Wayland display...")
            self.display = Display()
            self.display.connect()
            # Alias for type hinting to light up the '.get_registry()' method below
            self.also_display: wl_display.WlDisplayProxy = self.display
            print("Connected to Wayland display")

            print("Getting registry...")
            self.registry = self.also_display.get_registry()
            self.also_registry: wl_registry.WlRegistryProxy = self.registry
            # self.registry.dispatcher["global"] = self.registry_handler
            # Alias for type hinting to light up '.dispatcher' attribute 
            # below, and '.bind()' method in 'registry_handler()'
            self.also_registry.dispatcher["global"] = self.registry_handler
            print("Registry obtained")

            print("Running roundtrip to process registry events...")
            self.display.roundtrip()

            if self.topl_mgmt_prot_supported and self.topl_mgmt:
                print("Protocol is supported, waiting for events...")
                # Main event loop to keep the client running and handle events
                while True:
                    self.display.dispatch()
            else:
                print("Protocol '[z]wlr_foreign_toplevel_manager_v1' is NOT supported.")

        except Exception as e:
            print("An error occurred:")
            print(traceback.format_exc())
        finally:
            # This 'finally' is to avoid a segmentation fault when the script ends.
            if self.display is not None:
                print("Disconnecting from Wayland display")
                self.display.disconnect()
                print("Disconnected from Wayland display")


if __name__ == "__main__":
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
