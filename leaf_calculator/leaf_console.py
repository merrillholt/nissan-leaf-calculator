"""Console interface for Nissan Leaf Charging Calculator.

This module provides a text-based console interface for calculating
Nissan Leaf charging times with interactive menus.
"""

from datetime import datetime
from typing import Callable, Mapping, Optional, Tuple, Union

from .leaf_core import (
    DEFAULT_TARGETS,
    PRESETS,
    NissanLeafCharger,
    summarize,
    validate_battery_health,
    validate_current_charge,
    validate_target_percentage,
)


class ConsoleInterface:
    """Console interface for the Nissan Leaf Charging Calculator."""

    def __init__(self, charger: Optional[NissanLeafCharger] = None):
        """Initialize the console interface.

        Args:
            charger: Pre-configured calculator, e.g. one built from
                command-line flags. A default one is created if omitted.
        """
        self.charger = charger if charger is not None else NissanLeafCharger()
        self.start_time = datetime.now()

    def get_valid_number(
            self, prompt: str, validator: Callable[[object], float]
    ) -> Optional[float]:
        """Get a valid number input from the user.

        Args:
            prompt: The prompt to display to the user
            validator: Shared validator from leaf_core that returns the
                parsed value or raises ValueError with a usable message

        Returns:
            Float value or None if user wants to quit
        """
        while True:
            value = input(prompt).strip().lower()
            if value == 'q':
                return None

            try:
                return validator(value)
            except ValueError as exc:
                print(exc)

    def display_menu(
            self, options: Mapping[str, Tuple[str, Union[int, float, str]]],
            title: str
    ) -> str:
        """Display a menu and get user selection.

        Args:
            options: Dictionary of options with descriptions and values
            title: Title of the menu

        Returns:
            Selected option key
        """
        while True:
            print(f'\n{title}:')
            for key, (desc, _) in options.items():
                print(f'{key}. {desc}')
            print('q. Return to main menu')

            choice = input('Enter your choice: ').strip().lower()
            if choice in options or choice == 'q':
                return choice
            print('Invalid choice, please try again')

    def display_results(self):
        """Display charging time calculations."""
        self.start_time = datetime.now()
        print('\nCharging Time Estimates:')
        print('-' * 50)
        print(f'Start time: {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print('-' * 50)

        for row in summarize(self.charger, self.start_time):
            print(f'\nTo {row["target"]:g}% charge:')
            if 'error' in row:
                print(f'Error: {row["error"]}')
                continue
            print(f'Duration: {row["duration"]}')
            print(f'Completion time: {row["completion"]}')

    def _targets_summary(self) -> str:
        """Return the configured targets as a readable string."""
        return ', '.join(f'{target:g}%' for target in self.charger.targets)

    def _choose_preset(self):
        """Prompt for a scenario preset and apply it."""
        presets = {
            str(index + 1): (f'{preset.label} -- {preset.description}',
                             preset.key)
            for index, preset in enumerate(PRESETS.values())
        }
        choice = self.display_menu(presets, 'Select Scenario Preset')
        if choice == 'q':
            return
        preset = self.charger.apply_preset(presets[choice][1])
        print(f'\nApplied "{preset.label}": '
              f'{preset.charging_rate:g} kW to {preset.target:g}%')

    def _set_targets(self):
        """Prompt for the target charge levels to report."""
        print(f'\nCurrent targets: {self._targets_summary()}')
        print('Enter targets separated by commas, blank for the default '
              f'({", ".join(f"{t:g}%" for t in DEFAULT_TARGETS)}), '
              'or q to cancel.')
        raw = input('Targets: ').strip().lower()
        if raw == 'q':
            return
        if not raw:
            self.charger.targets = list(DEFAULT_TARGETS)
            print(f'Targets reset to {self._targets_summary()}')
            return

        try:
            targets = [
                validate_target_percentage(part)
                for part in raw.split(',') if part.strip()
            ]
        except ValueError as exc:
            print(exc)
            return

        if not targets:
            print('No targets entered')
            return

        self.charger.targets = targets
        print(f'Targets set to {self._targets_summary()}')

    def run(self):
        """Run the main console interface loop."""
        # Convert charging rates to format expected by display_menu
        charging_rates = {
            str(i+1): (name, rate)
            for i, (name, rate) in enumerate(self.charger.CHARGING_RATES.items())
        }

        # Convert battery capacities to format expected by display_menu
        battery_capacities = {
            str(i+1): (name, capacity)
            for i, (name, capacity) in enumerate(
                self.charger.BATTERY_CAPACITIES.items())
        }

        print('Nissan Leaf Charging Calculator')
        print('Enter "q" at any prompt to return to the main menu')

        actions = {
            '1': lambda: self._pick(
                battery_capacities, 'Select Battery Capacity',
                'battery_capacity'),
            '2': lambda: self._pick(
                charging_rates, 'Select Charging Rate', 'charging_rate'),
            '3': lambda: self._prompt(
                'Enter battery health percentage (0-100): ',
                validate_battery_health, 'battery_health'),
            '4': lambda: self._prompt(
                'Enter current charge percentage (0-100): ',
                validate_current_charge, 'current_charge'),
            '5': self._choose_preset,
            '6': self._set_targets,
            '7': self.display_results,
            '8': self._reset_start_time,
        }

        while True:
            self._print_settings()
            choice = input('\nEnter your choice: ').strip().lower()

            if choice == 'q':
                break

            action = actions.get(choice)
            if action is None:
                print('Invalid choice, please try again')
            else:
                action()

        print('\nThank you for using the Nissan Leaf Charging Calculator!')

    def _print_settings(self):
        """Print the current settings and the main menu."""
        print('\nCurrent Settings:')
        print('-' * 50)
        print(f'Battery Capacity: {self.charger.battery_capacity:g} kWh')
        print(f'Charging Rate: {self.charger.charging_rate:g} kW')
        print(f'Battery Health: {self.charger.battery_health:g}%')
        print(f'Current Charge: {self.charger.current_charge:g}%')
        print(f'Targets: {self._targets_summary()}')
        print('-' * 50)

        print('\nOptions:')
        print('1. Set Battery Capacity')
        print('2. Set Charging Rate')
        print('3. Set Battery Health')
        print('4. Set Current Charge')
        print('5. Apply Scenario Preset')
        print('6. Set Target Charge Levels')
        print('7. Calculate Charging Times')
        print('8. Reset Start Time')
        print('q. Quit')

    def _pick(self, options, title, attribute):
        """Show a menu and assign the chosen value to a charger attribute."""
        choice = self.display_menu(options, title)
        if choice != 'q':
            setattr(self.charger, attribute, options[choice][1])

    def _prompt(self, prompt, validator, attribute):
        """Prompt for a validated number and assign it to the charger."""
        value = self.get_valid_number(prompt, validator)
        if value is not None:
            setattr(self.charger, attribute, value)

    def _reset_start_time(self):
        """Reset the reference time used for completion estimates."""
        self.start_time = datetime.now()
        print(f'\nStart time reset to: '
              f'{self.start_time.strftime("%Y-%m-%d %H:%M:%S")}')


def main():
    """Main entry point of the application."""
    console = ConsoleInterface()
    console.run()


if __name__ == '__main__':
    main()
