from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


class NissanLeafCharger:
    """Core calculator class for Nissan Leaf charging times."""

    CHARGING_RATES = {
        '1': ('Level 1 (120V)', 1.4),
        '2': ('Level 2 (240V) 3.3kW', 3.3),
        '3': ('Level 2 (240V) 6.6kW', 6.6)
    }

    BATTERY_CAPACITIES = {
        '1': ('40 kWh', 40),
        '2': ('62 kWh', 62)
    }


    def __init__(self):
        """Initialize the charger calculator with default values."""
        self.battery_capacity = 40  # Default to 40 kWh
        self.battery_health = 100  # Default to 100%
        self.current_charge = 0  # Default to 0%
        self.charging_rate = 6.6  # Default to 6.6kW
        self.start_time = datetime.now()

    def calculate_charging_time(self, target_percentage: float) -> float:
        """Calculate time needed to reach target charge level.

        Args:
          target_percentage: Target charge percentage (0-100)

        Returns:
          Float representing hours needed to reach target charge

        Raises:
          ValueError: If target_percentage is not between 0 and 100
        """
        if not (0 <= target_percentage <= 100):
            raise ValueError('Target percentage must be between 0 and 100')

        actual_capacity = self.battery_capacity * (self.battery_health / 100)
        current_energy = actual_capacity * (self.current_charge / 100)
        target_energy = actual_capacity * (target_percentage / 100)
        energy_needed = target_energy - current_energy

        if self.charging_rate <= 0:
            return float('inf')

        energy_needed *= 1.1  # Add 10% for charging inefficiency
        return energy_needed / self.charging_rate


class ConsoleInterface:
    """Console interface for the Nissan Leaf Charging Calculator."""

    def __init__(self):
        """Initialize the console interface."""
        self.charger = NissanLeafCharger()

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

    def display_menu(self, options: Dict[str, Tuple[str, float]], title: str) -> str:
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

    def format_time(self, hours: float) -> str:
        """Format time in hours to a readable string.

        Args:
          hours: Number of hours to format

        Returns:
          Formatted string representation of the time
        """
        if hours == float('inf'):
            return 'Invalid input'

        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)

        if hours_int == 0:
            return f'{minutes} minutes'
        elif minutes == 0:
            return f'{hours_int} hours'
        else:
            return f'{hours_int} hours {minutes} minutes'

    def calculate_completion_time(self, hours: float) -> str:
        """Calculate and format the completion time.

        Args:
          hours: Number of hours to add to start time

        Returns:
          Formatted string of completion time
        """
        if hours == float('inf'):
            return 'Invalid input'

        completion_time = self.charger.start_time + timedelta(hours=hours)
        return completion_time.strftime('%Y-%m-%d %H:%M:%S')

    def display_results(self):
        """Display charging time calculations."""
        print('\nCharging Time Estimates:')
        print('-' * 50)
        print(f'Start time: {self.charger.start_time.strftime("%Y-%m-%d %H:%M:%S")}')
        print('-' * 50)

        for target in [80, 100]:
            try:
                hours = self.charger.calculate_charging_time(target)
                duration = self.format_time(hours)
                completion = self.calculate_completion_time(hours)
                print(f'\nTo {target}% charge:')
                print(f'Duration: {duration}')
                print(f'Completion time: {completion}')
            except ValueError as e:
                print(f'\nError calculating {target}% charge: {e}')

    def run(self):
        """Run the main console interface loop."""
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

            elif choice == '1':
                battery_choice = self.display_menu(
                    NissanLeafCharger.BATTERY_CAPACITIES,
                    'Select Battery Capacity'
                )
                if battery_choice != 'q':
                    self.charger.battery_capacity = NissanLeafCharger.BATTERY_CAPACITIES[
                        battery_choice][1]

            elif choice == '2':
                rate_choice = self.display_menu(
                    NissanLeafCharger.CHARGING_RATES,
                    'Select Charging Rate'
                )
                if rate_choice != 'q':
                    self.charger.charging_rate = NissanLeafCharger.CHARGING_RATES[
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
                self.charger.start_time = datetime.now()
                print(f'\nStart time reset to: '
                      f'{self.charger.start_time.strftime("%Y-%m-%d %H:%M:%S")}')

            else:
                print('Invalid choice, please try again')

        print('\nThank you for using the Nissan Leaf Charging Calculator!')


def main():
    """Main entry point of the application."""
    console = ConsoleInterface()
    console.run()


if __name__ == '__main__':
    main()