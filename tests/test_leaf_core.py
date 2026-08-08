import pytest
from datetime import datetime, timedelta

from leaf_calculator.leaf_core import NissanLeafCharger, ChargingTimeCalculator


class TestNissanLeafCharger:
    """Test cases for the NissanLeafCharger class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.charger = NissanLeafCharger()

    def test_init_default_values(self):
        """Test that charger initializes with correct default values."""
        assert self.charger.battery_capacity == 40
        assert self.charger.battery_health == 100
        assert self.charger.current_charge == 0
        assert self.charger.charging_rate == 6.6

    def test_charging_rates_constant(self):
        """Test that charging rates are properly defined."""
        expected_rates = {
            'Level 1 (120V)': 1.4,
            'Level 2 (240V) 3.3kW': 3.3,
            'Level 2 (240V) 6.6kW': 6.6
        }
        assert self.charger.CHARGING_RATES == expected_rates

    def test_battery_capacities_constant(self):
        """Test that battery capacities are properly defined."""
        expected_capacities = {
            '40 kWh': 40,
            '62 kWh': 62
        }
        assert self.charger.BATTERY_CAPACITIES == expected_capacities

    def test_calculate_charging_time_basic(self):
        """Test basic charging time calculation."""
        # 40 kWh battery, 100% health, 0% current, 6.6kW rate to 80%
        # Expected: 40 * 0.8 * 1.1 / 6.6 = 5.33 hours
        result = self.charger.calculate_charging_time(80)
        expected = (40 * 0.8 * 1.1) / 6.6
        assert abs(result - expected) < 0.01

    def test_calculate_charging_time_partial_charge(self):
        """Test charging time calculation from partial charge."""
        self.charger.current_charge = 20
        # From 20% to 80% = 60% of 40kWh = 24kWh * 1.1 / 6.6
        result = self.charger.calculate_charging_time(80)
        expected = (40 * 0.6 * 1.1) / 6.6
        assert abs(result - expected) < 0.01

    def test_calculate_charging_time_degraded_battery(self):
        """Test charging time with degraded battery health."""
        self.charger.battery_health = 80
        # 40 kWh * 0.8 health * 0.8 target * 1.1 / 6.6
        result = self.charger.calculate_charging_time(80)
        expected = (40 * 0.8 * 0.8 * 1.1) / 6.6
        assert abs(result - expected) < 0.01

    def test_calculate_charging_time_different_battery_size(self):
        """Test charging time with 62 kWh battery."""
        self.charger.battery_capacity = 62
        result = self.charger.calculate_charging_time(80)
        expected = (62 * 0.8 * 1.1) / 6.6
        assert abs(result - expected) < 0.01

    def test_calculate_charging_time_different_charging_rate(self):
        """Test charging time with different charging rate."""
        self.charger.charging_rate = 3.3
        result = self.charger.calculate_charging_time(80)
        expected = (40 * 0.8 * 1.1) / 3.3
        assert abs(result - expected) < 0.01

    def test_calculate_charging_time_same_as_current(self):
        """Test charging time when target equals current charge."""
        self.charger.current_charge = 50
        result = self.charger.calculate_charging_time(50)
        assert result == 0

    def test_calculate_charging_time_lower_than_current(self):
        """Target below current charge returns a negative duration.

        The value is deliberately not clamped to zero so that callers can
        distinguish 'already past the target' from 'exactly at the target'.
        """
        self.charger.current_charge = 80
        result = self.charger.calculate_charging_time(50)
        assert result < 0

    def test_already_past_target_is_reported_not_flattened(self):
        """A target below current charge surfaces as a message, not 0 minutes."""
        self.charger.current_charge = 90
        hours = self.charger.calculate_charging_time(80)
        assert ChargingTimeCalculator.format_time(hours) == \
            'Already at target charge'
        assert ChargingTimeCalculator.calculate_completion_time(
            datetime(2023, 1, 1, 10, 0, 0), hours
        ) == 'Already at target charge'

    def test_calculate_charging_time_zero_health_raises(self):
        """Zero battery health is rejected rather than reporting 0 minutes."""
        self.charger.battery_health = 0
        with pytest.raises(ValueError, match='Battery health must be'):
            self.charger.calculate_charging_time(100)

    def test_calculate_charging_time_negative_health_raises(self):
        """Negative battery health raises ValueError."""
        self.charger.battery_health = -5
        with pytest.raises(ValueError, match='Battery health must be'):
            self.charger.calculate_charging_time(100)

    def test_calculate_charging_time_health_above_100_raises(self):
        """Battery health above 100% raises ValueError."""
        self.charger.battery_health = 101
        with pytest.raises(ValueError, match='Battery health must be'):
            self.charger.calculate_charging_time(100)

    def test_calculate_charging_time_invalid_current_charge_raises(self):
        """Current charge outside 0-100 raises ValueError."""
        self.charger.current_charge = 150
        with pytest.raises(ValueError, match='Current charge must be'):
            self.charger.calculate_charging_time(100)

    def test_calculate_charging_time_zero_rate(self):
        """Test charging time with zero charging rate."""
        self.charger.charging_rate = 0
        result = self.charger.calculate_charging_time(80)
        assert result == float('inf')

    def test_calculate_charging_time_negative_rate(self):
        """Test charging time with negative charging rate."""
        self.charger.charging_rate = -1
        result = self.charger.calculate_charging_time(80)
        assert result == float('inf')

    def test_calculate_charging_time_invalid_target_high(self):
        """Test that invalid high target percentage raises ValueError."""
        with pytest.raises(ValueError, match='Target percentage must be between 0 and 100'):
            self.charger.calculate_charging_time(101)

    def test_calculate_charging_time_invalid_target_low(self):
        """Test that invalid low target percentage raises ValueError."""
        with pytest.raises(ValueError, match='Target percentage must be between 0 and 100'):
            self.charger.calculate_charging_time(-1)

    def test_calculate_charging_time_boundary_values(self):
        """Test charging time calculation with boundary values."""
        # Test 0% target
        result = self.charger.calculate_charging_time(0)
        assert result == 0

        # Test 100% target
        result = self.charger.calculate_charging_time(100)
        expected = (40 * 1.0 * 1.1) / 6.6
        assert abs(result - expected) < 0.01

    def test_charging_inefficiency_factor(self):
        """Test that 10% inefficiency factor is applied."""
        # Calculate without inefficiency
        energy_needed = 40 * 0.8  # 80% of 40kWh
        time_without_inefficiency = energy_needed / 6.6

        # Calculate with inefficiency (actual method)
        time_with_inefficiency = self.charger.calculate_charging_time(80)

        # Should be 10% more time due to inefficiency
        assert abs(time_with_inefficiency - (time_without_inefficiency * 1.1)) < 0.01


class TestChargingTimeCalculator:
    """Test cases for the ChargingTimeCalculator class."""

    def test_format_time_minutes_only(self):
        """Test formatting time when less than 1 hour."""
        result = ChargingTimeCalculator.format_time(0.5)  # 30 minutes
        assert result == "30 minutes"

    def test_format_time_hours_only(self):
        """Test formatting time when exact hours."""
        result = ChargingTimeCalculator.format_time(2.0)
        assert result == "2 hours"

    def test_format_time_hours_and_minutes(self):
        """Test formatting time with both hours and minutes."""
        result = ChargingTimeCalculator.format_time(2.75)  # 2 hours 45 minutes
        assert result == "2 hours 45 minutes"

    def test_format_time_single_hour(self):
        """Test formatting time with single hour."""
        result = ChargingTimeCalculator.format_time(1.0)
        assert result == "1 hour"

    def test_format_time_single_minute(self):
        """Test formatting time with single minute."""
        result = ChargingTimeCalculator.format_time(1/60)  # 1 minute
        assert result == "1 minute"

    def test_format_time_zero(self):
        """Test formatting zero time."""
        result = ChargingTimeCalculator.format_time(0)
        assert result == "0 minutes"

    def test_format_time_infinity(self):
        """Test formatting infinite time."""
        result = ChargingTimeCalculator.format_time(float('inf'))
        assert result == "Invalid input"

    def test_format_time_negative(self):
        """Test formatting negative time returns already-at-target message."""
        result = ChargingTimeCalculator.format_time(-1.5)
        assert result == "Already at target charge"

    def test_format_time_rounding(self):
        """Test that minutes are properly rounded."""
        result = ChargingTimeCalculator.format_time(1.99)  # 1 hour 59.4 minutes
        assert result == "1 hour 59 minutes"

    def test_format_time_rounds_up_rather_than_truncating(self):
        """59.94 minutes reads as 1 hour, not 59 minutes."""
        result = ChargingTimeCalculator.format_time(0.999)
        assert result == "1 hour"

    def test_format_time_rounding_carries_into_hours(self):
        """A minute value that rounds to 60 carries into the hours column."""
        result = ChargingTimeCalculator.format_time(2.9999)
        assert result == "3 hours"

    def test_calculate_completion_time_normal(self):
        """Test completion time calculation."""
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        hours = 2.5
        result = ChargingTimeCalculator.calculate_completion_time(start_time, hours)
        expected = "2023-01-01 12:30:00"
        assert result == expected

    def test_calculate_completion_time_overnight(self):
        """Test completion time calculation overnight."""
        start_time = datetime(2023, 1, 1, 23, 0, 0)
        hours = 2
        result = ChargingTimeCalculator.calculate_completion_time(start_time, hours)
        expected = "2023-01-02 01:00:00"
        assert result == expected

    def test_calculate_completion_time_infinity(self):
        """Test completion time calculation with infinite hours."""
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        hours = float('inf')
        result = ChargingTimeCalculator.calculate_completion_time(start_time, hours)
        assert result == "Invalid input"

    def test_calculate_completion_time_fractional_seconds(self):
        """Test completion time calculation with fractional hours."""
        start_time = datetime(2023, 1, 1, 10, 0, 0)
        hours = 1.50833333  # 1 hour 30 minutes 30 seconds (more precise)
        result = ChargingTimeCalculator.calculate_completion_time(start_time, hours)
        # Allow for rounding differences in seconds
        assert "2023-01-01 11:30:" in result
        assert result.startswith("2023-01-01 11:30:")