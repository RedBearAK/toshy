#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__version__ = '20240915'

# Indicator tray icon menu app for Toshy, using pygobject/gi
TOSHY_PART      = 'tray'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Tray Icon app'
APP_VERSION     = __version__

# -------- COMMON COMPONENTS --------------------------------------------------

import os
import re
import sys
try:
    import dbus
except ModuleNotFoundError:
    dbus = None
import time
import fcntl
import psutil
import shutil
import signal
import threading
# import traceback
import subprocess

from subprocess import DEVNULL
from typing import List, Dict, Tuple

# Local imports
import lib.env as env

from lib.env_context import EnvironmentInfo
from lib.logger import *
from lib import logger
from lib.settings_class import Settings

logger.FLUSH        = True
logger.VERBOSE      = True

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
RUN_TMP_DIR                     = os.environ.get('XDG_RUNTIME_DIR', f'/tmp/toshy_uid{USER_ID}')
TOSHY_RUN_TMP_DIR               = os.path.join(RUN_TMP_DIR, 'toshy_runtime_cache')

LOCK_FILE_DIR                   = f'{TOSHY_RUN_TMP_DIR}/lock'
LOCK_FILE_NAME                  = f'toshy_{TOSHY_PART}.lock'
LOCK_FILE                       = os.path.join(LOCK_FILE_DIR, LOCK_FILE_NAME)

if not os.path.exists(LOCK_FILE_DIR):
    try:
        os.makedirs(LOCK_FILE_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        error(f'NON-FATAL: Problem creating lockfile directory: {LOCK_FILE_DIR}')
        error(e)

# recursively set user's Toshy temp folder as only read/write by owner
try:
    chmod_cmd = shutil.which('chmod')
    os.system(f'{chmod_cmd} 0700 {TOSHY_RUN_TMP_DIR}')
except Exception as e:
    error(f'NON-FATAL: Problem when setting permissions on temp folder.')
    error(e)

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

# assets_path         = os.path.join(current_folder_path, 'assets')
# icon_file_active    = os.path.join(assets_path, "toshy_app_icon_rainbow.svg")
# icon_file_grayscale = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse_grayscale.svg")
# icon_file_inverse   = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse.svg")

# Fix for Solus Budgie failing to show proper icons when using full path. Use base file name string.
# Icon files will all be copied into the local-share-icons location to make this work. 
icon_file_active                = "toshy_app_icon_rainbow"
icon_file_grayscale             = "toshy_app_icon_rainbow_inverse_grayscale"
icon_file_inverse               = "toshy_app_icon_rainbow_inverse"

loop = None

# Settings class object setup
config_dir_path = current_folder_path
cnfg = Settings(config_dir_path)
cnfg.watch_database()   # start watching the preferences file for changes

# Notification handler object setup
from lib.notification_manager import NotificationManager
ntfy = NotificationManager(icon_file_active, title='Toshy Alert (Tray)')


def is_init_systemd():
    try:
        with open("/proc/1/comm", "r") as f:
            return f.read().strip() == 'systemd'
    except FileNotFoundError:
        print("Toshy_Tray: The /proc/1/comm file does not exist.")
        return False
    except PermissionError:
        print("Toshy_Tray: Permission denied when trying to read the /proc/1/comm file.")
        return False


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
            load_prefs_submenu_settings()
            load_optspec_layout_submenu_settings()
            load_kbtype_submenu_settings()


sysctl_cmd      = f"{shutil.which('systemctl')}"
user_sysctl     = f'{sysctl_cmd} --user'

toshy_svc_sessmon               = 'toshy-session-monitor.service'
toshy_svc_config                = 'toshy-config.service'
toshy_svc_kde_dbus              = 'toshy-kde-dbus.service'

svc_status_sessmon              = '???'              #  ❓  # 'Undefined'
svc_status_config               = '???'              #  ❓  # 'Undefined'

svc_status_glyph_active         = 'Active'               #  ✅  #  😀  #
svc_status_glyph_inactive       = 'Inactive'              #  ❌  #  ⏸  #  🛑  #
svc_status_glyph_unknown        = 'Unknown'              #  ❓  #  ❔  #


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
    if dbus is None:
        error('The "dbus" module is not available. Cannot monitor services.')
        return

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
                # debug(f'TOSHY_TRAY: DBusException trying to get proxies:\n\t{dbus_err}')
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
            config_label_text = f'       Config: {svc_status_config}'
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
    _ntfy_msg = 'Toshy systemd services (re)started.\nIn X11, tap a modifier key before trying shortcuts.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


def fn_stop_toshy_services(widget):
    """Stop Toshy services with CLI command"""
    toshy_svcs_stop_cmd = os.path.join(home_local_bin, 'toshy-services-stop')
    subprocess.Popen([toshy_svcs_stop_cmd], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(3)
    _ntfy_icon_file = icon_file_inverse
    _ntfy_msg = 'Toshy systemd services stopped.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


def fn_restart_toshy_config_only(widget):
    """Start the manual run config script"""
    toshy_cfg_restart_cmd = os.path.join(home_local_bin, 'toshy-config-restart')
    subprocess.Popen([toshy_cfg_restart_cmd], stdout=DEVNULL, stderr=DEVNULL)


def fn_stop_toshy_config_only(widget):
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


def run_cmd_lst_in_terminal(command_list: List[str]):
    """Give a command composed of a list of strings to a terminal emulator app 
        that may be appropriate for the environment, using different techniques to 
        determine which terminal emulator app might be the most correct."""

    # Check if command_list is a list of strings
    if not isinstance(command_list, list) or not all(isinstance(item, str) for item in command_list):
        debug('The function run_cmd_lst_in_terminal() expects a list of strings.')
        return

    # List of common terminal emulators in descending order of commonness.
    # Each element is a tuple composed of: 
    # (terminal command name, option used to pass a command to shell, DE list)
    # Each terminal app option can be associated with multiple DEs to 
    # somewhat intelligently use the "correct" terminal for a DE. 
    terminal_apps_lst_of_tup: List[Tuple[str, List[str], ]] = [
        ('gnome-terminal',      ['--'],     ['gnome', 'unity', 'cinnamon']              ),
        ('konsole',             ['-e'],     ['kde']                                     ),
        ('xfce4-terminal',      ['-e'],     ['xfce']                                    ),
        ('mate-terminal',       ['-e'],     ['mate']                                    ),
        ('qterminal',           ['-e'],     ['lxqt']                                    ),
        ('lxterminal',          ['-e'],     ['lxde']                                    ),
        ('terminology',         ['-e'],     ['enlightenment']                           ),
        ('cosmic-term',         ['-e'],     ['cosmic']                                  ),
        ('kitty',               ['-e'],     []                                          ),
        ('alacritty',           ['-e'],     []                                          ),
        ('tilix',               ['-e'],     []                                          ),
        ('terminator',          ['-e'],     []                                          ),
        ('xterm',               ['-e'],     []                                          ),
        ('rxvt',                ['-e'],     []                                          ),
        ('urxvt',               ['-e'],     []                                          ),
        ('st',                  ['-e'],     []                                          ),
        # 'kgx' is short for "King's Cross" and represents GNOME Console
        ('kgx',                 ['-e'],     []                                          ),
    ]

    def _run_cmd_lst_in_term(term_app_cmd_path, term_app_args_lst, command_list: List[str]):
        """Utility closure function to actually run the command in a specific terminal"""
        if term_app_cmd_path is None:
            return False
        cmd_lst_for_Popen: List[str] = [term_app_cmd_path] + term_app_args_lst + command_list
        try:
            # run the terminal emulator and give it the provided command list argument
            subprocess.Popen(cmd_lst_for_Popen)
            return True
        except subprocess.SubprocessError as proc_err:
            debug(f'Error opening terminal to run command list:\n\t{proc_err}')
            return False

    term_app_cmd_path = None

    # Try to find a matching terminal for the current desktop environment first
    for terminal_app_cmd, term_app_args_lst, *DE_lst in terminal_apps_lst_of_tup:
        # DE list element will be inside another list due to the unpacking syntax!
        desktop_env_lst = DE_lst[0] if DE_lst else ['no_specific_de']
        if DESKTOP_ENV in desktop_env_lst:
            term_app_cmd_path = shutil.which(terminal_app_cmd)
        if _run_cmd_lst_in_term(term_app_cmd_path, term_app_args_lst, command_list):
            return

    # If no DE-specific terminal is found, iterate through the list again without DE consideration
    for terminal_app_cmd, term_app_args_lst, *_ in terminal_apps_lst_of_tup:
        term_app_cmd_path = shutil.which(terminal_app_cmd)
        if _run_cmd_lst_in_term(term_app_cmd_path, term_app_args_lst, command_list):
            return

    ntfy_icon_file = icon_file_inverse  # predefined path to icon file
    ntfy_msg = "ERROR: No suitable terminal emulator could be opened."
    ntfy.send_notification(ntfy_msg, ntfy_icon_file)
    debug(f'{ntfy_msg}')


def fn_show_services_log(widget):
    run_cmd_lst_in_terminal(['toshy-services-log'])


def fn_remove_tray_icon(widget):
    global loop
    remove_lockfile()
    loop.quit()
    pkill_cmd = shutil.which('pkill')
    os.system(f'{pkill_cmd} -f "toshy_tray.py"')
    # Gtk.main_quit()
    sys.exit(0)


def set_item_active_with_retry(menu_item, state=True, max_retries=5):
    """Attempt to set the menu item's active state with retries."""

    # This function is necessary to set the items active state when another app changes the setting.
    for _ in range(max_retries):
        menu_item.set_active(state)
        time.sleep(0.1)
        if menu_item.get_active() == state:
            return
        time.sleep(0.1)
    if not menu_item.get_active() == state:
        error(f"ERROR: Failed to set item '{menu_item.get_label()}' to state '{state}'.")


# -------- MENU ITEMS --------------------------------------------------

services_label_item = Gtk.MenuItem(label=" ---- Services Status ---- ")
services_label_item.set_sensitive(False)
menu.append(services_label_item)

toshy_config_status_item = Gtk.MenuItem(    label="      Config: (?)")
toshy_config_status_item.set_sensitive(False)
menu.append(toshy_config_status_item)

session_monitor_status_item = Gtk.MenuItem( label="     SessMon: (?)")
session_monitor_status_item.set_sensitive(False)
menu.append(session_monitor_status_item)


def is_service_enabled(service_name):
    """Check if a user service is enabled using systemctl."""

    if shutil.which('systemctl') and is_init_systemd():
        pass
    else:
        # If either 'systemctl' is missing or init is not 'systemd', just return False
        return False

    is_enabled_cmd_lst = ["systemctl", "--user", "is-enabled"]

    try:
        subprocess.run(is_enabled_cmd_lst + [service_name],
                        check=True, stdout=DEVNULL, stderr=DEVNULL)
        return True  # is-enabled succeeds
    except subprocess.CalledProcessError:
        return False  # is-enabled fails, service is disabled or not found


toshy_svc_config_unit_enabled   = is_service_enabled("toshy-config.service")
toshy_svc_sessmon_unit_enabled  = is_service_enabled("toshy-session-monitor.service")


def fn_toggle_toshy_svcs_autostart(widget):
    """Check the status of Toshy services, flip the status, change the menu item label"""
    global toshy_svc_config_unit_enabled, toshy_svc_sessmon_unit_enabled

    if shutil.which('systemctl') and is_init_systemd():
        pass
    else:
        # If either 'systemctl' is missing or init is not 'systemd', immediately return
        return

    try:
        if widget.get_active():
            # Enable user services
            enable_cmd_lst = ["systemctl", "--user", "enable"]
            subprocess.run(enable_cmd_lst + [toshy_svc_sessmon], check=True)
            subprocess.run(enable_cmd_lst + [toshy_svc_kde_dbus], check=True)
            subprocess.run(enable_cmd_lst + [toshy_svc_config], check=True)
            debug("Toshy systemd services enabled. Will autostart at login.")
            _ntfy_icon_file = icon_file_active
            _ntfy_msg = ('Toshy systemd services are ENABLED.\n'
                            'Toshy will start at login.')
        else:
            # Disable user services
            disable_cmd_lst = ["systemctl", "--user", "disable"]
            subprocess.run(disable_cmd_lst + [toshy_svc_config], check=True)
            subprocess.run(disable_cmd_lst + [toshy_svc_kde_dbus], check=True)
            subprocess.run(disable_cmd_lst + [toshy_svc_sessmon], check=True)
            debug("Toshy systemd services disabled. Will NOT autostart at login.")
            _ntfy_icon_file = icon_file_grayscale
            _ntfy_msg = ('Toshy systemd services are DISABLED.\n'
                            'Toshy will NOT start at login.')
    except subprocess.CalledProcessError as proc_err:
        debug(f"Error toggling Toshy systemd user services: {proc_err}")

    time.sleep(0.5)
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


autostart_toshy_svcs_item = Gtk.CheckMenuItem(label="Autostart Toshy Services")
autostart_toshy_svcs_item.set_active(   toshy_svc_sessmon_unit_enabled and 
                                        toshy_svc_config_unit_enabled       )
autostart_toshy_svcs_item.connect("toggled", fn_toggle_toshy_svcs_autostart)
menu.append(autostart_toshy_svcs_item)

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

restart_toshy_script_item = Gtk.MenuItem(label="Re/Start Config-Only")
restart_toshy_script_item.connect("activate", fn_restart_toshy_config_only)
menu.append(restart_toshy_script_item)

stop_toshy_script_item = Gtk.MenuItem(label="Stop Config-Only")
stop_toshy_script_item.connect("activate", fn_stop_toshy_config_only)
menu.append(stop_toshy_script_item)

separator_below_script_item = Gtk.SeparatorMenuItem()
menu.append(separator_below_script_item)  #-------------------------------------#

if not barebones_config:

    def load_prefs_submenu_settings():
        cnfg.load_settings()
        set_item_active_with_retry(forced_numpad_item, cnfg.forced_numpad)
        set_item_active_with_retry(media_arrows_fix_item, cnfg.media_arrows_fix)
        set_item_active_with_retry(multi_lang_item, cnfg.multi_lang)
        set_item_active_with_retry(ST3_in_VSCode_item, cnfg.ST3_in_VSCode)
        set_item_active_with_retry(Caps2Cmd_item, cnfg.Caps2Cmd)
        set_item_active_with_retry(Caps2Esc_Cmd_item, cnfg.Caps2Esc_Cmd)
        set_item_active_with_retry(Enter2Ent_Cmd_item, cnfg.Enter2Ent_Cmd)

    def save_prefs_settings(widget):
        cnfg.forced_numpad      = forced_numpad_item.get_active()
        cnfg.media_arrows_fix   = media_arrows_fix_item.get_active()
        cnfg.multi_lang         = multi_lang_item.get_active()
        cnfg.ST3_in_VSCode      = ST3_in_VSCode_item.get_active()
        cnfg.Caps2Cmd           = Caps2Cmd_item.get_active()
        cnfg.Caps2Esc_Cmd       = Caps2Esc_Cmd_item.get_active()
        cnfg.Enter2Ent_Cmd      = Enter2Ent_Cmd_item.get_active()
        cnfg.save_settings()
        GLib.idle_add(load_prefs_submenu_settings)  # Queue the update to run in GTK's main loop

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
        layout = cnfg.optspec_layout
        if   layout == 'US':            set_item_active_with_retry(optspec_us_item, True)
        elif layout == 'ABC':           set_item_active_with_retry(optspec_abc_extended_item, True)
        elif layout == 'Disabled':      set_item_active_with_retry(optspec_disabled_item, True)

    def save_optspec_layout_setting(menu_item, layout):
        if not menu_item.get_active():
            return
        
        cnfg.optspec_layout = layout
        cnfg.save_settings()
        load_optspec_layout_submenu_settings()

    # OptSpec layout submenu
    optspec_layout_submenu = Gtk.Menu()
    optspec_layout_item = Gtk.MenuItem(label='OptSpec Layout')
    optspec_layout_item.set_submenu(optspec_layout_submenu)
    menu.append(optspec_layout_item)

    # Create submenu items using RadioMenuItem
    group_optspec = None
    optspec_us_item = Gtk.RadioMenuItem.new_with_label(group_optspec, 'US')
    optspec_us_item.connect('toggled', save_optspec_layout_setting, 'US')
    optspec_layout_submenu.append(optspec_us_item)
    group_optspec = optspec_us_item.get_group()

    optspec_abc_extended_item = Gtk.RadioMenuItem.new_with_label(group_optspec, 'ABC Extended')
    optspec_abc_extended_item.connect('toggled', save_optspec_layout_setting, 'ABC')
    optspec_layout_submenu.append(optspec_abc_extended_item)

    optspec_disabled_item = Gtk.RadioMenuItem.new_with_label(group_optspec, 'Disabled*')
    optspec_disabled_item.connect('toggled', save_optspec_layout_setting, 'Disabled')
    optspec_layout_submenu.append(optspec_disabled_item)


    def load_kbtype_submenu_settings():
        cnfg.load_settings()
        kbtype = cnfg.override_kbtype
        if kbtype == 'Auto-Adapt':      set_item_active_with_retry(kbtype_auto_adapt_item, True)
        elif kbtype == 'Apple':         set_item_active_with_retry(kbtype_apple_item, True)
        elif kbtype == 'Chromebook':    set_item_active_with_retry(kbtype_chromebook_item, True)
        elif kbtype == 'IBM':           set_item_active_with_retry(kbtype_ibm_item, True)
        elif kbtype == 'Windows':       set_item_active_with_retry(kbtype_windows_item, True)

    def save_kbtype_setting(menu_item, kbtype):
        if not menu_item.get_active():
            return
        
        cnfg.override_kbtype = kbtype
        cnfg.save_settings()

        GLib.idle_add(load_kbtype_submenu_settings)

        valid_kbtypes = ['IBM', 'Chromebook', 'Windows', 'Apple']
        if cnfg.override_kbtype in valid_kbtypes:
            message = ('Overriding keyboard type disables auto-adaptation.\r'
                    'This is meant as a temporary fix only! See README.')
            ntfy.send_notification(message, icon_file_grayscale, urgency='critical')

    ###############################################################
    # Keyboard Type submenu
    kbtype_submenu = Gtk.Menu()
    kbtype_item = Gtk.MenuItem(label='Keyboard Type')
    kbtype_item.set_submenu(kbtype_submenu)
    menu.append(kbtype_item)

    # create submenu items using RadioMenuItem
    group_kbtype = None
    kbtype_auto_adapt_item = Gtk.RadioMenuItem.new_with_label(group_kbtype, 'Auto-Adapt*')
    kbtype_auto_adapt_item.connect('toggled', save_kbtype_setting, 'Auto-Adapt')
    kbtype_submenu.append(kbtype_auto_adapt_item)
    group_kbtype = kbtype_auto_adapt_item.get_group()

    kbtype_apple_item = Gtk.RadioMenuItem.new_with_label(group_kbtype, 'Apple')
    kbtype_apple_item.connect('toggled', save_kbtype_setting, 'Apple')
    kbtype_submenu.append(kbtype_apple_item)

    kbtype_chromebook_item = Gtk.RadioMenuItem.new_with_label(group_kbtype, 'Chromebook')
    kbtype_chromebook_item.connect('toggled', save_kbtype_setting, 'Chromebook')
    kbtype_submenu.append(kbtype_chromebook_item)

    kbtype_ibm_item = Gtk.RadioMenuItem.new_with_label(group_kbtype, 'IBM')
    kbtype_ibm_item.connect('toggled', save_kbtype_setting, 'IBM')
    kbtype_submenu.append(kbtype_ibm_item)

    kbtype_windows_item = Gtk.RadioMenuItem.new_with_label(group_kbtype, 'Windows')
    kbtype_windows_item.connect('toggled', save_kbtype_setting, 'Windows')
    kbtype_submenu.append(kbtype_windows_item)

    separator_below_kbtype_submenu_item = Gtk.SeparatorMenuItem()
    menu.append(separator_below_kbtype_submenu_item)  #-------------------------------------#

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


def load_autostart_tray_icon_setting():
    cnfg.load_settings()
    # set_item_active_with_retry(autostart_tray_icon_item, cnfg.autostart_tray_icon)


def fn_save_autostart_tray_icon_setting(widget):
    autostart_tray_icon_bool    = widget.get_active()
    # debug(f'{autostart_tray_icon_setting = }')
    cnfg.autostart_tray_icon    = autostart_tray_icon_bool
    cnfg.save_settings()
    load_autostart_tray_icon_setting()

    tray_dt_file_name           = 'Toshy_Tray.desktop'
    home_apps_path              = os.path.join(home_dir, '.local', 'share', 'applications')
    tray_dt_file_path           = os.path.join(home_apps_path, tray_dt_file_name)

    home_autostart_path         = os.path.join(home_dir, '.config', 'autostart')
    tray_link_file_path         = os.path.join(home_autostart_path, tray_dt_file_name)

    if autostart_tray_icon_bool:
        # do the enabling of tray icon autostart:
        # create symlink file ~/.config/autostart/Toshy_Tray.desktop
        #   with target file ~/.local/share/applications/Toshy_Tray.desktop
        # alternative: os.symlink(source, dest, target_is_directory=False)
        cmd_lst = ['ln', '-sf', tray_dt_file_path, tray_link_file_path]
        try:
            subprocess.run(cmd_lst, check=True) #, stdout=DEVNULL, stderr=DEVNULL)
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem enabling tray icon autostart:\n\t{proc_err}')
    else:
        # do the disabling of tray icon autostart:
        # remove the symlink file ~/.config/autostart/Toshy_Tray.desktop
        # alternative: os.remove(path) or os.unlink(path)
        cmd_lst = ['rm', '-f', tray_link_file_path]
        try:
            subprocess.run(cmd_lst, check=True) # , stdout=DEVNULL, stderr=DEVNULL)
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem disabling tray icon autostart:\n\t{proc_err}')


autostart_tray_icon_item = Gtk.CheckMenuItem(label="Autostart Tray Icon")
autostart_tray_icon_item.set_active(cnfg.autostart_tray_icon)
autostart_tray_icon_item.connect("toggled", fn_save_autostart_tray_icon_setting)
menu.append(autostart_tray_icon_item)

remove_tray_icon_item = Gtk.MenuItem(label="Remove Icon from Tray")
remove_tray_icon_item.connect("activate", fn_remove_tray_icon)
menu.append(remove_tray_icon_item)

menu.show_all()


def main():

    global loop
    global DESKTOP_ENV
    # env_info_dct   = env.get_env_info()
    env_ctxt_getter = EnvironmentInfo()
    env_info_dct   = env_ctxt_getter.get_env_info()
    DESKTOP_ENV = str(env_info_dct.get('DESKTOP_ENV', None)).casefold()

    if shutil.which('systemctl') and is_init_systemd():
        # help out the config file user service
        cmd_lst = [
            "systemctl", "--user", "import-environment",
            "KDE_SESSION_VERSION",
            "PATH",
            "XDG_SESSION_TYPE",
            "XDG_SESSION_DESKTOP",
            "XDG_CURRENT_DESKTOP",
            "DESKTOP_SESSION",
            "DISPLAY",
            "WAYLAND_DISPLAY",
        ]
        subprocess.run(cmd_lst)
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
        # load the settings for the keyboard type submenu
        load_kbtype_submenu_settings()
        # load the setting for the autostart tray icon item
        load_autostart_tray_icon_setting()

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
