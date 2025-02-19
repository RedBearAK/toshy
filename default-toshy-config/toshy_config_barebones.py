# -*- coding: utf-8 -*-
__version__ = '20250218'
###############################################################################
############################   Welcome to Toshy!   ############################
###  
###  This is a highly customized fork of the config file that powers 
###  Kinto.sh, by Ben Reaves
###      (https://kinto.sh)
###  
###  All credit for the basis of this config goes to Ben Reaves. 
###      (https://github.com/rbreaves/)
###  
###  Much assistance was provided by Josh Goebel, the developer of the
###  `xkeysnail` fork `keyszer`, which is now forked into `xwaykeyz` to
###  provide support for some (most?) Wayland environments.
###      (http://github.com/joshgoebel/keyszer)
###  
###############################################################################

import re
import os
import sys
import time
import shutil
import inspect
import subprocess

from subprocess import DEVNULL
from typing import Callable, List, Dict, Tuple, Union

from xwaykeyz.config_api import *
from xwaykeyz.lib.key_context import KeyContext
from xwaykeyz.lib.logger import debug, error
from xwaykeyz.models.modifier import Modifier


###################################################################################################
###  SLICE_MARK_START: keymapper_api  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

# Keymapper-specific config settings - REMOVE OR SET TO DEFAULTS FOR DISTRIBUTION
dump_diagnostics_key(Key.F15)   # default key: F15
emergency_eject_key(Key.F16)    # default key: F16

timeouts(
    multipurpose        = 1,        # default: 1 sec
    suspend             = 1,        # default: 1 sec, try 0.1 sec for touchpads/trackpads
)

# Delays often needed for Wayland and/or virtual machines or slow systems
throttle_delays(
    key_pre_delay_ms    = 12,      # default: 0 ms, range: 0-150 ms, suggested: 1-50 ms
    key_post_delay_ms   = 18,      # default: 0 ms, range: 0-150 ms, suggested: 1-100 ms
)

devices_api(
    # Only the specified devices will be "grabbed" and watched for during 
    # device connections/disconnections. 
    only_devices = [
        # 'Example Disconnected Keyboard',
        # 'Example Connected Keyboard',
    ]
)

###  SLICE_MARK_END: keymapper_api  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################




home_dir = os.path.expanduser('~')
icons_dir = os.path.join(home_dir, '.local', 'share', 'icons')

# get the path of this file (not the main module loading it)
config_globals = inspect.stack()[1][0].f_globals
current_folder_path = os.path.dirname(os.path.abspath(config_globals["__config__"]))
sys.path.insert(0, current_folder_path)

# Local imports after path has been set
from lib.env_context import EnvironmentInfo
from lib.machine_context import get_machine_id_hash
from lib.notification_manager import NotificationManager
from lib.settings_class import Settings

assets_path         = os.path.join(current_folder_path, 'assets')
icon_file_active    = os.path.join(assets_path, "toshy_app_icon_rainbow.svg")
icon_file_grayscale = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse_grayscale.svg")
icon_file_inverse   = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse.svg")

# Toshy config file
TOSHY_PART      = 'config'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Barebones Config'
APP_VERSION     = __version__

# Settings object used to tweak preferences "live" between gui, tray and config.
cnfg = Settings(current_folder_path)
cnfg.watch_database()       # activate watchdog observer on the sqlite3 db file
cnfg.watch_synergy_log()    # activate watchdog observer on the Synergy log file
debug("")
debug(cnfg, ctx="CG")



#############################  ENVIRONMENT  ##############################
###                                                                    ###
###                                                                    ###
###      ███████ ███    ██ ██    ██ ██ ██████   ██████  ███    ██      ###
###      ██      ████   ██ ██    ██ ██ ██   ██ ██    ██ ████   ██      ###
###      █████   ██ ██  ██ ██    ██ ██ ██████  ██    ██ ██ ██  ██      ###
###      ██      ██  ██ ██  ██  ██  ██ ██   ██ ██    ██ ██  ██ ██      ###
###      ███████ ██   ████   ████   ██ ██   ██  ██████  ██   ████      ###
###                                                                    ###
###                                                                    ###
##########################################################################
# Set up some useful environment variables

###################################################################################################
###  SLICE_MARK_START: env_overrides  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

# MANUALLY set any environment information if the auto-identification isn't working:
OVERRIDE_DISTRO_ID              = None
OVERRIDE_DISTRO_VER             = None
OVERRIDE_VARIANT_ID             = None
OVERRIDE_SESSION_TYPE           = None
OVERRIDE_DESKTOP_ENV            = None
OVERRIDE_DE_MAJ_VER             = None
OVERRIDE_WINDOW_MGR             = None

wlroots_compositors             = [
    # Comma-separated list of Wayland desktop environments or window managers
    # that should try to use the 'wlroots' window context provider. Use the 
    # 'WINDOW_MGR' name that appears when running `toshy-env`, or 'DESKTOP_ENV'
    # if the window manager name is not identified. 
    # 'obscurewm',
    # 'unknown-wm',

]

###  SLICE_MARK_END: env_overrides  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################

# Leave all of this alone! Don't try to override values here. 
DISTRO_ID                       = None
DISTRO_VER                      = None
VARIANT_ID                      = None
SESSION_TYPE                    = None
DESKTOP_ENV                     = None
DE_MAJ_VER                      = None
WINDOW_MGR                      = None

env_ctxt_getter = EnvironmentInfo()
env_ctxt: Dict[str, str] = env_ctxt_getter.get_env_info()

DISTRO_ID       = locals().get('OVERRIDE_DISTRO_ID')    or env_ctxt.get('DISTRO_ID',    'keymissing')
DISTRO_VER      = locals().get('OVERRIDE_DISTRO_VER')   or env_ctxt.get('DISTRO_VER',   'keymissing')
VARIANT_ID      = locals().get('OVERRIDE_VARIANT_ID')   or env_ctxt.get('VARIANT_ID',   'keymissing')
SESSION_TYPE    = locals().get('OVERRIDE_SESSION_TYPE') or env_ctxt.get('SESSION_TYPE', 'keymissing')
DESKTOP_ENV     = locals().get('OVERRIDE_DESKTOP_ENV')  or env_ctxt.get('DESKTOP_ENV',  'keymissing')
DE_MAJ_VER      = locals().get('OVERRIDE_DE_MAJ_VER')   or env_ctxt.get('DE_MAJ_VER',   'keymissing')
WINDOW_MGR      = locals().get('OVERRIDE_WINDOW_MGR')   or env_ctxt.get('WINDOW_MGR',   'keymissing')

debug("")
debug(  f'Toshy (barebones) config sees this environment:'
        f'\n\t{DISTRO_ID        = }'
        f'\n\t{DISTRO_VER       = }'
        f'\n\t{VARIANT_ID       = }'
        f'\n\t{SESSION_TYPE     = }'
        f'\n\t{DESKTOP_ENV      = }'
        f'\n\t{DE_MAJ_VER       = }'
        f'\n\t{WINDOW_MGR       = }\n', ctx="CG")


# TODO: Add a list here to concat with 'wlroots_compositors', instead of
# continuing to add new environments into the 'wlroots' provider inside 
# the keymapper. 
known_wlroots_compositors = [
    # 'hyprland',
    # 'labwc',
    # 'miracle-wm',
    # 'miriway',
    # 'miriway-shell',    # actual process name for 'miriway' compositor?
    # 'niri',
    # 'qtile',
    # 'river',
    # 'sway',
    # 'wayfire',
]

# Make sure the 'wlroots_compositors' list variable exists before checking it.
# Older config files won't have it in the 'env_overrides' slice. 
wlroots_compositors = locals().get('wlroots_compositors', [])

all_wlroots_compositors = known_wlroots_compositors + wlroots_compositors

# Direct the keymapper to try to use `wlroots` window context for
# all DEs/WMs in user list, if list is not empty.
if wlroots_compositors and WINDOW_MGR in wlroots_compositors:
    debug(f"Will use 'wlroots' context provider for '{WINDOW_MGR}' WM", ctx="CG")
    debug("File an issue on GitHub repo if this works for your WM.", ctx="CG")
    _wl_compositor = 'wlroots'
elif wlroots_compositors and DESKTOP_ENV in wlroots_compositors:
    debug(f"Will use 'wlroots' context provider for '{DESKTOP_ENV}' DE", ctx="CG")
    debug("File an issue on GitHub repo if this works for your DE.", ctx="CG")
    _wl_compositor = 'wlroots'
elif WINDOW_MGR in known_wlroots_compositors:
    debug(f"WM '{WINDOW_MGR}' is in known 'wlroots' compositor list.", ctx="CG")
    _wl_compositor = 'wlroots'
elif DESKTOP_ENV in known_wlroots_compositors:
    debug(f"DE '{DESKTOP_ENV}' is in known 'wlroots' compositor list.", ctx="CG")
    _wl_compositor = 'wlroots'
# elif (SESSION_TYPE, DESKTOP_ENV) == ('wayland', 'lxqt') and WINDOW_MGR == 'kwin_wayland':
#     # The Toshy KWin script must be installed in the LXQt/KWin environment for this to work!
#     debug(f"DE is LXQt, WM is '{WINDOW_MGR}', using 'kwin_wayland' window context method.", ctx="CG")
#     _desktop_env = 'kde'
# elif (SESSION_TYPE, DESKTOP_ENV) == ('wayland', 'lxqt') and WINDOW_MGR in all_wlroots_compositors:
#     debug(f"DE is LXQt, WM is '{WINDOW_MGR}', using 'wlroots' window context method.", ctx="CG")
#     _desktop_env = 'wlroots'
else:
    _wl_compositor = WINDOW_MGR

try:
    # Help the keymapper select the correct window context provider object
    environ_api(session_type = SESSION_TYPE, wl_compositor = _wl_compositor) # type: ignore
except NameError:
    error(f"The API function 'environ_api' is not defined yet. Wrong keymapper branch?")
    pass


# Global variable to store the local machine ID at runtime, for machine-specific keymaps.
# Allows syncing a single config file between different machines without overlapping the
# hardware/media key overrides, or any other machine-specific customization.
# Get the ID for each machine with the `toshy-machine-id` command, for use in `if` conditions.
MACHINE_ID = get_machine_id_hash()



#################  VARIABLES  ####################
###                                            ###
###                                            ###
###      ██    ██  █████  ██████  ███████      ###
###      ██    ██ ██   ██ ██   ██ ██           ###
###      ██    ██ ███████ ██████  ███████      ###
###       ██  ██  ██   ██ ██   ██      ██      ###
###        ████   ██   ██ ██   ██ ███████      ###
###                                            ###
###                                            ###
##################################################
# Establish important global variables here


STARTUP_TIMESTAMP = time.time()     # only gets evaluated once for each run of keymapper

# Variable to hold the keyboard type
KBTYPE = None

# Short names for the `xwaykeyz/keyszer` string and Unicode processing helper functions
ST = to_US_keystrokes           # was 'to_keystrokes' originally
UC = unicode_keystrokes
ignore_combo = ComboHint.IGNORE

###############################################################################
# This is a "trick" to negate the need to put quotes around all the key labels 
# inside the "lists of dicts" to be given to the matchProps() function.
# Makes the variables evaluate to equivalent strings inside the dicts. 
# Provides for nice syntax highlighting and visual separation of key:value. 
clas        = 'clas'        # key label for matchProps() arg to match: wm_class
name        = 'name'        # key label for matchProps() arg to match: wm_name
devn        = 'devn'        # key label for matchProps() arg to match: device_name
not_clas    = 'not_clas'    # key label for matchProps() arg to NEGATIVE match: wm_class
not_name    = 'not_name'    # key label for matchProps() arg to NEGATIVE match: wm_name
not_devn    = 'not_devn'    # key label for matchProps() arg to NEGATIVE match: device_name
numlk       = 'numlk'       # key label for matchProps() arg to match: numlock_on
capslk      = 'capslk'      # key label for matchProps() arg to match: capslock_on
cse         = 'cse'         # key label for matchProps() arg to enable: case sensitivity
lst         = 'lst'         # key label for matchProps() arg to pass in a [list] of {dicts}
dbg         = 'dbg'         # key label for matchProps() arg to set debugging info string

# global variables for the isDoubleTap() function
tapTime1 = time.time()
tapInterval = 0.24
tapCount = 0
last_dt_combo = None




######################  LISTS  #######################
###                                                ###
###                                                ###
###      ██      ██ ███████ ████████ ███████       ###
###      ██      ██ ██         ██    ██            ###
###      ██      ██ ███████    ██    ███████       ###
###      ██      ██      ██    ██         ██       ###
###      ███████ ██ ███████    ██    ███████       ###
###                                                ###
###                                                ###
######################################################


def toRgxStr(lst_of_str) -> str:
    """
    Convert a list of strings into single casefolded regex pattern string.
    """
    def raise_TypeError(): raise TypeError(f"\n\n###  toRgxStr wants a list of strings  ###\n")
    if not isinstance(lst_of_str, list): raise_TypeError()
    if any([not isinstance(x, str) for x in lst_of_str]): raise_TypeError()
    lst_of_str_clean = [str(x).replace('^','').replace('$','') for x in lst_of_str]
    return "|".join('^'+x.casefold()+'$' for x in lst_of_str_clean)


def negRgx(rgx_str):
    """
    Convert positive match regex pattern into negative lookahead regex pattern.
    """
    # remove any ^$
    rgx_str_strip = str(rgx_str).replace('^','').replace('$','')
    # add back ^$, but only around ENTIRE STRING (ignore any vertical bars/pipes)
    rgx_str_add = str('^'+rgx_str_strip+'$')
    # convert ^$ to complicated negative lookahead pattern that actually works
    neg_rgx_str = str(rgx_str_add).replace('^','^(?:(?!^').replace('$','$).)*$')
    return neg_rgx_str



###################################################################################################
###  SLICE_MARK_START: kbtype_override  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

keyboards_UserCustom_dct = {
    # Add your keyboard device here if its type is misidentified.
    # Valid types to map device to: Apple, Windows, IBM, Chromebook (case sensitive)
    # Example:
    'My Keyboard Device Name': 'Apple',
}

###  SLICE_MARK_END: kbtype_override  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################

# Create a "UserCustom" keyboard dictionary with casefolded keys
kbds_UserCustom_dct_cf = {k.casefold(): v for k, v in keyboards_UserCustom_dct.items()}


# Lists of keyboard device names, to match keyboard type
keyboards_IBM = [
    # Add specific IBM-style keyboard device names to this list
    'IBM Enhanced (101/102-key) Keyboard',
    'IBM Rapid Access Keyboard',
    'IBM Space Saver II',
    'IBM Model M',
    'IBM Model F',
]
keyboards_Chromebook = [
    # Add specific Chromebook keyboard device names to this list
    'Google.*Keyboard',
]
keyboards_Windows = [
    # Add specific Windows/PC keyboard device names to this list
    'AT Translated Set 2 keyboard',
]
keyboards_Apple = [
    # Add specific Apple/Mac keyboard device names to this list
    'Mitsumi Electric Apple Extended USB Keyboard',
    'Magic Keyboard with Numeric Keypad',
    'Magic Keyboard',
    'MX Keys Mac Keyboard',
]

kbtype_lists = {
    'IBM':          keyboards_IBM,
    'Chromebook':   keyboards_Chromebook,
    'Windows':      keyboards_Windows,
    'Apple':        keyboards_Apple
}

# List of all known keyboard devices from all lists
all_keyboards       = [kb for kbtype in kbtype_lists.values() for kb in kbtype]

# keyboard lists compiled to regex objects (replacing spaces with wildcards)
kbds_IBM_rgx        = [re.compile(kb.replace(" ", ".*"), re.I) for kb in keyboards_IBM]
kbds_Chromebook_rgx = [re.compile(kb.replace(" ", ".*"), re.I) for kb in keyboards_Chromebook]
kbds_Windows_rgx    = [re.compile(kb.replace(" ", ".*"), re.I) for kb in keyboards_Windows]
kbds_Apple_rgx      = [re.compile(kb.replace(" ", ".*"), re.I) for kb in keyboards_Apple]

# Dict mapping keyboard type keywords onto 
kbtype_lists_rgx    = {
    'IBM':          kbds_IBM_rgx,
    'Chromebook':   kbds_Chromebook_rgx,
    'Windows':      kbds_Windows_rgx,
    'Apple':        kbds_Apple_rgx
}

# List of all known keyboard devices from all lists
all_kbds_rgx        = re.compile(toRgxStr(all_keyboards), re.I)

not_win_type_rgx    = re.compile("IBM|Chromebook|Apple", re.I)


# Suggested location for customizing lists and variables for use with the "when" conditions.
###################################################################################################
###  SLICE_MARK_START: user_custom_lists  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE



###  SLICE_MARK_END: user_custom_lists  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################



###################################  CUSTOM FUNCTIONS  ####################################
###                                                                                     ###
###                                                                                     ###
###      ███████ ██    ██ ███    ██  ██████ ████████ ██  ██████  ███    ██ ███████      ###
###      ██      ██    ██ ████   ██ ██         ██    ██ ██    ██ ████   ██ ██           ###
###      █████   ██    ██ ██ ██  ██ ██         ██    ██ ██    ██ ██ ██  ██ ███████      ###
###      ██      ██    ██ ██  ██ ██ ██         ██    ██ ██    ██ ██  ██ ██      ██      ###
###      ██       ██████  ██   ████  ██████    ██    ██  ██████  ██   ████ ███████      ###
###                                                                                     ###
###                                                                                     ###
###########################################################################################


# Instantiate a useful notification object class instance, to make notifications easier
ntfy = NotificationManager(icon_file_active, title='Toshy Alert (Config)')


def isKBtype(kbtype: str, map=None):
    # guard against failure to give valid type arg (we don't need to casefold anything with this)
    if kbtype not in ['IBM', 'Chromebook', 'Windows', 'Apple']:
        raise ValueError(f"Invalid type given to isKBtype() function: '{kbtype}'"
                f'\n\t Valid keyboard types (case sensitive): IBM | Chromebook | Windows | Apple')
    def _isKBtype(ctx: KeyContext):
        # debug(f"KBTYPE: '{KBTYPE}' | isKBtype check from map: '{map}'")
        return kbtype == KBTYPE
    return _isKBtype


kbtype_cache_dct = {}


def getKBtype():
    """
    ### Get the keyboard type string for the current device
    
    #### Valid Types
    
    - IBM | Chromebook | Windows | Apple
    
    #### Hierarchy of validations:
    
    - Check if a forced override of keyboard type is applied by user preference.
    - Check cache dictionary for device name stored from previous run of function.
    - Check if the device name is in the keyboards_UserCustom_dct dictionary.
    - Check if the device name matches any keyboard type list.
    - Check if any keyboard type string is found in the device name string.
    - Check if the device name indicates a "Windows" keyboard by excluding other types.
    """

    valid_kbtypes = ['IBM', 'Chromebook', 'Windows', 'Apple']

    def _getKBtype(ctx: KeyContext):
        # debug(f"Entering getKBtype with override value: '{cnfg.override_kbtype}'")
        global KBTYPE
        kbd_dev_name = ctx.device_name

        def log_kbtype(msg, cache_dev):
            debug(f"KBTYPE: '{KBTYPE}' | {msg}: '{kbd_dev_name}'")
            if cache_dev:
                kbtype_cache_dct[kbd_dev_name] = (KBTYPE, msg)

        # If user wants to override, apply override and return.
        # Breaks per-device adaptatation capability while engaged!
        if cnfg.override_kbtype in valid_kbtypes:
            KBTYPE = cnfg.override_kbtype
            log_kbtype(f"WARNING: Override applied! Dev", cache_dev=False)
            return

        # Check in the kbtype cache dict for the device
        if kbd_dev_name in kbtype_cache_dct:
            KBTYPE, cached_msg = kbtype_cache_dct[kbd_dev_name]
            log_kbtype(f'(CACHED) {cached_msg}', cache_dev=False)
            return

        kbd_dev_name_cf = ctx.device_name.casefold()

        # Check if there is a custom type for the device
        custom_kbtype = kbds_UserCustom_dct_cf.get(kbd_dev_name_cf, '')
        if custom_kbtype and custom_kbtype in valid_kbtypes:
            KBTYPE = custom_kbtype
            log_kbtype('Custom type for dev', cache_dev=True)
            return

        # Check against the keyboard type lists
        for kbtype, regex_lst in kbtype_lists_rgx.items():
            for rgx in regex_lst:
                if rgx.search(kbd_dev_name_cf):
                    KBTYPE = kbtype
                    log_kbtype('Rgx matched on dev', cache_dev=True)
                    return

        # Check if any keyboard type string is found in the device name
        for kbtype in ['IBM', 'Chromebook', 'Windows', 'Apple']:
            if kbtype.casefold() in kbd_dev_name_cf:
                KBTYPE = kbtype
                log_kbtype('Type in dev name', cache_dev=True)
                return

        # Check if the device name indicates a "Windows" keyboard
        if ('windows' not in kbd_dev_name_cf 
            and not not_win_type_rgx.search(kbd_dev_name_cf) 
            and not all_kbds_rgx.search(kbd_dev_name_cf) ):
            KBTYPE = 'Windows'
            log_kbtype('Default type for dev', cache_dev=True)
            return

        # Default to None if no matching keyboard type is found
        KBTYPE = 'unidentified'
        error(f"KBTYPE: '{KBTYPE}' | Dev fell through all checks: '{kbd_dev_name}'")

    return _getKBtype  # Return the inner function


def isDoubleTap(dt_combo):
    """
    VERY EXPERIMENTAL!!!
    
    Simplistic detection of double-tap of a key or combo.
    
    BLOCKS single-tap function, if used with a single key as the input, but the
    'normal' (non-modifier) key of a combo will still be usable when used by 
    itself as a non-double-tapped key press.
    
    Example: 'RC-CapsLock' will respond when "Cmd" key (under Toshy remapping)
    is held and CapsLock key is double-tapped. Nothing will happen if 
    Cmd+CapsLock is pressed without double-tapping CapsLock key within the
    configured time interval. But the CapsLock key will still work by itself.
    
    If double-tap input "combo" is just 'CapsLock', the functioning of a single-tap
    CapsLock key press will be BLOCKED. Nothing will happen unless the key is 
    double-tapped within the configured time interval.
    
    Only cares about the 'real' key in a combo of Mods+key, like in the example
    above with 'RC-CapsLock'. 
    
    The proper way to do this would be inside the keymapper, in the async event loop
    that deals with input/output functions. 
    """
    def _isDoubleTap():
        global tapTime1
        global tapInterval
        global tapCount
        global last_dt_combo
        _tapTime = time.time()
        # This first "if" block has a logic defect, if a different key in the
        # same keymap is also set up to send the same "dt_combo" value.
        if tapCount == 1 and last_dt_combo != dt_combo:
            debug(f'## isDoubleTap: \n\tDifferent combo: \n\t{last_dt_combo, dt_combo=}')
            last_dt_combo = None
            tapCount = 0
        # 2nd tap beyond time interval? Treat as new double-tap cycle.
        if tapCount == 1 and _tapTime - tapTime1 >= tapInterval:
            debug(f'## isDoubleTap: \n\tTime diff (too long): \n\t{_tapTime - tapTime1=}')
            tapCount = 0
        # Try to keep held key from producing repeats of dt_combo.
        # If repeat rate very slow or delay very short, this won't work well. 
        if tapCount == 1 and _tapTime - tapTime1 < 0.07:
            debug(f'## isDoubleTap: \n\tTime diff (too short): \n\t{_tapTime - tapTime1=}')
            tapCount = 0
            return None
        # 2nd tap within interval window? Reset cycle & send dt_combo.
        if tapCount == 1 and _tapTime - tapTime1 < tapInterval:
            debug(f'## isDoubleTap: \n\tTime diff (just right): \n\t{_tapTime - tapTime1=}')
            tapCount = 0
            tapTime1 = 0.0
            return dt_combo
        # New cycle? Set count = 1, tapTime1 = now. Send nothing. 
        if tapCount == 0:
            debug(f'## isDoubleTap: \n\tTime diff (1st cycle): \n\t{_tapTime - tapTime1=}')
            last_dt_combo = dt_combo
            tapCount = 1
            tapTime1 = _tapTime
            return None
    return _isDoubleTap


total_matchProps_iterations = 0
MAX_MATCHPROPS_ITERATIONS = 1000
MAX_MATCHPROPS_ITERATIONS_REACHED = False


# Correct syntax to reject all positional parameters: put `*,` at beginning
def matchProps(*,
    # string parameters (positive matching)
    clas: str = None, name: str = None, devn: str = None,
    # string parameters (negative matching)
    not_clas: str = None, not_name: str = None, not_devn: str = None,
    # bool parameters
    numlk: bool = None, capslk: bool = None, cse: bool = None,
    # list of dicts of parameters (positive)
    lst: List[Dict[str, Union[str, bool]]] = None,
    # list of dicts of parameters (negative)
    not_lst: List[Dict[str, Union[str, bool]]] = None,
    dbg: str = None,    # debugging info (such as: which modmap/keymap?)
) -> Callable[[KeyContext], bool]:
    """
    ### Match all given properties to current window context.       \n
    - Parameters must be _named_, no positional arguments.          \n
    - All parameters optional, but at least one must be given.      \n
    - Defaults to case insensitive matching of:                     \n
        - WM_CLASS, WM_NAME, device_name                            \n
    - To negate/invert regex pattern match use:                     \n
        - `not_clas` `not_name` `not_devn` params or...             \n
        - "^(?:(?!^pattern$).)*$"                                   \n
    - To force case insensitive pattern match use:                  \n 
        - "^(?i:pattern)$" or...                                    \n
        - "^(?i)pattern$"                                           \n

    ### Accepted Parameters:                                        \n
    `clas` = WM_CLASS    (regex/string) [xprop WM_CLASS]            \n
    `name` = WM_NAME     (regex/string) [xprop _NET_WM_NAME]        \n
    `devn` = Device Name (regex/string) [xwaykeyz --list-devices]   \n
    `not_clas` = `clas` but inverted, matches when "not"            \n
    `not_name` = `name` but inverted, matches when "not"            \n
    `not_devn` = `devn` but inverted, matches when "not"            \n
    `numlk`    = Num Lock LED state         (bool)                  \n
    `capslk`   = Caps Lock LED state        (bool)                  \n
    `cse`      = Case Sensitive matching    (bool)                  \n
    `lst`      = List of dicts of the above arguments               \n
    `not_lst`  = `lst` but inverted, matches when "not"             \n
    `dbg`      = Debugging info             (string)                \n

    ### Negative match parameters: 
    - `not_clas`|`not_name`|`not_devn`                              \n
    Parameters take same regex patterns as `clas`|`name`|`devn`     \n
    but result in a True condition only if pattern is NOT found.    \n
    Negative parameters cannot be used together with the normal     \n
    positive matching equivalent parameter in same instance.        \n

    ### List of Dicts parameter: `lst`|`not_lst`
    A [list] of {dicts} with each dict containing 1 to 6 of the     \n
    named parameters above, to be processed recursively as args.    \n
    A dict can also contain a single `lst` or `not_lst` argument.   \n

    ### Debugging info parameter: `dbg`
    A string that will print as part of logging output. Use to      \n
    help identify origin of logging output.                         \n
    -                                                               \n
    """
    # Reference for successful negative lookahead pattern, and 
    # explanation of why it works:
    # https://stackoverflow.com/questions/406230/\
        # regular-expression-to-match-a-line-that-doesnt-contain-a-word

    global MAX_MATCHPROPS_ITERATIONS_REACHED
    global total_matchProps_iterations

    # Return `False` immediately if screen does not have focus (e.g. Synergy),
    # but only after the guard clauses have had a chance to evaluate on
    # all possible uses of the function that may exist in the config.
    if MAX_MATCHPROPS_ITERATIONS_REACHED and not cnfg.screen_has_focus:
        return False

    if total_matchProps_iterations >= MAX_MATCHPROPS_ITERATIONS:
        MAX_MATCHPROPS_ITERATIONS_REACHED = True
        bypass_guard_clauses = True
    else:
        total_matchProps_iterations += 1
        current_timestamp = time.time()

        # 'STARTUP_TIMESTAMP' is a global variable, set when config is executed
        time_elapsed = current_timestamp - STARTUP_TIMESTAMP

        # Bypass all guard clauses if more than a few seconds have passed since keymapper 
        # started and loaded the config file. Inputs never change until keymapper 
        # restarts and reloads the config file, so we don't need to keep checking.
        bypass_guard_clauses = time_elapsed > 6

    logging_enabled = False

    allowed_params  = (clas, name, devn, not_clas, not_name, not_devn, 
                        numlk, capslk, cse, lst, not_lst, dbg)
    lst_dct_params  = (clas, name, devn, not_clas, not_name, not_devn, 
                        numlk, capslk, cse)
    string_params   = (clas, name, devn, not_clas, not_name, not_devn, dbg)

    # This was using up a lot of CPU time, actually. Bad idea. 
    # dct_param_strs  = list(inspect.signature(matchProps).parameters.keys())

    # Static list of parameter names. Using this instead of `inspect` cuts CPU 
    # usage considerably, for reasons I don't yet understand. Apparently the
    # keymapper is actually running the entire function again on each key 
    # press and release, rather than just re-evaluating the inner closure.
    dct_param_strs = [
        'clas', 'name', 'devn', 'not_clas', 'not_name', 'not_devn',
        'numlk', 'capslk', 'cse', 'lst', 'not_lst', 'dbg'
    ]

    if not MAX_MATCHPROPS_ITERATIONS_REACHED or not bypass_guard_clauses:
        if all([x is None for x in allowed_params]): 
            raise ValueError(f"\n\n(EE) matchProps(): Received no valid argument\n")
        if any([x not in (True, False, None) for x in (numlk, capslk, cse)]): 
            raise TypeError(f"\n\n(EE) matchProps(): Params 'numlk|capslk|cse' are bools\n")
        if any([x is not None and not isinstance(x, str) for x in string_params]):
            raise TypeError(    f"\n\n(EE) matchProps(): These parameters must be strings:"
                                f"\n\t'clas|name|devn|not_clas|not_name|not_devn|dbg'\n")
        if clas and not_clas or name and not_name or devn and not_devn or lst and not_lst:
            raise ValueError(   f"\n\n(EE) matchProps(): Do not mix positive and "
                                f"negative match params for same property\n")

    # consolidate positive and negative matching params into new vars
    # only one should be in use at a time (checked above)
    _lst = not_lst if lst is None else lst
    _clas = not_clas if clas is None else clas
    _name = not_name if name is None else name
    _devn = not_devn if devn is None else devn

    # process lists of conditions
    if _lst is not None:

        if not MAX_MATCHPROPS_ITERATIONS_REACHED or not bypass_guard_clauses:
            if any([x is not None for x in lst_dct_params]): 
                raise TypeError(f"\n\n(EE) matchProps(): Param 'lst|not_lst' must be used alone\n")
            if not isinstance(_lst, list) or not all(isinstance(item, dict) for item in _lst): 
                raise TypeError(
                    f"\n\n(EE) matchProps(): Param 'lst|not_lst' wants a [list] of {{dicts}}\n")
            # verify that every {dict} in [list of dicts] only contains valid parameter names
            for dct in _lst:
                for param in list(dct.keys()):
                    if param not in dct_param_strs:
                        error(f"matchProps(): Invalid parameter: '{param}'")
                        error(f"Invalid parameter is in this dict: \n\t{dct}")
                        error(f"Dict is in this list:")
                        for item in _lst:
                            print(f"\t{item}")
                        raise ValueError(
                            f"\n(EE) matchProps(): Invalid parameter found in dict in list. "
                            f"See log output before traceback.\n")

        def _matchProps_Lst(ctx: KeyContext):
            if not cnfg.screen_has_focus:
                return False
            if not_lst is not None:
                if logging_enabled: print(f"## _matchProps_Lst()[not_lst] ## {dbg=}")
                return not any(matchProps(**dct)(ctx) for dct in not_lst)
            else:
                if logging_enabled: print(f"## _matchProps_Lst()[lst] ## {dbg=}")
                return any(matchProps(**dct)(ctx) for dct in lst)

        return _matchProps_Lst      # outer function returning inner function

    # compile case insensitive regex object for given params, unless cse=True
    if _clas is not None: clas_rgx = re.compile(_clas, 0 if cse else re.I)
    if _name is not None: name_rgx = re.compile(_name, 0 if cse else re.I)
    if _devn is not None: devn_rgx = re.compile(_devn, 0 if cse else re.I)

    def _matchProps(ctx: KeyContext):
        if not cnfg.screen_has_focus:
            return False
        cond_list       = []
        nt_err          = 'ERR: matchProps: NoneType in ctx.'
        if _clas is not None:
            clas_match = re.search(clas_rgx, ctx.wm_class or nt_err + 'wm_class')
            cond_list.append(not clas_match if not_clas is not None else clas_match)
        if _name is not None:
            name_match = re.search(name_rgx, ctx.wm_name or nt_err + 'wm_name')
            cond_list.append(not name_match if not_name is not None else name_match)
        if _devn is not None:
            devn_match = re.search(devn_rgx, ctx.device_name or nt_err + 'device_name')
            cond_list.append(not devn_match if not_devn is not None else devn_match)
        # these two MUST check explicitly for "is not None" because external input is True/False,
        # and we want to be able to match the LED_on state of either "True" or "False"
        if numlk is not None: cond_list.append( numlk is ctx.numlock_on  )
        if capslk is not None: cond_list.append( capslk is ctx.capslock_on )
        if logging_enabled: # and all(cnd_lst): # << add this to show only "True" condition lists
            print(f'####  CND_LST ({all(cond_list)})  ####  {dbg=}')
            for elem in cond_list:
                print('##', re.sub(r'^.*span=.*\), ', '', str(elem)).replace('>',''))
            print('-------------------------------------------------------------------')
        return all(cond_list)

    return _matchProps      # outer function returning inner function


# Boolean variable to toggle Enter key state between F2 and Enter
# True = Enter key sends F2, False = Enter key sends Enter
_enter_is_F2 = True     # DON'T CHANGE THIS! Must be set to True here. 


def iEF2(combo_if_true, latch_or_combo_if_false, 
                keep_value_if_true=False, keep_value_if_false=False):
    """
    Formerly 'is_Enter_F2'
    Send a different combo for the Enter key based on the state of the _enter_is_F2 variable,
    or latch the variable to True or False to control the Enter key output on the next use.
    
    Args:
        combo_if_true:              The combo to send if _enter_is_F2 is True.
        latch_or_combo_if_false:    The combo to send if _enter_is_F2 is False, or
                                    a Boolean to latch _enter_is_F2 to a specific value.
        keep_value_if_true (opt.):  If True, _enter_is_F2 will be kept True if it is currently True.
                                    If False, _enter_is_F2 will be set to False if it is currently True.
        keep_value_if_false (opt.): If True, _enter_is_F2 will be kept False if it is currently False.
                                    If False, _enter_is_F2 will be set to True if it is currently False.
    
    Returns:
        A function that, when called, returns the appropriate combo based on the current
        state of _enter_is_F2 and the provided parameters, and updates _enter_is_F2
        based on the provided parameters.
    
    This enables a simulation of the Finder "Enter to rename" capability, allowing
    for complex control over the Enter key's behavior in various scenarios.
    """
    def _is_Enter_F2():
        global _enter_is_F2
        combo_list = [combo_if_true]
        if latch_or_combo_if_false in (True, False):    # Latch variable to given bool value
            _enter_is_F2 = latch_or_combo_if_false
        elif _enter_is_F2:                              # If Enter is F2 now, set to be Enter next
            if keep_value_if_true is False:
                _enter_is_F2 = False
        else:                                           # If Enter is Enter now, set to be F2 next
            combo_list = [latch_or_combo_if_false]
            if keep_value_if_false is False:
                _enter_is_F2 = True
        debug(f"_is_Enter_F2:  {combo_list      = }")
        debug(f"_is_Enter_F2:  {_enter_is_F2    = }")
        return combo_list
    return _is_Enter_F2


def iEF2NT():
    """Feed `is_Enter_F2` function `None` and `True` as arguments, with short name"""
    return iEF2(None, True)


def macro_tester():
    """Type out a macro with useful info and a Unicode test.
        WARNING: Safe only for use in apps that accept text blocks/typing of many characters."""
    def _macro_tester(ctx: KeyContext):
        return [
                    C("Enter"),
                    ST(f"Class: '{ctx.wm_class}'"), C("Enter"),
                    ST(f"Title: '{ctx.wm_name}'"), C("Enter"),
                    ST(f"Keybd: '{ctx.device_name}'"), C("Enter"),
                    ST(f"Keyboard type: '{KBTYPE}'"), C("Enter"),
                    ST("Next test should come out on ONE LINE!"), C("Enter"),
                    ST("Unicode and Shift Test: 🌹—€—\u2021—ÿ—\U00002021 12345 !@#$% |\\ !!!!!!"),
                    C("Enter")
        ]
    return _macro_tester


def is_valid_command(command):
    """Check if the command path is valid and executable"""
    return command and os.path.isfile(command) and os.access(command, os.X_OK)


# Result will be None if DE is not in list OR if 'kdialog' not available.
# kdialog_cmd = shutil.which('kdialog') if DESKTOP_ENV.casefold() in ['kde', 'lxqt'] else None
# DISABLING KDIALOG BECAUSE IT KIND OF SUCKS QUITE A BIT COMPARED TO ZENITY/QARMA
kdialog_cmd = shutil.which('kdialog') if DESKTOP_ENV.casefold() in ['kdialog_is_lame'] else None


zenity_is_qarma = False

zenity_cmd = shutil.which('zenity-gtk')
if not zenity_cmd:
    zenity_cmd = shutil.which('qarma')
    if zenity_cmd:
        zenity_is_qarma = True
if not zenity_cmd:
    zenity_cmd = shutil.which('zenity')

debug(f"Zenity command path: '{zenity_cmd}'")

zenity_icon_option = None

if zenity_cmd:
    try:
        zenity_help_output = subprocess.check_output([zenity_cmd, '--help-info'])
        help_text = str(zenity_help_output)
        if '--icon=' in help_text:
            zenity_icon_option = '--icon=toshy_app_icon_rainbow'
        elif '--icon-name=' in help_text:
            zenity_icon_option = '--icon-name=toshy_app_icon_rainbow'
    except subprocess.CalledProcessError:
        pass  # zenity --help-info failed, assume icon is not supported
else:
    error('ERR: Zenity command is missing! Diagnostic dialog not available!')


def notify_context():
    """pop up a dialog with context info"""
    def _notify_context(ctx: KeyContext):

        dialog_cmd              = None
        nwln_str                = '\n'

        if kdialog_cmd:
            dialog_cmd          = kdialog_cmd
            nwln_str            = '<br>'
        elif zenity_cmd:
            dialog_cmd          = zenity_cmd
            nwln_str            = '<br>' if zenity_is_qarma else '\n'
        elif not zenity_cmd and not kdialog_cmd:
            error('ERR: Diagnostic dialog not available. Necessary commands missing.')
            return

        if not is_valid_command(dialog_cmd):
            error(f"ERR: Dialog command not valid: '{dialog_cmd}'")
            return

        # fix a problem with zenity and <tags> in text
        def escape_markup(text: str):
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        ctx_clas        = ctx.wm_class
        ctx_name        = ctx.wm_name
        ctx_devn        = ctx.device_name

        message         = ( 
            f"<tt>"
            f"<b>Class:</b> '{escape_markup(ctx_clas)}' {nwln_str}"
            f"<b>Title:</b> '{escape_markup(ctx_name)}' {nwln_str}"
            f"{nwln_str}"
            f"<b>Input keyboard name:</b> '{ctx_devn}' {nwln_str}"
            f"<b>Device seen as type:</b> '{KBTYPE}' {nwln_str}"
            f"{nwln_str}"
            f"<b>Toshy (barebones) config sees this environment:</b>  {nwln_str}"
            f"<b> • DISTRO_ID ____________</b> '{DISTRO_ID      }' {nwln_str}"
            f"<b> • DISTRO_VER ___________</b> '{DISTRO_VER     }' {nwln_str}"
            f"<b> • VARIANT_ID ___________</b> '{VARIANT_ID     }' {nwln_str}"
            f"<b> • SESSION_TYPE _________</b> '{SESSION_TYPE   }' {nwln_str}"
            f"<b> • DESKTOP_ENV __________</b> '{DESKTOP_ENV    }' {nwln_str}"
            f"<b> • DE_MAJ_VER ___________</b> '{DE_MAJ_VER     }' {nwln_str}"
            f"<b> • WINDOW_MGR ___________</b> '{WINDOW_MGR     }' {nwln_str}"
            f"{nwln_str}"
            f"<b> __________________________________________________ </b>{nwln_str}"
            f"<i>Keyboard shortcuts (Ctrl+C/Cmd+C) may not work here.</i>{nwln_str}"
            f"<i>Select text with mouse. Triple-click to select all. </i>{nwln_str}"
            f"<i>Right-click with mouse and choose 'Copy' from menu. </i>{nwln_str}"
            f"</tt>"
        )

        zenity_cmd_lst = [  zenity_cmd, '--info', '--no-wrap', 
                            '--title=Toshy Context Info',
                            '--text=' + message ]

        # insert the icon argument if it's supported
        if zenity_icon_option is not None:
            zenity_cmd_lst.insert(3, zenity_icon_option)

        kdialog_cmd_lst = [kdialog_cmd, '--msgbox', message, '--title', 'Toshy Context Info']
        # Add icon if needed: kdialog_cmd_lst += ['--icon', '/path/to/icon']
        # TODO: Figure out why icon argument doesn't work. Need a proper icon theme folder?
        # Figured out: Kdialog does not support custom icons!
        kdialog_cmd_lst += ['--icon', 'toshy_app_icon_rainbow']

        if dialog_cmd == kdialog_cmd:
            subprocess.Popen(kdialog_cmd_lst, cwd=icons_dir, stderr=DEVNULL, stdout=DEVNULL)
        elif dialog_cmd == zenity_cmd:
            subprocess.Popen(zenity_cmd_lst, cwd=icons_dir, stderr=DEVNULL, stdout=DEVNULL)

        # Optionally, also send a system notification:
        # ntfy.send_notification(message)
    return _notify_context



###################################################################################################
###  SLICE_MARK_START: barebones_user_cfg  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE


# Example keymap that adds British Pound and Euro symbols to any keyboard layout.
keymap("Currency character overlay", {
    C("RAlt-Key_4"):            UC(0x00A3),                     # £ British Pound currency symbol
    C("RAlt-Key_5"):            UC(0x20AC),                     # € Euro currency symbol
}, when = lambda _: True is True)



###  SLICE_MARK_END: barebones_user_cfg  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################
keymap("Diagnostics", {
    C("Shift-Super-Alt-i"):        isDoubleTap(notify_context),     # Diagnostic dialog (primary)
    C("Shift-Super-Alt-h"):        isDoubleTap(notify_context),     # Diagnostic dialog (alternate)
    C("Shift-Super-Alt-t"):        isDoubleTap(macro_tester),       # Type out test macro
}, when = lambda ctx: ctx is ctx )
