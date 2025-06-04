#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

def toggle_item(widget):
    # This should toggle the checkmark, but doesn't update visually in COSMIC
    widget.set_active(not widget.get_active())
    print(f"Item active state: {widget.get_active()}")  # State changes internally

indicator = AppIndicator3.Indicator.new(
    "test-indicator",
    "applications-system",
    AppIndicator3.IndicatorCategory.APPLICATION_STATUS
)
indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

menu = Gtk.Menu()
check_item = Gtk.CheckMenuItem(label="Test Toggle")
menu.append(check_item)

button_item = Gtk.MenuItem(label="Click to Toggle Above Item")
button_item.connect("activate", lambda w: toggle_item(check_item))
menu.append(button_item)

menu.show_all()
indicator.set_menu(menu)

# Test programmatic update after 2 seconds
GLib.timeout_add_seconds(2, lambda: toggle_item(check_item))

GLib.MainLoop().run()
