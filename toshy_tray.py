#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Indicator tray icon menu app for Toshy, using pygobject/gi
TOSHY_PART      = 'tray'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Tray Icon app'
APP_VERSION     = '2023.0709'

# -------- COMMON COMPONENTS --------------------------------------------------

import os
import re
import sys
import time
import dbus
import fcntl
import psutil
import shutil
import signal
import threading
# import traceback
import subprocess
from subprocess import DEVNULL

# Local imports
from lib.logger import *
from lib import logger
from lib.settings_class import Settings


logger.VERBOSE = True

if not str(sys.platform) == "linux":
    raise OSError("This app is designed to be run only on Linux")

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir = os.path.expanduser("~")
home_local_bin = os.path.join(home_dir, '.local', 'bin')
local_site_packages_dir = os.path.join(home_dir, f".local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages")
# parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

def pattern_found_in_module(pattern, module_path):
    try:
        with open(module_path, 'r', encoding='utf-8') as file:
            content = file.read()
            return bool(re.search(pattern, content))
    except FileNotFoundError as file_err:
        print(f"Error: The file {module_path} was not found.\n\t {file_err}")
        return False
    except IOError as io_err:
        print(f"Error: An issue occurred while reading the file {module_path}.\n\t {io_err}")
        return False

pattern = 'SLICE_MARK_START: barebones_user_cfg'
module_path = os.path.abspath(os.path.join(current_folder_path, 'toshy_config.py'))

# check if the config file is a "barebones" type
if pattern_found_in_module(pattern, module_path):
    barebones_config = True
else:
    barebones_config = False


sys.path.insert(0, local_site_packages_dir)
sys.path.insert(0, current_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{current_folder_path}:{local_site_packages_dir}:{existing_path}'
os.environ['PATH'] = f"{home_local_bin}:{os.environ['PATH']}"


#########################################################################
def signal_handler(sig, frame):
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        remove_lockfile()
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

signal.signal(signal.SIGINT,    signal_handler)
signal.signal(signal.SIGQUIT,   signal_handler)
#########################################################################
# Let signal handler be defined and called before other things ^^^^^^^


USER_ID         = f'{os.getuid()}'
# support multiple simultaneous users via per-user temp folder
TOSHY_USER_TMP_DIR   = f'/tmp/toshy_uid{USER_ID}'

PREF_FILE_DIR   = f'{current_folder_path}'
PREF_FILE_NAME  = f'toshy_user_preferences.json'
PREF_FILE       = os.path.join(PREF_FILE_DIR, PREF_FILE_NAME)

LOCK_FILE_DIR   = f'{TOSHY_USER_TMP_DIR}/lock'
LOCK_FILE_NAME  = f'toshy_{TOSHY_PART}.lock'
LOCK_FILE       = os.path.join(LOCK_FILE_DIR, LOCK_FILE_NAME)

if not os.path.exists(LOCK_FILE_DIR):
    try:
        os.makedirs(LOCK_FILE_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        debug(f'NON-FATAL ERROR: Problem creating lockfile directory: {LOCK_FILE_DIR}')
        debug(e)

# recursively set user's Toshy temp folder as only read/write by owner
try:
    chmod_cmd = shutil.which('chmod')
    os.system(f'{chmod_cmd} 0700 {TOSHY_USER_TMP_DIR}')
except Exception as e:
    debug(f'NON-FATAL ERROR: Problem when setting permissions on temp folder.')
    debug(e)

###############################################################################
# START of functions dealing with the lockfile

def get_pid_from_lockfile():
    try:
        with open(LOCK_FILE, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
            pid = int(f.read().strip())
            fcntl.flock(f, fcntl.LOCK_UN)
            return pid
    except (IOError, ValueError, PermissionError) as e:
        # debug(f'NON-FATAL: No existing lockfile or lockfile could not be read:')
        # debug(e)
        return None

def write_pid_to_lockfile():
    try:
        with open(LOCK_FILE, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.write(str(os.getpid()))
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
    except (IOError, ValueError, PermissionError) as e:
        debug(f'NON-FATAL: Problem writing PID to lockfile:')
        debug(e)

def remove_lockfile():
    try:
        os.unlink(LOCK_FILE)
        # debug(f'Lockfile removed.')
    except Exception as e:
        debug(f'NON-FATAL: Problem when trying to remove lockfile.')
        debug(e)

def terminate_process(pid):
    for sig in [signal.SIGTERM, signal.SIGKILL]:
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            time.sleep(0.5)
            return None
        if process.status() == psutil.STATUS_ZOMBIE:
            time.sleep(0.5)
            return None
        os.kill(pid, sig)
        time.sleep(0.5)
    raise EnvironmentError(f'FATAL ERROR: Failed to close existing process with PID: {pid}')

def handle_existing_process():
    pid = get_pid_from_lockfile()
    if pid:
        terminate_process(pid)

# END of functions dealing with the lockfile
###############################################################################



###############################################################################
# -------- TOSHY TRAY SPECIFIC COMPONENTS -------------------------------------
###############################################################################

# What we need for the indicator tray icon and menu
import gi.repository
gi.require_version('Gtk', '3.0')

try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
except (ValueError, ImportError) as e:
    # debug(f'ImportError: Falling back on AppIndicator3 instead of AyatanaAppIndicator3.')
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3

from gi.repository import Gtk, GLib


# Define some globals for the commands run by menu items

assets_path         = os.path.join(current_folder_path, 'assets')
icon_file_active    = os.path.join(assets_path, "toshy_app_icon_rainbow.svg")
icon_file_grayscale = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse_grayscale.svg")
icon_file_inverse   = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse.svg")

loop = None

# Settings class object setup
config_dir_path = current_folder_path
cnfg = Settings(config_dir_path)
cnfg.watch_database()   # start watching the preferences file for changes

# Notification handler object setup
from lib.notification_manager import NotificationManager
ntfy = NotificationManager(icon_file_active, title='Toshy Alert (Tray)')


def get_settings_list(settings_obj):
    # get all attributes from the object
    all_attributes = [attr for attr in dir(settings_obj) if not callable(getattr(settings_obj, attr)) and not attr.startswith("__")]
    # filter out attributes that are not strings or booleans
    filtered_attributes = [attr for attr in all_attributes if isinstance(getattr(settings_obj, attr), (str, bool, int))]
    # create a list of tuples with attribute name and value pairs
    settings_list = [(attr, getattr(settings_obj, attr)) for attr in filtered_attributes]
    return settings_list


# Store the settings as a list to see when they change.
# Monitor from a separate thread.
last_settings_list = get_settings_list(cnfg)


def fn_monitor_internal_settings():
    global last_settings_list
    while True:
        time.sleep(1)
        if last_settings_list != get_settings_list(cnfg):
            # debug(f'settings list changed...')
            last_settings_list = get_settings_list(cnfg)
            load_optspec_layout_submenu_settings()
            load_prefs_submenu_settings()


sysctl_cmd      = f"{shutil.which('systemctl')}"
user_sysctl     = f'{sysctl_cmd} --user'

toshy_svc_sessmon           = 'toshy-session-monitor.service'
toshy_svc_config            = 'toshy-config.service'

svc_status_sessmon          = '❓'              # 'Undefined'
svc_status_config           = '❓'              # 'Undefined'

svc_status_glyph_active     = '✅'              # 😀 ✅  #
svc_status_glyph_inactive   = '❌'              # ❌ ⏸ 🛑 #
svc_status_glyph_unknown    = '❓'              # ❔  #


# -------- CREATE MENU --------------------------------------------------------

menu = Gtk.Menu()
# Add menu items here using Gtk.MenuItem and Gtk.ImageMenuItem

tray_indicator = AppIndicator3.Indicator.new(
    "Toshy Tray Icon Undefined",
    icon_name=icon_file_grayscale,
    category=AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
tray_indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
tray_indicator.set_menu(menu)
tray_indicator.set_title("Toshy Status Indicator") # try to set what might show in tooltip


def fn_monitor_toshy_services():
    global svc_status_config, svc_status_sessmon
    toshy_svc_config_unit_state = None
    toshy_svc_sessmon_unit_state = None
    last_svcs_state_tup = (None, None)
    _first_run = True

    session_bus    = dbus.SessionBus()

    systemd1_dbus_obj   = session_bus.get_object(
        'org.freedesktop.systemd1', 
        '/org/freedesktop/systemd1'
    )
    systemd1_mgr_iface  = dbus.Interface(
        systemd1_dbus_obj, 
        'org.freedesktop.systemd1.Manager'
    )

    toshy_svc_config_unit_path  = None
    toshy_svc_sessmon_unit_path = None

    def get_svc_states_dbus():
        nonlocal toshy_svc_config_unit_state, toshy_svc_sessmon_unit_state
        toshy_svc_config_unit_obj = session_bus.get_object(
            'org.freedesktop.systemd1', 
            toshy_svc_config_unit_path)
        toshy_svc_config_unit_iface = dbus.Interface(
            toshy_svc_config_unit_obj, 
            'org.freedesktop.DBus.Properties')
        toshy_svc_config_unit_state = str(
            toshy_svc_config_unit_iface.Get(
                'org.freedesktop.systemd1.Unit', 'ActiveState'))

        toshy_svc_sessmon_unit_obj = session_bus.get_object(
            'org.freedesktop.systemd1', 
            toshy_svc_sessmon_unit_path)
        toshy_svc_sessmon_unit_iface = dbus.Interface(
            toshy_svc_sessmon_unit_obj, 
            'org.freedesktop.DBus.Properties')
        toshy_svc_sessmon_unit_state = str(
            toshy_svc_sessmon_unit_iface.Get(
                'org.freedesktop.systemd1.Unit', 'ActiveState'))
        return (toshy_svc_config_unit_state, toshy_svc_sessmon_unit_state)

    time.sleep(0.6)   # wait a bit before starting the loop

    while True:

        if not toshy_svc_config_unit_path or not toshy_svc_sessmon_unit_path:
            try:
                toshy_svc_config_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_config)
                toshy_svc_sessmon_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_sessmon)
            except dbus.exceptions.DBusException as dbus_err:
                debug(f'TOSHY_TRAY: DBusException trying to get proxies:\n\t{dbus_err}')
                time.sleep(3)
                continue

        try:
            curr_svcs_state_tup = get_svc_states_dbus()
        except dbus.exceptions.DBusException as dbus_err:
            toshy_svc_config_unit_path  = None
            toshy_svc_sessmon_unit_path = None
            time.sleep(2)
            continue

        if toshy_svc_config_unit_state == "active":
            svc_status_config = svc_status_glyph_active
        elif toshy_svc_config_unit_state == "inactive":
            svc_status_config = svc_status_glyph_inactive
        else:
            svc_status_config = svc_status_glyph_unknown

        if toshy_svc_sessmon_unit_state == "active":
            svc_status_sessmon = svc_status_glyph_active
        elif toshy_svc_sessmon_unit_state == "inactive":
            svc_status_sessmon = svc_status_glyph_inactive
        else:
            svc_status_sessmon = svc_status_glyph_unknown

        time.sleep(0.1)
        curr_icon = tray_indicator.get_property('icon-name')
        if curr_svcs_state_tup == ('active', 'active') and curr_icon != icon_file_active:
            # debug(f'Toshy services active, but active icon not set! Fixing.')
            tray_indicator.set_icon_full(icon_file_active, "Toshy Tray Icon Active")
        elif curr_svcs_state_tup == ('inactive', 'inactive') and curr_icon != icon_file_inverse:
            # debug(f'Toshy services inactive, but inactive icon not set! Fixing.')
            tray_indicator.set_icon_full(icon_file_inverse, "Toshy Tray Icon Inactive")
        elif curr_svcs_state_tup not in [('active', 'active'), ('inactive', 'inactive')]:
            # debug(f'\nToshy services status unknown. Setting grayscale/undefined icon.')
            # debug(f'{curr_svcs_state_tup = }\n')
            tray_indicator.set_icon_full(icon_file_grayscale, "Toshy Tray Icon Undefined")

        max_attempts = 5
        
        for attempt in range(max_attempts):
            try:
                _ = toshy_config_status_item.get_label()
                _ = session_monitor_status_item.get_label()
                break
            except NameError:
                time.sleep(0.01)  # Add a small delay between attempts
                continue
        else:
            error(f"Error: Menu items not ready after {max_attempts} attempts")
            time.sleep(2)
            continue

        if curr_svcs_state_tup != last_svcs_state_tup:
            config_label_text = f'         Config: {svc_status_config}'
            sessmon_label_text = f'     SessMon: {svc_status_sessmon}'
            for attempt in range(max_attempts):
                try:
                    toshy_config_status_item.set_label(config_label_text)
                    time.sleep(0.05) # give the event loop time to complete set_label
                    if toshy_config_status_item.get_label() == config_label_text:
                        break
                except NameError: pass  # Let it pass if menu item not ready yet
                time.sleep(0.01)  # Add a small delay between attempts
            else:
                error(f"Error: Failed to update Config label after {max_attempts} attempts")

            for attempt in range(max_attempts):
                try:
                    session_monitor_status_item.set_label(sessmon_label_text)
                    time.sleep(0.05) # give the event loop time to complete set_label
                    if session_monitor_status_item.get_label() == sessmon_label_text:
                        break
                except NameError: pass  # Let it pass if menu item not ready yet
                time.sleep(0.01)  # Add a small delay between attempts
            else:
                error(f"Error: Failed to update SessMon label after {max_attempts} attempts")

        last_svcs_state_tup = curr_svcs_state_tup

        time.sleep(2)



# -------- MENU ACTION FUNCTIONS ----------------------------------------------

def fn_restart_toshy_services(widget):
    """(Re)Start Toshy services with CLI command"""
    toshy_svcs_restart_cmd = os.path.join(home_local_bin, 'toshy-services-restart')
    subprocess.Popen([toshy_svcs_restart_cmd], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(3)
    _ntfy_icon_file = icon_file_active
    _ntfy_msg = 'Toshy systemd services (re)started.\nTap any modifier key before trying shortcuts.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)

def fn_stop_toshy_services(widget):
    """Stop Toshy services with CLI command"""
    toshy_svcs_stop_cmd = os.path.join(home_local_bin, 'toshy-services-stop')
    subprocess.Popen([toshy_svcs_stop_cmd], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(3)
    _ntfy_icon_file = icon_file_inverse
    _ntfy_msg = 'Toshy systemd services stopped.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


def fn_restart_toshy_script(widget):
    """Start the manual run config script"""
    toshy_cfg_restart_cmd = os.path.join(home_local_bin, 'toshy-config-restart')
    subprocess.Popen([toshy_cfg_restart_cmd], stdout=DEVNULL, stderr=DEVNULL)

def fn_stop_toshy_script(widget):
    """Stop the manual run config script"""
    toshy_cfg_stop_cmd = os.path.join(home_local_bin, 'toshy-config-stop')
    subprocess.Popen([toshy_cfg_stop_cmd], stdout=DEVNULL, stderr=DEVNULL)

def fn_open_preferences(widget):
    subprocess.Popen(['toshy-gui'])

def fn_open_config_folder(widget):
    try:
        xdg_open_cmd = shutil.which('xdg-open')
        subprocess.Popen([xdg_open_cmd, current_folder_path])
    except FileNotFoundError as e:
        error('File not found. I have no idea how this error is possible.')
        error(e)

def run_cmd_in_terminal(command):
    # List of common terminal emulators in descending order of commonness.
    terminal_app_cmd_lst = [
        ("gnome-terminal", ["--"]),
        ("konsole", ["-e"]),
        ("xfce4-terminal", ["-e"]),
        ("mate-terminal", ["-e"]),
        ("xterm", ["-e"]),
        ("rxvt", ["-e"]),
        ("urxvt", ["-e"]),
    ]
    for terminal, terminal_args in terminal_app_cmd_lst:
        terminal_path = shutil.which(terminal)
        if terminal_path is not None:
            # run the terminal emulator with the command
            subprocess.Popen([terminal_path] + terminal_args + [command])
            return
    _ntfy_icon_file = icon_file_inverse
    _ntfy_msg = "ERROR: No suitable terminal emulator found.\nFile an issue on GitHub."
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


def fn_show_services_log(widget):
    run_cmd_in_terminal('toshy-services-log')

def fn_remove_tray_icon(widget):
    global loop
    remove_lockfile()
    loop.quit()
    pkill_cmd = shutil.which('pkill')
    os.system(f'{pkill_cmd} -f "toshy_tray.py"')
    # Gtk.main_quit()
    sys.exit(0)

# -------- MENU ITEMS --------------------------------------------------

services_label_item = Gtk.MenuItem(label=" ---- Services Status ---- ")
services_label_item.set_sensitive(False)
menu.append(services_label_item)

toshy_config_status_item = Gtk.MenuItem(    label="         Config: (?)")
toshy_config_status_item.set_sensitive(False)
menu.append(toshy_config_status_item)

session_monitor_status_item = Gtk.MenuItem( label="     SessMon: (?)")
session_monitor_status_item.set_sensitive(False)
menu.append(session_monitor_status_item)

separator_above_svcs_item = Gtk.SeparatorMenuItem()
menu.append(separator_above_svcs_item)  #-------------------------------------#

restart_toshy_svcs_item = Gtk.MenuItem(label="Re/Start Toshy Services")
restart_toshy_svcs_item.connect("activate", fn_restart_toshy_services)
menu.append(restart_toshy_svcs_item)

quit_toshy_svcs_item = Gtk.MenuItem(label="Stop Toshy Services")
quit_toshy_svcs_item.connect("activate", fn_stop_toshy_services)
menu.append(quit_toshy_svcs_item)

separator_below_svcs_item = Gtk.SeparatorMenuItem()
menu.append(separator_below_svcs_item)  #-------------------------------------#

restart_toshy_script_item = Gtk.MenuItem(label="Re/Start Toshy Script")
restart_toshy_script_item.connect("activate", fn_restart_toshy_script)
menu.append(restart_toshy_script_item)

stop_toshy_script_item = Gtk.MenuItem(label="Stop Toshy Script")
stop_toshy_script_item.connect("activate", fn_stop_toshy_script)
menu.append(stop_toshy_script_item)

separator_below_script_item = Gtk.SeparatorMenuItem()
menu.append(separator_below_script_item)  #-------------------------------------#

if not barebones_config:

    def load_prefs_submenu_settings():
        cnfg.load_settings()
        forced_numpad_item.set_active(cnfg.forced_numpad)
        media_arrows_fix_item.set_active(cnfg.media_arrows_fix)
        multi_lang_item.set_active(cnfg.multi_lang)
        ST3_in_VSCode_item.set_active(cnfg.ST3_in_VSCode)
        Caps2Cmd_item.set_active(cnfg.Caps2Cmd)
        Caps2Esc_Cmd_item.set_active(cnfg.Caps2Esc_Cmd)
        Enter2Ent_Cmd_item.set_active(cnfg.Enter2Ent_Cmd)

    def save_prefs_settings(widget):
        cnfg.forced_numpad      = forced_numpad_item.get_active()
        cnfg.media_arrows_fix   = media_arrows_fix_item.get_active()
        cnfg.multi_lang         = multi_lang_item.get_active()
        cnfg.ST3_in_VSCode      = ST3_in_VSCode_item.get_active()
        cnfg.Caps2Cmd           = Caps2Cmd_item.get_active()
        cnfg.Caps2Esc_Cmd       = Caps2Esc_Cmd_item.get_active()
        cnfg.Enter2Ent_Cmd      = Enter2Ent_Cmd_item.get_active()
        cnfg.save_settings()

    ###############################################################
    # Preferences submenu

    prefs_submenu = Gtk.Menu()
    prefs_submenu_item = Gtk.MenuItem(label="Preferences")
    prefs_submenu_item.set_submenu(prefs_submenu)
    menu.append(prefs_submenu_item)

    multi_lang_item = Gtk.CheckMenuItem(label='Alt_Gr on Right Cmd')
    multi_lang_item.set_active(cnfg.multi_lang)
    multi_lang_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(multi_lang_item)

    Caps2Cmd_item = Gtk.CheckMenuItem(label='CapsLock is Cmd')
    Caps2Cmd_item.set_active(cnfg.Caps2Cmd)
    Caps2Cmd_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(Caps2Cmd_item)

    Caps2Esc_Cmd_item = Gtk.CheckMenuItem(label='CapsLock is Esc & Cmd')
    Caps2Esc_Cmd_item.set_active(cnfg.Caps2Esc_Cmd)
    Caps2Esc_Cmd_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(Caps2Esc_Cmd_item)

    Enter2Ent_Cmd_item = Gtk.CheckMenuItem(label='Enter is Ent & Cmd')
    Enter2Ent_Cmd_item.set_active(cnfg.Enter2Ent_Cmd)
    Enter2Ent_Cmd_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(Enter2Ent_Cmd_item)

    ST3_in_VSCode_item = Gtk.CheckMenuItem(label='Sublime3 in VSCode')
    ST3_in_VSCode_item.set_active(cnfg.ST3_in_VSCode)
    ST3_in_VSCode_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(ST3_in_VSCode_item)

    forced_numpad_item = Gtk.CheckMenuItem(label='Forced Numpad')
    forced_numpad_item.set_active(cnfg.forced_numpad)
    forced_numpad_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(forced_numpad_item)

    media_arrows_fix_item = Gtk.CheckMenuItem(label='Media Arrows Fix')
    media_arrows_fix_item.set_active(cnfg.media_arrows_fix)
    media_arrows_fix_item.connect('toggled', save_prefs_settings)
    prefs_submenu.append(media_arrows_fix_item)

    # End of Preferences submenu
    ###############################################################

    def load_optspec_layout_submenu_settings():
        cnfg.load_settings()
        optspec_us_item.set_active(cnfg.optspec_layout == 'US')
        optspec_abc_extended_item.set_active(cnfg.optspec_layout == 'ABC')
        optspec_disabled_item.set_active(cnfg.optspec_layout == 'Disabled')

    def save_optspec_layout_setting(menu_item, layout):
        if menu_item.get_active():
            cnfg.optspec_layout = layout
            cnfg.save_settings()
            load_optspec_layout_submenu_settings()


    ###############################################################
    # OptSpec layout submenu
    optspec_layout_submenu = Gtk.Menu()
    optspec_layout_item = Gtk.MenuItem(label='OptSpec Layout')
    optspec_layout_item.set_submenu(optspec_layout_submenu)
    menu.append(optspec_layout_item)

    # create submenu items for each layout option
    optspec_us_item = Gtk.CheckMenuItem(label='US*')
    optspec_us_item.connect('toggled', save_optspec_layout_setting, 'US')
    optspec_layout_submenu.append(optspec_us_item)

    optspec_abc_extended_item = Gtk.CheckMenuItem(label='ABC Extended')
    optspec_abc_extended_item.connect('toggled', save_optspec_layout_setting, 'ABC')
    optspec_layout_submenu.append(optspec_abc_extended_item)

    optspec_disabled_item = Gtk.CheckMenuItem(label='Disabled')
    optspec_disabled_item.connect('toggled', save_optspec_layout_setting, 'Disabled')
    optspec_layout_submenu.append(optspec_disabled_item)

    separator_below_prefs_submenu_item = Gtk.SeparatorMenuItem()
    menu.append(separator_below_prefs_submenu_item)  #-------------------------------------#

    preferences_item = Gtk.MenuItem(label="Open Preferences App")
    preferences_item.connect("activate", fn_open_preferences)
    menu.append(preferences_item)

open_config_folder_item = Gtk.MenuItem(label="Open Config Folder")
open_config_folder_item.connect("activate", fn_open_config_folder)
menu.append(open_config_folder_item)

show_services_log_item = Gtk.MenuItem(label="Show Services Log")
show_services_log_item.connect("activate", fn_show_services_log)
menu.append(show_services_log_item)

separator_above_remove_icon_item = Gtk.SeparatorMenuItem()
menu.append(separator_above_remove_icon_item)  #-------------------------------------#

remove_tray_icon_item = Gtk.MenuItem(label="Remove Icon from Tray")
remove_tray_icon_item.connect("activate", fn_remove_tray_icon)
menu.append(remove_tray_icon_item)

menu.show_all()


def is_init_systemd():
    try:
        with open("/proc/1/comm", "r") as f:
            return f.read().strip() == 'systemd'
    except FileNotFoundError:
        print("Toshy_GUI: The /proc/1/comm file does not exist.")
        return False
    except PermissionError:
        print("Toshy_GUI: Permission denied when trying to read the /proc/1/comm file.")
        return False


def main():

    global loop

    if shutil.which('systemctl') and is_init_systemd():
        # help out the config file user service
        subprocess.run([
            "systemctl", 
            "--user", 
            "import-environment", 
            "XDG_SESSION_TYPE", 
            "XDG_SESSION_DESKTOP", 
            "XDG_CURRENT_DESKTOP"
        ])    
        # Start a separate thread to watch the status of Toshy systemd services (or script?)
        monitor_toshy_services_thread = threading.Thread(target=fn_monitor_toshy_services)
        monitor_toshy_services_thread.daemon = True
        monitor_toshy_services_thread.start()

    # Start separate thread to watch the internal state of settings
    monitor_internal_settings_thread = threading.Thread(target=fn_monitor_internal_settings)
    monitor_internal_settings_thread.daemon = True
    monitor_internal_settings_thread.start()

    if not barebones_config:
        # load the settings for the preferences submenu toggle items
        load_prefs_submenu_settings()
        # load the settings for the optspec layout submenu
        load_optspec_layout_submenu_settings()

    # GUI loop event
    loop = GLib.MainLoop()
    loop.run()
    # Gtk.main()


if __name__ == "__main__":
    # debug("")
    # debug(cnfg)       # prints out the __str__ method of Settings class
    handle_existing_process()
    write_pid_to_lockfile()
    main()

# debug(f'###  Exiting {TOSHY_PART_NAME}  ###\n')
