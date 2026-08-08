import pytest
import sys
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the Python Modules directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "Python Modules"))

try:
    from leaf_gui import NissanLeafGUI
except ImportError:
    # Skip GUI tests if tkinter is not available
    pytest.skip("tkinter not available", allow_module_level=True)


class TestNissanLeafGUI:
    """Test cases for the NissanLeafGUI class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during testing
        self.gui = NissanLeafGUI(self.root)

    def teardown_method(self):
        """Clean up after each test method."""
        if self.root:
            self.root.destroy()

    def test_init(self):
        """Test GUI initialization."""
        assert self.gui.root is not None
        assert self.gui.charger is not None
        assert self.gui.start_time is not None
        assert hasattr(self.gui, 'battery_var')
        assert hasattr(self.gui, 'health_var')
        assert hasattr(self.gui, 'current_var')
        assert hasattr(self.gui, 'charging_var')

    def test_initial_values(self):
        """Test initial variable values."""
        assert self.gui.battery_var.get() == "40 kWh"
        assert self.gui.health_var.get() == "100"
        assert self.gui.current_var.get() == "0"
        assert self.gui.charging_var.get() == "Level 2 (240V) 6.6kW"

    def test_validate_number_valid(self):
        """Test validate_number with valid input."""
        result = self.gui.validate_number("50.5")
        assert result == 50.5

    def test_validate_number_zero(self):
        """Test validate_number with zero."""
        result = self.gui.validate_number("0")
        assert result == 0.0

    def test_validate_number_negative(self):
        """Test validate_number with negative number."""
        result = self.gui.validate_number("-10")
        assert result == -10.0

    def test_validate_number_invalid(self):
        """Test validate_number with invalid input."""
        result = self.gui.validate_number("abc")
        assert result == 0.0

    def test_validate_number_empty(self):
        """Test validate_number with empty string."""
        result = self.gui.validate_number("")
        assert result == 0.0

    def test_update_calculations(self):
        """Test update_calculations method."""
        # Set test values
        self.gui.battery_var.set("62 kWh")
        self.gui.health_var.set("85")
        self.gui.current_var.set("30")
        self.gui.charging_var.set("Level 2 (240V) 3.3kW")

        # Update calculations
        self.gui.update_calculations()

        # Verify charger was updated
        assert self.gui.charger.battery_capacity == 62
        assert self.gui.charger.battery_health == 85
        assert self.gui.charger.current_charge == 30
        assert self.gui.charger.charging_rate == 3.3

    def test_validate_and_update_out_of_range_high(self):
        """Test validate_and_update with value > 100."""
        self.gui.health_var.set("150")
        self.gui.validate_and_update()
        # Should reset to default value
        assert self.gui.health_var.get() == "100"

    def test_validate_and_update_out_of_range_low(self):
        """Test validate_and_update with value < 0."""
        self.gui.current_var.set("-10")
        self.gui.validate_and_update()
        # Should reset to default value
        assert self.gui.current_var.get() == "0"

    def test_battery_capacity_mapping(self):
        """Test battery capacity string to value mapping."""
        self.gui.battery_var.set("40 kWh")
        self.gui.update_calculations()
        assert self.gui.charger.battery_capacity == 40

        self.gui.battery_var.set("62 kWh")
        self.gui.update_calculations()
        assert self.gui.charger.battery_capacity == 62

    def test_charging_rate_mapping(self):
        """Test charging rate string to value mapping."""
        self.gui.charging_var.set("Level 1 (120V)")
        self.gui.update_calculations()
        assert self.gui.charger.charging_rate == 1.4

        self.gui.charging_var.set("Level 2 (240V) 3.3kW")
        self.gui.update_calculations()
        assert self.gui.charger.charging_rate == 3.3

        self.gui.charging_var.set("Level 2 (240V) 6.6kW")
        self.gui.update_calculations()
        assert self.gui.charger.charging_rate == 6.6

    def test_error_handling(self):
        """Test that update_calculations handles errors gracefully."""
        # Set invalid battery capacity that doesn't exist in the dict
        self.gui.battery_var.set("Invalid Battery")

        # Should handle error gracefully without crashing
        try:
            self.gui.update_calculations()
        except KeyError:
            pass  # Expected behavior for invalid battery selection

    def test_comboboxes_are_readonly(self):
        """Selection widgets reject typed input.

        An editable combobox lets the user type a value that is not a key in
        CHARGING_RATES/BATTERY_CAPACITIES, which used to raise KeyError and
        silently blank every result label.
        """
        assert str(self.gui.battery_combo.cget('state')) == 'readonly'
        assert str(self.gui.charging_combo.cget('state')) == 'readonly'

    def test_error_is_shown_not_just_blanked(self):
        """An unusable input explains itself instead of blanking silently."""
        self.gui.health_var.set("0")
        self.gui.update_calculations()

        assert self.gui.time_80_label.cget('text') == ''
        assert 'Battery health' in self.gui.error_label.cget('text')

    def test_error_clears_on_recovery(self):
        """The error line disappears once the input is valid again."""
        self.gui.health_var.set("0")
        self.gui.update_calculations()
        assert self.gui.error_label.cget('text') != ''

        self.gui.health_var.set("100")
        self.gui.update_calculations()
        assert self.gui.error_label.cget('text') == ''
        assert self.gui.time_80_label.cget('text') != ''

    def test_already_at_target_shown_in_results(self):
        """Charging past 80% reports that, rather than '0 minutes'."""
        self.gui.current_var.set("90")
        self.gui.update_calculations()

        assert self.gui.time_80_label.cget('text') == 'Already at target charge'
        assert self.gui.completion_80_label.cget('text') == \
            'Already at target charge'
        assert self.gui.time_100_label.cget('text') != 'Already at target charge'