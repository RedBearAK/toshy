#!/usr/bin/env python3
__version__ = '20250226'

# NOTE: This new context module for monitoring keyboard-mouse sharing sofware was
# originally produced by Claude 3.7 Sonnet, based on the window_context module in
# the keymapper (xwaykeyz) as a template. [2025-02-25]

import os
import re
import abc
import time
import platform
import subprocess

from typing import Dict, List, Optional, Set, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from xwaykeyz.lib.logger import debug, error, warn


class SharedDeviceMonitorInterface(abc.ABC):
    """Abstract base class for all shared device monitor classes"""

    @classmethod
    @abc.abstractmethod
    def get_supported_software(cls):
        """
        Returns a list of software names this monitor supports.
        
        :returns: A list of strings, each representing a software name
                    (e.g., 'synergy', 'input-leap', 'deskflow')
        """
        pass

    @abc.abstractmethod
    def is_running(self):
        """
        Checks if the software is currently running.
        
        :returns: True if the software is running, False otherwise
        """
        pass

    @abc.abstractmethod
    def get_log_file_path(self):
        """
        Returns the path to the log file for this software.
        
        :returns: String path to the log file, or None if not available
        """
        pass

    @abc.abstractmethod
    def parse_log_line(self, line: str) -> Optional[bool]:
        """
        Parses a line from the log file to determine if it indicates a focus change.
        
        :param line: A line from the log file
        :returns: True if focus entered, False if focus left, None if not a focus change event
        """
        pass


class SynergyMonitor(SharedDeviceMonitorInterface):
    """Monitor for Synergy software"""

    def __init__(self):
        self.process_names = ['synergy', 'synergys', 'synergyc']
        self.log_paths = [
            # Observed in the wild
            os.path.expanduser("~/.local/state/Synergy/synergy.log"),
            # Guesses by Claude
            os.path.expanduser("~/.local/share/Synergy/synergy.log"),
            os.path.expanduser("~/.config/Synergy/synergy.log"),
        ]

    @classmethod
    def get_supported_software(cls):
        return ['synergy']

    def is_running(self):
        """Check if any Synergy process is running"""
        for process_name in self.process_names:
            try:
                result = subprocess.run(['pgrep', '-x', process_name], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except subprocess.SubprocessError:
                pass
        return False

    def get_log_file_path(self):
        """Return the first existing log file path"""
        for path in self.log_paths:
            if os.path.exists(path):
                return path
        return None

    def parse_log_line(self, line: str) -> Optional[bool]:
        """Parse Synergy log line for focus events"""
        if "leaving screen" in line:
            return False
        elif "entering screen" in line:
            return True
        return None


class InputLeapMonitor(SharedDeviceMonitorInterface):
    """Monitor for Input Leap software"""

    def __init__(self):
        self.process_names = ['input-leap', 'input-leaps', 'input-leapc']
        self.log_paths = [
            # Observed in the wild
            os.path.expanduser("/var/log/input-leap.log"),
            # Guesses by Claude
            os.path.expanduser("~/.local/state/InputLeap/input-leap.log"),
            os.path.expanduser("~/.local/share/InputLeap/input-leap.log"),
            os.path.expanduser("~/.config/InputLeap/input-leap.log"),
        ]

    @classmethod
    def get_supported_software(cls):
        return ['input-leap']

    def is_running(self):
        """Check if any Input Leap process is running"""
        for process_name in self.process_names:
            try:
                result = subprocess.run(['pgrep', '-x', process_name], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except subprocess.SubprocessError:
                pass
        return False

    def get_log_file_path(self):
        """Return the first existing log file path"""
        for path in self.log_paths:
            if os.path.exists(path):
                return path
        return None

    def parse_log_line(self, line: str) -> Optional[bool]:
        """Parse Input Leap log line for focus events"""
        if "leaving screen" in line:
            return False
        elif "entering screen" in line:
            return True
        return None


class DeskflowMonitor(SharedDeviceMonitorInterface):
    """Monitor for Deskflow software"""

    def __init__(self):
        self.process_names = ['deskflow', 'deskflows', 'deskflowc']
        self.log_paths = [
            # Observed in the wild
            os.path.expanduser("~/deskflow.log"),
            # Guesses by Claude
            os.path.expanduser("~/.local/state/Deskflow/deskflow.log"),
            os.path.expanduser("~/.local/share/Deskflow/deskflow.log"),
            os.path.expanduser("~/.config/Deskflow/deskflow.log"),
        ]

    @classmethod
    def get_supported_software(cls):
        return ['deskflow']

    def is_running(self):
        """Check if any Deskflow process is running"""
        for process_name in self.process_names:
            try:
                result = subprocess.run(['pgrep', '-x', process_name], 
                                        capture_output=True, text=True)
                if result.returncode == 0:
                    return True
            except subprocess.SubprocessError:
                pass
        return False

    def get_log_file_path(self):
        """Return the first existing log file path"""
        for path in self.log_paths:
            if os.path.exists(path):
                return path
        return None

    def parse_log_line(self, line: str) -> Optional[bool]:
        """Parse Deskflow log line for focus events"""
        if "leaving screen" in line:
            return False
        elif "entering screen" in line:
            return True
        return None


class LogWatcherHandler(FileSystemEventHandler):
    """Handler for log file changes"""

    def __init__(self, log_path: str, parse_func: Callable[[str], Optional[bool]], 
                    on_focus_change: Callable[[bool], None]):
        super().__init__()
        self.log_path = log_path
        self.parse_func = parse_func
        self.on_focus_change = on_focus_change
        self.last_position = 0
        self.initialized = False

    def on_modified(self, event: FileSystemEvent):
        if event.src_path == self.log_path:
            self.handle_log_file_change()

    def on_created(self, event: FileSystemEvent):
        if event.src_path == self.log_path:
            self.handle_log_file_change()

    def handle_log_file_change(self):
        if not os.path.exists(self.log_path):
            return

        with open(self.log_path, 'r') as f:
            if not self.initialized:
                # On first run, just read the last bit of the file
                f.seek(0, os.SEEK_END)
                end_pos = f.tell()
                f.seek(max(end_pos - 1024, 0))
                if f.tell() != 0:
                    f.readline()  # Skip partial line
                self.initialized = True
            else:
                f.seek(self.last_position)

            lines = f.readlines()
            self.last_position = f.tell()

            # Process lines to find focus changes
            most_recent_state = None
            for line in lines:
                line = line.strip()
                state = self.parse_func(line)
                if state is not None:
                    most_recent_state = state

            # If we found a focus change, notify the callback
            if most_recent_state is not None:
                self.on_focus_change(most_recent_state)


class SharedDeviceContext:
    """
    Manages focus tracking for shared device software (Synergy, Input Leap, Deskflow)
    """

    def __init__(self):
        self.observer = Observer()
        self.handlers = {}
        self.monitors = []
        self.screen_has_focus = True
        self.active_monitors = set()

        # Initialize all available monitors
        for monitor_class in SharedDeviceMonitorInterface.__subclasses__():
            self.monitors.append(monitor_class())

        # Log which monitors are available
        software_list = [software for monitor in self.monitors 
                        for software in monitor.get_supported_software()]
        debug(f"SharedDeviceContext initialized with support for:\n       {', '.join(software_list)}")

    def detect_active_software(self) -> Set[str]:
        """
        Detects which shared device software is currently running
        
        :returns: Set of software names that are currently running
        """
        active_software = set()
        for monitor in self.monitors:
            if monitor.is_running():
                active_software.update(monitor.get_supported_software())
        return active_software

    def start_monitoring(self):
        """
        Start monitoring all active shared device software
        """
        # Detect which software is running
        active_software = self.detect_active_software()

        if not active_software:
            debug("No shared device software detected")
            return

        debug(f"Detected active shared device software: {', '.join(active_software)}")

        # Start monitoring each active software
        for monitor in self.monitors:
            supported_software = set(monitor.get_supported_software())
            if not supported_software.intersection(active_software):
                continue

            log_path = monitor.get_log_file_path()
            if not log_path:
                warn(f"No log file found for {', '.join(supported_software)}")
                continue

            log_dir = os.path.dirname(log_path)
            if not os.path.exists(log_dir):
                warn(f"Log directory does not exist: {log_dir}")
                continue

            # Create a handler for this log file
            handler = LogWatcherHandler(
                log_path=log_path,
                parse_func=monitor.parse_log_line,
                on_focus_change=self.on_focus_change
            )

            # Schedule the handler with the observer
            self.observer.schedule(handler, path=log_dir, recursive=False)
            self.handlers[log_path] = handler
            self.active_monitors.update(supported_software)

            debug(f"Monitoring {', '.join(supported_software)} log file:\n       {log_path}")

        # Start the observer if we have any handlers
        if self.handlers:
            self.observer.start()
            debug("Log file monitoring started")

            # Initialize the log handlers
            for log_path, handler in self.handlers.items():
                if os.path.exists(log_path):
                    handler.handle_log_file_change()

    def stop_monitoring(self):
        """
        Stop monitoring all shared device software
        """
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            debug("Log file monitoring stopped")
            
        self.handlers.clear()
        self.active_monitors.clear()

    def on_focus_change(self, has_focus: bool):
        """
        Callback function for when focus changes
        
        :param has_focus: True if the screen has focus, False otherwise
        """
        if has_focus != self.screen_has_focus:
            self.screen_has_focus = has_focus
            print()
            debug(f"Screen focus changed: {'entered screen' if has_focus else 'left screen'}",
                ctx="FC")

    def get_focus_state(self) -> bool:
        """
        Returns the current focus state
        
        :returns: True if the screen has focus, False otherwise
        """
        return self.screen_has_focus

    def refresh_monitoring(self):
        """
        Refresh which software is being monitored
        """
        self.stop_monitoring()
        self.start_monitoring()


# For testing the module directly
if __name__ == "__main__":
    context = SharedDeviceContext()
    context.start_monitoring()

    try:
        while True:
            time.sleep(1)
            print(f"Screen has focus: {context.get_focus_state()}")
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        context.stop_monitoring()
