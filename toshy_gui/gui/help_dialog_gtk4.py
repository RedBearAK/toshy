import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib


class HelpDialog(Gtk.Window):
    """
    Reusable help dialog for displaying control explanations.
    
    Creates a modal dialog with help text and an OK button.
    """
    
    def __init__(self, parent, title, help_text):
        super().__init__()
        
        self.set_title("Toshy Preferences Help")  # Static title for all help dialogs
        self.set_transient_for(parent)
        self.set_modal(True)
        self.set_resizable(False)
        self.set_default_size(450, 300)
        
        # Set up CSS for the dialog
        self.setup_css()
        
        # Set up the dialog content
        self.setup_ui(title, help_text)
        
        # Connect keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
    def setup_css(self):
        """Set up CSS for the help dialog"""
        css_provider = Gtk.CssProvider()
        
        css_data = """
        .help-dialog-heading {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .help-text {
            font-size: 16px;
            line-height: 1.1;
        }
        """
        css_provider.load_from_data(css_data, -1)
        
        # Apply CSS to the display
        display = self.get_display()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
    def setup_ui(self, title, help_text):
        """Set up the help dialog user interface with title and help_text"""
        # Main container with padding
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        
        # Title (feature name as heading within dialog)
        title_label = Gtk.Label(label=title)
        # title_label.set_halign(Gtk.Align.START)
        title_label.set_halign(Gtk.Align.CENTER)
        title_label.add_css_class("help-dialog-heading")
        main_box.append(title_label)
        
        # Help text label with proper wrapping
        help_label = Gtk.Label(label=help_text)
        help_label.set_wrap(True)
        help_label.set_wrap_mode(Gtk.WrapMode.WORD)
        help_label.set_max_width_chars(60)
        help_label.set_halign(Gtk.Align.START)
        help_label.set_valign(Gtk.Align.START)
        help_label.set_justify(Gtk.Justification.LEFT)
        help_label.add_css_class("help-text")
        main_box.append(help_label)
        
        # Add expandable spacer to push OK button to bottom  
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        main_box.append(spacer)
        
        # Button box for OK button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        
        # OK button
        ok_button = Gtk.Button(label="OK")
        ok_button.set_size_request(100, 35)
        ok_button.add_css_class("suggested-action")
        ok_button.connect('clicked', self.on_ok_clicked)
        button_box.append(ok_button)
        main_box.append(button_box)
        
        self.set_child(main_box)
        
        # Set focus to OK button
        ok_button.grab_focus()
        
    def setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the dialog"""
        # Create key controller for keyboard events
        key_controller = Gtk.EventControllerKey()
        key_controller.connect('key-pressed', self.on_key_pressed)
        self.add_controller(key_controller)
        
    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard shortcuts"""
        # Close on Escape
        if keyval == 65307:  # Escape key
            self.close()
            return True
        
        # Close on Ctrl+W
        if keyval == 119 and state & Gtk.accelerator_get_default_mod_mask() == 4:  # Ctrl+W
            self.close()
            return True
            
        # Close on Enter/Return
        if keyval in [65293, 65421]:  # Return or KP_Enter
            self.close()
            return True
            
        return False
        
    def on_ok_clicked(self, button):
        """Handle OK button click"""
        self.close()


class HelpButton(Gtk.Button):
    """
    A standardized help button that shows a help dialog when clicked.
    """
    
    def __init__(self, parent_window, help_title, help_text, size=24):
        super().__init__()
        
        self.parent_window = parent_window
        self.help_title = help_title
        self.help_text = help_text
        
        # Set up the button appearance
        self.set_label("?")
        self.set_size_request(size, size)
        self.set_tooltip_text("Show help for this option")
        
        # Connect click handler
        self.connect('clicked', self.on_help_clicked)
        
    def on_help_clicked(self, button):
        """Handle help button click - show the help dialog"""
        dialog = HelpDialog(self.parent_window, self.help_title, self.help_text)
        dialog.present()


def create_control_with_help(parent_window, control_widget, help_title, help_text):
    """
    Utility function to create a horizontal box containing a control and help button.
    
    Args:
        parent_window: The main window (for dialog parent)
        control_widget: The main control (switch, radio button, etc.)
        help_title: Title for the help dialog
        help_text: Explanatory text for the help dialog
        
    Returns:
        Gtk.Box containing the control and help button
    """
    container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    
    # Add the main control
    container.append(control_widget)
    
    # Add the help button
    help_button = HelpButton(parent_window, help_title, help_text)
    container.append(help_button)
    
    return container
