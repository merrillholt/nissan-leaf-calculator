#!/usr/bin/env python3

"""Main entry point for the Nissan Leaf Charging Calculator application.

Provides a command-line interface to choose between the GUI and console interfaces.
"""

import argparse
import sys


def main():
    """Main entry point. Parses arguments and launches the appropriate interface."""
    parser = argparse.ArgumentParser(
        description="Nissan Leaf Charging Calculator"
    )
    parser.add_argument(
        "--console", "-c",
        action="store_true",
        help="Run the application in console mode"
    )
    parser.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Run the application in GUI mode (default)"
    )
    
    args = parser.parse_args()
    
    # If both or neither is specified, default to GUI
    if (args.console and args.gui) or (not args.console and not args.gui):
        args.gui = True
        args.console = False
    
    # Adjust Python path to import modules with spaces in directory name
    import os
    import sys
    
    # Add the modules directory to path to handle spaces in directory name
    modules_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Python Modules")
    sys.path.insert(0, modules_dir)
    
    # Now import the appropriate module and run it
    if args.console:
        from leaf_console import main as console_main
        console_main()
    else:  # GUI mode
        try:
            from leaf_gui import main as gui_main
            gui_main()
        except ImportError as e:
            if "tkinter" in str(e):
                print("Error: tkinter is not installed. Please install tkinter.")
                print("Try running the console version with --console")
            else:
                print(f"Error importing GUI: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
