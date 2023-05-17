# -*- coding: utf-8 -*-

import re
import os
import sys
import time
import inspect
import subprocess

from typing import Any, Callable, List, Dict, Union
from keyszer.lib.logger import debug, error
from keyszer.lib.key_context import KeyContext
from keyszer.config_api import *


# Keyszer-specific config settings - REMOVE OR SET TO DEFAULTS FOR DISTRIBUTION
dump_diagnostics_key(Key.F15)   # default key: F15
emergency_eject_key(Key.F16)    # default key: F16
timeouts(
    multipurpose    = 1,        # default: 1 sec
    suspend         = 1,        # default: 1 sec, try 0.1 sec for touchpads
)
throttle_delays(
    key_pre_delay_ms  = 0,      # default: 0 ms, range: 0-150 ms, suggested: 1-50 ms
    key_post_delay_ms = 0,      # default: 0 ms, range: 0-150 ms, suggested: 1-100 ms
)


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

# get the path of this file (not the main module loading it)
config_globals = inspect.stack()[1][0].f_globals
config_dir_path = os.path.dirname(os.path.abspath(config_globals["__config__"]))
sys.path.insert(0, config_dir_path)

import lib.env
from lib.settings_class import Settings

# Toshy config file
TOSHY_PART      = 'config'   # CUSTOMIZE TO SPECIFIC TOSHY COMPONENT! (gui, tray, config)
TOSHY_PART_NAME = 'Toshy Config file'
APP_VERSION     = '2023.0516'

# Settings object used to tweak preferences "live" between gui, tray and config.
cnfg = Settings(config_dir_path)
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

OVERRIDE_DISTRO_NAME     = None
OVERRIDE_DISTRO_VER      = None
OVERRIDE_SESSION_TYPE    = None
OVERRIDE_DESKTOP_ENV     = None

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

# future API to inject environment info into `keyszer`
# environ_context(
#     session_type = SESSION_TYPE,
#     distro_name = DISTRO_NAME,
#     desktop_env = DESKTOP_ENV
# )



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
# Establish important variables here

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
case = 'case'           # key label for matchProps() arg to enable: case sensitivity
lst = 'lst'             # key label for matchProps() arg to pass in a [list] of {dicts}
dbg = 'dbg'             # key label for matchProps() arg to set debugging info string

# global variables for the isDoubleTap() function
tapTime1 = time.time()
tapInterval = 0.24
tapCount = 0
last_dt_combo = None




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


def isKBtype(kbtype: str, map=None):
    """
    ## Match on the keyboard type for conditional modmaps and keymaps
    
    ### Valid Types
    
    - IBM | Chromebook | Windows | Apple

    ### Hierarchy of validations:

    1. Is device name in keyboard type list matching `kbtype` arg?
    2. Is `kbtype` string in the device name string?
    3. Is `kbtype` "Windows" and other type strings _not_ in device name
        and device name _not_ in `all_keyboards` list?
    """
    regex_list = kbtype_lists.get(kbtype, [])
    def _isKBtype(ctx: KeyContext):
        logging_enabled = False
        kb_dev_name = ctx.device_name.casefold()
        for regex in regex_list:
            if re.search(regex, kb_dev_name, re.I):
                if logging_enabled:
                    debug(f'KB_TYPE: "{kbtype}" {re.search(regex, kb_dev_name, re.I)}')
                return True
        if kbtype.casefold() in kb_dev_name:
            if logging_enabled:
                debug(f'KB_TYPE: "{kbtype}" Keyword found in device name.')
            return True
        if kbtype == "Windows":
            if not re.search("IBM|Chromebook|Apple", kb_dev_name, re.I):
                if kb_dev_name not in all_keyboards:
                    if logging_enabled:
                        debug(f'KB_TYPE: "{kbtype}" Unidentified, not in other lists, "IBM|Chromebook|Apple" not in name.')
                    return True
        return False

    return _isKBtype


def isDoubleTap(dt_combo):
    """
    Simplistic detection of double-tap of a key. BLOCKS single-tap function.
    Only cares about the 'real' key in a combo of Mods+key.
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


# def toggle_media_arrows_fix():
#     """Toggle the value of the media_arrows_fix variable"""
#     # Needs "from subprocess import run" somewhere
#     def _toggle_media_arrows_fix():
#         global media_arrows_fix
#         media_arrows_fix = not media_arrows_fix
#         if media_arrows_fix:
#             subprocess.run('notify-send -u critical ALERT "Media Arrows Fix is now ENABLED.\
#                 \rMedia function arrow keys will be PgUp/PgDn/Home/End\
#                 \rwhen used with the Fn key.\
#                 \rDisable with Shift+Opt+Cmd+M."', shell=True)
#             debug("Media Arrows Fix is now ENABLED.")
#         else:
#             subprocess.run('notify-send -u critical ALERT "Media Arrows Fix is now DISABLED.\
#                 \rRe-enable with Shift+Opt+Cmd+M."', shell=True)
#             debug("Media Arrows Fix is now DISABLED.")

#     return _toggle_media_arrows_fix


# Correct syntax to reject all positional parameters: put `*,` at beginning
def matchProps(*,
    # string parameters (positive matching)
    clas: str = None, name: str = None, devn: str = None,
    # string parameters (negative matching)
    not_clas: str = None, not_name: str = None, not_devn: str = None,
    # bool parameters
    numlk: bool = None, capslk: bool = None, case: bool = None,
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
    `case`     = Case Sensitive matching    (bool)                  \n
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
                        numlk, capslk, case, lst, not_lst, dbg)
    lst_dct_params  = (clas, name, devn, not_clas, not_name, not_devn, 
                        numlk, capslk, case)
    string_params   = (clas, name, devn, not_clas, not_name, not_devn, dbg)
    dct_param_strs  = list(inspect.signature(matchProps).parameters.keys())

    if all([x is None for x in allowed_params]): 
        raise ValueError(f"\n\n(EE) matchProps(): Received no valid argument\n")
    if any([x not in (True, False, None) for x in (numlk, capslk, case)]): 
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
    if _clas is not None: clas_rgx = re.compile(_clas) if case else re.compile(_clas, re.I)
    if _name is not None: name_rgx = re.compile(_name) if case else re.compile(_name, re.I)
    if _devn is not None: devn_rgx = re.compile(_devn) if case else re.compile(_devn, re.I)

    def _matchProps(ctx: KeyContext):
        cond_list = []
        if _clas is not None:
            clas_match = re.search(clas_rgx, ctx.wm_class)
            cond_list.append(not clas_match if not_clas is not None else clas_match)
        if _name is not None:
            name_match = re.search(name_rgx, ctx.wm_name)
            cond_list.append(not name_match if not_name is not None else name_match)
        if _devn is not None:
            devn_match = re.search(devn_rgx, ctx.device_name)
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


def toRgxStr(lst_of_str):
    """
    Convert a list of strings into a casefolded             \n
    concatenated regex pattern string.
    """
    if not isinstance(lst_of_str, list): raise TypeError(\
        f"\n\n###  toRgxStr wants a list of strings  ###\n")
    elif isinstance(lst_of_str, list):
        if any([not isinstance(x, str) for x in lst_of_str]): raise TypeError(\
            f"\n\n###  toRgxStr wants a list of strings  ###\n")
        lst_of_str_clean = [str(x).replace('^','').replace('$','') for x in lst_of_str]
        return "|".join(str('^'+x.casefold()+'$') for x in lst_of_str_clean)


def negRgx(rgx_str):
    """
    Invert/convert a positive match regex pattern into      \n
    a negative lookahead regex pattern.
    """
    # remove any ^$
    rgx_str_strip = str(rgx_str).replace('^','').replace('$','')
    # add back ^$, but only around ENTIRE STRING (ignore any vertical bars/pipes)
    rgx_str_add = str('^'+rgx_str_strip+'$')
    # convert ^$ to complicated negative lookahead pattern that actually works
    neg_rgx_str = str(rgx_str_add).replace('^','^(?:(?!^').replace('$','$).)*$')
    return neg_rgx_str



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

# Use the following for testing terminal keymaps
# terminals = [ "", ... ]
# xbindkeys -mk
terminals = [
    "alacritty",
    "cutefish-terminal",
    "deepin-terminal",
    "eterm",
    "gnome-terminal",
    "gnome-terminal-server",
    "guake",
    "hyper",
    "io.elementary.terminal",
    "kinto-gui.py",
    "kitty",
    "Kgx",                      # GNOME Console terminal app
    "konsole",
    "lxterminal",
    "mate-terminal",
    "org.gnome.Console",
    "roxterm",
    "qterminal",
    "st",
    "sakura",
    "station",
    "tabby",
    "terminator",
    "termite",
    "tilda",
    "tilix",
    "urxvt",
    "xfce4-terminal",
    "xterm",
    "yakuake",
]
terminals = [x.casefold() for x in terminals]
termStr = toRgxStr(terminals)

terminals_lod = [
    {clas:"^alacritty$"                 },
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
    {clas:"^org.remmina.Remmina$",       not_name:"^Remmina Remote Desktop Client$|^Remote Connection Profile$"},
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

# Add remote desktop clients & VMs for no remapping
terminals.extend(remotes)
termStr_ext = toRgxStr(terminals)

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

# Use for browser specific hotkeys
browsers = [
    "Brave-browser",
    "Chromium",
    "Chromium-browser",
    "Discord",
    "Epiphany",
    "Firefox",
    "Firefox Developer Edition",
    "firefoxdeveloperedition",
    "Google-chrome",
    "microsoft-edge",
    "microsoft-edge-dev",
    "Navigator",
    "org.deepin.browser",
    "Waterfox",
]
browsers = [x.casefold() for x in browsers]
browserStr = "|".join(str('^'+x+'$') for x in browsers)

chromes = [
    "Brave-browser",
    "Chromium",
    "Chromium-browser",
    "Google-chrome",
    "microsoft-edge",
    "microsoft-edge-dev",
    "org.deepin.browser",
]
chromes = [x.casefold() for x in chromes]
chromeStr = "|".join(str('^'+x+'$') for x in chromes)

filemanagers = [
    "caja",
    "dde-file-manager",
    "dolphin",
    "io.elementary.files",
    "nautilus",
    "nemo",
    "org.gnome.nautilus",
    "pcmanfm",
    "pcmanfm-qt",
    "spacefm",
    "thunar",
]
filemanagers = [x.casefold() for x in filemanagers]
filemanagerStr = "|".join(str('^'+x+'$') for x in filemanagers)

### dialogs_Esc_lod = send these windows the Escape key for Cmd+W
dialogs_Esc_lod = [
    {clas:"^.*nautilus$",                name:"^.*Properties$|^Preferences$|^Create Archive$"},
    {clas:"^Transmission-gtk$",          not_name:"^Transmission$"},
    {clas:"^org.gnome.Software$",        not_name:"^Software$"},
    {clas:"^gnome-text-editor|org.gnome.TextEditor$", name:"^Preferences$"},
    {clas:"^org.gnome.Shell.Extensions$"},
]

### dialogs_CloseWin_lod = send these windows the "Close window" combo for Cmd+W
dialogs_CloseWin_lod = [
    {clas:"^Gnome-control-center$",      not_name:"^Settings$"},
    {clas:"^gnome-terminal$",            name:"^Preferences.*$"},
    {clas:"^gnome-terminal-pref.*$",   name:"^Preferences.*$"},
    {clas:"^pcloud$"                     },
    {clas:"^Totem$",                     not_name:"^Videos$"},
]

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
    'Google .* Keyboard',
    '.* Chromebook Keyboard',
]
keyboards_Windows = [
    # Add specific Windows/PC keyboard device names to this list
    'AT Translated Set 2 keyboard',
]
keyboards_Apple = [
    # Add specific Apple/Mac keyboard device names to this list
    'Mitsumi Electric Apple Extended USB Keyboard',
]

kbtype_lists = {
    'IBM': keyboards_IBM, 
    'Chromebook': keyboards_Chromebook, 
    'Windows': keyboards_Windows, 
    'Apple': keyboards_Apple
}

# List of all known keyboard devices from all lists
all_keyboards = [kb for kbtype in kbtype_lists.values() for kb in kbtype]
all_kbs_rgx = re.compile(toRgxStr(all_keyboards), re.I)



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


modmap("Cond modmap - Media Arrows Fix",{
    # Fix arrow keys with media functions instead of PgUp/PgDn/Home/End
    Key.PLAYPAUSE:              Key.PAGE_UP,
    Key.STOPCD:                 Key.PAGE_DOWN,
    Key.PREVIOUSSONG:           Key.HOME,
    Key.NEXTSONG:               Key.END,
# }, when = lambda _: media_arrows_fix is True)
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    cnfg.media_arrows_fix is True )


modmap("Cond modmap - Forced Numpad feature",{
    # Make numpad be a numpad regardless of Numlock state (like an Apple keyboard in macOS)
    Key.KP1:                    Key.KEY_1,
    Key.KP2:                    Key.KEY_2,
    Key.KP3:                    Key.KEY_3,
    Key.KP4:                    Key.KEY_4,
    Key.KP5:                    Key.KEY_5,
    Key.KP6:                    Key.KEY_6,
    Key.KP7:                    Key.KEY_7,
    Key.KP8:                    Key.KEY_8,
    Key.KP9:                    Key.KEY_9,
    Key.KP0:                    Key.KEY_0,
    Key.KPDOT:                  Key.DOT,  
    Key.KPENTER:                Key.ENTER,
# }, when = lambda _: forced_numpad is True)
}, when = lambda ctx: 
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    cnfg.forced_numpad is True )


modmap("Cond modmap - GTK3 numpad nav keys fix",{
    # Make numpad nav keys work correctly in GTK3 apps
    # Key.KP5:                    Key.X,                          # GTK3 numpad fix - TEST TO SEE IF WORKING
    # Numpad PgUp/PgDn/Home/End keys
    Key.KP9:                    Key.PAGE_UP, 
    Key.KP3:                    Key.PAGE_DOWN, 
    Key.KP7:                    Key.HOME, 
    Key.KP1:                    Key.END,
    # Numpad arrow keys
    Key.KP8:                    Key.UP, 
    Key.KP2:                    Key.DOWN, 
    Key.KP4:                    Key.LEFT, 
    Key.KP6:                    Key.RIGHT,
    # Numpad Insert/Delete/Enter keys
    Key.KP0:                    Key.INSERT, 
    Key.KPDOT:                  Key.DELETE, 
    Key.KPENTER:                Key.ENTER,
# }, when = lambda ctx: ctx.numlock_on is False and forced_numpad is False)
# }, when = lambda ctx: ctx.numlock_on is False and cnfg.forced_numpad is False )
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    matchProps(numlk=False)(ctx) and 
    cnfg.forced_numpad is False )


# multipurpose_modmap("Optional Tweaks",
#     # {Key.ENTER:                 [Key.ENTER, Key.RIGHT_CTRL]     # Enter2Cmd
#     # {Key.CAPSLOCK:              [Key.ESC, Key.RIGHT_CTRL]       # Caps2Esc
#     # {Key.LEFT_META:             [Key.ESC, Key.RIGHT_CTRL]       # Caps2Esc - Chromebook
#     {                                                             # Placeholder
# })


multipurpose_modmap("Enter2Cmd", {
    Key.ENTER:                  [Key.ENTER, Key.RIGHT_CTRL]     # Enter2Cmd
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    cnfg.Enter2Ent_Cmd is True )

multipurpose_modmap("Caps2Esc - not Chromebook kbd", {
    Key.CAPSLOCK:               [Key.ESC, Key.RIGHT_CTRL]       # Caps2Esc - not Chromebook
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    not isKBtype('Chromebook')(ctx) and 
    cnfg.Caps2Esc_Cmd is True )

multipurpose_modmap("Caps2Esc - Chromebook kbd", {
    Key.LEFT_META:               [Key.ESC, Key.RIGHT_CTRL]       # Caps2Esc - Chromebook
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Chromebook')(ctx) and 
    cnfg.Caps2Esc_Cmd is True )



# Fix for avoiding modmapping when using Synergy keyboard/mouse sharing.
# Synergy doesn't set a wm_class, so this may cause issues with other
# applications that also don't set the wm_class.
# Enable only if you use Synergy. (This is only for use with xkeysnail.)
# define_conditional_modmap(lambda wm_class: wm_class == '', {})
###########################
# Suggestion (untested):
# For use with keyszer, to avoid catching GNOME Shell task switcher (which has
# an empty WM_CLASS but sets a WM_NAME): 
# modmap("Synergy fix", {}, when = lambda ctx: ctx.wm_class == '' and ctx.wm_name == '')
# If Synergy actually sets a WM_NAME like GNOME Shell does, you'd need to use
# one of these alternatives:
# modmap("Synergy fix", {}, when = lambda ctx: ctx.wm_class == '' and ctx.wm_name == 'SYNERGY_WM_NAME')
# Or: 
# modmap("Synergy fix", {}, when = lambda ctx: ctx.wm_class == '' and not ctx.wm_name == 'gnome-shell')


# [Global GUI conditional modmaps] Change modifier keys as in xmodmap
modmap("Cond modmap - GUI - Caps2Cmd - not Cbk kdb", {
    Key.CAPSLOCK:               Key.RIGHT_CTRL,                 # Caps2Cmd
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    not isKBtype('Chromebook')(ctx) and 
    cnfg.Caps2Cmd
)
modmap("Cond modmap - GUI - Caps2Cmd - Cbk kdb", {
    Key.LEFT_META:              Key.RIGHT_CTRL,                 # Caps2Cmd - Chromebook
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Chromebook')(ctx) and 
    cnfg.Caps2Cmd
)
modmap("Cond modmap - GUI - IBM kbd - multi_lang OFF", {
    # - IBM
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # IBM - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.RIGHT_ALT,                  # IBM - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('IBM', map='mmap GUI IBM ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - GUI - IBM kbd", {
    # - IBM
    Key.CAPSLOCK:               Key.LEFT_META,                  # IBM
    Key.LEFT_CTRL:              Key.LEFT_ALT,                   # IBM
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # IBM
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('IBM', map='mmap GUI IBM')(ctx)
)
modmap("Cond modmap - GUI - Cbk kbd - multi_lang OFF", {
    # - Chromebook
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # Chromebook - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.RIGHT_ALT,                  # Chromebook - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Chromebook', map='mmap GUI Cbk ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - GUI - Cbk kbd", {
    # - Chromebook
    Key.LEFT_CTRL:              Key.LEFT_ALT,                   # Chromebook
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # Chromebook
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Chromebook', map='mmap GUI Cbk')(ctx)
)
modmap("Cond modmap - GUI - Win kbd - multi_lang OFF", {
    # - Default Mac/Win
    # - Default Win
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # WinMac - Multi-language (Remove)
    Key.RIGHT_META:             Key.RIGHT_ALT,                  # WinMac - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.RIGHT_META,                 # WinMac - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Windows', map='mmap GUI Win ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - GUI - Win kbd", {
    # - Default Mac/Win
    # - Default Win
    Key.LEFT_CTRL:              Key.LEFT_META,                  # WinMac
    Key.LEFT_META:              Key.LEFT_ALT,                   # WinMac
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # WinMac
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Windows', map='mmap GUI Win')(ctx)
)
modmap("Cond modmap - GUI - Mac kbd - multi_lang OFF", {
    # - Mac Only
    Key.RIGHT_META:             Key.RIGHT_CTRL,                 # Mac - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.RIGHT_META,                 # Mac - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Apple', map='mmap GUI Apple ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - GUI - Mac kbd", {
    # - Mac Only
    Key.LEFT_CTRL:              Key.LEFT_META,                  # Mac
    Key.LEFT_META:              Key.RIGHT_CTRL,                 # Mac
}, when = lambda ctx:
    matchProps(not_lst=terminals_and_remotes_lod)(ctx) and 
    isKBtype('Apple', map='mmap GUI Apple')(ctx)
)


# [Global Terminals conditional modmaps] Change modifier keys in certain applications
modmap("Cond modmap - Terms - IBM kbd - multi_lang OFF", {
    # - IBM - Multi-language
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # IBM - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('IBM', map='mmap terms IBM ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - Terms - IBM kbd", {
    # - IBM
    Key.CAPSLOCK:               Key.LEFT_ALT,                   # IBM
    # Left Ctrl stays Left Ctrl
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # IBM
    # Right Meta does not exist on IBM keyboards
    Key.RIGHT_CTRL:             Key.RIGHT_ALT,                  # IBM
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('IBM', map='mmap terms IBM')(ctx)
)
modmap("Cond modmap - Terms - Cbk kbd - multi_lang OFF", {
    # - Chromebook
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # Chromebook - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Chromebook', map='mmap terms Cbk ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - Terms - Cbk kbd", {
    # - Chromebook
    # Left Ctrl Stays Left Ctrl
    Key.LEFT_META:              Key.LEFT_ALT,                   # Chromebook
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # Chromebook
    # Right Meta does not exist on chromebooks
    Key.RIGHT_CTRL:             Key.RIGHT_ALT,                  # Chromebook
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Chromebook', map='mmap terms Cbk')(ctx)
)
modmap("Cond modmap - Terms - Win kbd - multi_lang OFF", {
    # - Default Mac/Win
    # - Default Win
    Key.RIGHT_ALT:              Key.RIGHT_CTRL,                 # WinMac - Multi-language (Remove)
    Key.RIGHT_META:             Key.RIGHT_ALT,                  # WinMac - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.LEFT_CTRL,                  # WinMac - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Windows', map='mmap terms Win ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - Terms - Win kbd", {
    # - Default Mac/Win
    # - Default Win
    Key.LEFT_CTRL:              Key.LEFT_CTRL,                  # WinMac
    Key.LEFT_META:              Key.LEFT_ALT,                   # WinMac
    Key.LEFT_ALT:               Key.RIGHT_CTRL,                 # WinMac
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Windows', map='mmap terms Win')(ctx)
)
modmap("Cond modmap - Terms - Mac kbd - multi_lang OFF", {
    # - Mac Only
    # Left Ctrl Stays Left Ctrl
    Key.RIGHT_META:             Key.RIGHT_CTRL,                 # Mac - Multi-language (Remove)
    Key.RIGHT_CTRL:             Key.LEFT_CTRL,                  # Mac - Multi-language (Remove)
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Apple', map='mmap terms Apple ML-OFF')(ctx) and 
    cnfg.multi_lang is False
)
modmap("Cond modmap - Terms - Mac kbd", {
    # - Mac Only
    # Left Ctrl Stays Left Ctrl
    Key.LEFT_CTRL:              Key.LEFT_CTRL,                  # Mac (self-modmap)
    Key.LEFT_ALT:               Key.LEFT_ALT,                   # Mac (self-modmap)
    Key.LEFT_META:              Key.RIGHT_CTRL,                 # Mac
    Key.RIGHT_ALT:              Key.RIGHT_ALT,                  # Mac (self-modmap)
}, when = lambda ctx:
    matchProps(lst=terminals_lod)(ctx) and 
    isKBtype('Apple', map='mmap terms Apple')(ctx)
)



##########################  FORCED NUMPAD  ############################
###                                                                 ###
###                                                                 ###
###      ███    ██ ██    ██ ███    ███ ██████   █████  ██████       ###
###      ████   ██ ██    ██ ████  ████ ██   ██ ██   ██ ██   ██      ###
###      ██ ██  ██ ██    ██ ██ ████ ██ ██████  ███████ ██   ██      ###
###      ██  ██ ██ ██    ██ ██  ██  ██ ██      ██   ██ ██   ██      ###
###      ██   ████  ██████  ██      ██ ██      ██   ██ ██████       ###
###                                                                 ###
###                                                                 ###
#######################################################################

# Force the numpad to always be a numpad, like a Mac keyboard on macOS
# Numlock key becomes "Clear" key for use with calculator (sends Escape)
# Toggle feature on/off with Option+Numlock (Fn+Numlock might work on 
# Apple keyboards that have Fn key)


def forced_numpad_alert():
    """Show notification of state of Forced Numpad feature"""
    if cnfg.forced_numpad:
        subprocess.run('notify-send -u critical ALERT \
            "Forced Numpad feature is now ENABLED.\
            \rNumlock becomes "Clear" key (Escape).\
            \rDisable with Option+Numlock."', shell=True)
        debug("Forced Numpad feature is now ENABLED.")
    if not cnfg.forced_numpad:
        subprocess.run('notify-send -u critical ALERT \
            "Forced Numpad feature is now DISABLED.\
            \rRe-enable with Option+Numlock."', shell=True)
        debug("Forced Numpad feature is now DISABLED.")


def toggle_forced_numpad():
    """Toggle the Forced Numpad feature on or off."""
    cnfg.forced_numpad = not cnfg.forced_numpad
    cnfg.save_settings()
    forced_numpad_alert()


def isNumlockClearKey():
    """NumLock key is Clear (Esc) if Forced Numpad feature is enabled."""
    return C("Esc") if cnfg.forced_numpad else C("Numlock")



###########################  OPTSPECIALCHARS  ##############################
###                                                                      ###
###                                                                      ###
###       ██████  ██████  ████████ ███████ ██████  ███████  ██████       ###
###      ██    ██ ██   ██    ██    ██      ██   ██ ██      ██            ###
###      ██    ██ ██████     ██    ███████ ██████  █████   ██            ###
###      ██    ██ ██         ██         ██ ██      ██      ██            ###
###       ██████  ██         ██    ███████ ██      ███████  ██████       ###
###                                                                      ###
###                                                                      ###
############################################################################

###########   START OF OPTION KEY SPECIAL CHARACTER ENTRY SCHEME    #############
#################################################################################
### Full list of special characters on Apple US and ABC Extended keyboard layouts: 
### https://github.org/RedBearAK/optspecialchars


# Set this variable to False to disable the alert that appears 
# when using Apple logo shortcut (Shift+Option+K)
applelogoalert_enabled = True   # Default: True


# def toggle_optspec_US():
#     """Toggle the value of the _optspecialchars_US variable"""
#     # Needs "from subprocess import run" somewhere
#     def _toggle_optspec_US():
#         global optspec_US
#         global optspec_ABC
#         if optspec_ABC:
#             optspec_ABC = False                        # Disable the other layout, if active
#         optspec_US = not optspec_US
#         if optspec_US:
#             subprocess.run('notify-send -u critical ALERT "Kinto OptSpecialChars-US is now ENABLED.\
#                 \rWill interfere with Alt & Shift+Alt shortcuts!\
#                 \rDisable with Shift+Opt+Cmd+U."', shell=True)
#             print("(DD) OptSpecialChars-US is now ENABLED.", flush=True)
#         else:
#             subprocess.run('notify-send -u critical ALERT "Kinto OptSpecialChars-US is now DISABLED.\
#                 \rRe-enable with Shift+Opt+Cmd+U"', shell=True)
#             print("(DD) OptSpecialChars-US is now DISABLED.", flush=True)
#     return _toggle_optspec_US


# def toggle_optspec_ABC():
#     """Toggle the value of the _optspecialchars_ABC variable"""
#     # Needs "from subprocess import run" somewhere
#     def _toggle_optspec_ABC():
#         global optspec_ABC
#         global optspec_US
#         if optspec_US:
#             optspec_US = False                         # Disable the other layout, if active
#         optspec_ABC = not optspec_ABC
#         if optspec_ABC:
#             subprocess.run('notify-send -u critical ALERT "Kinto OptSpecialChars-ABC is now ENABLED.\
#                 \rWill interfere with Alt & Shift+Alt shortcuts!\
#                 \rDisable with Shift+Opt+Cmd+X."', shell=True)
#             print("(DD) OptSpecialChars-ABC is now ENABLED.", flush=True)
#         else:
#             subprocess.run('notify-send -u critical ALERT "Kinto OptSpecialChars-ABC is now DISABLED.\
#                 \rRe-enable with Shift+Opt+Cmd+X."', shell=True)
#             print("(DD) OptSpecialChars-ABC is now DISABLED.", flush=True)
#     return _toggle_optspec_ABC


# def disable_optspec():
#     """Disable both Option key special character entry scheme layouts"""
#     # Needs "from subprocess import run" somewhere
#     def _disable_optspec():
#         global optspec_ABC
#         global optspec_US
#         optspec_ABC = False
#         optspec_US = False
#         subprocess.run('notify-send -u critical ALERT "Kinto OptSpecialChars (US/ABC) is now DISABLED.\
#             \rTo re-enable ABC Extended: Shift+Opt+Cmd+X\
#             \rTo re-enable Standard US: Shift+Opt+Cmd+U"', shell=True)
#         print("(DD) OptSpecialChars (US/ABC) is now DISABLED.", flush=True)
#     return _disable_optspec


# keymap("OptSpecialChars toggles", {
#     C("Shift-Alt-RC-o"):        disable_optspec(),      # Disable all layouts
#     C("Shift-Alt-RC-u"):        toggle_optspec_US(),    # Toggle the US layout
#     C("Shift-Alt-RC-x"):        toggle_optspec_ABC(),   # Toggle the ABC Extended layout
# }, when = lambda ctx: ctx.wm_class.casefold() not in terminals)


def apple_logo_alert():
    """Show a notification about needing Baskerville Old Face 
    font for displaying Apple logo"""
    def _apple_logo_alert():
        global applelogoalert_enabled
        if applelogoalert_enabled:
            subprocess.run( 'notify-send -u critical ALERT "Apple logo requires '
                            'Baskerville Old Face font."', shell=True)
    return _apple_logo_alert



######################################################################################
###                                                                                ###
###                                                                                ###
###      ██████  ███████  █████  ██████      ██   ██ ███████ ██    ██ ███████      ###
###      ██   ██ ██      ██   ██ ██   ██     ██  ██  ██       ██  ██  ██           ###
###      ██   ██ █████   ███████ ██   ██     █████   █████     ████   ███████      ###
###      ██   ██ ██      ██   ██ ██   ██     ██  ██  ██         ██         ██      ###
###      ██████  ███████ ██   ██ ██████      ██   ██ ███████    ██    ███████      ###
###                                                                                ###
###                                                                                ###
######################################################################################

# variables to store dead keys diacritic accent character Unicode address
ac_Chr_main = None
_ac_Chr_copy = None


def set_dead_key_char(hex_unicode_addr):
    """
    Set the value of the dead keys accent character 
    variable, and its alternate. Does not clear the
    value of the alternate variable if input is 
    falsy (such as None or 0x0000 or 0). This allows
    the value to be used after the tripwire keymap
    clears the main variable value.
    """
    def _set_dead_key_char():
        global ac_Chr_main
        global _ac_Chr_copy
        # if hex_unicode_addr is None or hex_unicode_addr == 0x0000:
        #     pass
        # else:
        if hex_unicode_addr:
            _ac_Chr_copy = hex_unicode_addr
        ac_Chr_main = hex_unicode_addr

    return _set_dead_key_char


def get_dead_key_char():
    """Get the value of the alternate dead key accent character 
        variable, and print/type the resulting Unicode character."""
    def _get_dead_key_char():
        global _ac_Chr_copy
        return UC(_ac_Chr_copy)

    return _get_dead_key_char


setDK = set_dead_key_char
getDK = get_dead_key_char

deadkeys_ABC = [
    # Dead keys on ABC Extended keyboard layout (25, plus substitutes for problematic chars)
    0x0060,                     # Dead Keys Accent: Grave
    0x02C6,                     # Dead Keys Accent: Circumflex
    0x02D9,                     # Dead Keys Accent: Dot Above
    0x00B4,                     # Dead Keys Accent: Acute

    ###  Combining Double Grave has issues (spacing behavior) - substituting {U+02F5}
    0x030F,                     # Dead Keys Accent: Combining Double Grave
    ###  Substitute for Double Grave: Modifier Letter Middle Double Grave Accent
    0x02F5,                     # Dead Keys Accent: Double Grave - substitute for {U+030F}

    0x00A8,                     # Dead Keys Accent: Umlaut/Diaeresis
    0x02BC,                     # Dead Keys Accent: Apostrophe/Horn
    0x002C,                     # Dead Keys Accent: Comma Below
    0x00AF,                     # Dead Keys Accent: Macron/Line Above

    ###  Combining Inverted Breve has issues (spacing behavior) - substituting {U+1D16}
    0x0311,                     # Dead Keys Accent: Combining Inverted Breve
    ###  Substitute for Inverted Breve: Latin Small Letter Top Half O
    0x1D16,                     # Dead Keys Accent: Inverted Breve - substitute for {U+0311}

    ###  Combining Tilde Below has issues (spacing behavior) - substituting {U+02F7}
    0x0330,                     # Dead Keys Accent: Combining Tilde Below
    ###  Substitute for Tilde Below: Modifier Letter Low Tilde

    0x02F7,                     # Dead Keys Accent: Tilde Below
    0x2038,                     # Dead Keys Accent: Caret/Circumflex Below
    0x02CD,                     # Dead Keys Accent: Low Macron/Line Below
    0x02DD,                     # Dead Keys Accent: Double Acute
    0x02DA,                     # Dead Keys Accent: Ring Above
    0x002D,                     # Dead Keys Accent: Stroke/Hyphen-Minus
    0x2116,                     # Dead Keys Accent: Numero Sign
    0x02C0,                     # Dead Keys Accent: Hook Above/Glottal Stop
    0x002E,                     # Dead Keys Accent: Dot Below
    0x00B8,                     # Dead Keys Accent: Cedilla/Cedille
    0x02C7,                     # Dead Keys Accent: Caron/hacek
    0x02D8,                     # Dead Keys Accent: Breve
    0x02DC,                     # Dead Keys Accent: Tilde
    0x02DB,                     # Dead Keys Accent: Ogonek
    0x0294,                     # Dead Keys Accent: Hook
]

deadkeys_US = [
    # Dead keys on standard US keyboard layout (5)
    0x0060,                     # Dead Keys Accent: Grave
    0x00B4,                     # Dead Keys Accent: Acute
    0x00A8,                     # Dead Keys Accent: Umlaut/Diaeresis
    0x02C6,                     # Dead Keys Accent: Circumflex
    0x02DC,                     # Dead Keys Accent: Tilde
]

# Join the two dead keys lists together
deadkeys_list = []
deadkeys_list.extend(deadkeys_ABC)
deadkeys_list.extend(deadkeys_US)


#####################################
###   DEAD KEYS KEYMAPS - START   ###
#####################################
# Dead Keys conditional keymaps
# only active when the dead key variable matches
# and the layout variable matches (US or ABC)

#################################################
###  DEAD KEYS KEYMAPS - ABC EXTENDED LAYOUT  ###
#################################################

keymap("DK-ABC - Grave", {
    # Option+Grave              {U+0060}
    # Valid keys:
    # a e i n o u v w y
    # A E I N O U V W Y
    C("A"):                     UC(0x00E0),                     # à Latin Small Letter A with Grave
    C("E"):                     UC(0x00E8),                     # è Latin Small Letter E with Grave
    C("I"):                     UC(0x00EC),                     # ì Latin Small Letter I with Grave
    C("N"):                     UC(0x01F9),                     # ǹ Latin Small Letter N with Grave
    C("O"):                     UC(0x00F2),                     # ò Latin Small Letter O with Grave
    C("U"):                     UC(0x00F9),                     # ù Latin Small Letter U with Grave
    C("V"):                     UC(0x01DC),                     # ǜ Latin Small Letter U w/Diaeresis and Grave
    C("W"):                     UC(0x1E81),                     # ẁ Latin Small Letter W with Grave
    C("Y"):                     UC(0x1EF3),                     # ỳ Latin Small Letter Y with Grave
    C("Shift-A"):               UC(0x00C0),                     # À Latin Capital Letter A with Grave
    C("Shift-E"):               UC(0x00C8),                     # È Latin Capital Letter E with Grave
    C("Shift-I"):               UC(0x00CC),                     # Ì Latin Capital Letter I with Grave
    C("Shift-N"):               UC(0x01F8),                     # Ǹ Latin Capital Letter N with Grave
    C("Shift-O"):               UC(0x00D2),                     # Ò Latin Capital Letter O with Grave
    C("Shift-U"):               UC(0x00D9),                     # Ù Latin Capital Letter U with Grave
    C("Shift-V"):               UC(0x01DB),                     # Ǜ Latin Capital Letter U w/Diaeresis and Grave
    C("Shift-W"):               UC(0x1E80),                     # Ẁ Latin Capital Letter W with Grave
    C("Shift-Y"):               UC(0x1EF2),                     # Ỳ Latin Capital Letter Y with Grave
}, when = lambda _: ac_Chr_main == 0x0060 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Circumflex", {
    # Option+6                  {U+02C6}
    # Valid keys:
    # a c e g h i j m n o s u w y z
    # A C E G H I J M N O S U W Y Z
    C("A"):                     UC(0x00E2),                     # â Latin Small Letter A with Circumflex
    C("C"):                     UC(0x0109),                     # ĉ Latin Small Letter C with Circumflex
    C("E"):                     UC(0x00EA),                     # ê Latin Small Letter E with Circumflex
    C("G"):                     UC(0x011D),                     # ĝ Latin Small Letter G with Circumflex
    C("H"):                     UC(0x0125),                     # ĥ Latin Small Letter H with Circumflex
    C("I"):                     UC(0x00EE),                     # î Latin Small Letter I with Circumflex
    C("J"):                     UC(0x0135),                     # ĵ Latin Small Letter J with Circumflex
    C("M"):                    [UC(0x006D),UC(0x0302)],         # m̂ Latin Small Letter M with Circumflex
    C("N"):                    [UC(0x006E),UC(0x0302)],         # n̂ Latin Small Letter N with Circumflex
    C("O"):                     UC(0x00F4),                     # ô Latin Small Letter O with Circumflex
    C("S"):                     UC(0x015D),                     # ŝ Latin Small Letter S with Circumflex
    C("U"):                     UC(0x00FB),                     # û Latin Small Letter U with Circumflex
    C("W"):                     UC(0x0175),                     # ŵ Latin Small Letter W with Circumflex
    C("Y"):                     UC(0x0177),                     # ŷ Latin Small Letter Y with Circumflex
    C("Z"):                     UC(0x1E91),                     # ẑ Latin Small Letter Z with Circumflex
    C("Shift-A"):               UC(0x00C2),                     # Â Latin Capital Letter A with Circumflex
    C("Shift-C"):               UC(0x0108),                     # Ĉ Latin Capital Letter C with Circumflex
    C("Shift-E"):               UC(0x00CA),                     # Ê Latin Capital Letter E with Circumflex
    C("Shift-G"):               UC(0x011C),                     # Ĝ Latin Capital Letter G with Circumflex
    C("Shift-H"):               UC(0x0124),                     # Ĥ Latin Capital Letter H with Circumflex
    C("Shift-I"):               UC(0x00CE),                     # Î Latin Capital Letter I with Circumflex
    C("Shift-J"):               UC(0x0134),                     # Ĵ Latin Capital Letter J with Circumflex
    C("Shift-M"):              [UC(0x004D),UC(0x0302)],         # M̂ Latin Capital Letter M with Circumflex
    C("Shift-N"):              [UC(0x004E),UC(0x0302)],         # N̂ Latin Capital Letter N with Circumflex
    C("Shift-O"):               UC(0x00D4),                     # Ô Latin Capital Letter O with Circumflex
    C("Shift-S"):               UC(0x015C),                     # Ŝ Latin Capital Letter S with Circumflex
    C("Shift-U"):               UC(0x00DB),                     # Û Latin Capital Letter U with Circumflex
    C("Shift-W"):               UC(0x0174),                     # Ŵ Latin Capital Letter W with Circumflex
    C("Shift-Y"):               UC(0x0176),                     # Ŷ Latin Capital Letter Y with Circumflex
    C("Shift-Z"):               UC(0x1E90),                     # Ẑ Latin Capital Letter Z with Circumflex
}, when = lambda _: ac_Chr_main == 0x02C6 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Dot Above", {
    # Option+W                  {U+02D9}
    # Valid keys:
    # a b c d e f g h i m n o p r s t w x y z
    # A B C D E F G H I M N O P R S T W X Y Z
    C("A"):                     UC(0x0227),                     # ȧ Latin Small Letter A with Dot Above
    C("B"):                     UC(0x1E03),                     # ḃ Latin Small Letter B with Dot Above
    C("C"):                     UC(0x010B),                     # ċ Latin Small Letter C with Dot Above
    C("D"):                     UC(0x1E0B),                     # ḋ Latin Small Letter D with Dot Above
    C("E"):                     UC(0x0117),                     # ė Latin Small Letter E with Dot Above
    C("F"):                     UC(0x1E1F),                     # ḟ Latin Small Letter F with Dot Above
    C("G"):                     UC(0x0121),                     # ġ Latin Small Letter G with Dot Above
    C("H"):                     UC(0x1E23),                     # ḣ Latin Small Letter H with Dot Above
    C("I"):                     UC(0x0131),                     # ı Latin Small Letter Dotless I
    C("M"):                     UC(0x1E41),                     # ṁ Latin Small Letter M with Dot Above
    C("N"):                     UC(0x1E45),                     # ṅ Latin Small Letter N with Dot Above
    C("O"):                     UC(0x022F),                     # ȯ Latin Small Letter O with Dot Above
    C("P"):                     UC(0x1E57),                     # ṗ Latin Small Letter P with Dot Above
    C("R"):                     UC(0x1E59),                     # ṙ Latin Small Letter R with Dot Above
    C("S"):                     UC(0x1E61),                     # ṡ Latin Small Letter S with Dot Above
    C("T"):                     UC(0x1E6B),                     # ṫ Latin Small Letter T with Dot Above
    C("W"):                     UC(0x1E87),                     # ẇ Latin Small Letter W with Dot Above
    C("X"):                     UC(0x1E8B),                     # ẋ Latin Small Letter X with Dot Above
    C("Y"):                     UC(0x1E8F),                     # ẏ Latin Small Letter Y with Dot Above
    C("Z"):                     UC(0x017C),                     # ż Latin Small Letter Z with Dot Above
    C("Shift-A"):               UC(0x0226),                     # Ȧ Latin Capital Letter A with Dot Above
    C("Shift-B"):               UC(0x1E02),                     # Ḃ Latin Capital Letter B with Dot Above
    C("Shift-C"):               UC(0x010A),                     # Ċ Latin Capital Letter C with Dot Above
    C("Shift-D"):               UC(0x1E0A),                     # Ḋ Latin Capital Letter D with Dot Above
    C("Shift-E"):               UC(0x0116),                     # Ė Latin Capital Letter E with Dot Above
    C("Shift-F"):               UC(0x1E1E),                     # Ḟ Latin Capital Letter F with Dot Above
    C("Shift-G"):               UC(0x0120),                     # Ġ Latin Capital Letter G with Dot Above
    C("Shift-H"):               UC(0x1E22),                     # Ḣ Latin Capital Letter H with Dot Above
    C("Shift-I"):               UC(0x0130),                     # İ Latin Capital Letter I with Dot Above
    C("Shift-M"):               UC(0x1E40),                     # Ṁ Latin Capital Letter M with Dot Above
    C("Shift-N"):               UC(0x1E44),                     # Ṅ Latin Capital Letter N with Dot Above
    C("Shift-O"):               UC(0x022E),                     # Ȯ Latin Capital Letter O with Dot Above
    C("Shift-P"):               UC(0x1E56),                     # Ṗ Latin Capital Letter P with Dot Above
    C("Shift-R"):               UC(0x1E58),                     # Ṙ Latin Capital Letter R with Dot Above
    C("Shift-S"):               UC(0x1E60),                     # Ṡ Latin Capital Letter S with Dot Above
    C("Shift-T"):               UC(0x1E6A),                     # Ṫ Latin Capital Letter T with Dot Above
    C("Shift-W"):               UC(0x1E86),                     # Ẇ Latin Capital Letter W with Dot Above
    C("Shift-X"):               UC(0x1E8A),                     # Ẋ Latin Capital Letter X with Dot Above
    C("Shift-Y"):               UC(0x1E8E),                     # Ẏ Latin Capital Letter Y with Dot Above
    C("Shift-Z"):               UC(0x017B),                     # Ż Latin Capital Letter Z with Dot Above
}, when = lambda _: ac_Chr_main == 0x02D9 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Acute", {
    # Option+E                  {U+00B4}
    # Valid keys:
    # a c e g i m n o p r s w y z
    # A C E G I M N O P R S W Y Z
    C("A"):                     UC(0x00E1),                     # á Latin Small Letter A with Acute
    C("C"):                     UC(0x0107),                     # ć Latin Small Letter C with Acute
    C("E"):                     UC(0x00E9),                     # é Latin Small Letter E with Acute
    C("G"):                     UC(0x01F5),                     # ǵ Latin Small Letter G with Acute
    C("I"):                     UC(0x00ED),                     # í Latin Small Letter I with Acute
    C("M"):                     UC(0x1E3F),                     # ḿ Latin Small Letter M with Acute
    C("N"):                     UC(0x0144),                     # ń Latin Small Letter N with Acute
    C("O"):                     UC(0x00F3),                     # ó Latin Small Letter O with Acute
    C("P"):                     UC(0x1E55),                     # ṕ Latin Small Letter P with Acute
    C("R"):                     UC(0x0155),                     # ŕ Latin Small Letter R with Acute
    C("S"):                     UC(0x015B),                     # ś Latin Small Letter S with Acute
    C("W"):                     UC(0x1E83),                     # ẃ Latin Small Letter W with Acute
    C("Y"):                     UC(0x00FD),                     # ý Latin Small Letter Y with Acute
    C("Z"):                     UC(0x017A),                     # ź Latin Small Letter Z with Acute
    C("Shift-A"):               UC(0x00C1),                     # Á Latin Capital Letter A with Acute
    C("Shift-C"):               UC(0x0106),                     # Ć Latin Capital Letter C with Acute
    C("Shift-E"):               UC(0x00C9),                     # É Latin Capital Letter E with Acute
    C("Shift-G"):               UC(0x01F4),                     # Ǵ Latin Capital Letter G with Acute
    C("Shift-I"):               UC(0x00CD),                     # Í Latin Capital Letter I with Acute
    C("Shift-M"):               UC(0x1E3E),                     # Ḿ Latin Capital Letter M with Acute
    C("Shift-N"):               UC(0x0143),                     # Ń Latin Capital Letter N with Acute
    C("Shift-O"):               UC(0x00D3),                     # Ó Latin Capital Letter O with Acute
    C("Shift-P"):               UC(0x1E54),                     # Ṕ Latin Capital Letter P with Acute
    C("Shift-R"):               UC(0x0154),                     # Ŕ Latin Capital Letter R with Acute
    C("Shift-S"):               UC(0x015A),                     # Ś Latin Capital Letter S with Acute
    C("Shift-W"):               UC(0x1E82),                     # Ẃ Latin Capital Letter W with Acute
    C("Shift-Y"):               UC(0x00DD),                     # Ý Latin Capital Letter Y with Acute
    C("Shift-Z"):               UC(0x0179),                     # Ź Latin Capital Letter Z with Acute
}, when = lambda _: ac_Chr_main == 0x00B4 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Double Grave", {
    # Shift+Option+Y            {U+030F} [uses {U+02F5} Modifier Letter Middle Double Grave Accent]
    # Valid keys:
    # a e i o r u
    # A E I O R U
    C("A"):                     UC(0x0201),                     # ȁ Latin Small Letter A with Double Grave
    C("E"):                     UC(0x0205),                     # ȅ Latin Small Letter E with Double Grave
    C("I"):                     UC(0x0209),                     # ȉ Latin Small Letter I with Double Grave
    C("O"):                     UC(0x020D),                     # ȍ Latin Small Letter O with Double Grave
    C("R"):                     UC(0x0211),                     # ȑ Latin Small Letter R with Double Grave
    C("U"):                     UC(0x0215),                     # ȕ Latin Small Letter U with Double Grave
    C("Shift-A"):               UC(0x0200),                     # Ȁ Latin Capital Letter A with Double Grave
    C("Shift-E"):               UC(0x0204),                     # Ȅ Latin Capital Letter E with Double Grave
    C("Shift-I"):               UC(0x0208),                     # Ȉ Latin Capital Letter I with Double Grave
    C("Shift-O"):               UC(0x020C),                     # Ȍ Latin Capital Letter O with Double Grave
    C("Shift-R"):               UC(0x0210),                     # Ȑ Latin Capital Letter R with Double Grave
    C("Shift-U"):               UC(0x0214),                     # Ȕ Latin Capital Letter U with Double Grave
# }, when = lambda _: (ac_Chr_main == 0x030F or ac_Chr_main == 0x02F5) and cnfg.optspec_layout == 'ABC')
}, when=lambda _: ac_Chr_main in [0x030F, 0x02F5] and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Umlaut/Diaeresis", {
    # Option+U                  {U+00A8}
    # Valid keys:
    # a e h i o t u w x y
    # A E H I O T U W X Y
    C("A"):                     UC(0x00E4),                     # ä Latin Small Letter A with Diaeresis
    C("E"):                     UC(0x00EB),                     # ë Latin Small Letter E with Diaeresis
    C("H"):                     UC(0x1E27),                     # ḧ Latin Small Letter H with Diaeresis
    C("I"):                     UC(0x00EF),                     # ï Latin Small Letter I with Diaeresis
    C("O"):                     UC(0x00F6),                     # ö Latin Small Letter O with Diaeresis
    C("T"):                     UC(0x1E97),                     # ẗ Latin Small Letter T with Diaeresis
    C("U"):                     UC(0x00FC),                     # ü Latin Small Letter U with Diaeresis
    C("W"):                     UC(0x1E85),                     # ẅ Latin Small Letter W with Diaeresis
    C("X"):                     UC(0x1E8D),                     # ẍ Latin Small Letter X with Diaeresis
    C("Y"):                     UC(0x00FF),                     # ÿ Latin Small Letter Y with Diaeresis
    C("Shift-A"):               UC(0x00C4),                     # Ä Latin Capital Letter A with Diaeresis
    C("Shift-E"):               UC(0x00CB),                     # Ë Latin Capital Letter E with Diaeresis
    C("Shift-H"):               UC(0x1E26),                     # Ḧ Latin Capital Letter H with Diaeresis
    C("Shift-I"):               UC(0x00CF),                     # Ï Latin Capital Letter I with Diaeresis
    C("Shift-O"):               UC(0x00D6),                     # Ö Latin Capital Letter O with Diaeresis
    C("Shift-T"):              [UC(0x0054),UC(0x0308)],         # T̈ Latin Capital Letter T with Diaeresis
    C("Shift-U"):               UC(0x00DC),                     # Ü Latin Capital Letter U with Diaeresis
    C("Shift-W"):               UC(0x1E84),                     # Ẅ Latin Capital Letter W with Diaeresis
    C("Shift-X"):               UC(0x1E8C),                     # Ẍ Latin Capital Letter X with Diaeresis
    C("Shift-Y"):               UC(0x0178),                     # Ÿ Latin Capital Letter Y with Diaeresis
}, when = lambda _: ac_Chr_main == 0x00A8 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Apostrophe/Horn", {
    # Option+I                  {U+02BC}
    # Valid keys:
    # o u
    # O U
    C("O"):                     UC(0x01A1),                     # ơ Latin Small Letter O with Horn
    C("U"):                     UC(0x01B0),                     # ư Latin Small Letter U with Horn
    C("Shift-O"):               UC(0x01A0),                     # Ơ Latin Capital Letter O with Horn
    C("Shift-U"):               UC(0x01AF),                     # Ư Latin Capital Letter U with Horn
}, when = lambda _: ac_Chr_main == 0x02BC and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Comma Below", {
    # Option+P                  {U+002C}
    # Valid keys:
    # s t
    # S T
    C("S"):                     UC(0x0219),                     # ș Latin Small Letter S with Comma Below
    C("T"):                     UC(0x021B),                     # ț Latin Small Letter T with Comma Below
    C("Shift-S"):               UC(0x0218),                     # Ș Latin Capital Letter S with Comma Below
    C("Shift-T"):               UC(0x021A),                     # Ț Latin Capital Letter T with Comma Below
}, when = lambda _: ac_Chr_main == 0x002C and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Macron/Line Above", {
    # Option+A                  {U+00AF}
    # Valid keys:
    # a e g i l o r s v y z
    # A E G I L O R S V Y Z
    C("A"):                     UC(0x0101),                     # ā Latin Small Letter A with Macron
    C("E"):                     UC(0x0113),                     # ē Latin Small Letter E with Macron
    C("G"):                     UC(0x1E21),                     # ḡ Latin Small Letter G with Macron
    C("I"):                     UC(0x012B),                     # ī Latin Small Letter I with Macron
    C("L"):         [UC(0x006C),UC(0x0304),UC(0x0323)],         # ḹ Latin Small Letter L w/Macron and Dot Below
    C("O"):                     UC(0x014D),                     # ō Latin Small Letter O with Macron
    C("R"):         [UC(0x0072),UC(0x0304),UC(0x0323)],         # ṝ Latin Small Letter R w/Macron and Dot Below
    C("S"):                    [UC(0x0073),UC(0x0304)],         # s̄ Latin Small Letter S with Macron
    C("V"):                     UC(0x01D6),                     # ǖ Latin Small Letter U with Diaeresis and Macron
    C("Y"):                     UC(0x0233),                     # ȳ Latin Small Letter Y with Macron
    C("Z"):                    [UC(0x007A),UC(0x0304)],         # z̄ Latin Small Letter Z with Macron
    C("Shift-A"):               UC(0x0100),                     # Ā Latin Capital Letter A with Macron
    C("Shift-E"):               UC(0x0112),                     # Ē Latin Capital Letter E with Macron
    C("Shift-G"):               UC(0x1E20),                     # Ḡ Latin Capital Letter G with Macron
    C("Shift-I"):               UC(0x012A),                     # Ī Latin Capital Letter I with Macron
    C("Shift-L"):   [UC(0x004C),UC(0x0304),UC(0x0323)],         # Ḹ Latin Capital Letter L w/Macron and Dot Below
    C("Shift-O"):               UC(0x014C),                     # Ō Latin Capital Letter O with Macron
    C("Shift-R"):   [UC(0x0052),UC(0x0304),UC(0x0323)],         # Ṝ Latin Capital Letter R w/Macron and Dot Below
    C("Shift-S"):              [UC(0x0053),UC(0x0304)],         # S̄ Latin Capital Letter S with Macron
    C("Shift-V"):               UC(0x01D5),                     # Ǖ Latin Capital Letter U with Diaeresis and Macron
    C("Shift-Y"):               UC(0x0232),                     # Ȳ Latin Capital Letter Y with Macron
    C("Shift-Z"):              [UC(0x005A),UC(0x0304)],         # Z̄ Latin Capital Letter Z with Macron
}, when = lambda _: ac_Chr_main == 0x00AF and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Inverted Breve", {
    # Shift+Option+S            {U+0311}    [uses {U+1D16} as a substitute]
    # Valid keys:
    # a e i o r u
    # A E I O R U 
    C("A"):                     UC(0x0203),                     # ȃ Latin Small Letter A with Inverted Breve
    C("E"):                     UC(0x0207),                     # ȇ Latin Small Letter E with Inverted Breve
    C("I"):                     UC(0x020B),                     # ȋ Latin Small Letter I with Inverted Breve
    C("O"):                     UC(0x020F),                     # ȏ Latin Small Letter O with Inverted Breve
    C("R"):                     UC(0x0213),                     # ȓ Latin Small Letter R with Inverted Breve
    C("U"):                     UC(0x0217),                     # ȗ Latin Small Letter U with Inverted Breve
    C("Shift-A"):               UC(0x0202),                     # Ȃ Latin Capital Letter A with Inverted Breve
    C("Shift-E"):               UC(0x0206),                     # Ȇ Latin Capital Letter E with Inverted Breve
    C("Shift-I"):               UC(0x020A),                     # Ȋ Latin Capital Letter I with Inverted Breve
    C("Shift-O"):               UC(0x020E),                     # Ȏ Latin Capital Letter O with Inverted Breve
    C("Shift-R"):               UC(0x0212),                     # Ȓ Latin Capital Letter R with Inverted Breve
    C("Shift-U"):               UC(0x0216),                     # Ȗ Latin Capital Letter U with Inverted Breve
# }, when = lambda _: (ac_Chr_main == 0x0311 or ac_Chr_main == 0x1D16) and cnfg.optspec_layout == 'ABC')
}, when = lambda _: ac_Chr_main in [0x0311, 0x1D16] and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Tilde Below", {
    # Shift+Option+F            {U+0330}    [uses {U+02F7} as a substitute]
    # Valid keys:
    # e i u
    # E I U
    C("E"):                     UC(0x1E1B),                     # ḛ Latin Small Letter E with Tilde Below
    C("I"):                     UC(0x1E2D),                     # ḭ Latin Small Letter I with Tilde Below
    C("U"):                     UC(0x1E75),                     # ṵ Latin Small Letter U with Tilde Below
    C("Shift-E"):               UC(0x1E1A),                     # Ḛ Latin Capital Letter E with Tilde Below
    C("Shift-I"):               UC(0x1E2C),                     # Ḭ Latin Capital Letter I with Tilde Below
    C("Shift-U"):               UC(0x1E74),                     # Ṵ Latin Capital Letter U with Tilde Below
# }, when = lambda _: (ac_Chr_main == 0x0330 or ac_Chr_main == 0x02F7) and cnfg.optspec_layout == 'ABC')
}, when = lambda _: ac_Chr_main in [0x0330, 0x02F7] and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Caret/Circumflex Below", {
    # Shift+Option+G            {U+2038}
    # Valid keys:
    # d e l n t u
    # D E L N T U
    C("D"):                     UC(0x1E13),                     # ḓ Latin Small Letter D with Circumflex Below
    C("E"):                     UC(0x1E19),                     # ḙ Latin Small Letter E with Circumflex Below
    C("L"):                     UC(0x1E3D),                     # ḽ Latin Small Letter L with Circumflex Below
    C("N"):                     UC(0x1E4B),                     # ṋ Latin Small Letter N with Circumflex Below
    C("T"):                     UC(0x1E71),                     # ṱ Latin Small Letter T with Circumflex Below
    C("U"):                     UC(0x1E77),                     # ṷ Latin Small Letter U with Circumflex Below
    C("Shift-D"):               UC(0x1E12),                     # Ḓ Latin Capital Letter D with Circumflex Below
    C("Shift-E"):               UC(0x1E18),                     # Ḙ Latin Capital Letter E with Circumflex Below
    C("Shift-L"):               UC(0x1E3C),                     # Ḽ Latin Capital Letter L with Circumflex Below
    C("Shift-N"):               UC(0x1E4A),                     # Ṋ Latin Capital Letter N with Circumflex Below
    C("Shift-T"):               UC(0x1E70),                     # Ṱ Latin Capital Letter T with Circumflex Below
    C("Shift-U"):               UC(0x1E76),                     # Ṷ Latin Capital Letter U with Circumflex Below
}, when = lambda _: ac_Chr_main == 0x2038 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Low Macron/Line Below", {
    # Option+H                  {U+02CD}
    # Valid keys:
    # b d h k l n r t z
    # B D H K L N R T Z 
    C("B"):                     UC(0x1E07),                     # ḇ Latin Small Letter B with Line Below 
    C("D"):                     UC(0x1E0F),                     # ḏ Latin Small Letter D with Line Below 
    C("H"):                     UC(0x1E96),                     # ẖ Latin Small Letter H with Line Below 
    C("K"):                     UC(0x1E35),                     # ḵ Latin Small Letter K with Line Below 
    C("L"):                     UC(0x1E3B),                     # ḻ Latin Small Letter L with Line Below 
    C("N"):                     UC(0x1E49),                     # ṉ Latin Small Letter N with Line Below 
    C("R"):                     UC(0x1E5F),                     # ṟ Latin Small Letter R with Line Below 
    C("T"):                     UC(0x1E6F),                     # ṯ Latin Small Letter T with Line Below 
    C("Z"):                     UC(0x1E95),                     # ẕ Latin Small Letter Z with Line Below 
    C("Shift-B"):               UC(0x1E06),                     # Ḇ Latin Capital Letter B with Line Below 
    C("Shift-D"):               UC(0x1E0E),                     # Ḏ Latin Capital Letter D with Line Below 
    C("Shift-H"):              [UC(0x0048),UC(0x0331)],         # H̱ Latin Capital Letter H with Line Below
    C("Shift-K"):               UC(0x1E34),                     # Ḵ Latin Capital Letter K with Line Below 
    C("Shift-L"):               UC(0x1E3A),                     # Ḻ Latin Capital Letter L with Line Below 
    C("Shift-N"):               UC(0x1E48),                     # Ṉ Latin Capital Letter N with Line Below 
    C("Shift-R"):               UC(0x1E5E),                     # Ṟ Latin Capital Letter R with Line Below 
    C("Shift-T"):               UC(0x1E6E),                     # Ṯ Latin Capital Letter T with Line Below 
    C("Shift-Z"):               UC(0x1E94),                     # Ẕ Latin Capital Letter Z with Line Below 
}, when = lambda _: ac_Chr_main == 0x02CD and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Double Acute", {
    # Option+J                  {U+02DD}
    # Valid keys:
    # o u
    # O U
    C("O"):                     UC(0x0151),                     # ő Latin Small Letter O with Double Acute
    C("U"):                     UC(0x0171),                     # ű Latin Small Letter U with Double Acute
    C("Shift-O"):               UC(0x0150),                     # Ő Latin Capital Letter O with Double Acute
    C("Shift-U"):               UC(0x0170),                     # Ű Latin Capital Letter U with Double Acute
}, when = lambda _: ac_Chr_main == 0x02DD and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Ring Above", {
    # Option+K                  {U+02DA}
    # Valid keys:
    # a e o u w y
    # A E O U W Y 
    C("A"):                     UC(0x00E5),                     # å Latin Small Letter A with Ring Above
    C("E"):                    [UC(0x0065),UC(0x030A)],         # e̊ Latin Small Letter E with Ring Above
    C("O"):                    [UC(0x006F),UC(0x030A)],         # o̊ Latin Small Letter O with Ring Above
    C("U"):                     UC(0x016F),                     # ů Latin Small Letter U with Ring Above
    C("W"):                     UC(0x1E98),                     # ẘ Latin Small Letter W with Ring Above
    C("Y"):                     UC(0x1E99),                     # ẙ Latin Small Letter Y with Ring Above
    C("Shift-A"):               UC(0x00C5),                     # Å Latin Capital Letter A with Ring Above
    C("Shift-E"):              [UC(0x0045),UC(0x030A)],         # E̊ Latin Capital Letter E with Ring Above
    C("Shift-O"):              [UC(0x004F),UC(0x030A)],         # O̊ Latin Capital Letter O with Ring Above
    C("Shift-U"):               UC(0x016E),                     # Ů Latin Capital Letter U with Ring Above
    C("Shift-W"):              [UC(0x0057),UC(0x030A)],         # W̊ Latin Capital Letter W with Ring Above
    C("Shift-Y"):              [UC(0x0059),UC(0x030A)],         # Y̊ Latin Capital Letter Y with Ring Above
}, when = lambda _: ac_Chr_main == 0x02DA and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Stroke/Hyphen-Minus", {
    # Option+L                  {U+002D}
    # Valid keys:
    # b d g h i l o t u z
    #   D G H I L O T   Z 
    C("B"):                     UC(0x0180),                     # ƀ Latin Small Letter B with Stroke
    C("D"):                     UC(0x0111),                     # đ Latin Small Letter D with Stroke
    C("G"):                     UC(0x01E5),                     # ǥ Latin Small Letter G with Stroke
    C("H"):                     UC(0x0127),                     # ħ Latin Small Letter H with Stroke
    C("I"):                     UC(0x0268),                     # ɨ Latin Small Letter I with Stroke
    C("L"):                     UC(0x0142),                     # ł Latin Small Letter L with Stroke
    C("O"):                     UC(0x0275),                     # ɵ Latin Small Letter Barred O
    C("T"):                     UC(0x0167),                     # ŧ Latin Small Letter T with Stroke
    C("U"):                     UC(0x0289),                     # ʉ Latin Small Letter U Bar
    C("Z"):                     UC(0x01B6),                     # ƶ Latin Small Letter Z with Stroke
    C("Shift-D"):               UC(0x0110),                     # Đ Latin Capital Letter D with Stroke
    C("Shift-G"):               UC(0x01E4),                     # Ǥ Latin Capital Letter G with Stroke
    C("Shift-H"):               UC(0x0126),                     # Ħ Latin Capital Letter H with Stroke
    C("Shift-I"):               UC(0x0197),                     # Ɨ Latin Capital Letter I with Stroke
    C("Shift-L"):               UC(0x0141),                     # Ł Latin Capital Letter L with Stroke
    C("Shift-O"):               UC(0x019F),                     # Ɵ Latin Capital Letter O with Middle Tilde
    C("Shift-T"):               UC(0x0166),                     # Ŧ Latin Capital Letter T with Stroke
    C("Shift-Z"):               UC(0x01B5),                     # Ƶ Latin Capital Letter Z with Stroke
}, when = lambda _: ac_Chr_main == 0x002D and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Numero Sign", {
    # Shift+Option+Semicolon    {U+2116}
    # Valid keys:
    # 2 3 5 6 7 8 (digits with Option)
    # 2 3 5 6   8 (digits with Shift+Option)
    # a c e g h j k m n q r s u v w y z (letters with Option)
    # A C E G H J K M N Q R   U   W Y Z (letters with Shift+Option)
    C("3"):                     UC(0x025B),                     # ɛ  Latin Small Letter Open E
    C("5"):                     UC(0x01BD),                     # ƽ  Latin Small Letter Tone Five
    C("2"):                     UC(0x01A8),                     # ƨ  Latin Small Letter Tone Two
    C("6"):                     UC(0x0185),                     # ƅ  Latin Small Letter Tone Six
    C("7"):                     UC(0x204A),                     # ⁊  Tironian Sign Et 
    C("8"):                     UC(0x0223),                     # ȣ  Latin Small Letter Ou
    C("Shift-2"):               UC(0x01A7),                     # Ƨ  Latin Capital Letter Tone Two
    C("Shift-3"):               UC(0x0190),                     # Ɛ  Latin Capital Letter Open E
    C("Shift-5"):               UC(0x01BC),                     # Ƽ  Latin Capital Letter Tone Five
    C("Shift-6"):               UC(0x0184),                     # Ƅ  Latin Capital Letter Tone Six
    C("Shift-8"):               UC(0x0222),                     # Ȣ  Latin Capital Letter Ou
    C("a"):                     UC(0x0259),                     # ə  Latin Small Letter Schwa
    C("c"):                     UC(0x0254),                     # ɔ  Latin Small Letter Open O
    C("e"):                     UC(0x01DD),                     # ǝ  Latin Small Letter Turned E
    C("g"):                     UC(0x0263),                     # ɣ  Latin Small Letter Gamma
    C("h"):                     UC(0x0195),                     # ƕ  Latin Small Letter Hv
    C("j"):                     UC(0x019E),                     # ƞ  Latin Small Letter N with Long Right Leg
    C("k"):                     UC(0x0138),                     # ĸ  Latin Small Letter Kra
    C("m"):                     UC(0x026F),                     # ɯ  Latin Small Letter Turned M
    C("n"):                     UC(0x014B),                     # ŋ  Latin Small Letter Eng
    C("q"):                     UC(0x01A3),                     # ƣ  Latin Small Letter Oi
    C("r"):                     UC(0x0280),                     # ʀ  Latin Letter Small Capital R
    C("s"):                     UC(0x017F),                     # ſ  Latin Small Letter Long S
    C("u"):                     UC(0x028A),                     # ʊ  Latin Small Letter Upsilon
    C("v"):                     UC(0x028C),                     # ʌ  Latin Small Letter Turned V
    C("w"):                     UC(0x01BF),                     # ƿ  Latin Letter Wynn
    C("y"):                     UC(0x021D),                     # ȝ  Latin Small Letter Yogh
    C("z"):                     UC(0x0292),                     # ʒ  Latin Small Letter Ezh
    C("Shift-A"):               UC(0x018F),                     # Ə  Latin Capital Letter Schwa
    C("Shift-C"):               UC(0x0186),                     # Ɔ  Latin Capital Letter Open O
    C("Shift-E"):               UC(0x018E),                     # Ǝ  Latin Capital Letter Reversed E
    C("Shift-G"):               UC(0x0194),                     # Ɣ  Latin Capital Letter Gamma
    C("Shift-H"):               UC(0x01F6),                     # Ƕ  Latin Capital Letter Hwair
    C("Shift-J"):               UC(0x0220),                     # Ƞ  Latin Capital Letter N with Long Right Leg
    C("Shift-K"):              [UC(0x004B),UC(0x2019)],         # K’ Latin Capital Letter K with Apostrophe
    C("Shift-M"):               UC(0x019C),                     # Ɯ  Latin Capital Letter Turned M
    C("Shift-N"):               UC(0x014A),                     # Ŋ  Latin Capital Letter Eng
    C("Shift-Q"):               UC(0x01A2),                     # Ƣ  Latin Capital Letter Oi
    C("Shift-R"):               UC(0x01A6),                     # Ʀ  Latin Letter Yr
    C("Shift-U"):               UC(0x01B1),                     # Ʊ  Latin Capital Letter Upsilon
    C("Shift-W"):               UC(0x01F7),                     # Ƿ  Latin Capital Letter Wynn
    C("Shift-Y"):               UC(0x021C),                     # Ȝ  Latin Capital Letter Yogh
    C("Shift-Z"):               UC(0x01B7),                     # Ʒ  Latin Capital Letter Ezh
}, when = lambda _: ac_Chr_main == 0x2116 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Hook Above/Glottal Stop", {
    # Option+Z                  {U+02C0}
    # Valid keys:
    # a e i o u y
    # A E I O U Y 
    C("A"):                     UC(0x1EA3),                     # ả  Latin Small Letter A with Hook Above
    C("E"):                     UC(0x1EBB),                     # ẻ  Latin Small Letter E with Hook Above
    C("I"):                     UC(0x1EC9),                     # ỉ  Latin Small Letter I with Hook Above
    C("O"):                     UC(0x1ECF),                     # ỏ  Latin Small Letter O with Hook Above
    C("U"):                     UC(0x1EE7),                     # ủ  Latin Small Letter U with Hook Above
    C("Y"):                     UC(0x1EF7),                     # ỷ  Latin Small Letter Y with Hook Above
    C("Shift-A"):               UC(0x1EA2),                     # Ả  Latin Small Letter A with Hook Above
    C("Shift-E"):               UC(0x1EBA),                     # Ẻ  Latin Small Letter E with Hook Above
    C("Shift-I"):               UC(0x1EC8),                     # Ỉ  Latin Small Letter I with Hook Above
    C("Shift-O"):               UC(0x1ECE),                     # Ỏ  Latin Small Letter O with Hook Above
    C("Shift-U"):               UC(0x1EE6),                     # Ủ  Latin Small Letter U with Hook Above
    C("Shift-Y"):               UC(0x1EF6),                     # Ỷ  Latin Small Letter Y with Hook Above
}, when = lambda _: ac_Chr_main == 0x02C0 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Dot Below", {
    # Option+X                  {U+002E}
    # Valid keys:
    # a b d e h i k l m n o r s t u v w y z
    # A B D E H I K L M N O R S T U V W Y Z 
    C("A"):                     UC(0x1EA1),                     # ạ Latin Small Letter A with Dot Below
    C("B"):                     UC(0x1E05),                     # ḅ Latin Small Letter B with Dot Below
    C("D"):                     UC(0x1E0D),                     # ḍ Latin Small Letter D with Dot Below
    C("E"):                     UC(0x1EB9),                     # ẹ Latin Small Letter E with Dot Below
    C("H"):                     UC(0x1E25),                     # ḥ Latin Small Letter H with Dot Below
    C("I"):                     UC(0x1ECB),                     # ị Latin Small Letter I with Dot Below
    C("K"):                     UC(0x1E33),                     # ḳ Latin Small Letter K with Dot Below
    C("L"):                     UC(0x1E37),                     # ḷ Latin Small Letter L with Dot Below
    C("M"):                     UC(0x1E43),                     # ṃ Latin Small Letter M with Dot Below
    C("N"):                     UC(0x1E47),                     # ṇ Latin Small Letter N with Dot Below
    C("O"):                     UC(0x1ECD),                     # ọ Latin Small Letter O with Dot Below
    C("R"):                     UC(0x1E5B),                     # ṛ Latin Small Letter R with Dot Below
    C("S"):                     UC(0x1E63),                     # ṣ Latin Small Letter S with Dot Below
    C("T"):                     UC(0x1E6D),                     # ṭ Latin Small Letter T with Dot Below
    C("U"):                     UC(0x1EE5),                     # ụ Latin Small Letter U with Dot Below
    C("V"):                     UC(0x1E7F),                     # ṿ Latin Small Letter V with Dot Below
    C("W"):                     UC(0x1E89),                     # ẉ Latin Small Letter W with Dot Below
    C("Y"):                     UC(0x1EF5),                     # ỵ Latin Small Letter Y with Dot Below
    C("Z"):                     UC(0x1E93),                     # ẓ Latin Small Letter Z with Dot Below
    C("Shift-A"):               UC(0x1EA0),                     # Ạ Latin Capital Letter A with Dot Below
    C("Shift-B"):               UC(0x1E04),                     # Ḅ Latin Capital Letter B with Dot Below
    C("Shift-D"):               UC(0x1E0C),                     # Ḍ Latin Capital Letter D with Dot Below
    C("Shift-E"):               UC(0x1EB8),                     # Ẹ Latin Capital Letter E with Dot Below
    C("Shift-H"):               UC(0x1E24),                     # Ḥ Latin Capital Letter H with Dot Below
    C("Shift-I"):               UC(0x1ECA),                     # Ị Latin Capital Letter I with Dot Below
    C("Shift-K"):               UC(0x1E32),                     # Ḳ Latin Capital Letter K with Dot Below
    C("Shift-L"):               UC(0x1E36),                     # Ḷ Latin Capital Letter L with Dot Below
    C("Shift-M"):               UC(0x1E42),                     # Ṃ Latin Capital Letter M with Dot Below
    C("Shift-N"):               UC(0x1E46),                     # Ṇ Latin Capital Letter N with Dot Below
    C("Shift-O"):               UC(0x1ECC),                     # Ọ Latin Capital Letter O with Dot Below
    C("Shift-R"):               UC(0x1E5A),                     # Ṛ Latin Capital Letter R with Dot Below
    C("Shift-S"):               UC(0x1E62),                     # Ṣ Latin Capital Letter S with Dot Below
    C("Shift-T"):               UC(0x1E6C),                     # Ṭ Latin Capital Letter T with Dot Below
    C("Shift-U"):               UC(0x1EE4),                     # Ụ Latin Capital Letter U with Dot Below
    C("Shift-V"):               UC(0x1E7E),                     # Ṿ Latin Capital Letter V with Dot Below
    C("Shift-W"):               UC(0x1E88),                     # Ẉ Latin Capital Letter W with Dot Below
    C("Shift-Y"):               UC(0x1EF4),                     # Ỵ Latin Capital Letter Y with Dot Below
    C("Shift-Z"):               UC(0x1E92),                     # Ẓ Latin Capital Letter Z with Dot Below
}, when = lambda _: ac_Chr_main == 0x002E and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Cedilla/Cedille", {
    # Option+C                  {U+00B8}
    # Valid keys:
    # c d e g h k l n r s t z
    # C D E G H K L N R S T Z 
    C("C"):                     UC(0x00E7),                     # ç Latin Small Letter C with Cedilla
    C("D"):                     UC(0x1E11),                     # ḑ Latin Small Letter D with Cedilla
    C("E"):                     UC(0x0229),                     # ȩ Latin Small Letter E with Cedilla
    C("G"):                     UC(0x0123),                     # ģ Latin Small Letter G with Cedilla
    C("H"):                     UC(0x1E29),                     # ḩ Latin Small Letter H with Cedilla
    C("K"):                     UC(0x0137),                     # ķ Latin Small Letter K with Cedilla
    C("L"):                     UC(0x013C),                     # ļ Latin Small Letter L with Cedilla
    C("N"):                     UC(0x0146),                     # ņ Latin Small Letter N with Cedilla
    C("R"):                     UC(0x0157),                     # ŗ Latin Small Letter R with Cedilla
    C("S"):                     UC(0x015F),                     # ş Latin Small Letter S with Cedilla
    C("T"):                     UC(0x0163),                     # ţ Latin Small Letter T with Cedilla
    C("Z"):                    [UC(0x007A),UC(0x0327)],         # z̧ Latin Small Letter Z with Cedilla
    C("Shift-C"):               UC(0x00C7),                     # Ç Latin Capital Letter C with Cedilla
    C("Shift-D"):               UC(0x1E10),                     # Ḑ Latin Capital Letter D with Cedilla
    C("Shift-E"):               UC(0x0228),                     # Ȩ Latin Capital Letter E with Cedilla
    C("Shift-G"):               UC(0x0122),                     # Ģ Latin Capital Letter G with Cedilla
    C("Shift-H"):               UC(0x1E28),                     # Ḩ Latin Capital Letter H with Cedilla
    C("Shift-K"):               UC(0x0136),                     # Ķ Latin Capital Letter K with Cedilla
    C("Shift-L"):               UC(0x013B),                     # Ļ Latin Capital Letter L with Cedilla
    C("Shift-N"):               UC(0x0145),                     # Ņ Latin Capital Letter N with Cedilla
    C("Shift-R"):               UC(0x0156),                     # Ŗ Latin Capital Letter R with Cedilla
    C("Shift-S"):               UC(0x015E),                     # Ş Latin Capital Letter S with Cedilla
    C("Shift-T"):               UC(0x0162),                     # Ţ Latin Capital Letter T with Cedilla
    C("Shift-Z"):              [UC(0x005A),UC(0x0327)],         # Z̧ Latin Capital Letter Z with Cedilla
}, when = lambda _: ac_Chr_main == 0x00B8 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Caron/hacek", {
    # Option+V                  {U+02C7}
    # Valid keys:
    # a c d e g h i j k l n o r s t u v x z
    # A C D E G H I J K L N O R S T U V X Z 
    C("A"):                     UC(0x01CE),                     # ǎ Latin Small Letter A with Caron
    C("C"):                     UC(0x010D),                     # č Latin Small Letter C with Caron
    C("D"):                     UC(0x010F),                     # ď Latin Small Letter D with Caron
    C("E"):                     UC(0x011B),                     # ě Latin Small Letter E with Caron
    C("G"):                     UC(0x01E7),                     # ǧ Latin Small Letter G with Caron
    C("H"):                     UC(0x021F),                     # ȟ Latin Small Letter H with Caron
    C("I"):                     UC(0x01D0),                     # ǐ Latin Small Letter I with Caron
    C("J"):                     UC(0x01F0),                     # ǰ Latin Small Letter J with Caron
    C("K"):                     UC(0x01E9),                     # ǩ Latin Small Letter K with Caron
    C("L"):                     UC(0x013E),                     # ľ Latin Small Letter L with Caron
    C("N"):                     UC(0x0148),                     # ň Latin Small Letter N with Caron
    C("O"):                     UC(0x01D2),                     # ǒ Latin Small Letter O with Caron
    C("R"):                     UC(0x0159),                     # ř Latin Small Letter R with Caron
    C("S"):                     UC(0x0161),                     # š Latin Small Letter S with Caron
    C("T"):                     UC(0x0165),                     # ť Latin Small Letter T with Caron
    C("U"):                     UC(0x01D4),                     # ǔ Latin Small Letter U with Caron
    C("V"):                     UC(0x01DA),                     # ǚ Latin Small Letter U w/Diaeresis and Caron
    C("X"):                    [UC(0x0292),UC(0x030C)],         # ǯ Latin Small Letter Ezh with Caron
    C("Z"):                     UC(0x017E),                     # ž Latin Small Letter Z with Caron
    C("Shift-A"):               UC(0x01CD),                     # Ǎ Latin Capital Letter A with Caron
    C("Shift-C"):               UC(0x010C),                     # Č Latin Capital Letter C with Caron
    C("Shift-D"):               UC(0x010E),                     # Ď Latin Capital Letter D with Caron
    C("Shift-E"):               UC(0x011A),                     # Ě Latin Capital Letter E with Caron
    C("Shift-G"):               UC(0x01E6),                     # Ǧ Latin Capital Letter G with Caron
    C("Shift-H"):               UC(0x021E),                     # Ȟ Latin Capital Letter H with Caron
    C("Shift-I"):               UC(0x01CF),                     # Ǐ Latin Capital Letter I with Caron
    C("Shift-J"):              [UC(0x004A),UC(0x030C)],         # J̌ Latin Capital Letter J with Caron
    C("Shift-K"):               UC(0x01E8),                     # Ǩ Latin Capital Letter K with Caron
    C("Shift-L"):               UC(0x013D),                     # Ľ Latin Capital Letter L with Caron
    C("Shift-N"):               UC(0x0147),                     # Ň Latin Capital Letter N with Caron
    C("Shift-O"):               UC(0x01D1),                     # Ǒ Latin Capital Letter O with Caron
    C("Shift-R"):               UC(0x0158),                     # Ř Latin Capital Letter R with Caron
    C("Shift-S"):               UC(0x0160),                     # Š Latin Capital Letter S with Caron
    C("Shift-T"):               UC(0x0164),                     # Ť Latin Capital Letter T with Caron
    C("Shift-U"):               UC(0x01D3),                     # Ǔ Latin Capital Letter U with Caron
    C("Shift-V"):               UC(0x01D9),                     # Ǚ Latin Capital Letter U w/Diaeresis and Caron
    C("Shift-X"):              [UC(0x01B7),UC(0x030C)],         # Ǯ Latin Capital Letter Ezh with Caron
    C("Shift-Z"):               UC(0x017D),                     # Ž Latin Capital Letter Z with Caron
}, when = lambda _: ac_Chr_main == 0x02C7 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Breve", {
    # Option+B                  {U+02D8}
    # Valid keys:
    # a e g h i o u
    # A E G H I O U 
    C("A"):                     UC(0x0103),                     # ă Latin Small Letter A with Breve
    C("E"):                     UC(0x0115),                     # ĕ Latin Small Letter E with Breve
    C("G"):                     UC(0x011F),                     # ğ Latin Small Letter G with Breve
    C("H"):                     UC(0x1E2B),                     # ḫ Latin Small Letter H with Breve Below
    C("I"):                     UC(0x012D),                     # ĭ Latin Small Letter I with Breve
    C("O"):                     UC(0x014F),                     # ŏ Latin Small Letter O with Breve
    C("U"):                     UC(0x016D),                     # ŭ Latin Small Letter U with Breve
    C("Shift-A"):               UC(0x0102),                     # Ă Latin Capital Letter A with Breve
    C("Shift-E"):               UC(0x0114),                     # Ĕ Latin Capital Letter E with Breve
    C("Shift-G"):               UC(0x011E),                     # Ğ Latin Capital Letter G with Breve
    C("Shift-H"):               UC(0x1E2A),                     # Ḫ Latin Capital Letter H with Breve Below
    C("Shift-I"):               UC(0x012C),                     # Ĭ Latin Capital Letter I with Breve
    C("Shift-O"):               UC(0x014E),                     # Ŏ Latin Capital Letter O with Breve
    C("Shift-U"):               UC(0x016C),                     # Ŭ Latin Capital Letter U with Breve
}, when = lambda _: ac_Chr_main == 0x02D8 and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Tilde", {
    # Option+N                  {U+02DC}
    # Valid keys:
    # a e i n o u v y
    # A E I N O U V Y 
    C("A"):                     UC(0x00E3),                     # ã Latin Small Letter A with Tilde
    C("E"):                     UC(0x1EBD),                     # ẽ Latin Small Letter E with Tilde
    C("I"):                     UC(0x0129),                     # ĩ Latin Small Letter I with Tilde
    C("N"):                     UC(0x00F1),                     # ñ Latin Small Letter N with Tilde
    C("O"):                     UC(0x00F5),                     # õ Latin Small Letter O with Tilde
    C("U"):                     UC(0x0169),                     # ũ Latin Small Letter U with Tilde
    C("V"):                     UC(0x1E7D),                     # ṽ Latin Small Letter V with Tilde
    C("Y"):                     UC(0x1EF9),                     # ỹ Latin Small Letter Y with Tilde
    C("Shift-A"):               UC(0x00C3),                     # Ã Latin Capital Letter A with Tilde
    C("Shift-E"):               UC(0x1EBC),                     # Ẽ Latin Capital Letter E with Tilde
    C("Shift-I"):               UC(0x0128),                     # Ĩ Latin Capital Letter I with Tilde
    C("Shift-N"):               UC(0x00D1),                     # Ñ Latin Capital Letter N with Tilde
    C("Shift-O"):               UC(0x00D5),                     # Õ Latin Capital Letter O with Tilde
    C("Shift-U"):               UC(0x0168),                     # Ũ Latin Capital Letter U with Tilde
    C("Shift-V"):               UC(0x1E7C),                     # Ṽ Latin Capital Letter V with Tilde
    C("Shift-Y"):               UC(0x1EF8),                     # Ỹ Latin Capital Letter Y with Tilde
}, when = lambda _: ac_Chr_main == 0x02DC and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Ogonek", {
    # Option+M                  {U+02DB}
    # Valid keys:
    # a e i o u
    # A E I O U 
    C("A"):                     UC(0x0105),                     # ą Latin Small Letter A with Ogonek
    C("E"):                     UC(0x0119),                     # ę Latin Small Letter E with Ogonek
    C("I"):                     UC(0x012F),                     # į Latin Small Letter I with Ogonek
    C("O"):                     UC(0x01EB),                     # ǫ Latin Small Letter O with Ogonek
    C("U"):                     UC(0x0173),                     # ų Latin Small Letter U with Ogonek
    C("Shift-A"):               UC(0x0104),                     # Ą Latin Capital Letter A with Ogonek
    C("Shift-E"):               UC(0x0118),                     # Ę Latin Capital Letter E with Ogonek
    C("Shift-I"):               UC(0x012E),                     # Į Latin Capital Letter I with Ogonek
    C("Shift-O"):               UC(0x01EA),                     # Ǫ Latin Capital Letter O with Ogonek
    C("Shift-U"):               UC(0x0172),                     # Ų Latin Capital Letter U with Ogonek
}, when = lambda _: ac_Chr_main == 0x02DB and cnfg.optspec_layout == 'ABC')

keymap("DK-ABC - Hook", {
    # Shift+Option+Dot          {U+0294}
    # Valid keys:
    # b c d f g h i k n p q r s t u x y z 
    # B C D F G   I K N P   R S T U X Y Z 
    C("B"):                     UC(0x0253),                     # ɓ Latin Small Letter B with Hook
    C("C"):                     UC(0x0188),                     # ƈ Latin Small Letter C with Hook
    C("D"):                     UC(0x0257),                     # ɗ Latin Small Letter D with Hook
    C("F"):                     UC(0x0192),                     # ƒ Latin Small Letter F with Hook (function symbol)
    C("G"):                     UC(0x0260),                     # ɠ Latin Small Letter G with Hook
    C("H"):                     UC(0x0266),                     # ɦ Latin Small Letter H with Hook
    C("I"):                     UC(0x0269),                     # ɩ Latin Small Letter Iota
    C("K"):                     UC(0x0199),                     # ƙ Latin Small Letter K with Hook
    C("N"):                     UC(0x0272),                     # ɲ Latin Small Letter N with Left Hook
    C("P"):                     UC(0x01A5),                     # ƥ Latin Small Letter P with Hook
    C("Q"):                     UC(0x02A0),                     # ʠ Latin Small Letter Q with Hook
    C("R"):                     UC(0x0288),                     # ʈ Latin Small Letter T with Retroflex Hook
    C("S"):                     UC(0x0283),                     # ʃ Latin Small Letter Esh
    C("T"):                     UC(0x01AD),                     # ƭ Latin Small Letter T with Hook
    C("U"):                     UC(0x028B),                     # ʋ Latin Small Letter V with Hook
    C("X"):                     UC(0x0256),                     # ɖ Latin Small Letter D with Tail
    C("Y"):                     UC(0x01B4),                     # ƴ Latin Small Letter Y with Hook
    C("Z"):                     UC(0x0225),                     # ȥ Latin Small Letter Z with Hook
    C("Shift-B"):               UC(0x0181),                     # Ɓ Latin Capital Letter B with Hook
    C("Shift-C"):               UC(0x0187),                     # Ƈ Latin Capital Letter C with Hook
    C("Shift-D"):               UC(0x018A),                     # Ɗ Latin Capital Letter D with Hook
    C("Shift-F"):               UC(0x0191),                     # Ƒ Latin Capital Letter F with Hook
    C("Shift-G"):               UC(0x0193),                     # Ɠ Latin Capital Letter G with Hook
    C("Shift-I"):               UC(0x0196),                     # Ɩ Latin Capital Letter Iota
    C("Shift-K"):               UC(0x0198),                     # Ƙ Latin Capital Letter K with Hook
    C("Shift-N"):               UC(0x019D),                     # Ɲ Latin Capital Letter N with Left Hook
    C("Shift-P"):               UC(0x01A4),                     # Ƥ Latin Capital Letter P with Hook
    C("Shift-R"):               UC(0x01AE),                     # Ʈ Latin Capital Letter T with Retroflex Hook
    C("Shift-S"):               UC(0x01A9),                     # Ʃ Latin Capital Letter Esh
    C("Shift-T"):               UC(0x01AC),                     # Ƭ Latin Capital Letter T with Hook
    C("Shift-U"):               UC(0x01B2),                     # Ʋ Latin Capital Letter V with Hook
    C("Shift-X"):               UC(0x0189),                     # Ɖ Latin Capital Letter African D
    C("Shift-Y"):               UC(0x01B3),                     # Ƴ Latin Capital Letter Y with Hook
    C("Shift-Z"):               UC(0x0224),                     # Ȥ Latin Capital Letter Z with Hook
}, when = lambda _: ac_Chr_main == 0x0294 and cnfg.optspec_layout == 'ABC')


#######################################
###  DEAD KEYS KEYMAPS - US LAYOUT  ###
#######################################
keymap("DK-US - Grave", {
    # Valid keys:
    # a e i o u
    # A E I O U
    C("A"):                     UC(0x00E0),                     # à Latin Small a with Grave
    C("E"):                     UC(0x00E8),                     # è Latin Small e with Grave
    C("I"):                     UC(0x00EC),                     # ì Latin Small i with Grave
    C("O"):                     UC(0x00F2),                     # ò Latin Small o with Grave
    C("U"):                     UC(0x00F9),                     # ù Latin Small u with Grave
    C("Shift-A"):               UC(0x00C0),                     # À Latin Capital A with Grave
    C("Shift-E"):               UC(0x00C8),                     # È Latin Capital E with Grave
    C("Shift-I"):               UC(0x00CC),                     # Ì Latin Capital I with Grave
    C("Shift-O"):               UC(0x00D2),                     # Ò Latin Capital O with Grave
    C("Shift-U"):               UC(0x00D9),                     # Ù Latin Capital U with Grave
}, when = lambda _: ac_Chr_main == 0x0060 and cnfg.optspec_layout == 'US')

keymap("DK-US - Acute", {
    # Valid keys:
    # a e i o u
    # A E I O U
    C("A"):                     UC(0x00E1),                     # á Latin Small a with Acute
    C("E"):                     UC(0x00E9),                     # é Latin Small e with Acute
    C("I"):                     UC(0x00ED),                     # í Latin Small i with Acute
    C("O"):                     UC(0x00F3),                     # ó Latin Small o with Acute
    C("U"):                     UC(0x00FA),                     # ú Latin Small u with Acute
    C("Shift-A"):               UC(0x00C1),                     # Á Latin Capital A with Acute
    C("Shift-E"):               UC(0x00C9),                     # É Latin Capital E with Acute
    C("Shift-I"):               UC(0x00CD),                     # Í Latin Capital I with Acute
    C("Shift-O"):               UC(0x00D3),                     # Ó Latin Capital O with Acute
    C("Shift-U"):               UC(0x00DA),                     # Ú Latin Capital U with Acute
}, when = lambda _: ac_Chr_main == 0x00B4 and cnfg.optspec_layout == 'US')

keymap("DK-US - Umlaut", {
    # Valid keys:
    # a e i o u y
    # A E I O U Y
    C("A"):                     UC(0x00E4),                     # ä Latin Small a with Umlaut
    C("E"):                     UC(0x00EB),                     # ë Latin Small e with Umlaut
    C("I"):                     UC(0x00EF),                     # ï Latin Small i with Umlaut
    C("O"):                     UC(0x00F6),                     # ö Latin Small o with Umlaut
    C("U"):                     UC(0x00FC),                     # ü Latin Small u with Umlaut
    C("Y"):                     UC(0x00FF),                     # ÿ Latin Small y with Umlaut
    C("Shift-A"):               UC(0x00C4),                     # Ä Latin Capital A with Umlaut
    C("Shift-E"):               UC(0x00CB),                     # Ë Latin Capital E with Umlaut
    C("Shift-I"):               UC(0x00CF),                     # Ï Latin Capital I with Umlaut
    C("Shift-O"):               UC(0x00D6),                     # Ö Latin Capital O with Umlaut
    C("Shift-U"):               UC(0x00DC),                     # Ü Latin Capital U with Umlaut
    C("Shift-Y"):               UC(0x0178),                     # Ÿ Latin Capital Y with Umlaut
}, when = lambda _: ac_Chr_main == 0x00A8 and cnfg.optspec_layout == 'US')

keymap("DK-US - Circumflex", {
    # Valid keys:
    # a e i o u
    # A E I O U
    C("A"):                     UC(0x00E2),                     # â Latin Small a with Circumflex
    C("E"):                     UC(0x00EA),                     # ê Latin Small e with Circumflex
    C("I"):                     UC(0x00EE),                     # î Latin Small i with Circumflex
    C("O"):                     UC(0x00F4),                     # ô Latin Small o with Circumflex
    C("U"):                     UC(0x00FB),                     # û Latin Small u with Circumflex
    C("Shift-A"):               UC(0x00C2),                     # Â Latin Capital A with Circumflex
    C("Shift-E"):               UC(0x00CA),                     # Ê Latin Capital E with Circumflex
    C("Shift-I"):               UC(0x00CE),                     # Î Latin Capital I with Circumflex
    C("Shift-O"):               UC(0x00D4),                     # Ô Latin Capital O with Circumflex
    C("Shift-U"):               UC(0x00DB),                     # Û Latin Capital U with Circumflex
}, when = lambda _: ac_Chr_main == 0x02C6 and cnfg.optspec_layout == 'US')

keymap("DK-US - Tilde", {
    # Valid keys:
    # a n o
    # A N O
    C("A"):                     UC(0x00E3),                     # ã Latin Small a with Tilde
    C("N"):                     UC(0x00F1),                     # ñ Latin Small n with Tilde
    C("O"):                     UC(0x00F5),                     # õ Latin Small o with Tilde
    C("Shift-A"):               UC(0x00C3),                     # Ã Latin Capital A with Tilde
    C("Shift-N"):               UC(0x00D1),                     # Ñ Latin Capital N with Tilde
    C("Shift-O"):               UC(0x00D5),                     # Õ Latin Capital O with Tilde
}, when = lambda _: ac_Chr_main == 0x02DC and cnfg.optspec_layout == 'US')



#################################################################
###                                                           ###
###                                                           ###
###      ███████ ███████  ██████  █████  ██████  ███████      ###
###      ██      ██      ██      ██   ██ ██   ██ ██           ###
###      █████   ███████ ██      ███████ ██████  █████        ###
###      ██           ██ ██      ██   ██ ██      ██           ###
###      ███████ ███████  ██████ ██   ██ ██      ███████      ###
###                                                           ###
###                                                           ###
#################################################################
keymap("Escape actions for dead keys - Overrides for ABC Extended", {

    ###  activate other dead keys correctly while one is active

    # US layout dead keys (not here, see keymap below)

    # ABC Extended layout dead keys
    C("Alt-Grave"):     [getDK(),UC(0x0060),C("Shift-Left"),setDK(0x0060)], # Dead Key Accent: Grave
    C("Alt-6"):         [getDK(),UC(0x02C6),C("Shift-Left"),setDK(0x02C6)], # Dead Key Accent: Circumflex
    C("Alt-W"):         [getDK(),UC(0x02D9),C("Shift-Left"),setDK(0x02D9)], # Dead Key Accent: Dot Above
    C("Alt-E"):         [getDK(),UC(0x00B4),C("Shift-Left"),setDK(0x00B4)], # Dead Key Accent: Acute

    # C("Shift-Alt-Y"):   [getDK(),UC(0x030F),C("Shift-Left"),setDK(0x030F)], # Dead Key Accent: Combining Double Grave
    # Double Grave accent acts odd when using the Combining Double Grave {U+030F}
    # Substituting {U+02F5}: ˵ Modifier Letter Middle Double Grave Accent
    C("Shift-Alt-Y"):   [getDK(),UC(0x02F5),C("Shift-Left"),setDK(0x02F5)], # Dead Key Accent: Double Grave (substitute)

    C("Alt-U"):         [getDK(),UC(0x00A8),C("Shift-Left"),setDK(0x00A8)], # Dead Key Accent: Umlaut/Diaeresis
    C("Alt-I"):         [getDK(),UC(0x02BC),C("Shift-Left"),setDK(0x02BC)], # Dead Key Accent: Apostrophe/Horn
    C("Alt-P"):         [getDK(),UC(0x002C),C("Shift-Left"),setDK(0x002C)], # Dead Key Accent: Comma Below
    C("Alt-A"):         [getDK(),UC(0x00AF),C("Shift-Left"),setDK(0x00AF)], # Dead Key Accent: Macron/Line Above

    # C("Shift-Alt-S"):   [getDK(),UC(0x0311),C("Shift-Left"),setDK(0x0311)], # Dead Key Accent: Combining Inverted Breve
    C("Shift-Alt-S"):   [getDK(),UC(0x1D16),C("Shift-Left"),setDK(0x1D16)], # Dead Key Accent: Combining Inverted Breve

    # C("Shift-Alt-F"):   [getDK(),UC(0x0330),C("Shift-Left"),setDK(0x0330)], # Dead Key Accent: Combining Tilde Below
    # Tilde Below accent acts odd when using the Combining Tilde Below {U+0330}
    # Substituting {U+02F7}: ˷ Modifier Letter Low Tilde
    C("Shift-Alt-F"):   [getDK(),UC(0x02F7),C("Shift-Left"),setDK(0x02F7)], # Dead Key Accent: Tilde Below
    C("Shift-Alt-G"):   [getDK(),UC(0x2038),C("Shift-Left"),setDK(0x2038)], # Dead Key Accent: Caret/Circumflex Below

    C("Alt-H"):         [getDK(),UC(0x02CD),C("Shift-Left"),setDK(0x02CD)], # Dead Key Accent: Low Macron/Line Below
    C("Alt-J"):         [getDK(),UC(0x02DD),C("Shift-Left"),setDK(0x02DD)], # Dead Key Accent: Double Acute
    C("Alt-K"):         [getDK(),UC(0x02DA),C("Shift-Left"),setDK(0x02DA)], # Dead Key Accent: Ring Above
    C("Alt-L"):         [getDK(),UC(0x002D),C("Shift-Left"),setDK(0x002D)], # Dead Key Accent: Stroke/Hyphen-Minus

    C("Shift-Alt-Semicolon"): [getDK(),UC(0x2116),C("Shift-Left"),setDK(0x2116)], # Dead Key Accent: Numero Sign

    C("Alt-Z"):         [getDK(),UC(0x02C0),C("Shift-Left"),setDK(0x02C0)], # Dead Key Accent: Hook Above/Glottal Stop
    C("Alt-X"):         [getDK(),UC(0x002E),C("Shift-Left"),setDK(0x002E)], # Dead Key Accent: Dot Below
    C("Alt-C"):         [getDK(),UC(0x00B8),C("Shift-Left"),setDK(0x00B8)], # Dead Key Accent: Cedilla/Cedille
    C("Alt-V"):         [getDK(),UC(0x02C7),C("Shift-Left"),setDK(0x02C7)], # Dead Key Accent: Caron/hacek
    C("Alt-B"):         [getDK(),UC(0x02D8),C("Shift-Left"),setDK(0x02D8)], # Dead Key Accent: Breve
    C("Alt-N"):         [getDK(),UC(0x02DC),C("Shift-Left"),setDK(0x02DC)], # Dead Key Accent: Tilde
    C("Alt-M"):         [getDK(),UC(0x02DB),C("Shift-Left"),setDK(0x02DB)], # Dead Key Accent: Ogonek

    C("Shift-Alt-Dot"): [getDK(),UC(0x0294),C("Shift-Left"),setDK(0x0294)], # Dead Key Accent: Hook

}, when = lambda _: ac_Chr_main in deadkeys_list and cnfg.optspec_layout == 'ABC')

keymap("Escape actions for dead keys", {
    # special case shortcuts that should cancel dead keys
    C("Esc"):           [getDK(),setDK(None)],                              # Leave accent char if dead keys Escaped
    C("Space"):         [getDK(),setDK(None)],                              # Leave accent char if user hits Space
    C("Delete"):        [getDK(),setDK(None)],                              # Leave accent char if user hits Delete
    C("Backspace"):     [getDK(),C("Backspace"),setDK(None)],               # Delete character if user hits Backspace
    C("Tab"):           [getDK(),C("Tab"),setDK(None)],                     # Leave accent char, insert Tab
    C("Enter"):         [getDK(),C("Enter"),setDK(None)],                   # Leave accent char, Enter key
    C("Up"):            [getDK(),C("Up"),setDK(None)],                      # Leave accent char, up arrow
    C("Down"):          [getDK(),C("Down"),setDK(None)],                    # Leave accent char, down arrow
    C("Left"):          [getDK(),C("Left"),setDK(None)],                    # Leave accent char, left arrow
    C("Right"):         [getDK(),C("Right"),setDK(None)],                   # Leave accent char, right arrow
    C("RC-Tab"):        [getDK(),bind,C("Alt-Tab"),setDK(None)],            # Leave accent char, task switch
    C("Shift-RC-Tab"):  [getDK(),bind,C("Shift-Alt-Tab"),setDK(None)],      # Leave accent char, task switch (reverse)
    C("RC-Grave"):      [getDK(),bind,C("Alt-Grave"),setDK(None)],          # Leave accent char, in-app window switch
    C("Shift-RC-Tab"):  [getDK(),bind,C("Shift-Alt-Grave"),setDK(None)],    # Leave accent char, in-app window switch (reverse)

    # common shortcuts that should also cancel dead keys
    C("RC-a"):                  [getDK(),C("RC-a"),setDK(None)],            # Leave accent char, select all
    C("RC-z"):                  [getDK(),C("RC-z"),setDK(None)],            # Leave accent char, undo
    C("RC-x"):                  [getDK(),C("RC-x"),setDK(None)],            # Leave accent char, cut
    C("RC-c"):                  [getDK(),C("RC-c"),setDK(None)],            # Leave accent char, copy
    C("RC-v"):                  [getDK(),C("RC-v"),setDK(None)],            # Leave accent char, paste

    ###  activate other dead keys correctly while one is active

    # US layout dead keys
    C("Alt-Grave"):     [getDK(),UC(0x0060),C("Shift-Left"),setDK(0x0060)], # Dead Key Accent: Grave
    C("Alt-E"):         [getDK(),UC(0x00B4),C("Shift-Left"),setDK(0x00B4)], # Dead Key Accent: Acute
    C("Alt-U"):         [getDK(),UC(0x00A8),C("Shift-Left"),setDK(0x00A8)], # Dead Key Accent: Umlaut/Diaeresis
    C("Alt-I"):         [getDK(),UC(0x02C6),C("Shift-Left"),setDK(0x02C6)], # Dead Key Accent: Circumflex
    C("Alt-N"):         [getDK(),UC(0x02DC),C("Shift-Left"),setDK(0x02DC)], # Dead Key Accent: Tilde

    # ABC Extended layout dead keys (not here, see keymap above)


    # cancel dead keys with number keys row
    C("Grave"):                 [getDK(),C("Grave"),setDK(None)],
    C("Key_1"):                 [getDK(),C("Key_1"),setDK(None)],
    C("Key_2"):                 [getDK(),C("Key_2"),setDK(None)],
    C("Key_3"):                 [getDK(),C("Key_3"),setDK(None)],
    C("Key_4"):                 [getDK(),C("Key_4"),setDK(None)],
    C("Key_5"):                 [getDK(),C("Key_5"),setDK(None)],
    C("Key_6"):                 [getDK(),C("Key_6"),setDK(None)],
    C("Key_7"):                 [getDK(),C("Key_7"),setDK(None)],
    C("Key_8"):                 [getDK(),C("Key_8"),setDK(None)],
    C("Key_9"):                 [getDK(),C("Key_9"),setDK(None)],
    C("Key_0"):                 [getDK(),C("Key_0"),setDK(None)],
    C("Minus"):                 [getDK(),C("Minus"),setDK(None)],
    C("Equal"):                 [getDK(),C("Equal"),setDK(None)],
    C("Shift-Grave"):           [getDK(),C("Shift-Grave"),setDK(None)],
    C("Shift-Key_1"):           [getDK(),C("Shift-Key_1"),setDK(None)],
    C("Shift-Key_2"):           [getDK(),C("Shift-Key_2"),setDK(None)],
    C("Shift-Key_3"):           [getDK(),C("Shift-Key_3"),setDK(None)],
    C("Shift-Key_4"):           [getDK(),C("Shift-Key_4"),setDK(None)],
    C("Shift-Key_5"):           [getDK(),C("Shift-Key_5"),setDK(None)],
    C("Shift-Key_6"):           [getDK(),C("Shift-Key_6"),setDK(None)],
    C("Shift-Key_7"):           [getDK(),C("Shift-Key_7"),setDK(None)],
    C("Shift-Key_8"):           [getDK(),C("Shift-Key_8"),setDK(None)],
    C("Shift-Key_9"):           [getDK(),C("Shift-Key_9"),setDK(None)],
    C("Shift-Key_0"):           [getDK(),C("Shift-Key_0"),setDK(None)],
    C("Shift-Minus"):           [getDK(),C("Shift-Minus"),setDK(None)],
    C("Shift-Equal"):           [getDK(),C("Shift-Equal"),setDK(None)],

    # cancel dead keys with any letter on the keyboard that isn't supported by the dead key
    C("A"):                     [getDK(),C("A"),setDK(None)],
    C("B"):                     [getDK(),C("B"),setDK(None)],
    C("C"):                     [getDK(),C("C"),setDK(None)],
    C("D"):                     [getDK(),C("D"),setDK(None)],
    C("E"):                     [getDK(),C("E"),setDK(None)],
    C("F"):                     [getDK(),C("F"),setDK(None)],
    C("G"):                     [getDK(),C("G"),setDK(None)],
    C("H"):                     [getDK(),C("H"),setDK(None)],
    C("I"):                     [getDK(),C("I"),setDK(None)],
    C("J"):                     [getDK(),C("J"),setDK(None)],
    C("K"):                     [getDK(),C("K"),setDK(None)],
    C("L"):                     [getDK(),C("L"),setDK(None)],
    C("M"):                     [getDK(),C("M"),setDK(None)],
    C("N"):                     [getDK(),C("N"),setDK(None)],
    C("O"):                     [getDK(),C("O"),setDK(None)],
    C("P"):                     [getDK(),C("P"),setDK(None)],
    C("Q"):                     [getDK(),C("Q"),setDK(None)],
    C("R"):                     [getDK(),C("R"),setDK(None)],
    C("S"):                     [getDK(),C("S"),setDK(None)],
    C("T"):                     [getDK(),C("T"),setDK(None)],
    C("U"):                     [getDK(),C("U"),setDK(None)],
    C("V"):                     [getDK(),C("V"),setDK(None)],
    C("W"):                     [getDK(),C("W"),setDK(None)],
    C("X"):                     [getDK(),C("X"),setDK(None)],
    C("Y"):                     [getDK(),C("Y"),setDK(None)],
    C("Z"):                     [getDK(),C("Z"),setDK(None)],
    C("Shift-A"):               [getDK(),C("Shift-A"),setDK(None)],
    C("Shift-B"):               [getDK(),C("Shift-B"),setDK(None)],
    C("Shift-C"):               [getDK(),C("Shift-C"),setDK(None)],
    C("Shift-D"):               [getDK(),C("Shift-D"),setDK(None)],
    C("Shift-E"):               [getDK(),C("Shift-E"),setDK(None)],
    C("Shift-F"):               [getDK(),C("Shift-F"),setDK(None)],
    C("Shift-G"):               [getDK(),C("Shift-G"),setDK(None)],
    C("Shift-H"):               [getDK(),C("Shift-H"),setDK(None)],
    C("Shift-I"):               [getDK(),C("Shift-I"),setDK(None)],
    C("Shift-J"):               [getDK(),C("Shift-J"),setDK(None)],
    C("Shift-K"):               [getDK(),C("Shift-K"),setDK(None)],
    C("Shift-L"):               [getDK(),C("Shift-L"),setDK(None)],
    C("Shift-M"):               [getDK(),C("Shift-M"),setDK(None)],
    C("Shift-N"):               [getDK(),C("Shift-N"),setDK(None)],
    C("Shift-O"):               [getDK(),C("Shift-O"),setDK(None)],
    C("Shift-P"):               [getDK(),C("Shift-P"),setDK(None)],
    C("Shift-Q"):               [getDK(),C("Shift-Q"),setDK(None)],
    C("Shift-R"):               [getDK(),C("Shift-R"),setDK(None)],
    C("Shift-S"):               [getDK(),C("Shift-S"),setDK(None)],
    C("Shift-T"):               [getDK(),C("Shift-T"),setDK(None)],
    C("Shift-U"):               [getDK(),C("Shift-U"),setDK(None)],
    C("Shift-V"):               [getDK(),C("Shift-V"),setDK(None)],
    C("Shift-W"):               [getDK(),C("Shift-W"),setDK(None)],
    C("Shift-X"):               [getDK(),C("Shift-X"),setDK(None)],
    C("Shift-Y"):               [getDK(),C("Shift-Y"),setDK(None)],
    C("Shift-Z"):               [getDK(),C("Shift-Z"),setDK(None)],

    # cancel dead keys with other punctuation keys
    C("Left_Brace"):            [getDK(),C("Left_Brace"),setDK(None)],
    C("Right_Brace"):           [getDK(),C("Right_Brace"),setDK(None)],
    C("Backslash"):             [getDK(),C("Backslash"),setDK(None)],
    C("Semicolon"):             [getDK(),C("Semicolon"),setDK(None)],
    C("Apostrophe"):            [getDK(),C("Apostrophe"),setDK(None)],
    C("Comma"):                 [getDK(),C("Comma"),setDK(None)],
    C("Dot"):                   [getDK(),C("Dot"),setDK(None)],
    C("Slash"):                 [getDK(),C("Slash"),setDK(None)],
    C("Shift-Left_Brace"):      [getDK(),C("Shift-Left_Brace"),setDK(None)],
    C("Shift-Right_Brace"):     [getDK(),C("Shift-Right_Brace"),setDK(None)],
    C("Shift-Backslash"):       [getDK(),C("Shift-Backslash"),setDK(None)],
    C("Shift-Semicolon"):       [getDK(),C("Shift-Semicolon"),setDK(None)],
    C("Shift-Apostrophe"):      [getDK(),C("Shift-Apostrophe"),setDK(None)],
    C("Shift-Comma"):           [getDK(),C("Shift-Comma"),setDK(None)],
    C("Shift-Dot"):             [getDK(),C("Shift-Dot"),setDK(None)],
    C("Shift-Slash"):           [getDK(),C("Shift-Slash"),setDK(None)],

}, when = lambda _: ac_Chr_main in deadkeys_list)
# }, when = lambda _: ac_Chr in deadkeys_US or ac_Chr in deadkeys_ABC)

keymap("Disable Dead Keys",{
    # Nothing needs to be here. Tripwire keymap to disable active dead keys keymap(s)
}, when = lambda _: setDK(None)())



##############################################################################
###                                                                        ###
###                                                                        ###
###       █████  ██████   ██████     ███    ███  █████  ██ ███    ██       ###
###      ██   ██ ██   ██ ██          ████  ████ ██   ██ ██ ████   ██       ###
###      ███████ ██████  ██          ██ ████ ██ ███████ ██ ██ ██  ██       ###
###      ██   ██ ██   ██ ██          ██  ██  ██ ██   ██ ██ ██  ██ ██       ###
###      ██   ██ ██████   ██████     ██      ██ ██   ██ ██ ██   ████       ###
###                                                                        ###
###                                                                        ###
##############################################################################
# Main keymap for special characters on the ABC Extended layout
keymap("OptSpecialChars - ABC", {

    # Number keys row with Option
    ######################################################
    C("Alt-Grave"):     [UC(0x0060),C("Shift-Left"),setDK(0x0060)],     # Dead Key Accent: Grave

    C("Alt-1"):                 UC(0x00A1),                     # ¡ Inverted Exclamation Mark
    C("Alt-2"):                 UC(0x2122),                     # ™ Trade Mark Sign Emoji
    C("Alt-3"):                 UC(0x00A3),                     # £ British Pound currency symbol
    C("Alt-4"):                 UC(0x00A2),                     # ¢ Cent currency symbol
    C("Alt-5"):                 UC(0x00A7),                     # § Section symbol

    C("Alt-6"):         [UC(0x02C6),C("Shift-Left"),setDK(0x02C6)],     # Dead Key Accent: Circumflex

    C("Alt-7"):                 UC(0x00B6),                     # ¶ Paragraph mark (Pilcrow) symbol
    C("Alt-8"):                 UC(0x2022),                     # • Bullet Point symbol (solid)
    C("Alt-9"):                 UC(0x00AA),                     # ª Feminine Ordinal Indicator
    C("Alt-0"):                 UC(0x00BA),                     # º Masculine Ordinal Indicator
    C("Alt-Minus"):             UC(0x2013),                     # – En Dash punctuation mark
    C("Alt-Equal"):             UC(0x2260),                     # ≠ Not Equal To symbol

    # Number keys row with Shift+Option
    ######################################################
    C("Shift-Alt-Grave"):       UC(0x0300),                     # ` Combining Grave Accent
    C("Shift-Alt-1"):           UC(0x2044),                     # ⁄ Fraction Slash
    C("Shift-Alt-2"):           UC(0x20AC),                     # € Euro currency symbol
    C("Shift-Alt-3"):           UC(0x2039),                     # ‹ Single Left-Pointing Angle Quotation mark
    C("Shift-Alt-4"):           UC(0x203A),                     # › Single Right-Pointing Angle Quotation mark
    C("Shift-Alt-5"):           UC(0x2020),                     # † Simple dagger (cross) symbol
    C("Shift-Alt-6"):           UC(0x0302),                     #  ̂ Combining Circumflex Accent
    C("Shift-Alt-7"):           UC(0x2021),                     # ‡ Double dagger (cross) symbol
    C("Shift-Alt-8"):           UC(0x00B0),                     # ° Degree Sign
    C("Shift-Alt-9"):           UC(0x00B7),                     # · Middle Dot (interpunct/middot)
    C("Shift-Alt-0"):           UC(0x201A),                     # ‚ Single low-9 quotation mark
    C("Shift-Alt-Minus"):       UC(0x2014),                     # — Em Dash punctuation mark
    C("Shift-Alt-Equal"):       UC(0x00B1),                     # ± Plus Minus mathematical symbol

    # Tab key row with Option
    ######################################################
    C("Alt-Q"):                 UC(0x0153),                     # œ Small oe (oethel) ligature

    C("Alt-W"):         [UC(0x02D9),C("Shift-Left"),setDK(0x02D9)],     # Dead Key Accent: Dot Above
    C("Alt-E"):         [UC(0x00B4),C("Shift-Left"),setDK(0x00B4)],     # Dead Key Accent: Acute

    C("Alt-R"):                 UC(0x00AE),                     # ® Registered Trade Mark Sign
    C("Alt-T"):                 UC(0x00FE),                     # þ Latin Small Letter Thorn
    C("Alt-Y"):                 UC(0x00A5),                     # ¥ Japanese Yen currency symbol

    C("Alt-U"):         [UC(0x00A8),C("Shift-Left"),setDK(0x00A8)],     # Dead Key Accent: Umlaut/Diaeresis
    C("Alt-I"):         [UC(0x02BC),C("Shift-Left"),setDK(0x02BC)],     # Dead Key Accent: Apostrophe/Horn

    C("Alt-O"):                 UC(0x00F8),                     # ø Latin Small Letter o with Stroke

    C("Alt-P"):         [UC(0x002C),C("Shift-Left"),setDK(0x002C)],     # Dead Key Accent: Comma Below

    C("Alt-Left_Brace"):        UC(0x201C),                     # “ Left Double Quotation Mark
    C("Alt-Right_Brace"):       UC(0x2018),                     # ‘ Left Single Quotation Mark
    C("Alt-Backslash"):         UC(0x00AB),                     # « Left-Pointing Double Angle Quotation Mark

    # Tab key row with Shift+Option
    ######################################################
    C("Shift-Alt-Q"):           UC(0x0152),                     # Œ Capital OE (Oethel) ligature
    C("Shift-Alt-W"):           UC(0x0307),                     # ˙ Combining Dot Above
    C("Shift-Alt-E"):           UC(0x0301),                     #  ́ Combining Acute Accent
    C("Shift-Alt-R"):           UC(0x2030),                     # ‰ Per mille symbol (zero over zero-zero)
    C("Shift-Alt-T"):           UC(0x00DE),                     # Þ Latin Capital Letter Thorn

    # C("Shift-Alt-Y"):           UC(0x02F5), # UC(0x030F),       # ̏  Combining Double Grave Accent
    # Spacing issues when using Combining Double Grave {U+030F}
    # Substituting {U+02F5}: ˵ Modifier Letter Middle Double Grave Accent for initial presentation
    C("Shift-Alt-Y"):   [UC(0x02F5),C("Shift-Left"),setDK(0x02F5)],     # Dead Key Accent: Double Grave

    C("Shift-Alt-U"):           UC(0x0308),                     #  ̈ Combining Diaeresis/Umlaut
    C("Shift-Alt-I"):           UC(0x031B),                     # ̛ Combining Horn (Apostrophe)
    C("Shift-Alt-O"):           UC(0x00D8),                     # Ø Latin Capital Letter O with Stroke
    C("Shift-Alt-P"):           UC(0x0326),                     #  ̦ Combining Comma Below
    C("Shift-Alt-Left_Brace"):  UC(0x201D),                     # ” Right Double Quotation Mark
    C("Shift-Alt-Right_Brace"): UC(0x2019),                     # ’ Right Single Quotation Mark
    C("Shift-Alt-Backslash"):   UC(0x00BB),                     # » Right-Pointing Double Angle Quotation Mark

    # CapsLock key row with Option
    ######################################################

    C("Alt-A"):         [UC(0x00AF),C("Shift-Left"),setDK(0x00AF)],     # Dead Key Accent: Macron/Line Above

    C("Alt-S"):                 UC(0x00DF),                     # ß German Eszett/beta (Sharfes/Sharp S)
    C("Alt-D"):                 UC(0x00F0),                     # ð Latin Small Letter Eth
    C("Alt-F"):                 UC(0x0192),                     # ƒ Function/florin currency symbol
    C("Alt-G"):                 UC(0x00A9),                     # © Copyright Sign

    C("Alt-H"):         [UC(0x02CD),C("Shift-Left"),setDK(0x02CD)],     # Dead Key Accent: Low Macron/Line Below
    C("Alt-J"):         [UC(0x02DD),C("Shift-Left"),setDK(0x02DD)],     # Dead Key Accent: Double Acute
    C("Alt-K"):         [UC(0x02DA),C("Shift-Left"),setDK(0x02DA)],     # Dead Key Accent: Ring Above
    C("Alt-L"):         [UC(0x002D),C("Shift-Left"),setDK(0x002D)],     # Dead Key Accent: Stroke/Hyphen-Minus

    C("Alt-Semicolon"):         UC(0x2026),                     # … Horizontal ellipsis
    C("Alt-Apostrophe"):        UC(0x00E6),                     # æ Small ae ligature

    # CapsLock key row with Shift+Option
    ######################################################
    C("Shift-Alt-A"):           UC(0x0304),                     #  ̄ Combining Macron/Line Below

    # C("Shift-Alt-S"): [UC(0x0311),C("Shift-Left"),setDK(0x0311)],   # Dead Key Accent: Combining Inverted Breve
    # Combining Inverted Breve has spacing problems
    # Substituting {U+1D16}: ᴖ Latin Small Letter Top Half O
    C("Shift-Alt-S"):   [UC(0x1D16),C("Shift-Left"),setDK(0x1D16)],     # Dead Key Accent: Inverted Breve

    C("Shift-Alt-D"):           UC(0x00D0),                     # Ð Latin Capital Letter Eth

    # C("Shift-Alt-F"):   [UC(0x0330),C("Shift-Left"),setDK(0x0330)],     # Dead Key Accent: Tilde Below
    # Combining Tilde Below has spacing problems
    # Substituting {U+02F7}: ˷ Modifier Letter Low Tilde
    C("Shift-Alt-F"):   [UC(0x02F7),C("Shift-Left"),setDK(0x02F7)],     # Dead Key Accent: Tilde Below
    C("Shift-Alt-G"):   [UC(0x2038),C("Shift-Left"),setDK(0x2038)],     # Dead Key Accent: Caret/Circumflex Below

    C("Shift-Alt-H"):           UC(0x0331),                     # ̱  Combining Macron/Line Below
    C("Shift-Alt-J"):           UC(0x030B),                     #  ̋ Combining Double Acute Accent
    C("Shift-Alt-K"):           UC(0x030A),                     #  ̊ Combining Ring Above
    C("Shift-Alt-L"):           UC(0x0335),                     #  ̵ Combining Short Stroke Overlay

    C("Shift-Alt-Semicolon"):  [UC(0x2116),C("Shift-Left"),setDK(0x2116)],      # Dead Key Accent: Numero Sign

    C("Shift-Alt-Apostrophe"):  UC(0x00C6),                     # Æ Capital AE ligature

    # Shift keys row with Option
    ######################################################

    C("Alt-Z"): [UC(0x02C0),C("Shift-Left"),setDK(0x02C0)],     # Dead Key Accent: Hook Above/Glottal Stop
    C("Alt-X"): [UC(0x002E),C("Shift-Left"),setDK(0x002E)],     # Dead Key Accent: Dot Below
    C("Alt-C"): [UC(0x00B8),C("Shift-Left"),setDK(0x00B8)],     # Dead Key Accent: Cedilla/Cedille
    C("Alt-V"): [UC(0x02C7),C("Shift-Left"),setDK(0x02C7)],     # Dead Key Accent: Caron/hacek
    C("Alt-B"): [UC(0x02D8),C("Shift-Left"),setDK(0x02D8)],     # Dead Key Accent: Breve
    C("Alt-N"): [UC(0x02DC),C("Shift-Left"),setDK(0x02DC)],     # Dead Key Accent: Tilde
    C("Alt-M"): [UC(0x02DB),C("Shift-Left"),setDK(0x02DB)],     # Dead Key Accent: Ogonek

    C("Alt-Comma"):             UC(0x2264),                     # ≤ Less Than or Equal To symbol
    C("Alt-Dot"):               UC(0x2265),                     # ≥ Greater Than or Equal To symbol
    C("Alt-Slash"):             UC(0x00F7),                     # ÷ Obelus/Division symbol

    # Shift keys row with Shift+Option
    ######################################################
    C("Shift-Alt-Z"):           UC(0x0309),                     # ̉  Combining Hook Above (hoi)
    C("Shift-Alt-X"):           UC(0x0323),                     # ̣  Combining Dot Below (nang)
    C("Shift-Alt-C"):           UC(0x0327),                     #  ̧ Combining Cedilla
    C("Shift-Alt-V"):           UC(0x030C),                     #  ̌ Combining Caron/hacek
    C("Shift-Alt-B"):           UC(0x0306),                     #  ̆ Combining Breve
    C("Shift-Alt-N"):           UC(0x0303),                     #  ̃ Combining Tilde
    C("Shift-Alt-M"):           UC(0x0328),                     #  ̨ Combining Ogonek (nasal hook)
    C("Shift-Alt-Comma"):       UC(0x201E),                     # „ Double Low-9 Quotation Mark

    C("Shift-Alt-Dot"): [UC(0x0294),C("Shift-Left"),setDK(0x0294)],     # Dead Key Accent: Hook

    C("Shift-Alt-Slash"):       UC(0x00BF),                     # ¿ Inverted Question mark

# }, when = lambda ctx: ctx.wm_class.casefold() not in terminals and cnfg.optspec_layout == 'ABC')
}, when = lambda ctx: matchProps(not_lst=terminals_and_remotes_lod)(ctx) and cnfg.optspec_layout == 'ABC')



######################################################################
###                                                                ###
###                                                                ###
###      ██    ██ ███████     ███    ███  █████  ██ ███    ██      ###
###      ██    ██ ██          ████  ████ ██   ██ ██ ████   ██      ###
###      ██    ██ ███████     ██ ████ ██ ███████ ██ ██ ██  ██      ###
###      ██    ██      ██     ██  ██  ██ ██   ██ ██ ██  ██ ██      ###
###       ██████  ███████     ██      ██ ██   ██ ██ ██   ████      ###
###                                                                ###
###                                                                ###
######################################################################
# Main keymap for special characters on the standard US layout
keymap("OptSpecialChars - US", {

    # Number keys row with Option
    ######################################################
    C("Alt-Grave"): [UC(0x0060), C("Shift-Left"), setDK(0x0060)],       # Dead Key Accent: Grave

    C("Alt-1"):                 UC(0x00A1),                     # ¡ Inverted Exclamation Mark
    C("Alt-2"):                 UC(0x2122),                     # ™ Trade Mark Sign Emoji
    C("Alt-3"):                 UC(0x00A3),                     # £ British Pound currency symbol
    C("Alt-4"):                 UC(0x00A2),                     # ¢ Cent currency symbol
    C("Alt-5"):                 UC(0x221E),                     # ∞ Infinity mathematical symbol
    C("Alt-6"):                 UC(0x00A7),                     # § Section symbol
    C("Alt-7"):                 UC(0x00B6),                     # ¶ Paragraph mark (Pilcrow) symbol
    C("Alt-8"):                 UC(0x2022),                     # • Bullet Point symbol (solid)
    C("Alt-9"):                 UC(0x00AA),                     # ª Feminine Ordinal Indicator
    C("Alt-0"):                 UC(0x00BA),                     # º Masculine Ordinal Indicator
    C("Alt-Minus"):             UC(0x2013),                     # – En Dash punctuation mark
    C("Alt-Equal"):             UC(0x2260),                     # ≠ Not Equal To symbol

    # Number keys row with Shift+Option
    ######################################################
    C("Shift-Alt-Grave"):       UC(0x0060),                     # ` Grave Accent (non-combining)
    C("Shift-Alt-1"):           UC(0x2044),                     # ⁄ Fraction Slash
    C("Shift-Alt-2"):           UC(0x20AC),                     # € Euro currency symbol
    C("Shift-Alt-3"):           UC(0x2039),                     # ‹ Single Left-Pointing Angle Quotation mark
    C("Shift-Alt-4"):           UC(0x203A),                     # › Single Right-Pointing Angle Quotation mark
    C("Shift-Alt-5"):           UC(0xFB01),                     # ﬁ Latin Small Ligature Fi
    C("Shift-Alt-6"):           UC(0xFB02),                     # ﬂ Latin Small Ligature Fl
    C("Shift-Alt-7"):           UC(0x2021),                     # ‡ Double dagger (cross) symbol
    C("Shift-Alt-8"):           UC(0x00B0),                     # ° Degree Sign
    C("Shift-Alt-9"):           UC(0x00B7),                     # · Middle Dot (interpunct/middot)
    C("Shift-Alt-0"):           UC(0x201A),                     # ‚ Single low-9 quotation mark
    C("Shift-Alt-Minus"):       UC(0x2014),                     # — Em Dash punctuation mark
    C("Shift-Alt-Equal"):       UC(0x00B1),                     # ± Plus Minus mathematical symbol

    # Tab key row with Option
    ######################################################
    C("Alt-Q"):                 UC(0x0153),                     # œ Small oe (oethel) ligature
    C("Alt-W"):                 UC(0x2211),                     # ∑ N-Ary Summation (sigma) notation

    C("Alt-E"):         [UC(0x00B4), C("Shift-Left"), setDK(0x00B4)],   # Dead Key Accent: Acute

    C("Alt-R"):                 UC(0x00AE),                     # ® Registered Trade Mark Sign
    C("Alt-T"):                 UC(0x2020),                     # † Simple dagger (cross) symbol
    C("Alt-Y"):                 UC(0x00A5),                     # ¥ Japanese Yen currency symbol

    C("Alt-U"):         [UC(0x00A8), C("Shift-Left"), setDK(0x00A8)],   # Dead Key Accent: Umlaut/Diaeresis

    C("Alt-I"):         [UC(0x02C6), C("Shift-Left"), setDK(0x02C6)],   # Dead Key Accent: Circumflex

    C("Alt-O"):                 UC(0x00F8),                     # ø Latin Small Letter o with Stroke
    C("Alt-P"):                 UC(0x03C0),                     # π Greek Small Letter Pi
    C("Alt-Left_Brace"):        UC(0x201C),                     # “ Left Double Quotation Mark
    C("Alt-Right_Brace"):       UC(0x2018),                     # ‘ Left Single Quotation Mark
    C("Alt-Backslash"):         UC(0x00AB),                     # « Left-Pointing Double Angle Quotation Mark

    # Tab key row with Shift+Option
    ######################################################
    C("Shift-Alt-Q"):           UC(0x0152),                     # Œ Capital OE (Oethel) ligature
    C("Shift-Alt-W"):           UC(0x201E),                     # „ Double Low-9 Quotation mark
    C("Shift-Alt-E"):           UC(0x00B4),                     # ´ Acute Accent diacritic (non-combining)
    C("Shift-Alt-R"):           UC(0x2030),                     # ‰ Per mille symbol (zero over zero-zero)
    C("Shift-Alt-T"):           UC(0x02C7),                     # ˇ Caron/hacek diacritic (non-combining)
    C("Shift-Alt-Y"):           UC(0x00C1),                     # Á Latin Capital Letter A with Acute
    C("Shift-Alt-U"):           UC(0x00A8),                     # ¨ Diaeresis/Umlaut (non-combining)
    C("Shift-Alt-I"):           UC(0x02C6),                     # ˆ Circumflex Accent (non-combining)
    C("Shift-Alt-O"):           UC(0x00D8),                     # Ø Latin Capital Letter O with Stroke
    C("Shift-Alt-P"):           UC(0x220F),                     # ∏ N-Ary Product mathematical symbol
    C("Shift-Alt-Left_Brace"):  UC(0x201D),                     # ” Right Double Quotation Mark
    C("Shift-Alt-Right_Brace"): UC(0x2019),                     # ’ Right Single Quotation Mark
    C("Shift-Alt-Backslash"):   UC(0x00BB),                     # » Right-Pointing Double Angle Quotation Mark

    # CapsLock key row with Option
    ######################################################
    C("Alt-A"):                 UC(0x00E5),                     # å Small Letter a with Ring Above
    C("Alt-S"):                 UC(0x00DF),                     # ß German Eszett/beta (Sharfes/Sharp S)
    C("Alt-D"):                 UC(0x2202),                     # ∂ Partial Differential
    C("Alt-F"):                 UC(0x0192),                     # ƒ Function/florin currency symbol
    C("Alt-G"):                 UC(0x00A9),                     # © Copyright Sign
    C("Alt-H"):                 UC(0x02D9),                     # ˙ Dot Above diacritic (non-combining)
    C("Alt-J"):                 UC(0x2206),                     # ∆ Increment, laplace operator symbol
    C("Alt-K"):                 UC(0x02DA),                     # ˚ Ring Above diacritic (non-combining)
    C("Alt-L"):                 UC(0x00AC),                     # ¬ Not Sign angled dash symbol
    C("Alt-Semicolon"):         UC(0x2026),                     # … Horizontal ellipsis
    C("Alt-Apostrophe"):        UC(0x00E6),                     # æ Small ae ligature

    # CapsLock key row with Shift+Option
    ######################################################
    C("Shift-Alt-A"):           UC(0x00C5),                     # Å Capital Letter A with Ring Above
    C("Shift-Alt-S"):           UC(0x00CD),                     # Í Latin Capital Letter I with Acute
    C("Shift-Alt-D"):           UC(0x00CE),                     # Î Latin Capital Letter I with Circumflex
    C("Shift-Alt-F"):           UC(0x00CF),                     # Ï Latin Capital Letter I with Diaeresis
    C("Shift-Alt-G"):           UC(0x02DD),                     # ˝ Double Acute Accent (non-combining)
    C("Shift-Alt-H"):           UC(0x00D3),                     # Ó Latin Capital Letter O with Acute
    C("Shift-Alt-J"):           UC(0x00D4),                     # Ô Latin Capital Letter O with Circumflex
    #########################################################################################################
    # The Apple logo is at {U+F8FF} in a Unicode Private Use Area. Only at that location in Mac fonts. 
    # Symbol exists at {U+F000} in Baskerville Old Face font. 
    C("Shift-Alt-K"):   [apple_logo_alert(),UC(0xF000)],        #  Apple logo [req's Baskerville Old Face font]
    C("Shift-Alt-L"):           UC(0x00D2),                     # Ò Latin Capital Letter O with Grave
    C("Shift-Alt-Semicolon"):   UC(0x00DA),                     # Ú Latin Capital Letter U with Acute
    C("Shift-Alt-Apostrophe"):  UC(0x00C6),                     # Æ Capital AE ligature

    # Shift keys row with Option
    ######################################################
    C("Alt-Z"):                 UC(0x03A9),                     # Ω Greek Capital Letter Omega
    C("Alt-X"):                 UC(0x2248),                     # ≈ Almost Equal To symbol
    C("Alt-C"):                 UC(0x00E7),                     # ç Small Letter c with Cedilla
    C("Alt-V"):                 UC(0x221A),                     # √ Square Root radical sign
    C("Alt-B"):                 UC(0x222B),                     # ∫ Integral mathematical symbol

    C("Alt-N"): [UC(0x02DC), C("Shift-Left"), setDK(0x02DC)],   # Dead Key Accent: Tilde

    C("Alt-M"):                 UC(0x00B5),                     # µ Micro (mu) symbol
    C("Alt-Comma"):             UC(0x2264),                     # ≤ Less Than or Equal To symbol
    C("Alt-Dot"):               UC(0x2265),                     # ≥ Greater Than or Equal To symbol
    C("Alt-Slash"):             UC(0x00F7),                     # ÷ Obelus/Division symbol

    # Shift keys row with Shift+Option
    ######################################################
    C("Shift-Alt-Z"):           UC(0x00B8),                     # ¸ Spacing Cedilla diacritic (non-combining)
    C("Shift-Alt-X"):           UC(0x02DB),                     # ˛ Ogonek diacritic (non-combining)
    C("Shift-Alt-C"):           UC(0x00C7),                     # Ç Capital Letter C with Cedilla
    C("Shift-Alt-V"):           UC(0x25CA),                     # ◊ Lozenge (diamond) shape symbol
    C("Shift-Alt-B"):           UC(0x0131),                     # ı Latin Small Letter Dotless i
    C("Shift-Alt-N"):           UC(0x02DC),                     # ˜ Small Tilde character
    C("Shift-Alt-M"):           UC(0x00C2),                     # Â Latin Capital Letter A with Circumflex
    C("Shift-Alt-Comma"):       UC(0x00AF),                     # ¯ Macron/overline/overbar (non-combining)
    C("Shift-Alt-Dot"):         UC(0x02D8),                     # ˘ Breve diacritic (non-combining)
    C("Shift-Alt-Slash"):       UC(0x00BF),                     # ¿ Inverted Question mark

# }, when = lambda ctx: ctx.wm_class.casefold() not in terminals and cnfg.optspec_layout == 'US')
}, when = lambda ctx: matchProps(not_lst=terminals_and_remotes_lod)(ctx) and cnfg.optspec_layout == 'US')



####################################  USER APPS  #####################################
###                                                                                ###
###                                                                                ###
###      ██    ██ ███████ ███████ ██████       █████  ██████  ██████  ███████      ###
###      ██    ██ ██      ██      ██   ██     ██   ██ ██   ██ ██   ██ ██           ###
###      ██    ██ ███████ █████   ██████      ███████ ██████  ██████  ███████      ###
###      ██    ██      ██ ██      ██   ██     ██   ██ ██      ██           ██      ###
###       ██████  ███████ ███████ ██   ██     ██   ██ ██      ██      ███████      ###
###                                                                                ###
###                                                                                ###
######################################################################################
### Good place for adding new custom keymaps for user applications and custom function keys

# REMOVE THE CONTENTS OF THIS FOR GENERAL USE
keymap("User hardware keys", {

# }, when = lambda ctx: ctx.wm_class.casefold() not in remotes)
# }, when = matchProps(not_clas=remoteStr))
}, when = matchProps(not_lst=remotes_lod))



#################################  MISC APPS  #####################################
###                                                                             ###
###                                                                             ###
###      ███    ███ ██ ███████  ██████      █████  ██████  ██████  ███████      ###
###      ████  ████ ██ ██      ██          ██   ██ ██   ██ ██   ██ ██           ###
###      ██ ████ ██ ██ ███████ ██          ███████ ██████  ██████  ███████      ###
###      ██  ██  ██ ██      ██ ██          ██   ██ ██      ██           ██      ###
###      ██      ██ ██ ███████  ██████     ██   ██ ██      ██      ███████      ###
###                                                                             ###
###                                                                             ###
###################################################################################

keymap("Thunderbird email client", {
    C("Alt-RC-I"):              C("Shift-RC-I"),                # Dev tools
    # Enable Cmd+Option+Left/Right for tab navigation
    C("RC-Alt-Left"):           C("C-Page_Up"),                 # Go to prior tab (macOS Thunderbird tab nav shortcut)
    C("RC-Alt-Right"):          C("C-Page_Down"),               # Go to next tab (macOS Thunderbird tab nav shortcut)
}, when = matchProps(clas="^thunderbird.*$"))

keymap("Angry IP Scanner", {
    C("RC-comma"):              C("Shift-RC-P"),                # Open preferences
}, when = matchProps(clas="^Angry.*IP.*Scanner$"))

keymap("Transmission bittorrent client", {
    C("RC-i"):                  C("Alt-Enter"),                 # Open properties (Get Info) dialog
    C("RC-comma"):             [C("Alt-e"),C("p")],             # Open preferences (settings) dialog
}, when = matchProps(clas="^transmission-gtk$"))

JDownloader_lod = [
    {clas: "^.*jdownloader.*$"},
    {clas: "^java-lang-Thread$", name: "^JDownloader.*$"}       # Happens after auto-update of app
]
keymap("JDownloader", {
    C("RC-i"):                  C("Alt-Enter"),                 # Open properties
    C("RC-Backspace"):          C("Delete"),                    # Remove download from list
    C("RC-Comma"):              C("C-P"),                       # Open preferences (settings)
# }, when = matchProps(clas="^.*jdownloader.*$"))
}, when = matchProps(lst=JDownloader_lod))

keymap("Totem video player", {
    C("RC-dot"):                C("C-q"),                       # Stop (quit player, there is no "Stop" function)
}, when = matchProps(clas="^totem$"))

keymap("GNOME image viewer", {
    C("RC-i"):                  C("Alt-Enter"),                 # Image properties
}, when = matchProps(clas="^eog$"))




########################################  FINDER MODS  #############################################
###                                                                                              ###
###                                                                                              ###
###     ███████ ██ ███    ██ ██████  ███████ ██████      ███    ███  ██████  ██████  ███████     ###
###     ██      ██ ████   ██ ██   ██ ██      ██   ██     ████  ████ ██    ██ ██   ██ ██          ###
###     █████   ██ ██ ██  ██ ██   ██ █████   ██████      ██ ████ ██ ██    ██ ██   ██ ███████     ###
###     ██      ██ ██  ██ ██ ██   ██ ██      ██   ██     ██  ██  ██ ██    ██ ██   ██      ██     ###
###     ██      ██ ██   ████ ██████  ███████ ██   ██     ██      ██  ██████  ██████  ███████     ###
###                                                                                              ###
###                                                                                              ###
####################################################################################################

###  START OF FILE MANAGER GROUP OF KEYMAPS - FINDER MODS  ###

# Boolean variable to toggle Enter key state between F2 and Enter
# True = Enter key sends F2, False = Enter key sends Enter
_enter_is_F2 = True     # DON'T CHANGE THIS! Must be set to True here. 


def is_Enter_F2(combo_if_true, combo_if_false):
    """
    Send a different combo for Enter key depending on state of _enter_is_F2 variable,\n 
    or latch the variable to True or False to control the Enter key state on next use.
    
    This enables a simulation of the Finder "Enter to rename" capability.
    """
    def _is_Enter_F2():
        global _enter_is_F2
        combo_list = [combo_if_true]
        if combo_if_false in (True, False):                     # Latch variable to given bool value
            _enter_is_F2 = combo_if_false
        elif _enter_is_F2:                                      # If Enter is F2 now, set to be Enter next
            _enter_is_F2 = False
        else:                                                   # If Enter is Enter now, set to be F2 next
            combo_list = [combo_if_false]
            _enter_is_F2 = True
        return combo_list
    return _is_Enter_F2


# Keybindings overrides for Caja
# (overrides some bindings from general file manager code block below)
keymap("Overrides for Caja - Finder Mods", {
    # C("RC-Super-o"):            C("Shift-RC-Enter"),            # Open in new tab
    C("RC-Super-o"):            C("Shift-RC-W"),                # Open in new window
}, when = matchProps(clas="^caja$"))

# Keybindings overrides for DDE (Deepin) File Manager
# (overrides some bindings from general file manager code block below)
keymap("Overrides for DDE File Manager - Finder Mods", {
    C("RC-i"):                  C("RC-i"),                      # File properties dialog (Get Info)
    C("RC-comma"):              None,                           # Disable preferences shortcut (no shortcut available)
    C("RC-Up"):                 C("RC-Up"),                     # Go Up dir
    C("Shift-RC-Left_Brace"):   C("C-Shift-Tab"),               # Go to prior tab
    C("Shift-RC-Right_Brace"):  C("C-Tab"),                     # Go to next tab
    C("Shift-RC-Left"):         C("C-Shift-Tab"),               # Go to prior tab
    C("Shift-RC-Right"):        C("C-Tab"),                     # Go to next tab
}, when = matchProps(clas="^dde-file-manager$"))

# Keybindings overrides for Dolphin (KDE file manager)
# (overrides some bindings from general file manager code block below)
keymap("Overrides for Dolphin - Finder Mods", {
    C("RC-KEY_2"):              C("C-KEY_3"),                   # View as List (Detailed)
    C("RC-KEY_3"):              C("C-KEY_2"),                   # View as List (Compact)
    ##########################################################################################
    ### "Open in new window" (or new tab) requires manually setting custom shortcut of Ctrl+Shift+o
    ### in Dolphin's keyboard shortcuts. There is no default shortcut set for this function.
    ##########################################################################################
    C("RC-Super-o"):            C("Shift-RC-o"),                # Open in new window (or new tab, user's choice, see above)
    C("Shift-RC-N"):            is_Enter_F2(C("F10"), False),   # Create new folder (F10), toggle Enter to be Enter
    C("RC-comma"):              C("Shift-RC-comma"),            # Open preferences dialog
}, when = matchProps(clas="^dolphin$"))

# Keybindings overrides for elementary OS Files (Pantheon)
# (overrides some bindings from general file manager code block below)
keymap("Overrides for Pantheon - Finder Mods", {
    # C("RC-Super-o"):            C("Shift-Enter"),               # Open folder in new tab
    C("RC-comma"):              None,                           # Disable preferences shortcut since none available
}, when = matchProps(clas="^io.elementary.files$"))

# Keybindings overrides for Nautilus
# (overrides some bindings from general file manager code block below)
keymap("Overrides for Nautilus Create Archive dialog - Finder Mods", {
    C("Enter"):                 C("Enter"),                     # Use Enter as Enter in the Create Archive dialog
}, when = matchProps(clas="^.*nautilus$", name="Create Archive"))

keymap("Overrides for Nautilus - Finder Mods", {
    C("RC-N"):                  C("C-Alt-Space"),               # macOS Finder search window shortcut Cmd+Option+Space
    # For the above shortcut to work, a custom shortcut must be set up in the Settings app in GNOME 
    # to run command: "nautilus --new-window /home/USER" [ replace "USER" ]
    C("RC-KEY_1"):              C("C-KEY_2"),                   # View as Icons
    C("RC-KEY_2"):              C("C-KEY_1"),                   # View as List (Detailed)
    C("RC-Super-o"):            C("Shift-Enter"),               # Open in new window (disable line below)
    # C("RC-Super-o"):            C("RC-Enter"),                  # Open in new tab (disable line above)
    C("RC-comma"):              C("RC-comma"),                  # Overrides "Open preferences dialog" shortcut below
    C("RC-F"):                  C("RC-F"),                      # Don't toggle Enter key, pass Cmd+F
}, when = matchProps(clas="^org.gnome.nautilus$|^nautilus$"))

# Keybindings overrides for PCManFM and PCManFM-Qt
# (overrides some bindings from general file manager code block below)
keymap("Overrides for PCManFM-Qt - Finder Mods", {
    C("RC-Backspace"):          C("Delete"),                    # Move to Trash (delete, bypass dialog)
}, when = matchProps(clas="^pcmanfm-qt$"))

keymap("Overrides for PCManFM - Finder Mods", {
    C("RC-KEY_2"):              C("C-KEY_4"),                   # View as List (Detailed) [Not in PCManFM-Qt]
    C("RC-Backspace"):         [C("Delete"),C("Space")],        # Move to Trash (delete, bypass dialog)
    C("RC-F"):                  C("RC-F"),                      # Don't toggle Enter key state, pass Cmd+F
}, when = matchProps(clas="^pcmanfm$|^pcmanfm-qt$"))

# Keybindings overrides for SpaceFM
# (overrides some bindings from general file manager code block below)
keymap("Overrides for SpaceFM Find Files dialog - Finder Mods", {
    C("Enter"):                 C("Enter"),                     # Use Enter as Enter in the Find dialog
    C("Esc"):                   C("Alt-F4"),                    # Close Find Files dialog with Escape
    C("RC-W"):                  C("Alt-F4"),                    # Close Find Files dialog with Cmd+W
}, when = matchProps(clas="^SpaceFM$", name="Find FiLes"))

keymap("Overrides for SpaceFM - Finder Mods", {
    C("RC-Page_Up"):            C("C-Shift-Tab"),               # Go to prior tab
    C("RC-Page_Down"):          C("C-Tab"),                     # Go to next tab
    C("Shift-RC-Left_Brace"):   C("C-Shift-Tab"),               # Go to prior tab
    C("Shift-RC-Right_Brace"):  C("C-Tab"),                     # Go to next tab
    C("Shift-RC-Left"):         C("C-Shift-Tab"),               # Go to prior tab
    C("Shift-RC-Right"):        C("C-Tab"),                     # Go to next tab
    C("Shift-RC-N"):    is_Enter_F2(C("RC-F"), False),          # Switch Enter to Enter. New folder is Ctrl+F(???)
    # Need to catch WM_NAME of "Find Files" and override Enter key state back to being Enter. See above keymap.
    C("RC-F"):                  None,                           # No direct shortcut available and menu macros don't work in SpaceFM.
    C("RC-Backspace"):         [C("Delete"),C("Space")],        # Move to Trash (delete, bypass dialog)
    C("RC-comma"):             [C("Alt-V"),C("p")],             # Overrides "Open preferences dialog" shortcut below
    # This shortcut ^^^^^^^^^^^^^^^ is not fully working in SpaceFM. Opens "View" menu but not Preferences.
    # SpaceFM is doing some nasty binding that blocks all shortcuts, including Alt+Tab, while any menu is open.
}, when = matchProps(clas="^spacefm$"))

# Keybindings overrides for Thunar
# (overrides some bindings from general file manager code block below)
keymap("Overrides for Thunar - Finder Mods", {
    C("RC-Super-o"):            C("Shift-RC-P"),                # Open in new tab
    C("RC-comma"):             [C("Alt-E"),C("E")],             # Overrides "Open preferences dialog" shortcut below
    C("RC-F"):                  C("RC-F"),                      # Don't toggle Enter key, pass Cmd+F
}, when = matchProps(clas="^thunar$"))

# Keybindings overrides for GNOME XDG "Save As" and "Open File" dialogs
file_open_save_dialogs = [
    {clas:"^xdg-desktop-portal-gnome$|^firefox.*$", name:"^Open File$"},
    {clas:"^xdg-desktop-portal-gnome$|^firefox.*$", name:"^Save As$"},
]
keymap("XDG file dialogs", {
    C("RC-Left"):               C("Alt-Left"),                  # Go Back
    C("RC-Right"):              C("Alt-Right"),                 # Go Forward
    C("RC-Up"):                 C("Alt-Up"),                    # Go Up dir
    C("RC-Down"):               C("Enter"),                     # Go Down dir (open folder/file) [universal]
}, when = matchProps(lst=file_open_save_dialogs))

############################################################
##  Keybindings for Linux general file managers group:
##
##  Currently supported Linux file managers (file browsers):
##  
##  Caja File Browser (MATE file manager, fork of Nautilus)
##  DDE File Manager (Deepin Linux file manager)
##  Dolphin (KDE file manager)
##  Nautilus (GNOME file manager, may be named "Files")
##  Nemo (Cinnamon file manager, fork of Nautilus, may be named "Files")
##  Pantheon Files (elementary OS file manager, may be named "Files")
##  PCManFM (LXDE file manager)
##  PCManFM-Qt (LXQt file manager)
##  SpaceFM (Fork of PCManFM file manager)
##  Thunar File Manager (Xfce file manager)
##  
##  GNOME XDG file dialogs ("Open File" and "Save As" windows in apps like Firefox)
## 
##############################################

keymap("General File Managers - Finder Mods", {
    ###########################################################################################################
    ###  Show Properties (Get Info) | Open Settings/Preferences | Show/Hide hidden files                    ###
    ###########################################################################################################
    C("RC-i"):                  C("Alt-Enter"),                 # File properties dialog (Get Info)
    C("RC-comma"):             [C("Alt-E"),C("N")],             # Open preferences dialog
    C("Shift-RC-dot"):          C("RC-H"),                      # Show/hide hidden files ("dot" files)
    ###########################################################################################################
    ###  Navigation                                                                                         ###
    ###########################################################################################################
    C("RC-Left_Brace"):         C("Alt-Left"),                  # Go Back
    C("RC-Right_Brace"):        C("Alt-Right"),                 # Go Forward
    C("RC-Left"):               C("Alt-Left"),                  # Go Back
    C("RC-Right"):              C("Alt-Right"),                 # Go Forward
    C("RC-Up"):                 C("Alt-Up"),                    # Go Up dir
    # C("RC-Down"):               C("Alt-Down"),                  # Go Down dir (only works on folders) [not universal]
    # C("RC-Down"):               C("RC-O"),                      # Go Down dir (open folder/file) [not universal]
    C("RC-Down"):               C("Enter"),                     # Go Down dir (open folder/file) [universal]
    C("Shift-RC-Left_Brace"):   C("C-Page_Up"),                 # Go to prior tab
    C("Shift-RC-Right_Brace"):  C("C-Page_Down"),               # Go to next tab
    C("Shift-RC-Left"):         C("C-Page_Up"),                 # Go to prior tab
    C("Shift-RC-Right"):        C("C-Page_Down"),               # Go to next tab
    ###########################################################################################################
    ###  Open in New Window | Move to Trash                                                                 ###
    ###########################################################################################################
    C("RC-Super-o"):            C("Shift-RC-o"),                # Open in new window (or tab, depends) [not universal]
    C("RC-Backspace"):          C("Delete"),	                # Move to Trash (delete)
    C("RC-Delete"):             None,                           # Block Ctrl+Delete from performing any action (error in macOS)
    ###########################################################################################################
    ###  ENTER-KEY-TO-RENAME CUSTOM FUNCTION SHORTCUTS                                                      ###
    ###########################################################################################################
    C("Enter"):                 is_Enter_F2(C("F2"),C("Enter")),        # Send F2 to rename files, unless var is False
    C("Shift-RC-N"):            is_Enter_F2(C("Shift-RC-N"), False),    # New folder, set Enter to Enter
    C("RC-L"):                  is_Enter_F2(C("RC-L"), False),          # Set Enter to Enter for Location field
    C("RC-F"):                  is_Enter_F2(C("RC-F"), False),          # Set Enter to Enter for Find field
    C("Esc"):                   is_Enter_F2(C("Esc"), True),            # Send Escape, make sure Enter is back to F2
    C("Shift-RC-Enter"):        C("Enter"),                             # alternative "Enter" key for unusual cases
}, when = matchProps(clas=filemanagerStr))



###################################  BROWSERS  #####################################
###                                                                              ###
###                                                                              ###
###      ██████  ██████   ██████  ██     ██ ███████ ███████ ██████  ███████      ###
###      ██   ██ ██   ██ ██    ██ ██     ██ ██      ██      ██   ██ ██           ###
###      ██████  ██████  ██    ██ ██  █  ██ ███████ █████   ██████  ███████      ###
###      ██   ██ ██   ██ ██    ██ ██ ███ ██      ██ ██      ██   ██      ██      ###
###      ██████  ██   ██  ██████   ███ ███  ███████ ███████ ██   ██ ███████      ###
###                                                                              ###
###                                                                              ###
####################################################################################

# Open preferences in Firefox browsers
keymap("Firefox Browsers Overrides", {
    C("C-comma"):              [C("C-t"),sleep(0.05),ST("about:preferences"),C("Enter")],
    C("Shift-RC-N"):            C("Shift-RC-P"),                      # Open private window with Cmd+Shift+N like other browsers
    C("RC-Backspace"):         [C("Shift-Home"), C("Backspace")],     # Delete Entire Line Left of Cursor
    C("RC-Delete"):            [C("Shift-End"), C("Delete")],         # Delete Entire Line Right of Cursor
}, when = matchProps(clas="^Firefox.*$"))

keymap("Chrome Browsers Overrides", {
    C("C-comma"):              [C("Alt-e"), C("s"),C("Enter")], # Open preferences
    C("RC-q"):                  C("Alt-F4"),                    # Quit Chrome(s) browsers with Cmd+Q
    # C("RC-Left"):               C("Alt-Left"),                  # Page nav: Back to prior page in history (conflict with wordwise)
    # C("RC-Right"):              C("Alt-Right"),                 # Page nav: Forward to next page in history (conflict with wordwise)
    C("RC-Left_Brace"):         C("Alt-Left"),                  # Page nav: Back to prior page in history
    C("RC-Right_Brace"):        C("Alt-Right"),                 # Page nav: Forward to next page in history
}, when = matchProps(clas=chromeStr))

# Keybindings for General Web Browsers
keymap("General Web Browsers", {
    C("RC-Q"):                  C("RC-Q"),                      # Close all browsers Instances
    C("Alt-RC-I"):              C("Shift-RC-I"),                # Dev tools
    C("Alt-RC-J"):              C("Shift-RC-J"),                # Dev tools
    C("RC-Key_1"):              C("Alt-Key_1"),                 # Jump to Tab #1-#8
    C("RC-Key_2"):              C("Alt-Key_2"),
    C("RC-Key_3"):              C("Alt-Key_3"),
    C("RC-Key_4"):              C("Alt-Key_4"),
    C("RC-Key_5"):              C("Alt-Key_5"),
    C("RC-Key_6"):              C("Alt-Key_6"),
    C("RC-Key_7"):              C("Alt-Key_7"),
    C("RC-Key_8"):              C("Alt-Key_8"),
    C("RC-Key_9"):              C("Alt-Key_9"),                 # Jump to last tab
    # Enable Cmd+Shift+Braces for tab navigation (redundant with General GUI)
    # C("Shift-RC-Left_Brace"):   C("C-Page_Up"),                 # Go to prior tab
    # C("Shift-RC-Right_Brace"):  C("C-Page_Down"),               # Go to next tab
    # Enable Cmd+Option+Left/Right for tab navigation
    C("RC-Alt-Left"):           C("C-Page_Up"),                 # Go to prior tab
    C("RC-Alt-Right"):          C("C-Page_Down"),               # Go to next tab
    # Enable Ctrl+PgUp/PgDn for tab navigation
    C("Super-Page_Up"):         C("C-Page_Up"),                 # Go to prior tab
    C("Super-Page_Down"):       C("C-Page_Down"),               # Go to next tab
    # Use Cmd+Braces keys for tab navigation instead of page navigation 
    # C("C-Left_Brace"):        C("C-Page_Up"),
    # C("C-Right_Brace"):       C("C-Page_Down"),
}, when = matchProps(clas=browserStr))



############################################  CODE EDITORS  ##############################################
###                                                                                                    ###
###                                                                                                    ###
###       ██████  ██████  ██████  ███████     ███████ ██████  ██ ████████  ██████  ██████  ███████     ###
###      ██      ██    ██ ██   ██ ██          ██      ██   ██ ██    ██    ██    ██ ██   ██ ██          ###
###      ██      ██    ██ ██   ██ █████       █████   ██   ██ ██    ██    ██    ██ ██████  ███████     ###
###      ██      ██    ██ ██   ██ ██          ██      ██   ██ ██    ██    ██    ██ ██   ██      ██     ###
###       ██████  ██████  ██████  ███████     ███████ ██████  ██    ██     ██████  ██   ██ ███████     ###
###                                                                                                    ###
###                                                                                                    ###
##########################################################################################################


# Keybindings for IntelliJ
keymap("Jetbrains", {
    # General
    C("C-Key_0"):               C("Alt-Key_0"),                 # Open corresponding tool window
    C("C-Key_1"):               C("Alt-Key_1"),                 # Open corresponding tool window
    C("C-Key_2"):               C("Alt-Key_2"),                 # Open corresponding tool window
    C("C-Key_3"):               C("Alt-Key_3"),                 # Open corresponding tool window
    C("C-Key_4"):               C("Alt-Key_4"),                 # Open corresponding tool window
    C("C-Key_5"):               C("Alt-Key_5"),                 # Open corresponding tool window
    C("C-Key_6"):               C("Alt-Key_6"),                 # Open corresponding tool window
    C("C-Key_7"):               C("Alt-Key_7"),                 # Open corresponding tool window
    C("C-Key_8"):               C("Alt-Key_8"),                 # Open corresponding tool window
    C("C-Key_9"):               C("Alt-Key_9"),                 # Open corresponding tool window
    C("Super-Grave"):           C("C-Grave"),                   # Quick switch current scheme
    C("C-Comma"):               C("C-Alt-s"),                   # Open Settings dialog
    C("C-Semicolon"):           C("C-Alt-Shift-s"),             # Open Project Structure dialog
    # Debugging
    C("C-Alt-r"):               C("F9"),                        # Resume program
    # Search/Replace
    C("C-g"):                   C("F3"),                        # Find next
    C("C-Shift-F3"):            C("Shift-F3"),                  # Find previous
    C("Super-g"):               C("Alt-j"),                     # Select next occurrence
    C("C-Super-g"):             C("C-Alt-Shift-j"),             # Select all occurrences
    C("Super-Shift-g"):         C("Alt-Shift-j"),               # Unselect occurrence
    # Editing
    # C("Super-Space"):           C("LC-Space"),                  # Basic code completion (conflicts with input switching)
    # C("Super-Shift-Space"):     C("Shift-LC-Space"),            # Smart code completion (conflicts with input switching)
    C("Super-j"):               C("C-q"),                       # Quick documentation lookup
    C("C-n"):                   C("Alt-Insert"),                # Generate code...
    C("Super-o"):               C("C-o"),                       # Override methods
    C("Super-i"):               C("C-i"),                       # Implement methods
    C("Alt-Up"):                C("C-w"),                       # Extend selection
    C("Alt-Down"):              C("C-Shift-w"),                 # Shrink selection
    C("Super-Shift-q"):         C("Alt-q"),                     # Context info
    C("Super-Alt-o"):           C("C-Alt-o"),                   # Optimize imports
    C("Super-Alt-i"):           C("C-Alt-i"),                   # Auto-indent line(s)
    C("C-Backspace"):           C("C-y"),                       # Delete line at caret
    C("Super-Shift-j"):         C("C-Shift-j"),                 # Smart line join
    C("Alt-Delete"):            C("C-Delete"),                  # Delete to word end
    C("Alt-Backspace"):         C("C-Backspace"),               # Delete to word start
    C("C-Shift-Equal"):         C("C-KPPLUS"),                  # Expand code block
    C("C-Minus"):               C("C-KPMINUS"),                 # Collapse code block
    C("C-Shift-Equal"):         C("C-Shift-KPPLUS"),            # Expand all
    C("C-Shift-Minus"):         C("C-Shift-KPMINUS"),           # Collapse all
    C("C-w"):                   C("C-F4"),                      # Close active editor tab
    # Refactoring
    C("C-Delete"):              C("Alt-Delete"),                # Safe Delete
    C("C-T"):                   C("C-Alt-Shift-t"),             # Refactor this
    # Navigation
    C("C-o"):                   C("C-n"),                       # Go to class
    C("C-Shift-o"):             C("C-Shift-n"),                 # Go to file
    C("C-Alt-o"):               C("C-Alt-Shift-n"),             # Go to symbol
    C("Super-Right"):           C("Alt-Right"),                 # Go to next editor tab
    C("Super-Left"):            C("Alt-Left"),                  # Go to previous editor tab
    C("C-l"):                   C("C-g"),                       # Go to line
    C("Alt-Space"):             C("C-Shift-i"),                 # Open quick definition lookup
    C("C-Y"):                   C("C-Shift-i"),                 # Open quick definition lookup
    C("Super-Shift-b"):         C("C-Shift-b"),                 # Go to type declaration
    C("Super-Up"):              C("Alt-Up"),                    # Go to previous
    C("Super-Down"):            C("Alt-Down"),                  # Go to next method
    C("Super-h"):               C("C-h"),                       # Type hierarchy
    C("Super-Alt-h"):           C("C-Alt-h"),                   # Call hierarchy
    C("C-Down"):                C("C-Enter"),                   # Edit source/View source
    C("Alt-Home"):              C("Alt-Home"),                  # Show navigation bar
    C("F2"):                    C("F11"),                       # Toggle bookmark
    C("Super-F3"):              C("C-F11"),                     # Toggle bookmark with mnemonic
    C("Super-Key_0"):           C("C-Key_0"),                   # Go to numbered bookmark
    C("Super-Key_1"):           C("C-Key_1"),                   # Go to numbered bookmark
    C("Super-Key_2"):           C("C-Key_2"),                   # Go to numbered bookmark
    C("Super-Key_3"):           C("C-Key_3"),                   # Go to numbered bookmark
    C("Super-Key_4"):           C("C-Key_4"),                   # Go to numbered bookmark
    C("Super-Key_5"):           C("C-Key_5"),                   # Go to numbered bookmark
    C("Super-Key_6"):           C("C-Key_6"),                   # Go to numbered bookmark
    C("Super-Key_7"):           C("C-Key_7"),                   # Go to numbered bookmark
    C("Super-Key_8"):           C("C-Key_8"),                   # Go to numbered bookmark
    C("Super-Key_9"):           C("C-Key_9"),                   # Go to numbered bookmark
    C("C-F3"):                  C("Shift-F11"),                 # Show bookmarks
    # Compile and Run
    C("Super-Alt-r"):           C("Alt-Shift-F10"),             # Select configuration and run
    C("Super-Alt-d"):           C("Alt-Shift-F9"),              # Select configuration and debug
    C("Super-r"):               C("Shift-F10"),                 # Run
    C("Super-d"):               C("Shift-F9"),                  # Debug
    C("Super-Shift-r"):         C("C-Shift-F10"),               # Run context configuration from editor
    C("Super-Shift-d"):         C("C-Shift-F9"),                # Debug context configuration from editor
    # VCS/Local History
    C("Super-v"):               C("Alt-Grave"),                 # VCS quick popup
    C("Super-c"):               C("LC-c"),                      # Sigints - interrupt
}, when = matchProps(clas="^jetbrains-(?!.*toolbox).*$"))

keymap("Wordwise - not vscode", {
    # Wordwise remaining - for Everything but VS Code
    C("Alt-Left"):              C("C-Left"),                    # Left of Word
    C("Alt-Shift-Left"):        C("C-Shift-Left"),              # Select Left of Word
    C("Alt-Right"):             C("C-Right"),                   # Right of Word
    C("Alt-Shift-Right"):       C("C-Shift-Right"),             # Select Right of Word
    C("Alt-Shift-g"):           C("C-Shift-g"),                 # View source control
    # ** VS Code fix **
    #   Electron issue precludes normal keybinding fix.
    #   Alt menu auto-focus/toggle gets in the way.
    #
    #   refer to ./xkeysnail-config/vscode_keybindings.json
    # **
    #
    # ** Firefox fix **
    #   User will need to set "ui.key.menuAccessKeyFocuses"
    #   under about:config to false.
    #
    #   https://superuser.com/questions/770301/pentadactyl-how-to-disable-menu-bar-toggle-by-alt
    # **
    #
# }, when = lambda ctx: ctx.wm_class.casefold() not in mscodes)
}, when = matchProps(not_clas=vscodeStr_ext))


# Keybindings for VS Code and variants
keymap("VSCodes overrides for Chromebook/IBM - Sublime", {
    C("C-Alt-g"):               C("C-f2"),                      # Chromebook/IBM - Sublime - find_all_under
}, when = lambda ctx: matchProps(clas=vscodeStr)(ctx) and ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) and cnfg.ST3_in_VSCode)
keymap("VSCodes overrides for not Chromebook/IBM - Sublime", {
    C("Super-C-g"):             C("C-f2"),                      # Default - Sublime - find_all_under
}, when = lambda ctx: matchProps(clas=vscodeStr)(ctx) and not ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) and cnfg.ST3_in_VSCode)
keymap("VSCodes overrides for Chromebook/IBM", {
    C("Alt-c"):                 C("LC-c"),                      #  Chromebook/IBM - Terminal - Sigint
    C("Alt-x"):                 C("LC-x"),                      #  Chromebook/IBM - Terminal - Exit nano
}, when = lambda ctx: matchProps(clas=vscodeStr)(ctx) and ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) )
keymap("VSCodes overrides for not Chromebook/IBM", {
    C("Super-c"):               C("LC-c"),                      # Default - Terminal - Sigint
    C("Super-x"):               C("LC-x"),                      # Default - Terminal - Exit nano
}, when = lambda ctx: matchProps(clas=vscodeStr)(ctx) and not ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) )
keymap("VSCodes", {
    # C("Super-Space"):           C("LC-Space"),                  # Basic code completion (conflicts with input switching)

    # Find dialog options
    C("Alt-RC-C"):              C("Alt-C"),                     # Find: toggle "Match Case"
    C("Alt-RC-W"):              C("Alt-W"),                     # Find: toggle "Match Whole Word"
    C("Alt-RC-R"):              C("Alt-R"),                     # Find: toggle "Use Regular Expression"
    C("Alt-RC-L"):              C("Alt-L"),                     # Find: toggle "Find in Selection"
    C("Alt-RC-P"):              C("Alt-P"),                     # Replace: toggle "Preserve Case"

    C("Alt-RC-Z"):              C("Alt-Z"),                     # View: toggle "Word Wrap"

    # Wordwise remaining - for VS Code
    # Alt-F19 hack fixes Alt menu activation
    C("Alt-Left"):             [C("Alt-F19"),C("C-Left")],          # Left of Word
    C("Alt-Right"):            [C("Alt-F19"),C("C-Right")],         # Right of Word
    C("Alt-Shift-Left"):       [C("Alt-F19"),C("C-Shift-Left")],    # Select Left of Word
    C("Alt-Shift-Right"):      [C("Alt-F19"),C("C-Shift-Right")],   # Select Right of Word

    C("RC-Backspace"):          C("C-Backspace"),               # Delete Entire Line Left of Cursor

    # C("C-PAGE_DOWN"):           ignore_combo,                   # cancel next_view
    # C("C-PAGE_UP"):             ignore_combo,                   # cancel prev_view
    C("C-Alt-Left"):            C("C-PAGE_UP"),                 # next_view
    C("C-Alt-Right"):           C("C-PAGE_DOWN"),               # prev_view
    C("Shift-RC-Left_Brace"):   C("C-PAGE_UP"),                 # next_view
    C("Shift-RC-Right_Brace"):  C("C-PAGE_DOWN"),               # prev_view

    # VS Code Shortcuts
    C("C-g"):                   ignore_combo,                   # cancel Go to Line...
    C("Super-g"):               C("C-g"),                       # Go to Line...
    C("F3"):                    ignore_combo,                   # cancel Find next
    C("C-h"):                   ignore_combo,                   # cancel replace
    C("C-Alt-f"):               C("C-h"),                       # replace
    C("C-Shift-h"):             ignore_combo,                   # cancel replace_next
    C("C-Alt-e"):               C("C-Shift-h"),                 # replace_next
    C("f3"):                    ignore_combo,                   # cancel find_next
    C("C-g"):                   C("f3"),                        # find_next
    C("Shift-f3"):              ignore_combo,                   # cancel find_prev
    C("C-Shift-g"):             C("Shift-f3"),                  # find_prev
    # C("Super-c"):               C("LC-c"),                      # Default - Terminal - Sigint
    # C("Super-x"):               C("LC-x"),                      # Default - Terminal - Exit nano
    # C("Alt-c"):                 C("LC-c"),                      #  Chromebook/IBM - Terminal - Sigint
    # C("Alt-x"):                 C("LC-x"),                      #  Chromebook/IBM - Terminal - Exit nano
    # C("Super-C-g"):             C("C-f2"),                      # Default - Sublime - find_all_under
    # C("C-Alt-g"):               C("C-f2"),                      # Chromebook/IBM - Sublime - find_all_under
    # C("Super-Shift-up"):        C("Alt-Shift-up"),              # multi-cursor up - Sublime
    # C("Super-Shift-down"):      C("Alt-Shift-down"),            # multi-cursor down - Sublime
    # C(""):                      ignore_combo,                   # cancel
    # C(""):                      C(""),                          #
}, when = matchProps(clas=vscodeStr))

# Keybindings for Sublime Text
keymap("Sublime Text overrides for Chromebook/IBM", {
    C("Alt-c"):                 C("LC-c"),                      #  Chromebook/IBM - Terminal - Sigint
    C("Alt-x"):                 C("LC-x"),                      #  Chromebook/IBM - Terminal - Exit nano
    C("Alt-Refresh"):           ignore_combo,                   # Chromebook/IBM - cancel find_all_under
    C("Alt-C-g"):               C("Alt-Refresh"),               # Chromebook/IBM - find_all_under
}, when = lambda ctx: matchProps(clas=sublimeStr)(ctx) and ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) )
keymap("Sublime Text overrides for not Chromebook/IBM", {
    # C("Super-c"):               C("LC-c"),                      # Default - Terminal - Sigint
    # C("Super-x"):               C("LC-x"),                      # Default - Terminal - Exit nano
    C("Alt-f3"):                ignore_combo,                   # Default - cancel find_all_under
    C("Super-C-g"):             C("Alt-f3"),                    # Default - find_all_under
}, when = lambda ctx: matchProps(clas=sublimeStr)(ctx) and not ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) )
keymap("Sublime Text", {
    # C("Super-c"):               C("LC-c"),                      # Default - Terminal - Sigint
    # C("Super-x"):               C("LC-x"),                      # Default - Terminal - Exit nano
    # C("Alt-c"):                 C("LC-c"),                      #  Chromebook/IBM - Terminal - Sigint
    # C("Alt-x"):                 C("LC-x"),                      #  Chromebook/IBM - Terminal - Exit nano
    # C("Super-Space"):           C("C-Space"),                   # Basic code completion (conflicts with input switching)
    C("C-Super-up"):            C("Alt-o"),                     # Switch file
    C("Super-RC-f"):            C("f11"),                       # toggle_full_screen
    C("C-Alt-v"):              [C("C-k"), C("C-v")],            # paste_from_history
    C("C-up"):                  ignore_combo,                   # cancel scroll_lines up
    C("C-Alt-up"):              C("C-up"),                      # scroll_lines up
    C("C-down"):                ignore_combo,                   # cancel scroll_lines down
    C("C-Alt-down"):            C("C-down"),                    # scroll_lines down
    C("Super-Shift-up"):        C("Alt-Shift-up"),              # multi-cursor up
    C("Super-Shift-down"):      C("Alt-Shift-down"),            # multi-cursor down
    C("C-PAGE_DOWN"):           ignore_combo,                   # cancel next_view
    C("C-PAGE_UP"):             ignore_combo,                   # cancel prev_view
    C("C-Shift-left_brace"):    C("C-PAGE_DOWN"),               # next_view
    C("C-Shift-right_brace"):   C("C-PAGE_UP"),                 # prev_view
    C("C-Alt-right"):           C("C-PAGE_DOWN"),               # next_view
    C("C-Alt-left"):            C("C-PAGE_UP"),                 # prev_view
    C("insert"):                ignore_combo,                   # cancel toggle_overwrite
    C("C-Alt-o"):               C("insert"),                    # toggle_overwrite
    C("Alt-c"):                 ignore_combo,                   # cancel toggle_case_sensitive
    C("C-Alt-c"):               C("Alt-c"),                     # toggle_case_sensitive
    C("C-h"):                   ignore_combo,                   # cancel replace
    C("C-Alt-f"):               C("C-h"),                       # replace
    C("C-Shift-h"):             ignore_combo,                   # cancel replace_next
    C("C-Alt-e"):               C("C-Shift-h"),                 # replace_next
    C("f3"):                    ignore_combo,                   # cancel find_next
    C("C-g"):                   C("f3"),                        # find_next
    C("Shift-f3"):              ignore_combo,                   # cancel find_prev
    C("C-Shift-g"):             C("Shift-f3"),                  # find_prev
    C("C-f3"):                  ignore_combo,                   # cancel find_under
    C("Super-Alt-g"):           C("C-f3"),                      # find_under
    C("C-Shift-f3"):            ignore_combo,                   # cancel find_under_prev
    C("Super-Alt-Shift-g"):     C("C-Shift-f3"),                # find_under_prev
    C("Alt-f3"):                ignore_combo,                   # Default - cancel find_all_under
    C("Super-C-g"):             C("Alt-f3"),                    # Default - find_all_under
    # C("Alt-Refresh"):           ignore_combo,                   # Chromebook/IBM - cancel find_all_under
    # C("Alt-C-g"):               C("Alt-Refresh"),               # Chromebook/IBM - find_all_under
    C("C-Shift-up"):            ignore_combo,                   # cancel swap_line_up
    C("Super-Alt-up"):          C("C-Shift-up"),                # swap_line_up
    C("C-Shift-down"):          ignore_combo,                   # cancel swap_line_down
    C("Super-Alt-down"):        C("C-Shift-down"),              # swap_line_down
    C("C-Pause"):               ignore_combo,                   # cancel cancel_build
    C("Super-c"):               C("C-Pause"),                   # cancel_build
    C("f9"):                    ignore_combo,                   # cancel sort_lines case_s false
    C("f5"):                    C("f9"),                        # sort_lines case_s false
    C("Super-f9"):              ignore_combo,                   # cancel sort_lines case_s true
    C("Super-f5"):              C("Super-f9"),                  # sort_lines case_s true
    C("Alt-Shift-Key_1"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Key_1"):           C("Alt-Shift-Key_1"),           # set_layout
    C("Alt-Shift-Key_2"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Key_2"):           C("Alt-Shift-Key_2"),           # set_layout
    C("Alt-Shift-Key_3"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Key_3"):           C("Alt-Shift-Key_3"),           # set_layout
    C("Alt-Shift-Key_4"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Key_4"):           C("Alt-Shift-Key_4"),           # set_layout
    C("Alt-Shift-Key_8"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Shift-Key_2"):     C("Alt-Shift-Key_8"),           # set_layout
    C("Alt-Shift-Key_9"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Shift-Key_3"):     C("Alt-Shift-Key_9"),           # set_layout
    C("Alt-Shift-Key_5"):       ignore_combo,                   # cancel set_layout
    C("C-Alt-Shift-Key_5"):     C("Alt-Shift-Key_5"),           # set_layout
    # C(""):                    ignore_combo,                   # cancel
    # C(""):                    C(""),                          #
}, when = matchProps(clas=sublimeStr))



###########################  DIALOG FIXES  ###########################
###                                                                ###
###                                                                ###
###      ██████  ██  █████  ██       ██████   ██████  ███████      ###
###      ██   ██ ██ ██   ██ ██      ██    ██ ██       ██           ###
###      ██   ██ ██ ███████ ██      ██    ██ ██   ███ ███████      ###
###      ██   ██ ██ ██   ██ ██      ██    ██ ██    ██      ██      ###
###      ██████  ██ ██   ██ ███████  ██████   ██████  ███████      ###
###                                                                ###
###                                                                ###
######################################################################
### Fixes for the problem of modal dialogs and other "child" 
### windows failing to close with Cmd+W.
### Many dialogs respond to the Escape key, others may 
### require the "Close window" shortcut (normally Alt+F4 but not always) to close.
### 
### Cmd+W can't just be always mapped to the "Close window" shortcut for all apps 
### because some apps will "quit" rather than just closing a tab.
### 
### To add window conditions to the list, search for the list names in 
### the "LISTS" section near the top of this config file. 
### dialogs_Esc_lod = send these windows the Escape key for Cmd+W
### dialogs_CloseWin_lod = send these windows the "Close window" shortcut for Cmd+W

keymap("Cmd+W dialog fix - send Escape", {
    C("RC-W"):                  C("Esc"),
}, when = matchProps(lst=dialogs_Esc_lod))


keymap("Cmd+W dialog fix - Super+Q Manjaro GNOME", {
    C("RC-W"):                  C("Super-Q"),
}, when = lambda ctx:
    matchProps(lst=dialogs_CloseWin_lod)(ctx) and
    ( DISTRO_NAME == 'manjaro' and DESKTOP_ENV == 'gnome' ) )
keymap("Cmd+W dialog fix - Alt+F4", {
    C("RC-W"):                  C("Alt-F4"),
}, when = lambda ctx:
    matchProps(lst=dialogs_CloseWin_lod)(ctx) )



###########################  TAB NAV FIXES  #############################
###                                                                   ###
###                                                                   ###
###      ████████  █████  ██████      ███    ██  █████  ██    ██      ###
###         ██    ██   ██ ██   ██     ████   ██ ██   ██ ██    ██      ###
###         ██    ███████ ██████      ██ ██  ██ ███████ ██    ██      ###
###         ██    ██   ██ ██   ██     ██  ██ ██ ██   ██  ██  ██       ###
###         ██    ██   ██ ██████      ██   ████ ██   ██   ████        ###
###                                                                   ###
###                                                                   ###
#########################################################################
### Various fixes for supporting tab navigation shortcuts like Shift+Cmd+Braces

tab_UI_fix_CtrlShiftTab = [
    {clas:"^deepin-terminal$"},
    {clas:"^.*jDownloader.*$"},
    {clas:"^Kgx$"},
    {clas:"^kitty$"},
    {clas:"^org.gnome.Console$|^Console$"},
]

tab_UI_fix_CtrlAltPgUp = [
    {clas:"^gedit$"},
]

# Tab navigation overrides for tabbed UI apps that use Ctrl+Shift+Tab/Ctrl+Tab instead of Ctrl+PgUp/PgDn
keymap("Tab Nav fix for apps that use Ctrl+Shift+Tab/Ctrl+Tab", {
    C("Shift-RC-Left_Brace"):   C("C-Shift-Tab"),               # Tab nav: Go to prior tab (left)
    C("Shift-RC-Right_Brace"):  C("C-Tab"),                     # Tab nav: Go to next tab (right)
    C("Shift-RC-Left"):         C("C-Shift-Tab"),               # Tab nav: Go to prior tab (left)
    C("Shift-RC-Right"):        C("C-Tab"),                     # Tab nav: Go to next tab (right)
}, when = matchProps(lst=tab_UI_fix_CtrlShiftTab))

# Tab navigation overrides for tabbed UI apps that use Ctrl+Alt+PgUp/PgDn instead of Ctrl+PgUp/PgDn
keymap("Tab Nav fix for apps that use Ctrl+Alt+PgUp/PgDn", {
    C("Shift-RC-Left_Brace"):   C("C-Alt-Page_Up"),             # Go to prior tab (Left)
    C("Shift-RC-Right_Brace"):  C("C-Alt-Page_Down"),           # Go to next tab (Right)
}, when = matchProps(lst=tab_UI_fix_CtrlAltPgUp))

keymap("Konsole tab switching", {
    # Ctrl Tab - In App Tab Switching
    C("LC-Tab") :               C("Shift-Right"),
    C("Shift-LC-Tab") :         C("Shift-Left"),
    C("LC-Grave") :             C("Shift-Left"),
}, when = matchProps(clas="^konsole$"))

keymap("Elementary Terminal tab switching", {
    # Ctrl Tab - In App Tab Switching
    C("LC-Tab") :               C("Shift-LC-Right"),
    C("Shift-LC-Tab") :         C("Shift-LC-Left"),
    C("LC-Grave") :             C("Shift-LC-Left"),
}, when = matchProps(clas="^Io.elementary.terminal$|^kitty$"))



######################################  TERMINALS  #######################################
###                                                                                    ###
###                                                                                    ###
###      ████████ ███████ ██████  ███    ███ ██ ███    ██  █████  ██      ███████      ###
###         ██    ██      ██   ██ ████  ████ ██ ████   ██ ██   ██ ██      ██           ###
###         ██    █████   ██████  ██ ████ ██ ██ ██ ██  ██ ███████ ██      ███████      ###
###         ██    ██      ██   ██ ██  ██  ██ ██ ██  ██ ██ ██   ██ ██           ██      ###
###         ██    ███████ ██   ██ ██      ██ ██ ██   ████ ██   ██ ███████ ███████      ###
###                                                                                    ###
###                                                                                    ###
##########################################################################################

keymap("Alacritty terminal", {
    C("RC-K"):                  C("C-L"),                       # clear log
}, when = matchProps(clas="^alacritty$"))

keymap("Deepin Terminal overrides", {
    C("RC-w"):                  C("Alt-w"),                     # Close only current tab, instead of all other tabs
    C("RC-j"):                  None,                           # Block Cmd+J from remapping to vertical split (Ctrl+Shift+J) 
    C("RC-minus"):              C("C-minus"),                   # Decrease font size/zoom out 
    C("RC-equal"):              C("C-equal"),                   # Increase font size/zoom in
}, when = matchProps(clas="^deepin-terminal$"))

keymap("Kitty terminal - not tab nav", {
    C("RC-L"):                  C("C-L"),                       # Clear log
    C("RC-K"):                  C("C-L"),                       # Clear log (macOS)
}, when = matchProps(clas="^kitty$"))


# Overrides to General Terminals shortcuts for specific distros (or are they really just desktop environments?)
keymap("GenTerms overrides: elementary OS", {
    C("LC-Right"):              [bind,C("Super-Right")],        # SL - Change workspace (eos)
    C("LC-Left"):               [bind,C("Super-Left")],         # SL - Change workspace (eos)
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and DISTRO_NAME == 'eos')
keymap("GenTerms overrides: Pop!_OS", {
    C("LC-Right"):              [bind,C("Super-C-Up")],         # SL - Change workspace (popos)
    C("LC-Left"):               [bind,C("Super-C-Down")],       # SL - Change workspace (popos)
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and DISTRO_NAME == 'popos')
keymap("GenTerms overrides: Ubuntu/Fedora", {
    C("LC-Right"):              [bind,C("Super-Page_Up")],      # SL - Change workspace (ubuntu/fedora)
    C("LC-Left"):               [bind,C("Super-Page_Down")],    # SL - Change workspace (ubuntu/fedora)
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and ( DISTRO_NAME == 'ubuntu' or DISTRO_NAME == 'fedora' ) )


# Overrides to General Terminals shortcuts for specific desktop environments
keymap("GenTerms overrides: Budgie", {
    C("LC-Right"):              [bind,C("C-Alt-Right")],        # Default SL - Change workspace (budgie)
    C("LC-Left"):               [bind,C("C-Alt-Left")],         # Default SL - Change workspace (budgie)
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and DESKTOP_ENV == 'budgie' )
keymap("GenTerms overrides: GNOME", {
    ### Keyboard input source (language/layout) switching in GNOME
    # C("LC-Space"):              update_kb_layout,             # keyboard input source (language) switching (gnome)
    # C("Shift-LC-Space"):        update_kb_layout,             # keyboard input source (language) switching (reverse) (gnome)
    C("LC-Space"):             [bind,C("Super-Space")],         # keyboard input source (language) switching (gnome)
    C("Shift-LC-Space"):       [bind,C("Super-Shift-Space")],   # keyboard input source (language) switching (reverse) (gnome)
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and DESKTOP_ENV == 'gnome' )
keymap("GenTerms overrides: Xfce4", {
    C("RC-Grave"):             [bind,C("Super-Tab")],           # xfce4 Switch within app group
    C("Shift-RC-Grave"):       [bind,C("Super-Shift-Tab")],     # xfce4 Switch within app group
    C("LC-Right"):             [bind,C("C-Alt-Home")],          # SL - Change workspace xfce4
    C("LC-Left"):              [bind,C("C-Alt-End")],           # SL - Change workspace xfce4
}, when = lambda ctx: matchProps(clas=termStr)(ctx) and DESKTOP_ENV == 'xfce' )


# Active in all apps in the terminals list
keymap("General Terminals", {
    ### wordwise overrides of general GUI block
    C("Alt-Backspace"):         C("Alt-Shift-Backspace"),       # Wordwise delete word left of cursor in terminals
    C("Alt-Delete"):           [C("Esc"),C("d")],               # Wordwise delete word right of cursor in terminals
    C("RC-Backspace"):          C("C-u"),                       # Wordwise delete line left of cursor in terminals
    C("RC-Delete"):             C("C-k"),                       # Wordwise delete line right of cursor in terminals
    ### Tab navigation
    C("Shift-RC-Left"):         C("C-Page_Up"),                 # Tab nav: Go to prior tab (Left)
    C("Shift-RC-Right"):        C("C-Page_Down"),               # Tab nav: Go to next tab (Right)
    ### Keyboard input source (language/layout) switching in GNOME
    C("LC-Space"):              [bind,C("Super-Space")],        # keyboard input source (language) switching (gnome)
    C("Shift-LC-Space"):        [bind,C("Super-Shift-Space")],  # keyboard input source (language) switching (reverse) (gnome)
    C("LC-RC-f"):               C("Alt-F10"),                   # Toggle window maximized state
    # Ctrl Tab - In App Tab Switching
    C("LC-Tab") :               C("LC-PAGE_DOWN"),
    C("Shift-LC-Tab") :         C("LC-PAGE_UP"),
    C("LC-Grave") :             C("LC-PAGE_UP"),
    # C("Alt-Tab"):               ignore_combo,                   # Default - Cmd Tab - App Switching Default
    # C("RC-Tab"):                C("Alt-Tab"),                   # Default - Cmd Tab - App Switching Default
    # C("Shift-RC-Tab"):          C("Alt-Shift-Tab"),             # Default - Cmd Tab - App Switching Default
    # Converts Cmd to use Ctrl-Shift
    C("RC-MINUS"):              C("C-MINUS"),
    C("RC-EQUAL"):              C("C-Shift-EQUAL"),
    # C("RC-BACKSPACE"):          C("C-Shift-BACKSPACE"),           # Conflicts with wordwise shortcut above
    C("RC-W"):                  C("C-Shift-W"),
    C("RC-E"):                  C("C-Shift-E"),
    C("RC-R"):                  C("C-Shift-R"),
    C("RC-T"):                  C("C-Shift-t"),
    C("RC-Y"):                  C("C-Shift-Y"),
    C("RC-U"):                  C("C-Shift-U"),
    C("RC-I"):                  C("C-Shift-I"),
    C("RC-O"):                  C("C-Shift-O"),
    C("RC-P"):                  C("C-Shift-P"),
    C("RC-LEFT_BRACE"):         C("C-Shift-LEFT_BRACE"),
    C("RC-RIGHT_BRACE"):        C("C-Shift-RIGHT_BRACE"),
    C("RC-A"):                  C("C-Shift-A"),
    C("RC-S"):                  C("C-Shift-S"),
    C("RC-D"):                  C("C-Shift-D"),
    C("RC-F"):                  C("C-Shift-F"),
    C("RC-G"):                  C("C-Shift-G"),
    C("RC-H"):                  C("C-Shift-H"),
    C("RC-J"):                  C("C-Shift-J"),
    C("RC-K"):                  C("C-Shift-K"),
    C("RC-L"):                  C("C-Shift-L"),
    C("RC-SEMICOLON"):          C("C-Shift-SEMICOLON"),
    C("RC-APOSTROPHE"):         C("C-Shift-APOSTROPHE"),
    # C("RC-GRAVE"):              C("C-Shift-GRAVE"),             # Conflicts with General GUI window switching
    C("RC-Z"):                  C("C-Shift-Z"),
    C("RC-X"):                  C("C-Shift-X"),
    C("RC-C"):                  C("C-Shift-C"),
    C("RC-V"):                  C("C-Shift-V"),
    C("RC-B"):                  C("C-Shift-B"),
    C("RC-N"):                  C("C-Shift-N"),
    C("RC-M"):                  C("C-Shift-M"),
    C("RC-COMMA"):              C("C-Shift-COMMA"),
    C("RC-Dot"):                C("LC-c"),                      # Mimic macOS Cmd+Dot to cancel command
    C("RC-SLASH"):              C("C-Shift-SLASH"),
    C("RC-KPASTERISK"):         C("C-Shift-KPASTERISK"),

}, when = matchProps(clas=termStr))



#############################  GENERAL GUI  ################################
###                                                                      ###
###                                                                      ###
###       ██████  ███████ ███    ██ ███████ ██████   █████  ██           ###
###      ██       ██      ████   ██ ██      ██   ██ ██   ██ ██           ###
###      ██   ███ █████   ██ ██  ██ █████   ██████  ███████ ██           ###
###      ██    ██ ██      ██  ██ ██ ██      ██   ██ ██   ██ ██           ###
###       ██████  ███████ ██   ████ ███████ ██   ██ ██   ██ ███████      ###
###                                                                      ###
###                                                                      ###
############################################################################

# Note: terminals extends to remotes as well
keymap("Cmd+Dot not in terminals", {
    C("RC-Dot"):                C("Esc"),                       # Mimic macOS Cmd+dot = Escape key (not in terminals)
# }, when = lambda ctx: ctx.wm_class.casefold() not in terminals)
}, when = matchProps(not_clas=termStr_ext) )


# Overrides to General GUI shortcuts for specific keyboard types
keymap("GenGUI overrides: Chromebook/IBM", {
    # In-App Tab switching
    C("Alt-Tab"):              [bind,C("C-Tab")],               # Chromebook/IBM - In-App Tab switching
    C("Alt-Shift-Tab"):        [bind,C("C-Shift-Tab")],         # Chromebook/IBM - In-App Tab switching
    C("Alt-Grave") :           [bind,C("C-Shift-Tab")],         # Chromebook/IBM - In-App Tab switching
    C("RAlt-Backspace"):        C("Delete"),                    # Chromebook/IBM - Delete
    C("LAlt-Backspace"):        C("C-Backspace"),               # Chromebook/IBM - Delete Left Word of Cursor
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and ( isKBtype('Chromebook')(ctx) or isKBtype('IBM')(ctx) ) )
keymap("GenGUI overrides: not Chromebook", {
    # In-App Tab switching
    C("Super-Tab"):            [bind,C("LC-Tab")],              # Default not-chromebook
    C("Super-Shift-Tab"):      [bind,C("Shift-LC-Tab")],        # Default not-chromebook
    C("Alt-Backspace"):         C("C-Backspace"),               # Default not-chromebook
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and not isKBtype('Chromebook')(ctx) )


# Overrides to General GUI shortcuts for specific distros
keymap("GenGUI overrides: elementary OS", {
    C("RC-F3"):                 C("Super-d"),                   # Default SL - Show Desktop (gnome/kde,eos)
    C("RC-Space"):              C("Super-Space"),               # SL - Launch Application Menu (eos)
    C("RC-LC-f"):               C("Super-Up"),                  # SL- Maximize app eos
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'eos' )
keymap("GenGUI overrides: Fedora", {
    C("RC-H"):                  C("Super-h"),                   # Default SL - Minimize app (gnome/budgie/popos/fedora) not-deepin
    C("Super-Right"):          [bind,C("Super-Page_Up")],       # SL - Change workspace (ubuntu/fedora)
    C("Super-Left"):           [bind,C("Super-Page_Down")],     # SL - Change workspace (ubuntu/fedora)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'fedora' )
keymap("GenGUI overrides: Manjaro GNOME", {
    C("RC-Q"):              C("Super-Q"),                       # Close window
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'manjaro' and DESKTOP_ENV == 'gnome' )
keymap("GenGUI overrides: Manjaro Xfce", {
    C("RC-Space"):              C("Alt-F1"),                    # Open Whisker Menu with Cmd+Space
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'manjaro' and DESKTOP_ENV == 'xfce' )
keymap("GenGUI overrides: Manjaro", {
    C("RC-LC-f"):               C("Super-PAGE_UP"),             # SL- Maximize app manjaro
    C("RC-LC-f"):               C("Super-PAGE_DOWN"),           # SL - Minimize app manjaro
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'manjaro' )
keymap("GenGUI overrides: KDE Neon", {
    C("RC-Super-f"):            C("Super-Page_Up"),             # SL - Toggle maximized window state (kde_neon)
    C("RC-H"):                  C("Super-Page_Down"),           # SL - Minimize app (kde_neon)
                                                                # SL - Default SL - Change workspace (kde_neon)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'neon' )
keymap("GenGUI overrides: Pop!_OS", {
    C("RC-H"):                  C("Super-h"),                   # Default SL - Minimize app (gnome/budgie/popos/fedora) not-deepin
    C("Super-Right"):          [bind,C("Super-C-Up")],          # SL - Change workspace (popos)
    C("Super-Left"):           [bind,C("Super-C-Down")],        # SL - Change workspace (popos)
    C("RC-Q"):                  C("Super-q"),                   # SL - Close Apps (popos)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'popos' )
keymap("GenGUI overrides: Ubuntu", {
    C("Super-Right"):          [bind,C("Super-Page_Up")],       # SL - Change workspace (ubuntu/fedora)
    C("Super-Left"):           [bind,C("Super-Page_Down")],     # SL - Change workspace (ubuntu/fedora)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DISTRO_NAME == 'ubuntu' )


# Overrides to General GUI shortcuts for specific desktop environments
keymap("GenGUI overrides: Budgie", {
    C("Super-Right"):           C("C-Alt-Right"),               # Default SL - Change workspace (budgie)
    C("Super-Left"):            C("C-Alt-Left"),                # Default SL - Change workspace (budgie)
    C("RC-H"):                  C("Super-h"),                   # Default SL - Minimize app (gnome/budgie/popos/fedora) not-deepin
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'budgie' )
keymap("GenGUI overrides: Cinnamon", {
    C("RC-Space"):              C("C-Esc"),                     # Right click, configure Mint menu shortcut to Ctrl+Esc
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'cinnamon' )
keymap("GenGUI overrides: Deepin", {
    C("RC-H"):                  C("Super-n"),                   # Default SL - Minimize app (deepin)
    C("Alt-RC-Space"):          C("Super-e"),                   # Open Finder - (deepin)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'deepin' )
keymap("GenGUI overrides: GNOME", {
    # C("RC-Space"):              C("Alt-F1"),                    # Custom remap for alternate launcher
    C("RC-Space"):              C("Super-s"),                   # Show GNOME overview/app launcher
    C("RC-F3"):                 C("Super-d"),                   # Default SL - Show Desktop (gnome/kde,eos)
    C("RC-Super-f"):            C("Alt-F10"),                   # Default SL - Maximize app (gnome/kde)
    C("RC-H"):                  C("Super-h"),                   # Default SL - Minimize app (gnome/budgie/popos/fedora) not-deepin
    # Screenshot shortcuts for GNOME 42+
    C("RC-Shift-Key_3"):        C("Shift-Print"),               # Take a screenshot immediately (gnome)
    C("RC-Shift-Key_4"):        C("Alt-Print"),                 # Take a screenshot of a window (gnome)
    C("RC-Shift-Key_5"):        C("Print"),                     # Take a screenshot interactively (gnome)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'gnome' )
keymap("GenGUI overrides: IceWM", {
    C("RC-Space"):              Key.LEFT_META,                  # IceWM: Win95Keys=1 (Meta shows menu)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'icewm' )
keymap("GenGUI overrides: KDE", {
    C("RC-Space"):              C("Alt-F1"),                    # Default SL - Launch Application Menu (gnome/kde)
    C("RC-F3"):                 C("Super-d"),                   # Default SL - Show Desktop (gnome/kde,eos)
    C("RC-Super-f"):            C("Alt-F10"),                   # Default SL - Maximize app (gnome/kde)
    # Screenshot shortcuts for KDE Plasma desktops (Spectacle app)
    C("RC-Shift-Key_3"):        C("Shift-Print"),               # Take a screenshot immediately (kde)
    C("RC-Shift-Key_4"):        C("Alt-Print"),                 # Take a screenshot of a window (kde)
    C("RC-Shift-Key_5"):        C("Print"),                     # Take a screenshot interactively (kde)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'kde' )
keymap("GenGUI overrides: MATE", {
    C("RC-Space"):              C("Alt-Space"),                     # Right click, configure Mint menu shortcut to match
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'mate' )
keymap("GenGUI overrides: Xfce4", {
    C("RC-Grave"):             [bind,C("Super-Tab")],           # xfce4 Switch within app group
    C("Shift-RC-Grave"):       [bind,C("Super-Shift-Tab")],     # xfce4 Switch within app group
    C("RC-Space"):              C("Super-Space"),               # Launch Application Menu xfce4
    C("RC-F3"):                 C("C-Alt-d"),                   # SL- Show Desktop xfce4
    C("RC-H"):                  C("Alt-F9"),                    # SL - Minimize app xfce4
    # Screenshot shortcuts for Xfce desktops (xfce4-screenshooter app)
    C("RC-Shift-Key_3"):        C("Print"),                     # Take a screenshot immediately (kde)
    C("RC-Shift-Key_4"):        C("Alt-Print"),               # Take a screenshot of a window (kde)
    C("RC-Shift-Key_5"):        C("Shift-Print"),                 # Take a screenshot interactively (kde)
}, when = lambda ctx: matchProps(not_lst=remotes_lod)(ctx) and DESKTOP_ENV == 'xfce' )


# None referenced here originally
# - but remote clients and VM software ought to be set here
# These are the typical remaps for ALL GUI based apps
keymap("General GUI", {

    C("Alt-Numlock"):           toggle_forced_numpad,         # Turn the Forced Numpad feature on and off
    C("Fn-Numlock"):            toggle_forced_numpad,         # Turn the Forced Numpad feature on and off
    C("Numlock"):               isNumlockClearKey,            # Numlock key is "Clear" (Esc) if cnfg.forced_numpad is True

    C("Shift-RC-Left_Brace"):   C("C-Page_Up"),                 # Tab navigation: Go to prior (left) tab
    C("Shift-RC-Right_Brace"):  C("C-Page_Down"),               # Tab navigation: Go to next (right) tab
    C("RC-Space"):              C("Alt-F1"),                    # Default SL - Launch Application Menu (gnome/kde)
    C("RC-F3"):                 C("Super-d"),                   # Default SL - Show Desktop (gnome/kde,eos)
    C("RC-Super-f"):            C("Alt-F10"),                   # Default SL - Maximize app (gnome/kde)
    C("RC-Q"):                  C("Alt-F4"),                    # Default SL - not-popos
    C("Alt-Tab"):               ignore_combo,                   # Default - Cmd Tab - App Switching Default
    C("RC-Tab"):               [bind, C("Alt-Tab")],            # Default - Cmd Tab - App Switching Default
    C("Shift-RC-Tab"):         [bind, C("Alt-Shift-Tab")],      # Default - Cmd Tab - App Switching Default
    C("RC-Grave"):             [bind, C("Alt-Grave")],          # Default not-xfce4 - Cmd ` - Same App Switching
    C("Shift-RC-Grave"):       [bind, C("Alt-Shift-Grave")],    # Default not-xfce4 - Cmd ` - Same App Switching

    # Fn to Alt style remaps
    C("RAlt-Enter"):            C("insert"),                    # Insert

    # emacs style
    C("Super-a"):               C("Home"),                      # Beginning of Line
    C("Super-e"):               C("End"),                       # End of Line
    C("Super-b"):               C("Left"),
    C("Super-f"):               C("Right"),
    C("Super-n"):               C("Down"),
    C("Super-p"):               C("Up"),
    C("Super-k"):              [C("Shift-End"), C("Backspace")],
    C("Super-d"):               C("Delete"),

    # This is better done with a native custom shortcut in each DE
    # C("Alt-RC-Space"):          C(""),                          # Open Finder - Placeholder not-deepin

    # Wordwise
    C("RC-Left"):               C("Home"),                      # Beginning of Line
    C("Shift-RC-Left"):         C("Shift-Home"),                # Select all to Beginning of Line
    C("RC-Right"):              C("End"),                       # End of Line
    C("Shift-RC-Right"):        C("Shift-End"),                 # Select all to End of Line
    # C("RC-Left"):               C("C-LEFT_BRACE"),              # Firefox-nw - Back
    # C("RC-Right"):              C("C-RIGHT_BRACE"),             # Firefox-nw - Forward
    # C("RC-Left"):               C("Alt-LEFT"),                  # Chrome-nw - Back
    # C("RC-Right"):              C("Alt-RIGHT"),                 # Chrome-nw - Forward
    C("RC-Up"):                 C("C-Home"),                    # Beginning of File
    C("Shift-RC-Up"):           C("C-Shift-Home"),              # Select all to Beginning of File
    C("RC-Down"):               C("C-End"),                     # End of File
    C("Shift-RC-Down"):         C("C-Shift-End"),               # Select all to End of File
    C("Super-Backspace"):       C("C-Backspace"),               # Delete Left Word of Cursor
    C("Super-Delete"):          C("C-Delete"),                  # Delete Right Word of Cursor
    # C("Alt-Backspace"):         C("C-Backspace"),               # Default not-chromebook
    C("RC-Backspace"):          C("C-Shift-Backspace"),         # Delete Entire Line Left of Cursor
    C("Alt-Delete"):            C("C-Delete"),                  # Delete Right Word of Cursor
    # C(""):                      ignore_combo,                   # cancel
    # C(""):                      C(""),                          #

# }, when = lambda ctx: ctx.wm_class.casefold() not in remotes) # original conditional
# }, when = matchProps(not_clas=remoteStr))                      # matchProps with regex string
}, when = matchProps(not_lst=remotes_lod))                      # matchProps with list-of-dicts
