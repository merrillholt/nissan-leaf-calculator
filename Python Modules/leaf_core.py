"""Core calculation module for Nissan Leaf charging times.

This module provides the core charging calculation logic and time formatting
utilities used by both GUI and console interfaces.
"""

from datetime import datetime, timedelta


class NissanLeafCharger:
    """Core calculator class for Nissan Leaf charging times.

    Attributes:
        CHARGING_RATES: Dict of charging rates in kW for different charging levels
        BATTERY_CAPACITIES: Dict of available battery capacities in kWh
    """

    CHARGING_RATES = {
        'Level 1 (120V)': 1.4,
        'Level 2 (240V) 3.3kW': 3.3,
        'Level 2 (240V) 6.6kW': 6.6
    }

    BATTERY_CAPACITIES = {
        '40 kWh': 40,
        '62 kWh': 62
    }

    def __init__(self):
        """Initialize the charger calculator with default values."""
        self.battery_capacity = 40.0  # Default to 40 kWh
        self.battery_health = 100.0  # Default to 100%
        self.current_charge = 0.0     # Default to 0%
        self.charging_rate = 6.6      # Default to 6.6kW

    def calculate_charging_time(self, target_percentage: float) -> float:
        """Calculate time needed to reach target charge level.

        Args:
            target_percentage: Target charge percentage (0-100)

        Returns:
            Float representing hours needed to reach target charge

        Raises:
            ValueError: If target_percentage is not between 0 and 100
        """
        if not 0 <= target_percentage <= 100:
            raise ValueError('Target percentage must be between 0 and 100')

        actual_capacity = self.battery_capacity * (self.battery_health / 100)
        current_energy = actual_capacity * (self.current_charge / 100)
        target_energy = actual_capacity * (target_percentage / 100)
        energy_needed = target_energy - current_energy

        if self.charging_rate <= 0:
            return float('inf')

        if energy_needed <= 0:
            return 0.0

        energy_needed *= 1.1  # Add 10% for charging inefficiency
        return energy_needed / self.charging_rate


class ChargingTimeCalculator:
    """Utility class for calculating and formatting charging times."""

    @staticmethod
    def format_time(hours: float) -> str:
        """Format time in hours to a readable string.

        Args:
            hours: Number of hours to format

        Returns:
            Formatted string representation of the time
        """
        if hours == float('inf'):
            return 'Invalid input'
        if hours < 0:
            return 'Already at target charge'

        hours_int = int(hours)
        minutes = int((hours - hours_int) * 60)
        h_unit = 'hour' if hours_int == 1 else 'hours'
        m_unit = 'minute' if minutes == 1 else 'minutes'

        if hours_int == 0:
            return f'{minutes} {m_unit}'
        if minutes == 0:
            return f'{hours_int} {h_unit}'
        return f'{hours_int} {h_unit} {minutes} {m_unit}'

    @staticmethod
    def calculate_completion_time(start_time: datetime, hours: float) -> str:
        """Calculate and format the completion time.

        Args:
            start_time: Starting datetime
            hours: Number of hours to add to start time

        Returns:
            Formatted string of completion time
        """
        if hours == float('inf'):
            return 'Invalid input'

        completion_time = start_time + timedelta(hours=hours)
        return completion_time.strftime('%Y-%m-%d %H:%M:%S')
