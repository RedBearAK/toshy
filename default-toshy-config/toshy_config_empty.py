# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import shutil
import inspect
import subprocess

from subprocess import DEVNULL
from typing import Callable, List, Dict, Union

from keyszer.lib.logger import debug, error
from keyszer.lib.key_context import KeyContext
from keyszer.config_api import *


###################################################################################################
###  SLICE_MARK_START: keyszer_api  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

# Keyszer-specific config settings - REMOVE OR SET TO DEFAULTS FOR DISTRIBUTION
dump_diagnostics_key(Key.F15)   # default key: F15
emergency_eject_key(Key.F16)    # default key: F16

timeouts(
    multipurpose        = 1,        # default: 1 sec
    suspend             = 1,        # default: 1 sec, try 0.1 sec for touchpads
)

# Delays often needed for Wayland (at least in GNOME using shell extensions)
throttle_delays(
    key_pre_delay_ms    = 12,      # default: 0 ms, range: 0-150 ms, suggested: 1-50 ms
    key_post_delay_ms   = 18,      # default: 0 ms, range: 0-150 ms, suggested: 1-100 ms
)

###  SLICE_MARK_END: keyszer_api  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################



###############################################################################
############################   Welcome to Toshy!   ############################
###  
###  This is a highly customized fork of the config file that powers Kinto.sh, 
###  by Ben Reaves
###      (https://kinto.sh)
###  
###  All credit for the basis of this goes to Ben Reaves. 
###      (https://github.com/rbreaves/)
###  
###  Much assistance was provided by Josh Goebel, the developer of the
###  xkeysnail fork "keyszer"
###      (http://github.com/joshgoebel/keyszer)
###  
###############################################################################

home_dir = os.path.expanduser('~')
icons_dir = os.path.join(home_dir, '.local', 'share', 'icons')

# get the path of this file (not the main module loading it)
config_globals = inspect.stack()[1][0].f_globals
current_folder_path = os.path.dirname(os.path.abspath(config_globals["__config__"]))
sys.path.insert(0, current_folder_path)

import lib.env
from lib.settings_class import Settings

assets_path         = os.path.join(current_folder_path, 'assets')
icon_file_active    = os.path.join(assets_path, "toshy_app_icon_rainbow.svg")
icon_file_grayscale = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse_grayscale.svg")
icon_file_inverse   = os.path.join(assets_path, "toshy_app_icon_rainbow_inverse.svg")

# Toshy config file
TOSHY_PART      = 'config'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Config file'
APP_VERSION     = '2023.0604'

# Settings object used to tweak preferences "live" between gui, tray and config.
cnfg = Settings(current_folder_path)
cnfg.watch_database()   # activate watchdog observer on the sqlite3 db file
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
OVERRIDE_DISTRO_NAME     = None
OVERRIDE_DISTRO_VER      = None
OVERRIDE_SESSION_TYPE    = None
OVERRIDE_DESKTOP_ENV     = None

###  SLICE_MARK_END: env_overrides  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE
###################################################################################################

# leave all of this alone!
DISTRO_NAME     = None
DISTRO_VER      = None
SESSION_TYPE    = None
DESKTOP_ENV     = None

env_info: Dict[str, str] = lib.env.get_env_info()   # Returns a dict

DISTRO_NAME     = OVERRIDE_DISTRO_NAME  or env_info.get('DISTRO_NAME')
DISTRO_VER      = OVERRIDE_DISTRO_VER   or env_info.get('DISTRO_VER')
SESSION_TYPE    = OVERRIDE_SESSION_TYPE or env_info.get('SESSION_TYPE')
DESKTOP_ENV     = OVERRIDE_DESKTOP_ENV  or env_info.get('DESKTOP_ENV')

debug("")
debug(  f'Toshy config sees this environment:'
        f'\n\t{DISTRO_NAME      = }'
        f'\n\t{DISTRO_VER       = }'
        f'\n\t{SESSION_TYPE     = }'
        f'\n\t{DESKTOP_ENV      = }\n', ctx="CG")

try:
    # Pylance will complain if function undefined, without 'ignore' comment
    environ_api(session_type = SESSION_TYPE, wl_desktop_env = DESKTOP_ENV) # type: ignore
except NameError:
    debug(f"The API function 'environ_api' is not defined yet.")
    pass



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

# Variable to hold the keyboard type
KBTYPE = None

# Short names for the `keyszer` string and Unicode processing helper functions
ST = to_US_keystrokes           # was 'to_keystrokes' originally
UC = unicode_keystrokes
ignore_combo = ComboHint.IGNORE

###############################################################################
# This is a "trick" to negate the need to put quotes around all the key labels 
# inside the "lists of dicts" to be given to the matchProps() function.
# Makes the variables evaluate to equivalent strings inside the dicts. 
# Provides for nice syntax highlighting and visual separation of key:value. 
clas = 'clas'           # key label for matchProps() arg to match: wm_class
name = 'name'           # key label for matchProps() arg to match: wm_name
devn = 'devn'           # key label for matchProps() arg to match: device_name
not_clas = 'not_clas'   # key label for matchProps() arg to NEGATIVE match: wm_class
not_name = 'not_name'   # key label for matchProps() arg to NEGATIVE match: wm_name
not_devn = 'not_devn'   # key label for matchProps() arg to NEGATIVE match: device_name
numlk = 'numlk'         # key label for matchProps() arg to match: numlock_on
capslk = 'capslk'       # key label for matchProps() arg to match: capslock_on
cse = 'cse'             # key label for matchProps() arg to enable: case sensitivity
lst = 'lst'             # key label for matchProps() arg to pass in a [list] of {dicts}
dbg = 'dbg'             # key label for matchProps() arg to set debugging info string

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


# # OBSOLETED by the "list of dicts" `terminals_lod` below
# # Use the following for testing terminal keymaps
# # terminals = [ "", ... ]
# # xbindkeys -mk
# terminals = [
#     "alacritty",
#     "cutefish-terminal",
#     "deepin-terminal",
#     "eterm",
#     "gnome-terminal",
#     "gnome-terminal-server",
#     "guake",
#     "hyper",
#     "io.elementary.terminal",
#     "kinto-gui.py",
#     "kitty",
#     "Kgx",  # GNOME Console terminal app (comes from "King's Cross")
#     "konsole",
#     "lxterminal",
#     "mate-terminal",
#     "org.gnome.Console",
#     "org.kde.konsole",
#     "roxterm",
#     "qterminal",
#     "st",
#     "sakura",
#     "station",
#     "tabby",
#     "terminator",
#     "termite",
#     "tilda",
#     "tilix",
#     "urxvt",
#     "xfce4-terminal",
#     "xterm",
#     "yakuake",
# ]
# terminals = [x.casefold() for x in terminals]
# termStr = toRgxStr(terminals)

terminals_lod = [
    {clas:"^alacritty$"                 },
    {clas:"^com.raggesilver.BlackBox$"  },
    {clas:"^contour$"                   },
    {clas:"^cutefish-terminal$"         },
    {clas:"^deepin-terminal$"           },
    {clas:"^eterm$"                     },
    {clas:"^gnome-terminal$"            },
    {clas:"^gnome-terminal-server$"     },
    {clas:"^guake$"                     },
    {clas:"^hyper$"                     },
    {clas:"^io.elementary.terminal$"    },
    {clas:"^kinto-gui.py$"              },
    {clas:"^kitty$"                     },
    {clas:"^Kgx$"                       },
    {clas:"^konsole$"                   },
    {clas:"^lxterminal$"                },
    {clas:"^mate-terminal$"             },
    {clas:"^org.gnome.Console$"         },
    {clas:"^org.kde.konsole$"           },
    {clas:"^org.wezfurlong.wezterm$"    },
    {clas:"^roxterm$"                   },
    {clas:"^qterminal$"                 },
    {clas:"^st$"                        },
    {clas:"^sakura$"                    },
    {clas:"^station$"                   },
    {clas:"^tabby$"                     },
    {clas:"^terminator$"                },
    {clas:"^termite$"                   },
    {clas:"^tilda$"                     },
    {clas:"^tilix$"                     },
    {clas:"^urxvt$"                     },
    {clas:"^xfce4-terminal$"            },
    {clas:"^xterm$"                     },
    {clas:"^yakuake$"                   },
]

# TODO: remove usage of this in favor of `vscodes_lod` below it
vscodes = [
    "code",
    "vscodium",
    "code - oss",
]
vscodes = [x.casefold() for x in vscodes]
vscodeStr = toRgxStr(vscodes)

vscodes_lod = [
    {clas:"^code$"},
    {clas:"^vscodium$"},
    {clas:"^code - oss$"},
]

sublimes = [
    "sublime_text",
    "subl",
]
sublimes = [x.casefold() for x in sublimes]
sublimeStr = toRgxStr(sublimes)

JDownloader_lod = [
    {clas: "^.*jdownloader.*$"},
    {clas: "^java-lang-Thread$", name: "^JDownloader.*$"}   # Happens after auto-update of app
]

# Add remote desktop clients & VM software here
# Ideally we'd only exclude the client window,
# but that may not be easily done. 
# (Can be done now with `keyszer`, as long as main window has a 
# different WM_NAME than client windows. See `remotes_lod` below.)
remotes = [
    "Gnome-boxes",
    "org.remmina.Remmina",
    "Nxplayer.bin",
    "remmina",
    "qemu-system-.*",
    "qemu",
    "Spicy",
    "Virt-manager",
    "VirtualBox",
    "VirtualBox Machine",
    "xfreerdp",
    "Wfica",
]
remotes = [x.casefold() for x in remotes]
remoteStr = toRgxStr(remotes)

remotes_lod = [
    {clas:"^Gnome-boxes$"                },
    {clas:"^org.remmina.Remmina$", not_name:"^Remmina Remote Desktop Client$|^Remote Connection Profile$"},
    {clas:"^Nxplayer.bin$"               },
    {clas:"^remmina$"                    },
    {clas:"^qemu-system-.*$"             },
    {clas:"^qemu$"                       },
    {clas:"^Spicy$"                      },
    {clas:"^Virt-manager$"               },
    {clas:"^VirtualBox$"                 },
    {clas:"^VirtualBox Machine$"         },
    {clas:"^xfreerdp$"                   },
    {clas:"^Wfica$"                      },
]

# # OBSOLETED by "list of dicts" `terminals_lod` above
# # Add remote desktop clients & VMs for no remapping
# terminals.extend(remotes)
# termStr_ext = toRgxStr(terminals)

terminals_and_remotes_lod = [
    {lst:terminals_lod                  },
    {lst:remotes_lod                    },
]

vscodes.extend(remotes)
vscodeStr_ext = toRgxStr(vscodes)

vscodes_and_remotes_lod = [
    {lst:vscodes_lod                    },
    {lst:remotes_lod                    },
]

browsers_chrome = [
    "Brave-browser",
    "Chromium",
    "Chromium-browser",
    "Google-chrome",
    "microsoft-edge",
    "microsoft-edge-dev",
    "org.deepin.browser",
]
browsers_chrome         = [x.casefold() for x in browsers_chrome]
browsers_chromeStr      = "|".join('^'+x+'$' for x in browsers_chrome)

browsers_firefox = [
    "Firefox",
    "Firefox Developer Edition",
    "firefoxdeveloperedition",
    "LibreWolf",
    "Mullvad Browser",
    "Navigator",
    "Waterfox",
]
browsers_firefox        = [x.casefold() for x in browsers_firefox]
browsers_firefoxStr     = "|".join('^'+x+'$' for x in browsers_firefox)

browsers_all = [
    # unpack Chrome and Firefox lists into this general browser list
    *browsers_chrome,
    *browsers_firefox,
    "Discord",
    "Epiphany",
    "org.gnome.Epiphany",
]
browsers_all            = [x.casefold() for x in browsers_all]
browsers_allStr         = "|".join('^'+x+'$' for x in browsers_all)

filemanagers = [
    "caja",
    "dde-file-manager",
    "dolphin",
    "io.elementary.files",
    "nautilus",
    "nemo",
    "org.gnome.nautilus",
    "org.kde.dolphin",
    "pcmanfm",
    "pcmanfm-qt",
    "spacefm",
    "thunar",
]
filemanagers = [x.casefold() for x in filemanagers]
filemanagerStr = "|".join('^'+x+'$' for x in filemanagers)

### dialogs_Escape_lod = send these windows the Escape key for Cmd+W
dialogs_Escape_lod = [
    {clas:"^.*nautilus$", name:"^.*Properties$|^Preferences$|^Create Archive$"},
    {clas:"^Transmission-gtk$|^com.transmissionbt.Transmission.*$", not_name:"^Transmission$"},
    {clas:"^org.gnome.Software$", not_name:"^Software$"},
    {clas:"^gnome-text-editor$|^org.gnome.TextEditor$", name:"^Preferences$"},
    {clas:"^org.gnome.Shell.Extensions$"},
    {clas:"^konsole$|^org.kde.konsole$", name:"^Configure.*Konsole$|^Edit Profile.*Konsole$"},
    {clas:"^org.kde.KWrite$", name:"^Configure.*KWrite$"},
    {clas:"^org.kde.Dolphin$", name:"^Configure.*Dolphin$|^Properties.*Dolphin$"},
    {clas:"^xfce4-terminal$", name:"^Terminal Preferences$"},
    {clas:"^epiphany$|^org.gnome.Epiphany$", name:"^Preferences$"},
    {clas:"^Angry.*IP.*Scanner$",
        name:"^IP.*address.*details.*$|^Preferences.*$|^Scan.*Statistics.*$|^Edit.*openers.*$"},
]

### dialogs_CloseWin_lod = send these windows the "Close window" combo for Cmd+W
dialogs_CloseWin_lod = [
    {clas:"^Gnome-control-center$", not_name:"^Settings$"},
    {clas:"^gnome-terminal.*$", name:"^Preferences.*$"},
    {clas:"^gnome-terminal-pref.*$", name:"^Preferences.*$"},
    {clas:"^pcloud$"},
    {clas:"^Totem$", not_name:"^Videos$"},
    {clas:"^Angry.*IP.*Scanner$", name:"^Fetchers.*$|^Edit.*favorites.*$"},
]


###################################################################################################
###  SLICE_MARK_START: kbtype_override  ###  EDITS OUTSIDE THESE MARKS WILL BE LOST ON UPGRADE

keyboards_UserCustom_dct = {
    # Add your keyboard device here if its type is misidentified by isKBtype() function
    # Valid types to map device to: Apple, Windows, IBM, Chromebook
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


def check_notify_send():
    """check that notify-send command supports -p flag"""
    try:
        subprocess.run(['notify-send', '-p'], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Check if the error message contains "Unknown option" for -p flag
        error_output: bytes = e.stderr  # type hint to validate decode()
        if 'Unknown option' in error_output.decode('utf-8'):
            return False
    return True


is_p_option_supported = check_notify_send()

ntfy_cmd        = shutil.which('notify-send')
ntfy_prio       = '--urgency=normal' # '--urgency=critical'
ntfy_icon       = f'--icon=\"{icon_file_active}\"'
ntfy_title      = 'Toshy Alert'
ntfy_id_new     = None
ntfy_id_last    = '0' # initiate with integer string to avoid error


def isKBtype(kbtype: str, map=None):
    # guard against failure to give valid type arg
    if kbtype not in ['IBM', 'Chromebook', 'Windows', 'Apple']:
        raise ValueError(f"Invalid type given to isKBtype() function: '{kbtype}'"
                f'\n\t Valid keyboard types (case sensitive): IBM | Chromebook | Windows | Apple')
    kbtype_cf = kbtype.casefold()
    KBTYPE_cf = KBTYPE.casefold() if isinstance(KBTYPE, str) else None

    def _isKBtype(ctx):
        # debug(f"KBTYPE: '{KBTYPE}' | isKBtype check from map: '{map}'")
        return kbtype_cf == KBTYPE_cf
    return _isKBtype


kbtype_cache_dct = {}


def getKBtype():
    """
    ### Get the keyboard type string for the current device
    
    #### Valid Types
    
    - IBM | Chromebook | Windows | Apple
    
    #### Hierarchy of validations:
    
    1. Check if the device name is in the keyboards_UserCustom_dct dictionary.
    2. Check if the device name matches any keyboard type list.
    3. Check if any keyboard type string is found in the device name string.
    4. Check if the device name indicates a "Windows" keyboard by excluding other types.
    """

    def _getKBtype(ctx: KeyContext):
        global KBTYPE
        kbd_dev_name = ctx.device_name

        def log_kbtype(msg=None, cache_dev=True):
            debug(f"KBTYPE: '{KBTYPE}' | {msg}: '{kbd_dev_name}'")
            if cache_dev:
                kbtype_cache_dct[kbd_dev_name] = (KBTYPE, msg)

        # Check in the kbtype cache dict for the device
        if kbd_dev_name in kbtype_cache_dct:
            KBTYPE, cached_msg = kbtype_cache_dct[kbd_dev_name]
            log_kbtype(f'{cached_msg} (cached)', cache_dev=False)
            return

        kbd_dev_name_cf = ctx.device_name.casefold()

        # Check if there is a custom type for the device
        custom_kbtype = kbds_UserCustom_dct_cf.get(kbd_dev_name_cf, '')
        if custom_kbtype and custom_kbtype in ['IBM', 'Chromebook', 'Windows', 'Apple']:
            KBTYPE = custom_kbtype
            log_kbtype('Custom type for dev')
            return

        # Check against the keyboard type lists
        for kbtype, regex_lst in kbtype_lists_rgx.items():
            for rgx in regex_lst:
                if rgx.search(kbd_dev_name_cf):
                    KBTYPE = kbtype
                    log_kbtype('Rgx matched on dev')
                    return

        # Check if any keyboard type string is found in the device name
        for kbtype in ['IBM', 'Chromebook', 'Windows', 'Apple']:
            if kbtype.casefold() in kbd_dev_name_cf:
                KBTYPE = kbtype
                log_kbtype('Type in dev name')
                return

        # Check if the device name indicates a "Windows" keyboard
        if ('windows' not in kbd_dev_name_cf 
            and not not_win_type_rgx.search(kbd_dev_name_cf) 
            and not all_kbds_rgx.search(kbd_dev_name_cf) ):
            KBTYPE = 'Windows'
            log_kbtype('Default type for dev')
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
    `devn` = Device Name (regex/string) [keyszer --list-devices]    \n
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
    A dict can also contain a single `lst` or `not_lst` argment.    \n

    ### Debugging info parameter: `dbg`
    A string that will print as part of logging output. Use to      \n
    help identify origin of logging output.                         \n
    -                                                               \n
    """
    # Reference for successful negative lookahead pattern, and 
    # explanation of why it works:
    # https://stackoverflow.com/questions/406230/\
        # regular-expression-to-match-a-line-that-doesnt-contain-a-word

    logging_enabled = False
    allowed_params  = (clas, name, devn, not_clas, not_name, not_devn, 
                        numlk, capslk, cse, lst, not_lst, dbg)
    lst_dct_params  = (clas, name, devn, not_clas, not_name, not_devn, 
                        numlk, capslk, cse)
    string_params   = (clas, name, devn, not_clas, not_name, not_devn, dbg)
    dct_param_strs  = list(inspect.signature(matchProps).parameters.keys())

    if all([x is None for x in allowed_params]): 
        raise ValueError(f"\n\n(EE) matchProps(): Received no valid argument\n")
    if any([x not in (True, False, None) for x in (numlk, capslk, cse)]): 
        raise TypeError(f"\n\n(EE) matchProps(): Params 'nlk|clk|cse' are bools\n")
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
            if not_lst is not None:
                if logging_enabled: print(f"## _matchProps_Lst()[not_lst] ## {dbg=}")
                return not any(matchProps(**dct)(ctx) for dct in not_lst)
            else:
                if logging_enabled: print(f"## _matchProps_Lst()[lst] ## {dbg=}")
                return any(matchProps(**dct)(ctx) for dct in lst)

        return _matchProps_Lst      # outer function returning inner function

    # compile case insentitive regex object for given params, unless cse=True
    if _clas is not None: clas_rgx = re.compile(_clas) if cse else re.compile(_clas, re.I)
    if _name is not None: name_rgx = re.compile(_name) if cse else re.compile(_name, re.I)
    if _devn is not None: devn_rgx = re.compile(_devn) if cse else re.compile(_devn, re.I)

    def _matchProps(ctx: KeyContext):
        cond_list = []
        if _clas is not None:
            clas_match = re.search(clas_rgx,
                                    ctx.wm_class or 'ERR: matchProps: NoneType in ctx.wm_class')
            cond_list.append(not clas_match if not_clas is not None else clas_match)
        if _name is not None:
            name_match = re.search(name_rgx,
                                    ctx.wm_name or 'ERR: matchProps: NoneType in ctx.wm_name')
            cond_list.append(not name_match if not_name is not None else name_match)
        if _devn is not None:
            devn_match = re.search(devn_rgx,
                                    ctx.device_name or 'ERR: matchProps: NoneType in ctx.device_name')
            cond_list.append(not devn_match if not_devn is not None else devn_match)
        # these two MUST check explicitly for "is not None" because external input is True/False,
        # and we want to be able to match the LED_on state of either "True" or "False"
        if numlk is not None: cond_list.append( numlk is ctx.numlock_on  )
        if capslk is not None: cond_list.append( capslk is ctx.capslock_on )
        if logging_enabled: # and all(cnd_lst): # << add this to show only "True" condition lists
            print(f'####  CND_LST ({all(cond_list)})  ####  {dbg=}')
            for elem in cond_list:
                print('##', re.sub('^.*span=.*\), ', '', str(elem)).replace('>',''))
            print('-------------------------------------------------------------------')
        return all(cond_list)

    return _matchProps      # outer function returning inner function


# Boolean variable to toggle Enter key state between F2 and Enter
# True = Enter key sends F2, False = Enter key sends Enter
_enter_is_F2 = True     # DON'T CHANGE THIS! Must be set to True here. 


def is_Enter_F2(combo_if_true, latch_or_combo_if_false):
    """
    Send a different combo for Enter key depending on state of _enter_is_F2 variable,\n 
    or latch the variable to True or False to control the Enter key state on next use.
    
    This enables a simulation of the Finder "Enter to rename" capability.
    """
    def _is_Enter_F2():
        global _enter_is_F2
        combo_list = [combo_if_true]
        if latch_or_combo_if_false in (True, False):    # Latch variable to given bool value
            _enter_is_F2 = latch_or_combo_if_false
        elif _enter_is_F2:                              # If Enter is F2 now, set to be Enter next
            _enter_is_F2 = False
        else:                                           # If Enter is Enter now, set to be F2 next
            combo_list = [latch_or_combo_if_false]
            _enter_is_F2 = True
        return combo_list
    return _is_Enter_F2


def macro_tester():
    def _macro_tester(ctx: KeyContext):
        return [
                    C("Enter"),
                    ST(f"Appl. Class: '{ctx.wm_class}'"), C("Enter"),
                    ST(f"Wind. Title: '{ctx.wm_name}'"), C("Enter"),
                    ST(f"Kbd. Device: '{ctx.device_name}'"), C("Enter"),
                    ST("Next test should come out on ONE LINE!"), C("Enter"),
                    ST("Unicode and Shift Test: 🌹—€—\u2021—ÿ—\U00002021 12345 !@#$% |\ !!!!!!"),
                    C("Enter")
        ]
    return _macro_tester


zenity_icon_option = None
try:
    zenity_help_output = subprocess.check_output(['zenity', '--help-info'])
    help_text = str(zenity_help_output)
    if '--icon=' in help_text:
        zenity_icon_option = '--icon=toshy_app_icon_rainbow'
    elif '--icon-name=' in help_text:
        zenity_icon_option = '--icon-name=toshy_app_icon_rainbow'
except subprocess.CalledProcessError:
    pass  # zenity --help-info failed, assume icon is not supported

def notify_context():
    """pop up a notification with context info"""
    def _notify_context(ctx: KeyContext):
        global zenity_icon_option
        zenity_cmd = [  'zenity', '--info', '--no-wrap', 
                        '--title=Toshy Context Info',
                        (
                        '--text='
                        f"Appl. Class   = '{ctx.wm_class}'"
                        f"\nWndw. Title = '{ctx.wm_name}'"
                        f"\nKbd. Device = '{ctx.device_name}'"
                        )]
        # insert the icon argument if it's supported
        if zenity_icon_option is not None:
            zenity_cmd.insert(3, zenity_icon_option)
        subprocess.Popen(zenity_cmd, cwd=icons_dir, stderr=DEVNULL, stdout=DEVNULL)
    return _notify_context


# # DEPRECATED: old form of isKBtype()
# def XisKBtype(kbtype: str, map=None):
#     """
#     ### Match on the keyboard type for conditional modmaps and keymaps
    
#     #### Valid Types
    
#     - IBM | Chromebook | Windows | Apple
    
#     #### Hierarchy of validations:
    
#     1. Check if the device name is in the keyboards_UserCustom_dct dictionary.
#     2. Is device name in keyboard type list matching `kbtype` arg?
#     3. Is `kbtype` string in the device name string?
#     4. Is `kbtype` "Windows" and other type strings _not_ in device name
#         and device name _not_ in `all_keyboards` list?
#     """

#     # guard against failure to give valid type arg
#     if kbtype not in ['IBM', 'Chromebook', 'Windows', 'Apple']:
#         raise ValueError(  f"Invalid type given to isKBtype() function: '{kbtype}'"
#                 f'\n\t Valid keyboard types (case sensitive): IBM | Chromebook | Windows | Apple')

#     # Create a "UserCustom" keyboard dictionary with casefolded keys
#     kbds_UserCustom_lower_dct   = {k.casefold(): v for k, v in keyboards_UserCustom_dct.items()}
#     kbtype_cf                   = kbtype.casefold()
#     regex_lst                   = kbtype_lists_rgx.get(kbtype, [])
#     not_win_type_rgx            = re.compile("IBM|Chromebook|Apple", re.I)
#     all_kbds_rgx                = re.compile(toRgxStr(all_keyboards), re.I)

#     def _isKBtype(ctx: KeyContext):
#         logging_enabled = True
#         kb_dev_name = ctx.device_name.casefold()

#         # get custom type for device, if there is one
#         custom_kbtype   = str(kbds_UserCustom_lower_dct.get(kb_dev_name, ''))
#         cust_kbtype_cf  = custom_kbtype.casefold()
#         # check that a valid type is being given in custom dict
#         if custom_kbtype and custom_kbtype not in ['IBM', 'Chromebook', 'Windows', 'Apple']:
#             raise ValueError(  f"Invalid custom keyboard type: '{custom_kbtype}'"
#                     f'\n\t Valid keyboard types (case sensitive): IBM | Chromebook | Windows | Apple')
#             return False
#         # check for type match/mismatch only if custom type is truthy (no regex, literal string)
#         if cust_kbtype_cf and cust_kbtype_cf == kbtype_cf:
#             if logging_enabled:
#                 debug(f"KB_TYPE: '{kbtype}' | Type override given for device: '{ctx.device_name}'")
#             return True
#         elif cust_kbtype_cf and cust_kbtype_cf != kbtype_cf:
#             return False

#         for rgx in regex_lst:
#             match = rgx.search(kb_dev_name)
#             if match:
#                 if logging_enabled:
#                     debug(f"KB_TYPE: '{kbtype}' | Regex matched on device name: '{ctx.device_name}'")
#                 return True

#         if kbtype_cf == 'apple' and 'magic' in kb_dev_name and 'keyboard' in kb_dev_name:
#             if logging_enabled:
#                 debug(f"KB_TYPE: '{kbtype}' | Identified as Magic Keyboard: '{ctx.device_name}' ")
#             return True

#         if kbtype_cf in kb_dev_name:
#             if logging_enabled:
#                 debug(f"KB_TYPE: '{kbtype}' | Type found in device name: '{ctx.device_name}'")
#             return True

#         if kbtype_cf == 'windows':
#             # check there are no non-Windows type keywords in the device name
#             if not_win_type_rgx.search(kb_dev_name):
#                 return False
#             # check device name is not in any existing default list
#             # this seems unnecessary and redundant if regex matching is working...
#             if not all_kbds_rgx.search(kb_dev_name):
#                 if logging_enabled:
#                     debug(f"KB_TYPE: '{kbtype}' | Device given default type: '{ctx.device_name}'")
#                 return True
#         return False

#     return _isKBtype    # return the inner function



#################################  MODMAPS  ####################################
###                                                                          ###
###                                                                          ###
###      ███    ███  ██████  ██████  ███    ███  █████  ██████  ███████      ###
###      ████  ████ ██    ██ ██   ██ ████  ████ ██   ██ ██   ██ ██           ###
###      ██ ████ ██ ██    ██ ██   ██ ██ ████ ██ ███████ ██████  ███████      ###
###      ██  ██  ██ ██    ██ ██   ██ ██  ██  ██ ██   ██ ██           ██      ###
###      ██      ██  ██████  ██████  ██      ██ ██   ██ ██      ███████      ###
###                                                                          ###
###                                                                          ###
################################################################################
### Modmaps turn a key into a different key as long as the modmap is active
### The modified key can be used in shortcut combos as the new key




### KEYMAPS:

keymap("Currency character overlay", {
    C("RAlt-Key_3"):            UC(0x00A3),                     # £ British Pound currency symbol
    C("RAlt-Key_5"):            UC(0x20AC),                     # € Euro currency symbol
}, when = lambda _: True is True)
