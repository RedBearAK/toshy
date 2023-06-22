#!/usr/bin/env python3

import os
import sys
import time
import shutil
import signal
import zipfile
import platform
import subprocess

from subprocess import DEVNULL
from keyszer.lib.logger import debug, error

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


def main():
    qdbus_cmd = None

    if shutil.which('qdbus'):
        qdbus_cmd = 'qdbus'
    elif shutil.which('qdbus-qt5'):
        qdbus_cmd = 'qdbus-qt5'

    if qdbus_cmd is None:
        error(f"Cannot find 'qdbus' or 'qdbus-qt5'. Cannot check KWin script status.")
        sys.exit(1)

    toshy_kwin_script_name          = 'toshy-dbus-notifyactivewindow'
    toshy_kwin_script_is_loaded     = False
    kwin_dbus_obj                   = 'org.kde.KWin'
    kwin_kwin_path                  = '/KWin'
    kwin_scripting_path             = '/Scripting'
    kwin_scripting_iface            = 'org.kde.kwin.Scripting'

    def do_kwin_reconfigure():
        """Utility function to run the KWin reconfigure command"""
        try:
            subprocess.run([qdbus_cmd, kwin_dbus_obj, kwin_kwin_path, 'reconfigure'],
                            check=True, stderr=DEVNULL, stdout=DEVNULL)
            # time.sleep(1)
        except subprocess.CalledProcessError as proc_error:
            error(f'{LOG_PFX}: Error while running KWin reconfigure.\n\t{proc_error}')


    def kwin_responding():
        # Use qdbus to send a simple command to KWin and check the response
        try:
            output: bytes = subprocess.check_output([  qdbus_cmd,
                                                kwin_dbus_obj,
                                                kwin_kwin_path,
                                                'org.kde.KWin.currentDesktop'])
            return output.decode().strip() != ""
        except subprocess.CalledProcessError:
            return False


    # Wait for KWin to be ready for a D-Bus conversation about the KWin script
    loop_ct = 0
    while True and loop_ct < 9:
        loop_ct += 1
        if kwin_responding():
            break
        else:
            time.sleep(1)


    def is_kwin_script_loaded():
        try:
            output: bytes = subprocess.check_output([  qdbus_cmd,
                                                kwin_dbus_obj,
                                                kwin_scripting_path,
                                                f'{kwin_scripting_iface}.isScriptLoaded',
                                                toshy_kwin_script_name    ])
            # output is bytes object, not string!
            output_str = output.decode().strip()
            print(f"{LOG_PFX}: Script '{toshy_kwin_script_name}' loaded: {output_str}", flush=True)
            return output_str == 'true'
        except subprocess.CalledProcessError as e:
            print(f"{LOG_PFX}: Error checking if KWin script is loaded:\n\t{e}", flush=True)
            return False


    def load_kwin_script():
        try:
            subprocess.run([qdbus_cmd,
                            kwin_dbus_obj,
                            kwin_scripting_path,
                            f'{kwin_scripting_iface}.loadScript',
                            toshy_kwin_script_name    ],
                            check=True) #,
                            # stderr=DEVNULL,
                            # stdout=DEVNULL)
            print(f'{LOG_PFX}: Loaded KWin script.')
        except subprocess.CalledProcessError as e:
            print(f"{LOG_PFX}: Error loading KWin script:\n\t{e}")
            return False


    def setup_kwin2dbus_script():
        """Install the KWin script to notify D-Bus service about window focus changes"""
        # print(f'\n\n§  Setting up the Toshy KWin script...\n{separator}')
        kwin_script_name    = 'toshy-dbus-notifyactivewindow'
        kwin_script_path    = os.path.join( parent_folder_path,
                                            'kde-kwin-dbus-service', kwin_script_name)
        script_tmp_file     = f'{run_tmp_dir}/{kwin_script_name}.kwinscript'

        # Create a zip file (overwrite if it exists)
        with zipfile.ZipFile(script_tmp_file, 'w') as zipf:
            # Add main.js to the kwinscript package
            zipf.write(os.path.join(kwin_script_path, 'contents', 'code', 'main.js'),
                                    arcname='contents/code/main.js')
            # Add metadata.desktop to the kwinscript package
            zipf.write(os.path.join(kwin_script_path, 'metadata.json'), arcname='metadata.json')

        # Try to remove any installed KWin script entirely
        result = subprocess.run(
            ['kpackagetool5', '-t', 'KWin/Script', '-r', kwin_script_name],
            capture_output=True, text=True)
        if result.returncode != 0:
            pass
        else:
            print(f"{LOG_PFX}: Removed existing KWin script.", flush=True)

        # Install the KWin script
        try:
            subprocess.run(
                ['kpackagetool5', '-t', 'KWin/Script', '-i', script_tmp_file],
                check=True, capture_output=True, text=True)
            print(f"{LOG_PFX}: Installed the KWin script.")
        except subprocess.CalledProcessError as proc_err:
            error(f"{LOG_PFX}: Error installing the KWin script. The error was:\n\t{proc_err.stderr}")

        # Remove the temporary kwinscript file
        try:
            os.remove(script_tmp_file)
        except (FileNotFoundError, PermissionError): pass

        # Keep the script enabled after restart using kwriteconfig5 to kwinrc file
        try:
            subprocess.run(
                ['kwriteconfig5', '--file', 'kwinrc', '--group', 'Plugins', '--key',
                f'{kwin_script_name}Enabled', 'true'],
                check=True, capture_output=True, text=True)
            print(f"{LOG_PFX}: Enabled the KWin script.", flush=True)
        except subprocess.CalledProcessError as proc_err:
            error(f"{LOG_PFX}: Error enabling the KWin script. The error was:\n\t{proc_err.stderr}")

        # Try to get KWin to activate the script
        do_kwin_reconfigure()
        
        # Keep checking for a while to see if it loads
        setup_loop_ct = 0
        while not is_kwin_script_loaded() and setup_loop_ct <= 12:
            time.sleep(2)
            setup_loop_ct += 1

    is_loaded_loop_max = 30
    is_loaded_loop_ct = 0
    while not is_kwin_script_loaded() and is_loaded_loop_ct <= is_loaded_loop_max:
        is_loaded_loop_ct += 1
        if is_loaded_loop_ct == is_loaded_loop_max:
            print(f'{LOG_PFX}: ERROR! Unable to install the KWin script successfully.', flush=True)
            sys.exit(1)
        setup_kwin2dbus_script()
        time.sleep(1)

    # run the kickstart script here to generate a KWin event (hopefully)
    kickstart_script    = 'toshy-kwin-script-kickstart.sh'
    kickstart_cmd       = os.path.join(home_dir, '.config', 'toshy', 'scripts', kickstart_script)
    subprocess.Popen([kickstart_cmd], stderr=DEVNULL, stdout=DEVNULL)


if __name__ == "__main__":
    main()
