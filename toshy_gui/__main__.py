#!/usr/bin/env python3
"""
Entry point for python -m toshy_gui

Usage:
    python -m toshy_gui           # Run GTK-4 version (default)
    python -m toshy_gui --gtk4    # Run GTK-4 version
    python -m toshy_gui --tk      # Run tkinter version
"""

import argparse
from toshy_common.logger import debug


def main():
    parser = argparse.ArgumentParser(description='Toshy Preferences GUI')
    parser.add_argument('--gtk4', action='store_true',
                        help='Run GTK-4 version instead of tkinter')
    parser.add_argument('--tk', action='store_true',
                        help='Run tkinter version instead of GTK-4')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        import toshy_common.logger
        toshy_common.logger.VERBOSE = True
    
    if True is False: pass
    elif args.gtk4:
        debug("Launching GTK-4 version...")
        from .main_gtk4 import main as gtk4_main
        gtk4_main()
    elif args.tk:
        debug("Launching tkinter version...")
        from .main_tkinter import main as tkinter_main
        tkinter_main()
    else:
        debug("Launching GTK-4 version...")
        from .main_gtk4 import main as gtk4_main
        gtk4_main()


if __name__ == "__main__":
    main()
