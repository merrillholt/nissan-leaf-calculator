"""Console interface for Nissan Leaf Charging Calculator.

This module provides a text-based console interface for calculating
Nissan Leaf charging times with interactive menus.
"""

from datetime import datetime
from typing import Mapping, Optional, Tuple, Union

from .leaf_core import NissanLeafCharger, ChargingTimeCalculator


class ConsoleInterface:
    """Console interface for the Nissan Leaf Charging Calculator."""

    def __init__(self):
        """Initialize the console interface."""
        self.charger = NissanLeafCharger()
        self.start_time = datetime.now()

    def get_valid_number(
            self, prompt: str, min_val: float, max_val: float
    ) -> Optional[float]:
        """Get a valid number input from the user.

        Args:
            prompt: The prompt to display to the user
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value

        Returns:
            Float value or None if user wants to quit
        """
        while True:
            value = input(prompt).strip().lower()
            if value == 'q':
                return None

            try:
                num = float(value)
                if min_val <= num <= max_val:
                    return num
                print(
                    f'Please enter a number between {min_val} and {max_val}'
                )
            except ValueError:
                print('Please enter a valid number')

    def display_menu(
            self, options: Mapping[str, Tuple[str, Union[int, float]]], title: str
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

        for target in [80, 100]:
            try:
                hours = self.charger.calculate_charging_time(target)
                duration = ChargingTimeCalculator.format_time(hours)
                completion = ChargingTimeCalculator.calculate_completion_time(
                    self.start_time, hours
                )
                print(f'\nTo {target}% charge:')
                print(f'Duration: {duration}')
                print(f'Completion time: {completion}')
            except ValueError as e:
                print(f'\nError calculating {target}% charge: {e}')

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
            for i, (name, capacity) in enumerate(self.charger.BATTERY_CAPACITIES.items())
        }

        print('Nissan Leaf Charging Calculator')
        print('Enter "q" at any prompt to return to the main menu')

        while True:
            print('\nCurrent Settings:')
            print('-' * 50)
            print(f'Battery Capacity: {self.charger.battery_capacity} kWh')
            print(f'Charging Rate: {self.charger.charging_rate} kW')
            print(f'Battery Health: {self.charger.battery_health}%')
            print(f'Current Charge: {self.charger.current_charge}%')
            print('-' * 50)

            print('\nOptions:')
            print('1. Set Battery Capacity')
            print('2. Set Charging Rate')
            print('3. Set Battery Health')
            print('4. Set Current Charge')
            print('5. Calculate Charging Times')
            print('6. Reset Start Time')
            print('q. Quit')

            choice = input('\nEnter your choice: ').strip().lower()

            if choice == 'q':
                break

            if choice == '1':
                battery_choice = self.display_menu(
                    battery_capacities,
                    'Select Battery Capacity'
                )
                if battery_choice != 'q':
                    self.charger.battery_capacity = battery_capacities[
                        battery_choice][1]

            elif choice == '2':
                rate_choice = self.display_menu(
                    charging_rates,
                    'Select Charging Rate'
                )
                if rate_choice != 'q':
                    self.charger.charging_rate = charging_rates[
                        rate_choice][1]

            elif choice == '3':
                health = self.get_valid_number(
                    'Enter battery health percentage (0-100): ',
                    0,
                    100
                )
                if health is not None:
                    self.charger.battery_health = health

            elif choice == '4':
                charge = self.get_valid_number(
                    'Enter current charge percentage (0-100): ',
                    0,
                    100
                )
                if charge is not None:
                    self.charger.current_charge = charge

            elif choice == '5':
                self.display_results()

            elif choice == '6':
                self.start_time = datetime.now()
                print(f'\nStart time reset to: '
                      f'{self.start_time.strftime("%Y-%m-%d %H:%M:%S")}')

            else:
                print('Invalid choice, please try again')

        print('\nThank you for using the Nissan Leaf Charging Calculator!')


def main():
    """Main entry point of the application."""
    console = ConsoleInterface()
    console.run()


if __name__ == '__main__':
    main()
