#!/usr/bin/env python3

# Script to connect to Wayland compositor and query the focused window's app class and window title.

from pywayland.client import Display
from pywayland.protocol.wayland import WlRegistry, wl_display, wl_registry
import traceback
from typing import Optional

class WaylandClient:
    def __init__(self):
        """Initialize the WaylandClient."""
        self.display: Optional[Display] = None
        self.also_display: Optional[wl_display.WlDisplayProxy] = None
        self.registry: Optional[wl_registry.WlRegistryProxy] = None
        self.topl_mgmt_prot_supported = False
        self.toplevel_manager = None
        self.topl_mgmt_prot_name = None
        self.topl_mgmt_prot_ver = None

    def registry_handler(self, registry, name, interface, version):
        """Handle registry events."""
        print(f"Registry event: name={name}, interface={interface}, version={version}")
        if 'wlr' in interface:
            print('                             #### wlr protocol detected')
            print()
        topl_mgmt_prot_names = [
            'zwlr_foreign_toplevel_manager_v1',
            'wlr_foreign_toplevel_manager_v1',
        ]
        if interface in topl_mgmt_prot_names:
            self.topl_mgmt_prot_supported = True
            self.topl_mgmt_prot_name = interface
            self.topl_mgmt_prot_ver = version
            print(f"Protocol '{interface}' version '{version}' is SUPPORTED.")
            print()

            self.toplevel_manager = self.registry.bind(name, version, interface)

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
            # Alias to fix VSCode syntax highlighting on 'self.display.get_registry()' method
            self.also_display = self.display
            print("Connected to Wayland display")

            print("Getting registry...")
            self.registry = self.also_display.get_registry()
            self.registry.dispatcher["global"] = self.registry_handler
            print("Registry obtained")

            print("Running roundtrip to process registry events...")
            self.display.roundtrip()

            if self.topl_mgmt_prot_supported and self.toplevel_manager:
                print()
                print(f"Protocol '{self.topl_mgmt_prot_name}' "
                        f"version '{self.topl_mgmt_prot_ver}' is SUPPORTED.")
                print()
                # Query for focused window's app class and window title
                print("Querying for focused window's app class and window title...")
                self.toplevel_manager.dispatcher["toplevel"] = self.handle_toplevel_event
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
