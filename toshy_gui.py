#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Preferences app for Toshy, using tkinter GUI and "Sun Valley" theme
TOSHY_PART      = 'gui'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Preferences app'  # pretty name to print out
APP_VERSION     = '2023.0816'

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
import subprocess
from subprocess import DEVNULL

# Local imports
from lib.logger import *
from lib import logger
from lib.settings_class import Settings


logger.VERBOSE = False

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

PIPE_FILE_DIR   = f'{TOSHY_USER_TMP_DIR}/pipe'
PIPE_FILE_NAME  = f'toshy_{TOSHY_PART}.pipe'
PIPE_FILE       = os.path.join(PIPE_FILE_DIR, PIPE_FILE_NAME)

if not os.path.exists(PIPE_FILE_DIR):
    try:
        os.makedirs(PIPE_FILE_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        error(f'Problem creating pipe file directory: {PIPE_FILE_DIR}')
        error(e)

PREF_FILE_DIR   = f'{current_folder_path}'
PREF_FILE_NAME  = f'toshy_user_preferences.json'
PREF_FILE       = os.path.join(PREF_FILE_DIR, PREF_FILE_NAME)

DB_FILE_DIR     = f'{current_folder_path}'
DB_FILE_NAME    = f'toshy_user_preferences.sqlite'
DB_FILE         = os.path.join(DB_FILE_DIR, DB_FILE_NAME)

LOCK_FILE_DIR   = f'{TOSHY_USER_TMP_DIR}/lock'
LOCK_FILE_NAME  = f'toshy_{TOSHY_PART}.lock'
LOCK_FILE       = os.path.join(LOCK_FILE_DIR, LOCK_FILE_NAME)

if not os.path.exists(LOCK_FILE_DIR):
    try:
        os.makedirs(LOCK_FILE_DIR, mode=0o700, exist_ok=True)
    except Exception as e:
        error(f'NON-FATAL: Problem creating lockfile directory: {LOCK_FILE_DIR}')
        error(e)

# recursively set user's Toshy temp folder as only read/write by owner
try:
    chmod_cmd = shutil.which('chmod')
    os.system(f'{chmod_cmd} 0700 {TOSHY_USER_TMP_DIR}')
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
        debug(f'NON-FATAL: No existing lockfile or lockfile could not be read:')
        debug(e)
        return None

def write_pid_to_lockfile():
    try:
        with open(LOCK_FILE, 'w') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.write(str(os.getpid()))
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
    except (IOError, ValueError, PermissionError) as e:
        error(f'NON-FATAL: Problem writing PID to lockfile:')
        error(e)

def remove_lockfile():
    try:
        os.unlink(LOCK_FILE)
        debug(f'Lockfile removed.')
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
# -------- TOSHY PREFERENCES GUI SPECIFIC COMPONENTS --------------------------
###############################################################################


# Define some globals for the commands run by menu items

assets_path         = os.path.join(current_folder_path, 'assets')
icon_file_active    = os.path.join(assets_path, "toshy_app_icon_rainbow.svg")
icon_file_grayscale = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse_grayscale.svg")
icon_file_inverse   = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse.svg")


config_dir_path = current_folder_path
cnfg = Settings(config_dir_path)
cnfg.watch_database()
debug("")
debug(cnfg)   # prints out the __str__ method of Settings class

# Notification handler object setup
from lib.notification_manager import NotificationManager
ntfy = NotificationManager(icon_file_active, title='Toshy Alert (GUI)')


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
            # debug(f'Updating GUI preferences switch settings...')
            load_radio_btn_settings(cnfg, optspec_var, "optspec_layout")
            load_switch_settings(cnfg)
            last_settings_list = get_settings_list(cnfg)


sysctl_cmd      = f"{shutil.which('systemctl')}"
user_sysctl     = f'{sysctl_cmd} --user'

toshy_svc_sessmon   = 'toshy-session-monitor.service'
toshy_svc_config    = 'toshy-config.service'

svc_status_sessmon          = 'Unknown '              # 'Undefined'
svc_status_config           = 'Unknown '              # 'Undefined'

svc_status_glyph_active     = 'Active  '              # 😀 ✅  #
svc_status_glyph_inactive   = 'Inactive'              # ❌ ⏸ 🛑 #
svc_status_glyph_unknown    = 'Unknown '              # ❔  #


def fn_monitor_toshy_services():
    # debug('')
    # debug(f'Entering GUI monitoring function...')
    global svc_status_config, svc_status_sessmon
    toshy_svc_config_unit_state     = None
    toshy_svc_config_unit_path      = None
    toshy_svc_sessmon_unit_state    = None
    toshy_svc_sessmon_unit_path     = None
    last_svcs_state_tup             = (None, None)
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

    # Deal with the possibility that the services are not installed
    while not toshy_svc_sessmon_unit_path and not toshy_svc_config_unit_path:
        try:
            toshy_svc_config_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_config)
            toshy_svc_sessmon_unit_path = systemd1_mgr_iface.GetUnit(toshy_svc_sessmon)
        except dbus.exceptions.DBusException as e:
            debug("DBusException: {}".format(str(e)))

        if toshy_svc_sessmon_unit_path and toshy_svc_config_unit_path:
            break
        else:
            time.sleep(5)


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

    time.sleep(0.1)   # wait a bit before starting the loop

    while True:

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

        if curr_svcs_state_tup != last_svcs_state_tup:
            try:
                svc_status_lbl_config.config(   text=f'Toshy Config: {svc_status_config}')
                svc_status_lbl_sessmon.config(  text=f'Session Monitor: {svc_status_sessmon} ')
            except NameError: pass  # Let it pass if menu item not ready yet

        last_svcs_state_tup = curr_svcs_state_tup

        time.sleep(1)     # pause before next loop cycle


def fn_restart_toshy_services():
    """(Re)Start Toshy services with CLI command"""
    toshy_svcs_restart_cmd = os.path.join(home_local_bin, 'toshy-services-restart')
    subprocess.Popen([toshy_svcs_restart_cmd], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(3)
    _ntfy_icon_file = icon_file_active
    _ntfy_msg = 'Toshy systemd services (re)started.\nTap any modifier key before trying shortcuts.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


def fn_stop_toshy_services():
    """Stop Toshy services with CLI command"""
    toshy_svcs_stop_cmd = os.path.join(home_local_bin, 'toshy-services-stop')
    subprocess.Popen([toshy_svcs_stop_cmd], stdout=DEVNULL, stderr=DEVNULL)
    time.sleep(3)
    _ntfy_icon_file = icon_file_inverse
    _ntfy_msg = 'Toshy systemd services stopped.'
    ntfy.send_notification(_ntfy_msg, _ntfy_icon_file)


####################################################
# Start setting up the tkinter GUI window

import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import sv_ttk   # "Sun Valley" tkinter theme module

# CentOS 7 can't handle the PNG icon file, so use Pillow to open it
from PIL import Image, ImageTk

TOSHY_GUI_APP_CLASSNAME = 'Toshy-Prefs'


# className is what appears in task switcher (only first letter will be capitalized)
root = tk.Tk(className=f'{TOSHY_GUI_APP_CLASSNAME}') # tkinter window object instantiated, now put stuff in it
# Set what displays in the window title bar (not in task switcher)
root.title("Toshy Preferences")
# Set WM_CLASS for additional Toplevel windows
root.option_add("*Toplevel.className", f'{TOSHY_GUI_APP_CLASSNAME}')

root.config(padx=20, pady=20)

# screen_width = root.winfo_screenwidth()
# screen_height = root.winfo_screenheight()

# offset_x = screen_width     // 5    if screen_width     > 1900      else screen_width // 10
# offset_y = screen_height    // 10   if screen_height    > 1000      else screen_height // 20

# root.geometry(f'-{offset_x}+{offset_y}')

# Give tkinter window a nice icon 
# (desktop entry file shows nice icon in launcher but doesn't set icon in task switcher)
icon_file = os.path.join(current_folder_path, 'assets', 'toshy_app_icon_rainbow_512px.png')

# app_icon_image_path = tk.PhotoImage(file = icon_file)
# root.wm_iconphoto(False, app_icon_image_path)

# Use Pillow to open the image, to make it work on CentOS 7
image = Image.open(icon_file)
app_icon_image = ImageTk.PhotoImage(image)
root.wm_iconphoto(False, app_icon_image)

# Set a font style to use for switch text
switch_text_font_dict = {"family": "Helvetica", "size": 13}
sw_txt_font = tkfont.Font(**switch_text_font_dict)

# Set a font style to use for switch description labels
switch_label_font_dict = {"family": "Helvetica", "size": 12, "slant": "italic"}
sw_lbl_font = tkfont.Font(**switch_label_font_dict)
sw_lbl_font_color = 'gray'

# adjustments for switch description labels
sw_lbl_indent   = 50
btn_lbl_pady     = (0, 10)
sw_padx         = 0
btn_pady         = 0
wrap_len        = 380


####################################################
# Define functions for widgets actions to engage


def save_radio_settings(cnfg: Settings, var: tk.StringVar, key: str):
    setattr(cnfg, key, var.get())
    cnfg.save_settings()


def save_switch_settings(cnfg: Settings, var: tk.BooleanVar, key: str):
    setattr(cnfg, key, var.get())
    cnfg.save_settings()


def load_radio_btn_settings(cnfg: Settings, var: tk.StringVar, key: str):
    value = getattr(cnfg, key)
    var.set(value)


def load_switch_settings(cnfg: Settings):
    forced_numpad_switch_var.set(       cnfg.forced_numpad)
    media_arrows_fix_switch_var.set(    cnfg.media_arrows_fix)
    multi_lang_switch_var.set(          cnfg.multi_lang)
    ST3_in_VSCode_switch_var.set(       cnfg.ST3_in_VSCode)
    Caps2Cmd_switch_var.set(            cnfg.Caps2Cmd)
    Caps2Esc_Cmd_switch_var.set(        cnfg.Caps2Esc_Cmd)
    Enter2Ent_Cmd_switch_var.set(       cnfg.Enter2Ent_Cmd)
    theme_switch_var.set(               cnfg.gui_dark_theme)
    update_theme()


def update_theme():
    # set "Sun Valley" theme variant (not really sure about the best place to do this)
    if cnfg.gui_dark_theme:
        sv_ttk.set_theme('dark')
    else:
        sv_ttk.set_theme('light')


##########################
# Define columns/frames

top_frame = tk.Frame(root) #, width=900, highlightbackground='dim gray', highlightthickness=1)
top_frame.pack(anchor=tk.N, side=tk.TOP, expand=True, fill=tk.BOTH, pady=(0, 20), ipady=4, ipadx=4)

top_frame_left_column = tk.Frame(top_frame, width=400) #, highlightbackground='dim gray', highlightthickness=1)
top_frame_left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=4, ipadx=4) #, expand=False)
# top_frame_left_column.pack_propagate(False)

top_frame_middle_column = tk.Frame(top_frame) #, highlightbackground='dim gray', highlightthickness=1)
top_frame_middle_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=20, ipadx=20)
# top_frame_middle_column.pack_propagate(False)

top_frame_right_column = tk.Frame(top_frame, width=400) #, highlightbackground='dim gray', highlightthickness=1)
top_frame_right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, ipady=4, ipadx=4) #, expand=False)
# top_frame_right_column.pack_propagate(False)

# Create a new frame to hold all the other frames
middle_frame = tk.Frame(root)
middle_frame.pack(side=tk.TOP, fill=tk.BOTH)

left_column = tk.Frame(middle_frame) #, highlightbackground='dim gray', highlightthickness=1)#, bg='red', bd=5)
left_column.pack(side=tk.LEFT, fill=tk.BOTH)

left_column_low_spacer = tk.Frame(left_column) #, highlightbackground='gray', highlightthickness=1)
# push elements in left column up, leaving "space" below
left_column_low_spacer.pack(side=tk.BOTTOM, fill=tk.BOTH, ipady=30)

mid_center_column = tk.Frame(middle_frame) #, highlightbackground='dim gray', highlightthickness=1)
mid_center_column.pack(side=tk.LEFT, fill=tk.BOTH, ipadx=1)

mid_right_column = tk.Frame(middle_frame) #, highlightbackground='gray', highlightthickness=1)
mid_right_column.pack(side=tk.LEFT, fill=tk.BOTH)


###########################
# Widgets

# Top frame stuff

# Set a font style to use for service description labels
svc_lbl_font_dict = {"family": "monospace", "size": 12, "weight": "bold"}
svc_lbl_font_color = 'gray'
svc_lbl_font = tkfont.Font(**svc_lbl_font_dict)

services_label = tk.Label(
    top_frame_left_column,
    justify=tk.CENTER,
    text=('Toshy Services Status:   '),
    font=svc_lbl_font
)
services_label.pack(padx=sw_lbl_indent, pady=btn_lbl_pady)

svc_status_lbl_config = tk.Label(
    top_frame_left_column,
    justify=tk.CENTER,
    text=(  f'Toshy Config: {svc_status_config}' ),
    font=svc_lbl_font,
    fg=svc_lbl_font_color
)
svc_status_lbl_config.pack(anchor=tk.N, padx=sw_lbl_indent, pady=btn_lbl_pady)

svc_status_lbl_sessmon = tk.Label(
    top_frame_left_column,
    justify=tk.CENTER,
    text=(  f'Session Monitor: {svc_status_sessmon} ' ),
    font=svc_lbl_font,
    fg=svc_lbl_font_color
)
svc_status_lbl_sessmon.pack(anchor=tk.N, padx=sw_lbl_indent, pady=btn_lbl_pady)

svc_btn_pady = 12
# svc_btn_padx = 10

svc_status_config_btn = ttk.Button(
    top_frame_right_column,
    width=25,
    text='(Re)Start Toshy Services',
    command=fn_restart_toshy_services
)
svc_status_config_btn.pack(anchor=tk.W, padx=sw_lbl_indent, pady=svc_btn_pady)

svc_status_sessmon_btn = ttk.Button(
    top_frame_right_column,
    width=25,
    text='Stop Toshy Services',
    command=fn_stop_toshy_services
)
svc_status_sessmon_btn.pack(anchor=tk.W, padx=sw_lbl_indent, pady=svc_btn_pady)


###############################################################################
# START of Switches and description labels for options

###############################################################################
# Left column stuff

multi_lang_switch_var   = tk.BooleanVar(value=False)
multi_lang_switch       = ttk.Checkbutton(
    left_column,
    text='Alt_Gr on Right Cmd key',
    style='Switch.TCheckbutton',
    variable=multi_lang_switch_var
)

multi_lang_label = tk.Label(
    left_column,
    justify=tk.LEFT,
    text='Restores access to the Level3/4 additional\
        \ncharacters on non-US keyboards/layouts',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

ST3_in_VSCode_switch_var = tk.BooleanVar(value=False)
ST3_in_VSCode_switch     = ttk.Checkbutton(
    left_column, 
    text='ST3 shortcuts in VSCode(s)', 
    style='Switch.TCheckbutton', 
    variable=ST3_in_VSCode_switch_var
)

ST3_in_VSCode_label = tk.Label(
    left_column,
    justify=tk.LEFT,
    text=f'Use shortcuts from Sublime Text 3 in\
        \nVisual Studio Code (and variants)',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

Caps2Cmd_switch_var = tk.BooleanVar(value=False)
Caps2Cmd_switch     = ttk.Checkbutton(
    left_column, 
    text='CapsLock is Cmd key', 
    style='Switch.TCheckbutton', 
    variable=Caps2Cmd_switch_var
)

Caps2Cmd_label = tk.Label(
    left_column,
    justify=tk.LEFT,
    text='Modmap CapsLock to be Command key',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

Caps2Esc_Cmd_switch_var    = tk.BooleanVar(value=False)
Caps2Esc_Cmd_switch        = ttk.Checkbutton(
    left_column,
    text='Multipurpose CapsLock: Esc, Cmd',
    style='Switch.TCheckbutton', 
    variable=Caps2Esc_Cmd_switch_var
)

Caps2Esc_Cmd_switch_label = tk.Label(
    left_column,
    justify=tk.LEFT,
    text=f'Modmap CapsLock key to be:\
        \n  • Escape when tapped\
        \n  • Command key for hold/combo',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

Enter2Ent_Cmd_switch_var = tk.BooleanVar(value=False)
Enter2Enter_Cmd_switch = ttk.Checkbutton(
    left_column,
    text='Multipurpose Enter: Enter, Cmd',
    style='Switch.TCheckbutton',
    variable=Enter2Ent_Cmd_switch_var
)

Enter2Ent_Cmd_label = tk.Label(
    left_column,
    justify=tk.LEFT,
    text=f'Modmap Enter key to be:\
        \n  • Enter when tapped\
        \n  • Command key for hold/combo',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

# Do not pack these items into left column if using "barebones" config file
if not barebones_config:
    multi_lang_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    multi_lang_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    ST3_in_VSCode_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    ST3_in_VSCode_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    Caps2Cmd_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    Caps2Cmd_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    Caps2Esc_Cmd_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    Caps2Esc_Cmd_switch_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    Enter2Enter_Cmd_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    Enter2Ent_Cmd_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)


###############################################################################
# Left colum low spacer stuff


def show_popup_dialog(text = None):
    popup_root = tk.Toplevel(root)
    popup_root.title("Information")
    # popup_root.config(padx=10, pady=10)
    popup_root.bind("<Control-w>", lambda event: popup_root.destroy())
    popup_root.bind("<Escape>", lambda event: popup_root.destroy())
    # Make the popup window modal (does not work)
    popup_root.grab_set()

    text = f"""About (Work in Progress): 
    
Version: {APP_VERSION}

GUI for changing Toshy preferences, a config file for the keyszer keymapper, \
intended to make the keyboard in Linux work like a Mac.
"""

    main_popup_frame = tk.Frame(popup_root, highlightbackground='gray', highlightthickness=1)
    main_popup_frame.pack(anchor=tk.N, side=tk.TOP, ipadx=10, ipady=10, fill=tk.X, expand=True)
    
    label = tk.Label(main_popup_frame, justify=tk.LEFT, text=text, wraplength=350)
    label.pack(padx=10, pady=10, ipadx=10, ipady=10, expand=True)

    version_label = tk.Label(
        main_popup_frame,
        justify=tk.LEFT,
        text=f'Version {APP_VERSION}',
        # font=("bold", 14),
        font=sw_lbl_font,
        fg=sw_lbl_font_color
    )
    version_label.pack(anchor=tk.SW, padx=10, pady=10)

    ok_button = ttk.Button(main_popup_frame, text="OK", command=popup_root.destroy)
    ok_button.pack(padx=10, pady=10, expand=True)

    # Center the popup over the parent window (do this after packing widgets)
    popup_root.update_idletasks()
    width = popup_root.winfo_width()
    height = popup_root.winfo_height()
    if width < 450:
        width = 450
    # if height < 400:
    #     height = 400
    parent_x = root.winfo_rootx()
    parent_y = root.winfo_rooty()
    parent_width = root.winfo_width()
    parent_height = root.winfo_height()
    x = parent_x + (parent_width    // 2) - (width // 2)
    y = parent_y + (parent_height   // 3) - (height // 2)
    popup_root.geometry(f"{width}x{height}+{x}+{y}")
    # Wait for the popup window to close before resuming interaction with the main window
    popup_root.wait_window(popup_root)


help_about_btn = ttk.Button(
    left_column_low_spacer,
    width=25,
    text='Help / About',
    command=show_popup_dialog
)
help_about_btn.pack(anchor=tk.SW, side=tk.BOTTOM, padx=10, pady=6)

# Pack this after the help button, to get it to appear ABOVE the help button.
left_column_low_spacer_label = tk.Label(
    left_column_low_spacer,
    justify=tk.LEFT,
    text=f'Settings changes take effect immediately.',
    font=sw_lbl_font,
    fg=sw_lbl_font_color
)
left_column_low_spacer_label.pack(side=tk.BOTTOM, anchor=tk.SW, padx=10, pady=20, expand=True) #padx=10, pady=10)


###############################################################################
# Right column stuff

forced_numpad_switch_var   = tk.BooleanVar(value=True)
forced_numpad_switch       = ttk.Checkbutton(
    mid_right_column,
    text='Forced Numpad',
    style='Switch.TCheckbutton',
    variable=forced_numpad_switch_var
)

forced_numpad_label = tk.Label(
    mid_right_column,
    justify=tk.LEFT,
    text='Makes the numeric keypad always act like a Numpad, ignoring actual NumLock LED state.\
        \n   • NumLock key becomes "Clear" key (Escape)\
        \n   • Option+NumLock toggles NumLock OFF/ON\
        \n(Fn+NumLock will also toggle NumLock state, but only on real Apple keyboards)',
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

media_arrows_fix_switch_var = tk.BooleanVar(value=False)
media_arrows_fix_switch     = ttk.Checkbutton(
    mid_right_column,
    text='Media Arrows Fix',
    style='Switch.TCheckbutton',
    variable=media_arrows_fix_switch_var
)

media_arrows_fix_label = tk.Label(
    mid_right_column,
    justify=tk.LEFT,
    text=(  'Converts arrow keys that have "media" functions when used with '
            'Fn key, into PgUp/PgDn/Home/End keys'),
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

# Option-key special character radio button group
optspec_var = tk.StringVar(value="US") # default value
rad_btn_padx = sw_padx + 10

optspec_US_radio_btn = ttk.Radiobutton(
    mid_right_column,
    text='  Option-key Special Characters (US)*',
    style='Switch.TRadiobutton',
    variable=optspec_var, 
    value="US"
)

optspec_ABC_radio_btn = ttk.Radiobutton(
    mid_right_column,
    text='  Option-key Special Characters (ABC Extended)',
    style='Switch.TRadiobutton',
    variable=optspec_var, 
    value="ABC"
)

optspec_Disabled_radio_btn = ttk.Radiobutton(
    mid_right_column,
    text='  Disable Option-key Special Characters',
    style='Switch.TRadiobutton',
    variable=optspec_var, 
    value="Disabled"
)

optspec_label = tk.Label(
    mid_right_column,
    justify=tk.LEFT,
    text=(  'Option-key special characters are available on all regular keys and '
            'punctuation keys when holding Option or Shift+Option. Choices are '
            'standard US layout, ABC Extended layout, or disabled. Default is US '
            'layout.' ),
    font=sw_lbl_font,
    wraplength=wrap_len,
    fg=sw_lbl_font_color
)

# Do not pack these items into right column if using "barebones" config file
if not barebones_config:
    forced_numpad_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    forced_numpad_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    media_arrows_fix_switch.pack(anchor=tk.W, padx=sw_padx, pady=btn_pady)
    media_arrows_fix_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)
    optspec_US_radio_btn.pack(anchor=tk.W, padx=rad_btn_padx, pady=btn_pady)
    optspec_ABC_radio_btn.pack(anchor=tk.W, padx=rad_btn_padx, pady=btn_pady)
    optspec_Disabled_radio_btn.pack(anchor=tk.W, padx=rad_btn_padx, pady=btn_pady)
    optspec_label.pack(anchor=tk.W, padx=sw_lbl_indent, pady=btn_lbl_pady)

# left column stuff commands
multi_lang_switch.config(
    command=lambda: save_switch_settings(
        cnfg, multi_lang_switch_var, 'multi_lang'))
ST3_in_VSCode_switch.config(
    command=lambda: save_switch_settings(
        cnfg, ST3_in_VSCode_switch_var, 'ST3_in_VSCode'))
Caps2Cmd_switch.config(
    command=lambda: save_switch_settings(
        cnfg, Caps2Cmd_switch_var, 'Caps2Cmd'))
Caps2Esc_Cmd_switch.config(
    command=lambda: save_switch_settings(
        cnfg, Caps2Esc_Cmd_switch_var, 'Caps2Esc_Cmd'))
Enter2Enter_Cmd_switch.config(
    command=lambda: save_switch_settings(
        cnfg, Enter2Ent_Cmd_switch_var, 'Enter2Ent_Cmd'))

# right column stuff commands
forced_numpad_switch.config(
    command=lambda: save_switch_settings(
        cnfg, forced_numpad_switch_var, 'forced_numpad'))
media_arrows_fix_switch.config(
    command=lambda: save_switch_settings(
        cnfg, media_arrows_fix_switch_var, 'media_arrows_fix'))
optspec_US_radio_btn.config(command=lambda: save_radio_settings(cnfg, optspec_var, "optspec_layout"))
optspec_ABC_radio_btn.config(command=lambda: save_radio_settings(cnfg, optspec_var, "optspec_layout"))
optspec_Disabled_radio_btn.config(command=lambda: save_radio_settings(cnfg, optspec_var, "optspec_layout"))


# END of Switches and description labels for options
###############################################################################

theme_switch_var = tk.BooleanVar(value=True)
theme_switch = ttk.Checkbutton(
    mid_right_column, 
    text='Dark Theme', 
    style='Switch.TCheckbutton',
    variable=theme_switch_var, 
    # command=sv_ttk.toggle_theme
)
theme_switch.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)

theme_switch.config(
    command=lambda: (
        save_switch_settings(cnfg, theme_switch_var, 'gui_dark_theme'),
        sv_ttk.toggle_theme(),
    )
)

load_switch_settings(cnfg)
load_radio_btn_settings(cnfg, optspec_var, "optspec_layout")


def update_minsize():
    # update the layout and size of the window, or root.minsize will not work
    root.update_idletasks()
    # set the minimum resizable size to the initially created size of the window
    root.minsize(root.winfo_width(), root.winfo_height())
# root.after(100, update_minsize())

# No need to let the user resize the window - makes minsize setting kind of redundant
root.resizable(False, False)

# Make the window respond properly to Ctrl+W (Cmd+W when keymapper config is active)
root.bind("<Control-w>", lambda event: root.destroy())


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


if __name__ == "__main__":

    handle_existing_process()
    write_pid_to_lockfile()

    if shutil.which('systemctl') and is_init_systemd():
        # help out the config file user service
        subprocess.run(["systemctl", "--user", "import-environment", "XDG_SESSION_TYPE", "XDG_SESSION_DESKTOP", "XDG_CURRENT_DESKTOP"])    
        monitor_toshy_settings_thread = threading.Thread(target=fn_monitor_toshy_services)
        monitor_toshy_settings_thread.daemon = True
        monitor_toshy_settings_thread.start()

    # Start separate thread to watch the internal state of settings
    monitor_internal_settings_thread = threading.Thread(target=fn_monitor_internal_settings)
    monitor_internal_settings_thread.daemon = True
    monitor_internal_settings_thread.start()

    # Force the window to process pending tasks and calculate its dimensions
    root.update_idletasks()

    # Get the window size
    window_width = root.winfo_width()
    window_height = root.winfo_height()

    # Get the screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate the offsets to center the window
    offset_x = (screen_width - window_width) // 2
    offset_y = (screen_height - window_height) // 3

    # Apply the offsets
    root.geometry(f"+{offset_x}+{offset_y}")

    # This actually creates the tkinter GUI window, runs until window is closed
    # Nothing below this should be able to run until root window is closed
    root.mainloop()

# debug(f'###  Exiting Toshy Preferences app.  ###')
