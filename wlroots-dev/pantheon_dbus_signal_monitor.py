#!/usr/bin/env python3

from gi.repository import GLib
import dbus
import dbus.mainloop.glib

class GalaMonitor:
    def __init__(self):
        self.bus = None
        self.gala_interface = None

    def connect_to_gala(self):
        try:
            self.bus = dbus.SessionBus()
            self.gala_interface = self.bus.get_object(
                "org.pantheon.gala.DesktopIntegration",
                "/org/pantheon/gala/DesktopInterface"
            )
            print("Connected to Gala D-Bus interface.")
        except Exception as e:
            print(f"Failed to connect to Gala interface: {e}")
            return False
        return True

    def on_windows_changed(self, *args):
        print("WindowsChanged signal received.")

    def on_running_apps_changed(self, *args):
        print("RunningApplicationsChanged signal received.")

    def subscribe_signals(self):
        try:
            self.bus.add_signal_receiver(
                self.on_windows_changed,
                signal_name="WindowsChanged",
                dbus_interface="org.pantheon.gala.DesktopIntegration",
                path="/org/pantheon/gala/DesktopInterface"
            )

            self.bus.add_signal_receiver(
                self.on_running_apps_changed,
                signal_name="RunningApplicationsChanged",
                dbus_interface="org.pantheon.gala.DesktopIntegration",
                path="/org/pantheon/gala/DesktopInterface"
            )

            print("Subscribed to WindowsChanged and RunningApplicationsChanged signals.")
        except Exception as e:
            print(f"Failed to subscribe to signals: {e}")

    def run(self):
        if not self.connect_to_gala():
            return
        self.subscribe_signals()
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        loop = GLib.MainLoop()
        print("Listening for signals... Press Ctrl+C to exit.")
        try:
            loop.run()
        except KeyboardInterrupt:
            print("Exiting...")

if __name__ == "__main__":
    monitor = GalaMonitor()
    monitor.run()
