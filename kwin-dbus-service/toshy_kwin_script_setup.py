#!/usr/bin/env python3

import os
import sys
import time
import shutil
import signal
import zipfile
import platform
import subprocess

from typing import Dict
from subprocess import DEVNULL
from xwaykeyz.lib.logger import debug, error

# Independent module/script to deal with installing KWin script, if necessary
# Called by the KDE D-Bus launcher script

# Add paths to avoid errors like ModuleNotFoundError or ImportError
home_dir            = os.path.expanduser("~")
run_tmp_dir         = os.environ.get('XDG_RUNTIME_DIR') or '/tmp'
parent_folder_path  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
current_folder_path = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, current_folder_path)
sys.path.insert(0, parent_folder_path)

existing_path = os.environ.get('PYTHONPATH', '')
os.environ['PYTHONPATH'] = f'{parent_folder_path}:{current_folder_path}:{existing_path}'

# local imports now that path is prepped
from lib.env_context import EnvironmentInfo

if os.name == 'posix' and os.geteuid() == 0:
    error("This app should not be run as root/superuser.")
    sys.exit(1)

def signal_handler(sig, frame):
    """handle signals like Ctrl+C"""
    if sig in (signal.SIGINT, signal.SIGQUIT):
        # Perform any cleanup code here before exiting
        # traceback.print_stack(frame)
        debug(f'\nSIGINT or SIGQUIT received. Exiting.\n')
        sys.exit(0)

if platform.system() != 'Windows':
    signal.signal(signal.SIGINT,    signal_handler)
    signal.signal(signal.SIGQUIT,   signal_handler)
else:
    error(f'This is only meant to run on Linux. Exiting...')
    sys.exit(1)


sep_reps        = 80
sep_char        = '='
separator       = sep_char * sep_reps

LOG_PFX = 'TOSHY_KWIN_SETUP'


DISTRO_ID       = None
DISTRO_VER      = None
VARIANT_ID      = None
SESSION_TYPE    = None
DESKTOP_ENV     = None
DE_MAJ_VER      = None


def check_environment():
    """Retrieve the current environment from env module"""
    # env_info_dct   = env.get_env_info()
    env_ctxt_getter = EnvironmentInfo()
    env_info_dct   = env_ctxt_getter.get_env_info()
    global DISTRO_ID, DISTRO_VER, VARIANT_ID, SESSION_TYPE, DESKTOP_ENV, DE_MAJ_VER
    DISTRO_ID       = env_info_dct.get('DISTRO_ID',     'keymissing')
    DISTRO_VER      = env_info_dct.get('DISTRO_VER',    'keymissing')
    VARIANT_ID      = env_info_dct.get('VARIANT_ID',    'keymissing')
    SESSION_TYPE    = env_info_dct.get('SESSION_TYPE',  'keymissing')
    DESKTOP_ENV     = env_info_dct.get('DESKTOP_ENV',   'keymissing')
    DE_MAJ_VER      = env_info_dct.get('DE_MAJ_VER',    'keymissing')


check_environment()

if DESKTOP_ENV in ['kde', 'plasma'] and SESSION_TYPE == 'wayland':
    KDE_ver = DE_MAJ_VER
else:
    debug(f'{LOG_PFX}: Not a Wayland+KDE environment. Exiting.')
    time.sleep(2)
    sys.exit(0)

gdbus_cmd                       = None
if shutil.which('gdbus'):
    gdbus_cmd                   = 'gdbus'

dbus_send_cmd                   = None
if shutil.which('dbus-send'):
    dbus_send_cmd               = 'dbus-send'

qdbus_cmd                       = None
if shutil.which('qdbus-qt6'):
    qdbus_cmd                   = 'qdbus-qt6'
elif shutil.which('qdbus-qt5'):
    qdbus_cmd                   = 'qdbus-qt5'
elif shutil.which('qdbus'):
    qdbus_cmd                   = 'qdbus'

if gdbus_cmd is None and dbus_send_cmd is None and qdbus_cmd is None:
    error(f"No expected D-Bus utility was found. Cannot check KWin script status.")
    sys.exit(1)

kwin_script_name            = 'toshy-dbus-notifyactivewindow'
kwin_dbus_obj               = 'org.kde.KWin'
kwin_kwin_path              = '/KWin'
kwin_scripting_path         = '/Scripting'
kwin_scripting_iface        = 'org.kde.kwin.Scripting'


def do_kwin_reconfigure():
    """Utility function to run the KWin reconfigure command"""
    if dbus_send_cmd:
        # do KWin reconfigure with dbus-send utility
        cmd_lst = [ dbus_send_cmd, '--type=method_call',
                    f'--dest={kwin_dbus_obj}', kwin_kwin_path,
                    'org.kde.KWin.reconfigure']
        try:
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            time.sleep(1)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "dbus-send" to do KWin reconfigure.\n\t{proc_err}')

    if gdbus_cmd:
        # do KWin reconfigure with gdbus utility
        cmd_lst = [ gdbus_cmd, 'call', '--session', 
                    '--dest', kwin_dbus_obj,
                    '--object-path', kwin_kwin_path, 
                    '--method', 'org.kde.KWin.reconfigure']
        try:
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            time.sleep(1)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "gdbus" to do KWin reconfigure.\n\t{proc_err}')

    if qdbus_cmd:
        # do KWin reconfigure with qdbus utility
        cmd_lst = [ qdbus_cmd, kwin_dbus_obj, kwin_kwin_path, 'reconfigure']
        try:
            subprocess.run(cmd_lst, check=True, stderr=DEVNULL, stdout=DEVNULL)
            time.sleep(1)
            return
        except subprocess.CalledProcessError as proc_err:
            error(f'Problem using "{qdbus_cmd}" to do KWin reconfigure.\n\t{proc_err}')

    error(f'{LOG_PFX}: Failed to do KWin reconfigure.')


def is_kwin_script_loaded():
    """Utility function t check if the KWin script is loaded"""

    if dbus_send_cmd:
        cmd_lst = [
            dbus_send_cmd,
            '--print-reply=literal',
            '--dest=' + kwin_dbus_obj,
            '--type=method_call',
            kwin_scripting_path,
            f'{kwin_scripting_iface}.isScriptLoaded',
            'string:' + kwin_script_name
        ]
    elif gdbus_cmd:
        cmd_lst = [
            gdbus_cmd, 
            'call', 
            '--session', 
            '--dest', kwin_dbus_obj, 
            '--object-path', kwin_scripting_path, 
            '--method', f'{kwin_scripting_iface}.isScriptLoaded', 
            kwin_script_name
        ]
    elif qdbus_cmd:
        cmd_lst = [
            qdbus_cmd,
            kwin_dbus_obj,
            kwin_scripting_path,
            f'{kwin_scripting_iface}.isScriptLoaded',
            kwin_script_name
        ]

    try:
        output: bytes       = subprocess.check_output(cmd_lst)
        # output is bytes object, not string!
        output_str          = output.decode().strip()
        is_loaded           = 'true' in output_str.lower()
        print(f"{LOG_PFX}: Is '{kwin_script_name}' KWin script loaded: {is_loaded}", flush=True)
        return is_loaded
    except subprocess.CalledProcessError as proc_err:
        print(f"{LOG_PFX}: Error checking if KWin script is loaded:\n\t{proc_err}", flush=True)
        return False


def load_kwin_script():
    """Utility function to load the KWin script (CURRENTLY UNUSED)"""
    try:
        subprocess.run([qdbus_cmd,
                        kwin_dbus_obj,
                        kwin_scripting_path,
                        f'{kwin_scripting_iface}.loadScript',
                        kwin_script_name    ],
                        check=True) #,
                        # stderr=DEVNULL,
                        # stdout=DEVNULL)
        print(f'{LOG_PFX}: Loaded KWin script.', flush=True)
    except subprocess.CalledProcessError as e:
        print(f"{LOG_PFX}: Error loading KWin script:\n\t{e}", flush=True)
        return False


def unload_kwin_script():
    """Utility function to unload the KWin script (CURRENTLY UNUSED)"""
    try:
        subprocess.run([qdbus_cmd,
                        kwin_dbus_obj,
                        kwin_scripting_path,
                        f'{kwin_scripting_iface}.unloadScript',
                        kwin_script_name    ],
                        check=True) #,
                        # stderr=DEVNULL,
                        # stdout=DEVNULL)
        print(f'{LOG_PFX}: Loaded KWin script.', flush=True)
    except subprocess.CalledProcessError as e:
        print(f"{LOG_PFX}: Error loading KWin script:\n\t{e}", flush=True)
        return False


def setup_kwin2dbus_script():
    """Install the KWin script to notify D-Bus service about window focus changes"""
    # print(f'\n\n§  Setting up the Toshy KWin script...\n{separator}')

    if KDE_ver not in ['6', '5', '4']:
        error("ERROR: Toshy KWin script cannot be installed.")
        error(f"KDE major version invalid: '{KDE_ver}'")
        return

    if KDE_ver == '4':
        print('KDE 4 is not Wayland compatible. Toshy KWin script unnecessary.')
        return

    kpackagetool_cmd        = f'kpackagetool{KDE_ver}'
    kwriteconfig_cmd        = f'kwriteconfig{KDE_ver}'

    kwin_script_name        = 'toshy-dbus-notifyactivewindow'
    kwin_script_path        = os.path.join( parent_folder_path,
                                            'kwin-script',
                                            f'kde{KDE_ver}',
                                            kwin_script_name)
    script_tmp_file         = f'{run_tmp_dir}/{kwin_script_name}.kwinscript'

    # Create a zip file (overwrite if it exists)
    with zipfile.ZipFile(script_tmp_file, 'w') as zipf:
        # Add main.js to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                                arcname='contents/code/main.js')
        # Add metadata.desktop to the kwinscript package
        zipf.write(os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

    # Try to remove any installed KWin script entirely
    cmd_lst = [kpackagetool_cmd, '-t', 'KWin/Script', '-r', kwin_script_name]
    result = subprocess.run(cmd_lst, capture_output=True, text=True)
    if result.returncode != 0:
        pass
    else:
        print(f"{LOG_PFX}: Removed existing KWin script.", flush=True)

    # Install the KWin script
    cmd_lst = [kpackagetool_cmd, '-t', 'KWin/Script', '-i', script_tmp_file]
    try:
        subprocess.run(cmd_lst, check=True, capture_output=True, text=True)
        print(f"{LOG_PFX}: Installed the KWin script.", flush=True)
    except subprocess.CalledProcessError as proc_err:
        error(f"{LOG_PFX}: Error installing the KWin script. The error was:\n\t{proc_err.stderr}")

    # Remove the temporary kwinscript file
    try:
        os.remove(script_tmp_file)
    except (FileNotFoundError, PermissionError): pass

    # Keep the script enabled after restart using kwriteconfig5 to kwinrc file
    cmd_lst = [kwriteconfig_cmd, '--file', 'kwinrc', '--group', 'Plugins', '--key',
            f'{kwin_script_name}Enabled', 'true']
    try:
        subprocess.run(cmd_lst, check=True, capture_output=True, text=True)
        print(f"{LOG_PFX}: Enabled the KWin script.", flush=True)
    except subprocess.CalledProcessError as proc_err:
        error(f"{LOG_PFX}: Error enabling the KWin script. The error was:\n\t{proc_err.stderr}")

    # Try to get KWin to activate the script
    do_kwin_reconfigure()
    time.sleep(5)

    # Keep checking for a while to see if it loads
    setup_loop_ct = 0
    while not is_kwin_script_loaded() and setup_loop_ct <= 6:
        # repeat KWin reconfigure, seems to help push KWin to activate the script after login
        do_kwin_reconfigure()
        time.sleep(5)
        setup_loop_ct += 1

def main():
    """Check if the KWin script is loaded, set it up if needed, give it several chances to load"""

    # this loop and the one above is to help deal with the fact that it is 
    # really, really hard to start the KWin script right after login if 
    # it was just installed
    is_loaded_loop_max = 6
    is_loaded_loop_ct = 0
    while not is_kwin_script_loaded() and is_loaded_loop_ct <= is_loaded_loop_max:
        is_loaded_loop_ct += 1
        if is_loaded_loop_ct == is_loaded_loop_max:
            print(f'{LOG_PFX}: ERROR! Unable to activate the KWin script.', flush=True)
            sys.exit(1)
        setup_kwin2dbus_script()
        time.sleep(1)

    # run the kickstart script here to generate a KWin event (hopefully)
    kickstart_script    = 'toshy-kwin-script-kickstart.sh'
    kickstart_cmd       = os.path.join(home_dir, '.config', 'toshy', 'scripts', kickstart_script)
    subprocess.Popen([kickstart_cmd], stderr=DEVNULL, stdout=DEVNULL)


if __name__ == "__main__":
    main()
