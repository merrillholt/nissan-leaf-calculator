"""Command-line entry point for the Nissan Leaf Charging Calculator.

Parses arguments and launches the GUI, console or web interface.
"""

import argparse
import sys


def main() -> None:
    """Parse arguments and launch the requested interface."""
    parser = argparse.ArgumentParser(
        description="Nissan Leaf Charging Calculator"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--gui", "-g",
        action="store_true",
        help="Run the application in GUI mode (default)"
    )
    mode.add_argument(
        "--console", "-c",
        action="store_true",
        help="Run the application in console mode"
    )
    mode.add_argument(
        "--web", "-w",
        action="store_true",
        help="Run the application in web mode (Flask server)"
    )

    args = parser.parse_args()

    if args.console:
        # Deferred so a missing tkinter or Flask cannot break console mode.
        from .leaf_console import main as console_main  # pylint: disable=import-outside-toplevel
        console_main()
    elif args.web:
        _run_web()
    else:
        _run_gui()


def _run_web() -> None:
    """Start the Flask development server, or explain why it cannot start."""
    try:
        from .leaf_web import app  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        if "flask" in str(exc).lower():
            print("Error: Flask is not installed. Please install Flask.")
            print("Run: pip install Flask")
            print("Try running the console version with --console")
        else:
            print(f"Error importing web interface: {exc}")
        sys.exit(1)

    print("Starting Nissan Leaf Calculator web server...")
    print("Access the calculator at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    app.run(host='127.0.0.1', port=5000, debug=False)


def _run_gui() -> None:
    """Start the tkinter GUI, or explain why it cannot start."""
    try:
        from .leaf_gui import main as gui_main  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        if "tkinter" in str(exc):
            print("Error: tkinter is not installed. Please install tkinter.")
            print("Try running the console version with --console")
        else:
            print(f"Error importing GUI: {exc}")
        sys.exit(1)

    gui_main()


if __name__ == "__main__":
    main()
