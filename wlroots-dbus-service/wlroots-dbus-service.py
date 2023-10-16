#!/bin/env python3

from wlroots.wlr_types import ForeignToplevelManagerV1
from pywayland.client import Display

class WindowListener:
    def __init__(self):
        # Initialize Wayland Display
        self.display = Display()

        try:
            # Create an instance of ForeignToplevelManagerV1
            self.toplevel_manager = ForeignToplevelManagerV1.create(self.display)
        except TypeError:
            print("Failed to initialize the ForeignToplevelManager. Are you running in a supported Wayland environment?")
            exit(1)

        # Set up event handlers
        self.setup_event_handlers()

        # Run the Wayland event loop
        self.display.run()

    def setup_event_handlers(self):
        """Set up event handlers for the toplevel manager."""
        self.toplevel_manager.on('toplevel', self.on_new_toplevel)

    def _setup_toplevel_event_handlers(self, toplevel):
        """Set up event handlers for a single toplevel window."""
        toplevel.on('title', self.on_title_change)
        toplevel.on('app_id', self.on_app_id_change)

    def on_new_toplevel(self, toplevel):
        """Handle when a new toplevel window is announced."""
        print(f"New toplevel window: {toplevel.title} ({toplevel.app_id})")
        self._setup_toplevel_event_handlers(toplevel)

    def on_app_id_change(self, toplevel, app_id):
        """Handle when the app_id of a toplevel window changes."""
        print(f"Window {toplevel.title} changed app_id to {app_id}")

    def on_title_change(self, toplevel, title):
        """Handle when the title of a toplevel window changes."""
        print(f"Window changed title to {title}")

if __name__ == "__main__":
    listener = WindowListener()
