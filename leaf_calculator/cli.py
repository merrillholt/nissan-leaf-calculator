"""Command-line entry point for the Nissan Leaf Charging Calculator.

Parses arguments and either prints a one-shot estimate or launches the GUI,
console or web interface.
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional, Sequence

from .leaf_core import (
    PRESETS,
    NissanLeafCharger,
    summarize,
    validate_battery_capacity,
    validate_charging_rate,
    validate_current_charge,
    validate_battery_health,
    validate_target_percentage,
)
from .settings import load_battery_health, remember_battery_health

# Flags that describe the charge itself rather than which interface to run.
CHARGE_OPTIONS = ('battery', 'health', 'current', 'target', 'preset')


def _arg_type(validator, name: str):
    """Adapt a core validator for use as an argparse `type`.

    argparse reports a bare "invalid <function name> value" when a type
    callable raises ValueError, discarding the explanation. Re-raising as
    ArgumentTypeError makes it print the validator's own message instead.

    Args:
        validator: Validator from leaf_core.
        name: Name shown if argparse still needs to describe the type.

    Returns:
        A callable suitable for argparse's `type` parameter.
    """
    def convert(value):
        try:
            return validator(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc

    convert.__name__ = name
    return convert


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser.

    Returns:
        Parser covering interface selection and charge parameters.
    """
    parser = argparse.ArgumentParser(
        prog='nissan-leaf-calculator',
        description='Nissan Leaf Charging Calculator',
        epilog=(
            'Supplying any of --battery, --health, --current, --target or '
            '--preset prints an estimate and exits, with no prompts. '
            'Combine them with an interface flag to pre-populate it instead.'
        )
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        '--gui', '-g',
        action='store_true',
        help='Run the application in GUI mode (default)'
    )
    mode.add_argument(
        '--console', '-c',
        action='store_true',
        help='Run the application in console mode'
    )
    mode.add_argument(
        '--web', '-w',
        action='store_true',
        help='Run the application in web mode (Flask server)'
    )

    charge = parser.add_argument_group(
        'charge parameters',
        'Supply these to skip the prompts entirely.'
    )
    charge.add_argument(
        '--battery', '-b',
        type=_arg_type(validate_battery_capacity, 'capacity'),
        metavar='KWH',
        help='Battery capacity in kWh (' + ', '.join(
            f'{value:g}'
            for value in NissanLeafCharger.BATTERY_CAPACITIES.values()
        ) + ')'
    )
    charge.add_argument(
        '--health',
        type=_arg_type(validate_battery_health, 'percentage'),
        metavar='PCT',
        help='Battery health percentage, above 0 and up to 100. '
             'Remembered for future runs unless --no-save is given.'
    )
    charge.add_argument(
        '--current',
        type=_arg_type(validate_current_charge, 'percentage'),
        metavar='PCT',
        help='Current charge percentage, 0 to 100'
    )
    charge.add_argument(
        '--rate', '-r',
        type=_arg_type(validate_charging_rate, 'rate'),
        metavar='KW',
        help='Charging rate in kW (' + ', '.join(
            f'{value:g}'
            for value in NissanLeafCharger.CHARGING_RATES.values()
        ) + ')'
    )
    charge.add_argument(
        '--target', '-t',
        type=_arg_type(validate_target_percentage, 'percentage'),
        action='append',
        metavar='PCT',
        help='Target charge percentage; repeat for several targets '
             '(default: 80 and 100)'
    )
    charge.add_argument(
        '--preset', '-p',
        choices=sorted(PRESETS),
        # argparse runs help through %-formatting, so any literal percent
        # sign in a preset description has to be doubled or --help crashes.
        help=('Scenario preset setting rate and target: ' + '; '.join(
            f'{preset.key} = {preset.description}'
            for preset in PRESETS.values()
        )).replace('%', '%%')
    )
    charge.add_argument(
        '--no-save',
        action='store_true',
        help='Do not remember --health from this run, for one-off '
             'what-if queries'
    )
    charge.add_argument(
        '--no-taper',
        action='store_true',
        help='Assume a constant charging rate instead of modelling the '
             'slowdown the BMS applies as the pack fills'
    )

    return parser


def configure_charger(args: argparse.Namespace) -> NissanLeafCharger:
    """Build a charger from parsed arguments.

    The preset is applied first so that explicit flags override it.

    Args:
        args: Parsed command-line arguments.

    Returns:
        A configured NissanLeafCharger.
    """
    charger = NissanLeafCharger()
    charger.model_taper = not args.no_taper
    # Start from the remembered health so it applies to every interface.
    charger.battery_health = load_battery_health()

    if args.preset:
        charger.apply_preset(args.preset)

    if args.battery is not None:
        charger.battery_capacity = args.battery
    if args.health is not None:
        charger.battery_health = args.health
        if not args.no_save:
            problem = remember_battery_health(args.health)
            if problem:
                print(f'Warning: {problem}')
    if args.current is not None:
        charger.current_charge = args.current
    if args.rate is not None:
        charger.charging_rate = args.rate
    if args.target:
        charger.targets = list(args.target)

    return charger


def report(charger: NissanLeafCharger, start_time: datetime) -> None:
    """Print a one-shot estimate for the configured targets.

    Args:
        charger: Configured calculator.
        start_time: Timestamp the estimates are measured from.
    """
    print('Nissan Leaf Charging Calculator')
    print('-' * 52)
    print(f'Battery Capacity: {charger.battery_capacity:g} kWh')
    print(f'Battery Health:   {charger.battery_health:g}%')
    print(f'Current Charge:   {charger.current_charge:g}%')
    print(f'Charging Rate:    {charger.charging_rate:g} kW')
    print(f'Charge Taper:     {"modelled" if charger.model_taper else "ignored"}')
    print(f'Start time:       {start_time.strftime("%Y-%m-%d %H:%M:%S")}')
    print('-' * 52)

    for row in summarize(charger, start_time):
        print(f'\nTo {row["target"]:g}% charge:')
        if 'error' in row:
            print(f'Error: {row["error"]}')
            continue
        print(f'Duration:        {row["duration"]}')
        print(f'Completion time: {row["completion"]}')


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Parse arguments and launch the requested interface.

    Args:
        argv: Argument list, defaulting to sys.argv[1:].
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    charge_flags: List[str] = [
        name for name in CHARGE_OPTIONS if getattr(args, name, None)
    ]
    if args.rate is not None:
        charge_flags.append('rate')
    wants_interface = args.console or args.web or args.gui

    # Charge parameters with no interface requested means a one-shot report.
    if charge_flags and not wants_interface:
        report(configure_charger(args), datetime.now())
        return

    if args.console:
        # Deferred so a missing tkinter or Flask cannot break console mode.
        from .leaf_console import ConsoleInterface  # pylint: disable=import-outside-toplevel
        ConsoleInterface(configure_charger(args)).run()
    elif args.web:
        _run_web()
    else:
        _run_gui(args)


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


def _run_gui(args: argparse.Namespace) -> None:
    """Start the tkinter GUI, or explain why it cannot start.

    Args:
        args: Parsed arguments used to pre-populate the interface.
    """
    try:
        import tkinter as tk  # pylint: disable=import-outside-toplevel
        from .leaf_gui import NissanLeafGUI  # pylint: disable=import-outside-toplevel
    except ImportError as exc:
        if "tkinter" in str(exc):
            print("Error: tkinter is not installed. Please install tkinter.")
            print("Try running the console version with --console")
        else:
            print(f"Error importing GUI: {exc}")
        sys.exit(1)

    root = tk.Tk()
    NissanLeafGUI(root, configure_charger(args))
    root.mainloop()


if __name__ == "__main__":
    main()
