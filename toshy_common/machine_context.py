#!/usr/bin/env python3
__version__ = '20250710'

import sys
import hashlib

from signal import signal, SIGINT
from toshy_common.logger import debug, error


def handle_sigint(signum, frame):
    print("\nSIGINT received. Exiting gracefully.\n")
    sys.exit(0)


# Register the signal handler
signal(SIGINT, handle_sigint)


MACHINE_ID_HASH = None


def hash_value(value: str):
    """Hashes the value and returns a truncated SHA-256 hash."""
    return hashlib.sha256(value.encode()).hexdigest()[:8]  # Hash truncated to 8 chars


def print_hashed_value(value):
    """Print out the hashed value."""
    print(f"(ID) Hashed value for this machine, for use in your config file: '{value}'")


def get_machine_id_hash():
    """Reads the machine ID from the D-Bus or systemd file and stores it in a global variable."""
    global MACHINE_ID_HASH
    paths = ["/var/lib/dbus/machine-id", "/etc/machine-id"]

    for path in paths:
        try:
            with open(path, "r") as f:
                MACHINE_ID = f.read().strip()
                obfuscated_ID = f"{MACHINE_ID[:5]} ... {MACHINE_ID[-5:]}"
                print(f"(ID) Machine ID read from {path} (obfuscated): '{obfuscated_ID}'")
                MACHINE_ID_HASH = hash_value(MACHINE_ID)
                print_hashed_value(MACHINE_ID_HASH)
                return MACHINE_ID_HASH
        except FileNotFoundError:
            continue  # Try the next file if this one is missing
        except PermissionError:
            error(f"Permission denied when trying to read {path}.")
            return
        except Exception as e:
            error(f"Unexpected error occurred while reading {path}: {e}")
            return

    # If no valid machine ID is found
    error("Error: Could not retrieve a valid machine ID from known paths.")


def main():
    """Print out a hashed and trucated value based on the contents of the 
        local machine's unique ID from DBus or systemd machine ID file."""

    # File paths that may contain the unique machine ID:
    # /var/lib/dbus/machine-id
    # /etc/machine-id
    get_machine_id_hash()


if __name__ == "__main__":
    main()
