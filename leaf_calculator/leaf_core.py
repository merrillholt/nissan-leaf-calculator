"""Core calculation module for Nissan Leaf charging times.

This module provides the core charging calculation logic, the shared input
validators used by every front end, the scenario presets, and time
formatting utilities.
"""

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, NamedTuple, Sequence, Tuple

# Targets reported when the caller has not asked for anything specific.
DEFAULT_TARGETS: Tuple[float, ...] = (80.0, 100.0)


class ChargingPreset(NamedTuple):
    """A named charging scenario.

    Attributes:
        key: Short identifier used on the command line.
        label: Human-readable name shown in the interfaces.
        charging_rate: Charging rate in kW.
        target: Target charge percentage.
        description: One-line explanation of when the preset applies.
    """

    key: str
    label: str
    charging_rate: float
    target: float
    description: str


PRESETS: Dict[str, ChargingPreset] = {
    'home': ChargingPreset(
        key='home',
        label='Home overnight',
        charging_rate=6.6,
        target=80.0,
        description='Level 2 at 6.6 kW to 80%, the usual overnight routine.'
    ),
    'work': ChargingPreset(
        key='work',
        label='Workplace top-up',
        charging_rate=3.3,
        target=100.0,
        description='Level 2 at 3.3 kW to 100% over a working day.'
    ),
}


def validate_in_range(
        value, minimum: float, maximum: float, label: str,
        exclusive_min: bool = False
) -> float:
    """Coerce a value to float and check it against an inclusive range.

    Shared by the console, GUI, web and command-line front ends so the
    accepted ranges are defined exactly once.

    Args:
        value: Value to validate; anything float() accepts.
        minimum: Lowest acceptable value.
        maximum: Highest acceptable value.
        label: Field name used in error messages, e.g. 'Battery health'.
        exclusive_min: If True, the minimum itself is rejected.

    Returns:
        The value as a float.

    Raises:
        ValueError: If the value is not numeric or is outside the range.
    """
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} must be a number') from exc

    if math.isnan(number) or math.isinf(number):
        raise ValueError(f'{label} must be a finite number')

    too_low = number <= minimum if exclusive_min else number < minimum
    if too_low or number > maximum:
        bound = 'greater than' if exclusive_min else 'at least'
        raise ValueError(
            f'{label} must be {bound} {minimum:g} and at most {maximum:g}'
        )
    return number


def validate_choice(
        value, allowed: Sequence[float], label: str, unit: str = ''
) -> float:
    """Coerce a value to float and check it against a set of allowed values.

    Args:
        value: Value to validate.
        allowed: The permitted values.
        label: Field name used in error messages.
        unit: Optional unit appended to the list in the error message.

    Returns:
        The value as a float.

    Raises:
        ValueError: If the value is not numeric or is not permitted.
    """
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{label} must be a number') from exc

    if number not in [float(option) for option in allowed]:
        options = ', '.join(f'{option:g}' for option in allowed)
        suffix = f' {unit}' if unit else ''
        raise ValueError(f'{label} must be one of: {options}{suffix}')
    return number


def validate_battery_health(value) -> float:
    """Validate a battery health percentage.

    Zero is rejected: a 0 kWh pack would otherwise report an instant charge.
    """
    return validate_in_range(
        value, 0, 100, 'Battery health', exclusive_min=True
    )


def validate_current_charge(value) -> float:
    """Validate a current charge percentage."""
    return validate_in_range(value, 0, 100, 'Current charge')


def validate_target_percentage(value) -> float:
    """Validate a target charge percentage."""
    return validate_in_range(value, 0, 100, 'Target percentage')


def validate_battery_capacity(value) -> float:
    """Validate a battery capacity against the supported packs."""
    return validate_choice(
        value,
        list(NissanLeafCharger.BATTERY_CAPACITIES.values()),
        'Battery capacity',
        'kWh'
    )


def validate_charging_rate(value) -> float:
    """Validate a charging rate against the supported levels."""
    return validate_choice(
        value,
        list(NissanLeafCharger.CHARGING_RATES.values()),
        'Charging rate',
        'kW'
    )


class NissanLeafCharger:
    """Core calculator class for Nissan Leaf charging times.

    Attributes:
        CHARGING_RATES: Dict of charging rates in kW for different levels
        BATTERY_CAPACITIES: Dict of available battery capacities in kWh
        INEFFICIENCY_FACTOR: Multiplier applied to the energy drawn
        TAPER_START_PERCENT: State of charge at which the pack starts to
            accept less than the full rate
        TAPER_END_RATE_FRACTION: Fraction of the full rate still accepted at
            100% state of charge
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

    INEFFICIENCY_FACTOR = 1.1

    # The BMS reduces current as the pack fills, so the last stretch takes
    # disproportionately longer. Modelled as a linear decline from the full
    # rate at TAPER_START_PERCENT to TAPER_END_RATE_FRACTION of it at 100%.
    # This is a simplification: the real curve also depends on temperature
    # and on whether the supply can saturate the pack at all (Level 1 rarely
    # can), but it tracks observed Leaf AC charging far better than assuming
    # a constant rate all the way to full.
    TAPER_START_PERCENT = 80.0
    TAPER_END_RATE_FRACTION = 0.25

    def __init__(self):
        """Initialize the charger calculator with default values."""
        self.battery_capacity = 40.0  # Default to 40 kWh
        self.battery_health = 100.0   # Default to 100%
        self.current_charge = 0.0     # Default to 0%
        self.charging_rate = 6.6      # Default to 6.6kW
        self.model_taper = True       # Account for the charge taper
        self.targets: List[float] = list(DEFAULT_TARGETS)

    def apply_preset(self, key: str) -> ChargingPreset:
        """Apply a named scenario preset.

        Sets the charging rate and the reported target. Battery capacity,
        health and current charge are left alone, since those describe the
        car rather than the scenario.

        Args:
            key: Preset identifier, e.g. 'home' or 'work'.

        Returns:
            The preset that was applied.

        Raises:
            ValueError: If the key is not a known preset.
        """
        try:
            preset = PRESETS[key.strip().lower()]
        except (AttributeError, KeyError) as exc:
            options = ', '.join(sorted(PRESETS))
            raise ValueError(
                f'Unknown preset {key!r}. Available presets: {options}'
            ) from exc

        self.charging_rate = preset.charging_rate
        self.targets = [preset.target]
        return preset

    def _charge_span_at_full_rate(self, start: float, end: float) -> float:
        """Integrate 1/taper(s) over a span of state of charge.

        Converts a span of real percentage points into the equivalent number
        of percentage points that would be covered at the full charging rate,
        which is what makes the taper show up as extra time.

        Args:
            start: Starting state of charge, must not exceed end.
            end: Ending state of charge.

        Returns:
            Equivalent percentage points at the full charging rate.
        """
        if not self.model_taper:
            return end - start

        taper_start = self.TAPER_START_PERCENT
        span = 0.0

        # Below the taper threshold the pack accepts the full rate.
        flat_end = min(end, taper_start)
        if flat_end > start:
            span += flat_end - start

        # Above it the rate declines linearly, so the time integral is
        # logarithmic: the integral of ds / (1 - k*(s - taper_start)).
        taper_begin = max(start, taper_start)
        if end > taper_begin:
            decline = (
                (1 - self.TAPER_END_RATE_FRACTION) / (100 - taper_start)
            )
            rate_at_begin = 1 - decline * (taper_begin - taper_start)
            rate_at_end = 1 - decline * (end - taper_start)
            span += math.log(rate_at_begin / rate_at_end) / decline

        return span

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
        target_percentage = validate_target_percentage(target_percentage)
        self.battery_health = validate_battery_health(self.battery_health)
        self.current_charge = validate_current_charge(self.current_charge)

        if self.charging_rate <= 0:
            return float('inf')

        actual_capacity = self.battery_capacity * (self.battery_health / 100)
        # Energy drawn from the wall per percentage point of pack filled.
        energy_per_percent = (
            actual_capacity / 100 * self.INEFFICIENCY_FACTOR
        )

        if target_percentage <= self.current_charge:
            # Already at or past the target. Report the shortfall linearly:
            # the taper curve is meaningless when running backwards, and the
            # sign is all the caller needs.
            span = target_percentage - self.current_charge
        else:
            span = self._charge_span_at_full_rate(
                self.current_charge, target_percentage
            )

        return energy_per_percent * span / self.charging_rate


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


def summarize(
        charger: NissanLeafCharger, start_time: datetime
) -> List[Dict[str, Any]]:
    """Build the per-target result rows shared by every interface.

    Args:
        charger: Configured calculator.
        start_time: Timestamp the estimates are measured from.

    Returns:
        One mapping per configured target, each with 'target', 'hours',
        'duration' and 'completion' keys. A target that cannot be computed
        carries an 'error' key instead of 'duration'/'completion'.
    """
    rows: List[Dict[str, Any]] = []
    for target in charger.targets:
        try:
            hours = charger.calculate_charging_time(target)
        except ValueError as exc:
            rows.append({'target': target, 'error': str(exc)})
            continue
        rows.append({
            'target': target,
            'hours': hours,
            'duration': ChargingTimeCalculator.format_time(hours),
            'completion': ChargingTimeCalculator.calculate_completion_time(
                start_time, hours
            ),
        })
    return rows
