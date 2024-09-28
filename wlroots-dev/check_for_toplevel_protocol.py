#!/usr/bin/env python3


# Script to test checking for the wlroots foreign toplevel management protocol
# support in the Wayland compositor.

from pywayland.client import Display
from pywayland.protocol.wayland import WlRegistry, wl_display
import traceback
from typing import Optional

class WaylandClient:
    def __init__(self):
        self.display: Optional[Display] = None
        self.registry: Optional[WlRegistry]= None
        self.topl_mgmt_prot_supported = False
        self.topl_mgmt_prot_name = None
        self.topl_mgmt_prot_ver = None

    def registry_handler(self, registry, name, interface, version):

        wanted_interfaces = [
            'zwlr_foreign_toplevel_manager_v1',     # wlroots compositors should have this?
            'zcosmic_toplevel_info_v1',             # COSMIC desktop environment
            'ext_foreign_toplevel_list_v1',         # newer Wayland compositors may have this?
        ]

        if interface in wanted_interfaces:
            print()
            print(f"Protocol '{interface}' version '{version}' is SUPPORTED:")
            print(f"    Registry event: name={name}, interface={interface}, version={version}")
            print()
        else:
            print(f"Registry event: name={name}, interface={interface}, version={version}")

        if interface == 'zwlr_foreign_toplevel_manager_v1':
            self.topl_mgmt_prot_supported = True
            self.topl_mgmt_prot_name = interface
            self.topl_mgmt_prot_ver = version

    def run(self):
        try:
            print("Connecting to Wayland display...")
            self.display = Display()
            self.display.connect()
            print("Connected to Wayland display")

            print("Getting registry...")

            ########################################################################################
            # self.registry = self.display.get_registry()
            # Alias for 'display' to help VSCode understand where 'get_registry()' method lives
            self.also_display: wl_display.WlDisplayProxy = self.display
            ########################################################################################

            self.registry = self.also_display.get_registry()
            self.registry.dispatcher["global"] = self.registry_handler
            print("Registry obtained")

            print("Running roundtrip to process registry events...")
            print()
            self.display.roundtrip()

            # print()
            # if self.topl_mgmt_prot_supported:
            #     print(f"Protocol '{self.topl_mgmt_prot_name}' "
            #             f"version '{self.topl_mgmt_prot_ver}' is SUPPORTED.")
            # else:
            #     print("Protocol 'zwlr_foreign_toplevel_manager_v1' is NOT supported.")

        except Exception as e:
            print("An error occurred:")
            print(traceback.format_exc())
        finally:
            # This 'finally' is to avoid a segmentation fault when script ends.
            if self.display is not None:
                print()
                print("Disconnecting from Wayland display")
                self.display.disconnect()
                print("Disconnected from Wayland display")
                print()

if __name__ == '__main__':
    print("Starting Wayland client...")
    client = WaylandClient()
    client.run()
    print("Wayland client finished")
