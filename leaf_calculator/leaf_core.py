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
            Hours needed to reach the target charge. Zero if already exactly
            at the target, and a negative value if the current charge is
            already above it -- callers should render that via
            ChargingTimeCalculator, which reports it as 'Already at target
            charge'. Returns infinity if the charging rate is not positive.

        Raises:
            ValueError: If target_percentage is not between 0 and 100, or if
                the charger's battery health or current charge are outside
                their valid ranges.
        """
        if not 0 <= target_percentage <= 100:
            raise ValueError('Target percentage must be between 0 and 100')
        if not 0 < self.battery_health <= 100:
            raise ValueError(
                'Battery health must be greater than 0 and at most 100'
            )
        if not 0 <= self.current_charge <= 100:
            raise ValueError('Current charge must be between 0 and 100')

        actual_capacity = self.battery_capacity * (self.battery_health / 100)
        current_energy = actual_capacity * (self.current_charge / 100)
        target_energy = actual_capacity * (target_percentage / 100)
        energy_needed = target_energy - current_energy

        if self.charging_rate <= 0:
            return float('inf')

        # Add 10% for charging inefficiency. Applied to the energy drawn, so
        # a negative result (already past target) stays negative and is
        # reported as such rather than being flattened to zero.
        energy_needed *= 1.1
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

        # Round to the nearest minute rather than truncating, so 59.94
        # minutes reads as '1 hour' instead of '59 minutes'. divmod carries
        # a rounded-up 60 into the hours column.
        hours_int, minutes = divmod(round(hours * 60), 60)
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
        if hours < 0:
            # Charging is already done; a past timestamp would be misleading.
            return 'Already at target charge'

        completion_time = start_time + timedelta(hours=hours)
        return completion_time.strftime('%Y-%m-%d %H:%M:%S')
