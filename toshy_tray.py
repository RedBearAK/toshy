#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Indicator tray icon menu app for Toshy, using pygobject/gi
TOSHY_PART      = 'tray'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Tray Icon app'
APP_VERSION     = '2023.0417'

# -------- COMMON COMPONENTS --------------------------------------------------

import os
import sys
import time
import dbus
import fcntl
import psutil
import signal
import select
import threading
import traceback
import subprocess

# Local imports
from lib.logger import *
from lib import logger
from lib.settings_class import Settings


logger.VERBOSE = True

if not str(sys.platform) == "linux":
    raise OSError("This app is designed to be run only on Linux")

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir = os.path.expanduser("~")
local_site_packages_dir = os.path.join(home_dir, f".local/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages")
# parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, local_site_packages_dir)
sys.path.insert(0, current_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{current_folder_path}:{local_site_packages_dir}:{existing_path}'


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
signal.signal(signal.SIGHUP,    signal_handler)
signal.signal(signal.SIGUSR1,   signal_handler)
signal.signal(signal.SIGUSR2,   signal_handler)
#########################################################################
# Let signal handler be defined and called before other things ^^^^^^^


USER_ID         = f'{os.getuid()}'
# support multiple simultaneous users via per-user temp folder
TOSHY_USER_TMP_DIR   = f'/tmp/toshy_uid{USER_ID}'

# PIPE_FILE_DIR   = f'{TOSHY_USER_TMP_DIR}/pipe'
# PIPE_FILE_NAME  = f'toshy_{TOSHY_PART}.pipe'
# PIPE_FILE       = os.path.join(PIPE_FILE_DIR, PIPE_FILE_NAME)

# if not os.path.exists(PIPE_FILE_DIR):
#     try:
#         os.makedirs(PIPE_FILE_DIR, mode=0o700, exist_ok=True)
#     except Exception as e:
#         debug(f'Problem creating pipe file directory: {PIPE_FILE_DIR}')
#         debug(e)

PREF_FILE_DIR   = f'{current_folder_path}'
PREF_FILE_NAME  = f'toshy_user_preferences.json'
PREF_FILE       = os.path.join(PREF_FILE_DIR, PREF_FILE_NAME)

# DB_FILE_DIR     = f'{current_folder_path}'
# DB_FILE_NAME    = f'toshy_user_preferences.sqlite'
# DB_FILE         = os.path.join(DB_FILE_DIR, DB_FILE_NAME)

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
    os.system(f'/usr/bin/chmod 0700 {TOSHY_USER_TMP_DIR}')
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


def check_notify_send():
    try:
        # Run the notify-send command with the -p flag
        subprocess.run(['notify-send', '-p'], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Check if the error message contains "Unknown option" for -p flag
        error_output: bytes = e.stderr  # type hint to validate decode()
        if 'Unknown option' in error_output.decode('utf-8'):
            return False
    return True


is_p_option_supported = check_notify_send()

ntfy_cmd        = '/usr/bin/notify-send'
ntfy_prio       = '--urgency=critical'
ntfy_icon       = f'--icon=\"{icon_file_active}\"'
ntfy_title      = 'Toshy Alert'
ntfy_id_new     = None
ntfy_id_last    = '0' # initiate with integer string to avoid error

user_sysctl     = '/usr/bin/systemctl --user'
sysctl_cmd      = '/usr/bin/systemctl'

toshy_svc_session_monitor   = 'toshy-session-monitor.service'
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
    global last_settings_list
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

    toshy_svc_config_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_config)
    toshy_svc_sessmon_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_session_monitor)

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
        # if _first_run:   # bypass sleep on first run to set icons faster
        #     _first_run = False
        # else:
        #     time.sleep(1)

        curr_svcs_state_tup = get_svc_states_dbus()

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

        #######################################################################
        ##  Original method of getting service status with subprocess.run
        #######################################################################
        # result_status_session_monitor = subprocess.run([
        #     sysctl_cmd, "--user", "is-active", toshy_svc_session_monitor
        # ], capture_output=True).stdout.decode().strip()
        # if result_status_session_monitor == "active":
        #     svc_status_session_monitor = svc_status_glyph_active
        # elif result_status_session_monitor == "inactive":
        #     svc_status_session_monitor = svc_status_glyph_inactive
        # else:
        #     svc_status_session_monitor = svc_status_glyph_unknown

        # result_status_toshy_config = subprocess.run([
        #     sysctl_cmd, "--user", "is-active", toshy_svc_session_monitor
        # ], capture_output=True).stdout.decode().strip()
        # if result_status_toshy_config == "active":
        #     svc_status_config = svc_status_glyph_active
        # elif result_status_toshy_config == "inactive":
        #     svc_status_config = svc_status_glyph_inactive
        # else:
        #     svc_status_config = svc_status_glyph_unknown

        # curr_svcs_state_tup = (
        #     result_status_session_monitor,
        #     result_status_toshy_config
        # )
        #######################################################################
        #######################################################################

        if curr_svcs_state_tup != last_svcs_state_tup:
            try:
                services_status_item.set_label(
                    f'      Toshy Config: {svc_status_config}\n\n  Session Monitor: {svc_status_sessmon}')
            except NameError: pass  # Let it pass if menu item not ready yet

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

        last_svcs_state_tup = curr_svcs_state_tup

        if last_settings_list != get_settings_list(cnfg):
            # debug(f'settings list changed...')
            last_settings_list = get_settings_list(cnfg)
            load_optspec_layout_submenu_settings()
            load_prefs_submenu_settings()

        time.sleep(2)



# -------- MENU ACTION FUNCTIONS ----------------------------------------------

# def fn_update_services_status_item_label():
#     # have to declare globals to be able to update them!
#     global svcs_status_config, svcs_status_session_monitor

#     result_status_session_monitor = subprocess.run([
#         sysctl_cmd, "--user", "is-active", toshy_svc_session_monitor
#     ], capture_output=True).stdout.decode().strip()
#     if result_status_session_monitor == "active":
#         svcs_status_session_monitor = svcs_glyph_active
#     elif result_status_session_monitor == "inactive":
#         svcs_status_session_monitor = svcs_glyph_inactive
#     else:
#         svcs_status_session_monitor = svcs_glyph_unknown

#     result_status_toshy_config = subprocess.run([
#         sysctl_cmd, "--user", "is-active", toshy_svc_session_monitor
#     ], capture_output=True).stdout.decode().strip()
#     if result_status_toshy_config == "active":
#         svcs_status_config = svcs_glyph_active
#     elif result_status_toshy_config == "inactive":
#         svcs_status_config = svcs_glyph_inactive
#     else:
#         svcs_status_config = svcs_glyph_unknown

#     try:
#         services_status_item.set_label(f'\nSession Monitor: {svcs_status_session_monitor}\n    Toshy Config: {svcs_status_config}')
#     except NameError: pass

def fn_restart_toshy_services(widget):
    """(Re)Start config service first, then session monitor"""
    os.system(f'{sysctl_cmd} --user restart {toshy_svc_config}')
    time.sleep(0.2)
    os.system(f'{sysctl_cmd} --user restart {toshy_svc_session_monitor}')
    time.sleep(0.2)
    _ntfy_icon = f'--icon={icon_file_active}'
    _ntfy_msg = 'Toshy systemd services (re)started.\nTap any modifier key before trying shortcuts.'

    if is_p_option_supported:
        global ntfy_id_last, ntfy_id_new
        ntfy_id_new = subprocess.run(
            [ntfy_cmd, ntfy_prio, _ntfy_icon, ntfy_title, _ntfy_msg, '-p','-r',ntfy_id_last], 
            stdout=subprocess.PIPE).stdout.decode().strip()
        ntfy_id_last = ntfy_id_new
    else:
        subprocess.run([ntfy_cmd, ntfy_prio, _ntfy_icon, ntfy_title, _ntfy_msg])

def fn_stop_toshy_services(widget):
    """Stop session monitor, then config service"""
    os.system(f'{sysctl_cmd} --user stop {toshy_svc_session_monitor}')
    time.sleep(0.2)
    os.system(f'{sysctl_cmd} --user stop {toshy_svc_config}')
    time.sleep(0.2)
    _ntfy_icon = f'--icon={icon_file_inverse}'
    _ntfy_msg = 'Toshy systemd services stopped.'

    if is_p_option_supported:
        global ntfy_id_last, ntfy_id_new
        ntfy_id_new = subprocess.run(
            [ntfy_cmd, ntfy_prio, _ntfy_icon, ntfy_title, _ntfy_msg, '-p','-r',ntfy_id_last], 
            stdout=subprocess.PIPE).stdout.decode().strip()
        ntfy_id_last = ntfy_id_new
    else:
        subprocess.run([ntfy_cmd, ntfy_prio, _ntfy_icon, ntfy_title, _ntfy_msg])

def fn_open_preferences(widget):
    subprocess.Popen(['python3', f'{current_folder_path}/toshy_gui.py'])

def fn_open_config_folder(widget):
    try:
        subprocess.Popen(['/usr/bin/xdg-open', current_folder_path])
    except FileNotFoundError as e:
        error('File not found. I have no idea how this error is possible.')
        error(e)

def fn_remove_tray_icon(widget):
    global loop
    remove_lockfile()
    loop.quit()
    os.system('/usr/bin/pkill -f "toshy_tray.py"')
    # Gtk.main_quit()
    sys.exit(0)

# -------- MENU ITEMS --------------------------------------------------

services_status_item = Gtk.MenuItem(label="Preparing status...")
services_status_item.set_sensitive(False)
menu.append(services_status_item)

separator_above_svcs_item = Gtk.SeparatorMenuItem()
menu.append(separator_above_svcs_item)  #-------------------------------------#

restart_toshy_item = Gtk.MenuItem(label="Re/Start Toshy Services")
restart_toshy_item.connect("activate", fn_restart_toshy_services)
menu.append(restart_toshy_item)

quit_toshy_item = Gtk.MenuItem(label="Stop Toshy Services")
quit_toshy_item.connect("activate", fn_stop_toshy_services)
menu.append(quit_toshy_item)

separator_below_svcs_item = Gtk.SeparatorMenuItem()
menu.append(separator_below_svcs_item)  #-------------------------------------#

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

# def load_optspec_layout_submenu_settings():
#     cnfg.load_settings()
#     for menu_item in optspec_layout_submenu.get_children():
#         layout = menu_item.get_label()
#         if layout == cnfg.optspec_layout:
#             menu_item.set_active(True)
#         else:
#             menu_item.set_active(False)

# def save_optspec_layout_setting(menu_item, layout):
#     if menu_item.get_active():
#         setattr(cnfg, 'optspec_layout', layout)
#         cnfg.save_settings()
#         load_optspec_layout_submenu_settings()

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

separator_above_remove_icon_item = Gtk.SeparatorMenuItem()
menu.append(separator_above_remove_icon_item)  #-------------------------------------#

remove_tray_icon_item = Gtk.MenuItem(label="Remove Icon from Tray")
remove_tray_icon_item.connect("activate", fn_remove_tray_icon)
menu.append(remove_tray_icon_item)

menu.show_all()


def main():
    # help out the config file user service
    subprocess.run(["systemctl", "--user", "import-environment", "XDG_SESSION_TYPE", "XDG_SESSION_DESKTOP", "XDG_CURRENT_DESKTOP"])    

    global loop
    # Start a separate thread to watch the status of Toshy systemd services (or script?)
    monitor_toshy_services_thread = threading.Thread(target=fn_monitor_toshy_services)
    monitor_toshy_services_thread.daemon = True
    monitor_toshy_services_thread.start()

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
