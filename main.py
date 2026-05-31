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
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Run the application in web mode (Flask server)"
    )

    args = parser.parse_args()

    # Count how many modes are specified
    modes_specified = sum([args.console, args.gui, args.web])

    # If multiple or none specified, default to GUI
    if modes_specified == 0 or modes_specified > 1:
        args.gui = True
        args.console = False
        args.web = False
    
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
    elif args.web:
        try:
            from leaf_web import app
            print("Starting Nissan Leaf Calculator web server...")
            print("Access the calculator at: http://localhost:5000")
            print("Press Ctrl+C to stop the server")
            app.run(host='127.0.0.1', port=5000, debug=False)
        except ImportError as e:
            if "flask" in str(e).lower():
                print("Error: Flask is not installed. Please install Flask.")
                print("Run: pip3 install Flask")
                print("Try running the console version with --console")
            else:
                print(f"Error importing web interface: {e}")
            sys.exit(1)
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
