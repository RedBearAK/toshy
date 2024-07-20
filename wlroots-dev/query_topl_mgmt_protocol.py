#!/usr/bin/env python3


from pywayland.client import Display
from wlroots.wlr_types.foreign_toplevel_management_v1 import ForeignToplevelManagerV1
import traceback
from typing import Optional



class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        self.display: Optional[Display] = None
        self.registry = None
        self.topl_mgmt: Optional[ForeignToplevelManagerV1] = None
        self.topl_mgmt_prot_supported = False

    def registry_handler(self, registry, name, interface_name, version):
        """Handle registry events."""
        print(f"Registry event: name={name}, interface={interface_name}, version={version}")
        if interface_name == 'zwlr_foreign_toplevel_manager_v1':
            self.topl_mgmt_prot_supported = True

            # self.topl_mgmt = registry.bind(name, ForeignToplevelManagerV1, version)

            # Properly create a ForeignToplevelManagerV1 instance
            self.topl_mgmt = ForeignToplevelManagerV1.create(self.display)

            self.topl_mgmt.add_listener(self.handle_toplevel_event)
            print(f"Protocol name '{name}' interface '{interface_name}' version '{version}' is SUPPORTED.")

    def handle_toplevel_event(self, toplevel, event):
        """Handle toplevel events."""
        print(f"Toplevel event {event} occurred.")

    def run(self):
        """Run the Wayland client."""
        try:
            print("Connecting to Wayland display...")
            self.display = Display()
            self.display.connect()
            print("Connected to Wayland display")

            print("Getting registry...")
            self.registry = self.display.get_registry()
            self.registry.dispatcher["global"] = self.registry_handler
            print("Registry obtained")

            print("Running roundtrip to process registry events...")
            self.display.roundtrip()

            if self.topl_mgmt_prot_supported and self.topl_mgmt:
                print("Protocol is supported, waiting for events...")
                while True:
                    self.display.dispatch()
            else:
                print("Protocol 'zwlr_foreign_toplevel_manager_v1' is NOT supported.")

        except Exception as e:
            print("An error occurred:")
            print(traceback.format_exc())
        finally:
            if self.display is not None:
                print("Disconnecting from Wayland display")
                self.display.disconnect()
                print("Disconnected from Wayland display")

if __name__ == "__main__":
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
