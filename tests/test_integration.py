import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

from leaf_calculator.leaf_core import NissanLeafCharger, ChargingTimeCalculator


class TestIntegration:
    """Integration tests for the complete charging calculator system."""

    def test_end_to_end_calculation_scenario_1(self):
        """Test complete calculation scenario: Home overnight charging."""
        charger = NissanLeafCharger()
        calculator = ChargingTimeCalculator()

        # Scenario: 40kWh battery, 85% health, currently at 25%, charge to 80% at 6.6kW
        charger.battery_capacity = 40
        charger.battery_health = 85
        charger.current_charge = 25
        charger.charging_rate = 6.6

        # Calculate charging time
        time_to_80 = charger.calculate_charging_time(80)
        formatted_time = calculator.format_time(time_to_80)

        # Verify reasonable results
        assert 0 < time_to_80 < 10  # Should be between 0 and 10 hours
        assert "hours" in formatted_time or "minutes" in formatted_time

        # Calculate specific expected value
        # (40 * 0.85 * (0.80 - 0.25) * 1.1) / 6.6 ≈ 3.07 hours
        expected_time = (40 * 0.85 * 0.55 * 1.1) / 6.6
        assert abs(time_to_80 - expected_time) < 0.01

    def test_end_to_end_calculation_scenario_2(self):
        """Test complete calculation scenario: Workplace top-up."""
        charger = NissanLeafCharger()
        calculator = ChargingTimeCalculator()

        # Scenario: 62kWh battery, 95% health, currently at 60%, charge to 100% at 3.3kW
        charger.battery_capacity = 62
        charger.battery_health = 95
        charger.current_charge = 60
        charger.charging_rate = 3.3

        # Calculate charging time
        time_to_100 = charger.calculate_charging_time(100)
        formatted_time = calculator.format_time(time_to_100)

        # Verify reasonable results
        assert 0 < time_to_100 < 15  # Should be between 0 and 15 hours
        assert "hours" in formatted_time

        # The constant-rate figure, which the taper model must exceed since
        # this scenario charges well past the 80% taper threshold.
        flat_time = (62 * 0.95 * 0.40 * 1.1) / 3.3
        assert time_to_100 > flat_time

        charger.model_taper = False
        assert abs(charger.calculate_charging_time(100) - flat_time) < 0.01

    def test_end_to_end_calculation_scenario_3(self):
        """Test complete calculation scenario: Emergency charge."""
        charger = NissanLeafCharger()
        calculator = ChargingTimeCalculator()

        # Scenario: 40kWh battery, 70% health, currently at 5%, charge to 80% at 1.4kW (Level 1)
        charger.battery_capacity = 40
        charger.battery_health = 70
        charger.current_charge = 5
        charger.charging_rate = 1.4

        # Calculate charging time
        time_to_80 = charger.calculate_charging_time(80)
        formatted_time = calculator.format_time(time_to_80)

        # Verify reasonable results for slow charging
        assert 10 < time_to_80 < 30  # Should be longer due to Level 1 charging
        assert "hours" in formatted_time

        # Calculate specific expected value
        # (40 * 0.70 * (0.80 - 0.05) * 1.1) / 1.4 ≈ 16.5 hours
        expected_time = (40 * 0.70 * 0.75 * 1.1) / 1.4
        assert abs(time_to_80 - expected_time) < 0.01

    def test_consistency_between_modules(self):
        """Test that different modules produce consistent results."""
        # Test with core module
        charger1 = NissanLeafCharger()
        charger1.battery_capacity = 40
        charger1.battery_health = 90
        charger1.current_charge = 30
        charger1.charging_rate = 6.6

        result1 = charger1.calculate_charging_time(80)

        # Create another instance and verify same results
        charger2 = NissanLeafCharger()
        charger2.battery_capacity = 40
        charger2.battery_health = 90
        charger2.current_charge = 30
        charger2.charging_rate = 6.6

        result2 = charger2.calculate_charging_time(80)

        assert result1 == result2

    def test_realistic_charging_curves(self):
        """Test realistic charging scenarios and validate against expected curves."""
        charger = NissanLeafCharger()
        charger.battery_capacity = 40
        charger.battery_health = 100
        charger.charging_rate = 6.6

        # Test charging from different starting points to 80%
        start_points = [0, 10, 20, 30, 40, 50, 60, 70]
        times = []

        for start in start_points:
            charger.current_charge = start
            time = charger.calculate_charging_time(80)
            times.append(time)

        # Verify that charging time decreases as starting point increases
        for i in range(1, len(times)):
            assert times[i] < times[i-1], f"Time should decrease: {times[i]} >= {times[i-1]}"

        # Verify specific calculation for 0% to 80%
        charger.current_charge = 0
        full_charge_time = charger.calculate_charging_time(80)
        expected = (40 * 0.8 * 1.1) / 6.6  # 5.33 hours
        assert abs(full_charge_time - expected) < 0.01

    def test_edge_cases_comprehensive(self):
        """Test comprehensive edge cases across the system."""
        charger = NissanLeafCharger()
        calculator = ChargingTimeCalculator()

        # Test with minimum battery health
        charger.battery_health = 1
        charger.current_charge = 0
        charger.charging_rate = 6.6
        time = charger.calculate_charging_time(50)
        assert time > 0
        formatted = calculator.format_time(time)
        assert formatted != "Invalid input"

        # Test with maximum current charge
        charger.battery_health = 100
        charger.current_charge = 99
        time = charger.calculate_charging_time(100)
        assert time < 1  # Should be very short

        # Test with minimum charging rate
        charger.current_charge = 0
        charger.charging_rate = 0.1
        time = charger.calculate_charging_time(80)
        assert time > 100  # Should take very long

    def test_main_entry_point_runs(self):
        """`python main.py --help` works from a source checkout.

        Runs it for real rather than just loading the spec, so the whole
        import chain through leaf_calculator.cli is exercised.
        """
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "Nissan Leaf Charging Calculator" in result.stdout
        for flag in ("--gui", "--console", "--web"):
            assert flag in result.stdout

    def test_main_rejects_conflicting_modes(self):
        """Two interface flags is an error, not a silent fallback to GUI."""
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "main.py", "--console", "--web"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0
        assert "not allowed with" in result.stderr

    def test_package_console_script_entry_point(self):
        """The module entry point matches what [project.scripts] points at."""
        result = subprocess.run(
            [sys.executable, "-c",
             "from leaf_calculator.cli import main; print(callable(main))"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "True"

    def test_calculation_precision(self):
        """Test calculation precision and floating point handling."""
        charger = NissanLeafCharger()

        # Test with values that might cause floating point precision issues
        charger.battery_capacity = 40.1
        charger.battery_health = 99.9
        charger.current_charge = 33.3
        charger.charging_rate = 6.66

        result = charger.calculate_charging_time(77.7)

        # Should get a reasonable result without floating point errors
        assert result > 0
        assert result < 100
        assert not (result != result)  # Check for NaN

        # Test consistency with repeated calculations
        result2 = charger.calculate_charging_time(77.7)
        assert result == result2

    def test_system_robustness(self):
        """Test system robustness with various input combinations."""
        charger = NissanLeafCharger()
        calculator = ChargingTimeCalculator()

        # Test combinations of all supported battery sizes and charging rates
        battery_sizes = [40, 62]
        charging_rates = [1.4, 3.3, 6.6]
        health_levels = [50, 75, 100]

        for battery in battery_sizes:
            for rate in charging_rates:
                for health in health_levels:
                    charger.battery_capacity = battery
                    charger.charging_rate = rate
                    charger.battery_health = health
                    charger.current_charge = 25

                    # Should work for all combinations
                    time_80 = charger.calculate_charging_time(80)
                    time_100 = charger.calculate_charging_time(100)

                    assert time_80 > 0
                    assert time_100 > time_80

                    # Should format properly
                    formatted_80 = calculator.format_time(time_80)
                    formatted_100 = calculator.format_time(time_100)

                    assert formatted_80 != "Invalid input"
                    assert formatted_100 != "Invalid input"