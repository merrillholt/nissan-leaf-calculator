import pytest
import sys
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

try:
    from leaf_calculator.leaf_gui import NissanLeafGUI
    from leaf_calculator.leaf_core import NissanLeafCharger
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

    def duration(self, index=0):
        """Return the duration text of the given results row."""
        return self.gui.result_rows[index * 2].cget('text')

    def completion(self, index=0):
        """Return the completion text of the given results row."""
        return self.gui.result_rows[index * 2 + 1].cget('text')

    def test_non_numeric_input_reports_an_error(self):
        """Junk in a numeric field explains itself instead of becoming 0."""
        self.gui.health_var.set("abc")
        self.gui.update_calculations()
        assert 'must be a number' in self.gui.error_label.cget('text')
        assert self.duration() == ''

    def test_empty_input_reports_an_error(self):
        """An empty field is an error, not a silent zero."""
        self.gui.current_var.set("")
        self.gui.update_calculations()
        assert self.gui.error_label.cget('text') != ''

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
        """A health above 100 is reported rather than silently rewritten."""
        self.gui.health_var.set("150")
        self.gui.validate_and_update()
        assert 'Battery health' in self.gui.error_label.cget('text')
        # The user's input is left alone so they can correct it themselves.
        assert self.gui.health_var.get() == "150"

    def test_validate_and_update_out_of_range_low(self):
        """A negative current charge is reported rather than reset."""
        self.gui.current_var.set("-10")
        self.gui.validate_and_update()
        assert 'Current charge' in self.gui.error_label.cget('text')
        assert self.gui.current_var.get() == "-10"

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

        assert self.duration() == ''
        assert 'Battery health' in self.gui.error_label.cget('text')

    def test_error_clears_on_recovery(self):
        """The error line disappears once the input is valid again."""
        self.gui.health_var.set("0")
        self.gui.update_calculations()
        assert self.gui.error_label.cget('text') != ''

        self.gui.health_var.set("100")
        self.gui.update_calculations()
        assert self.gui.error_label.cget('text') == ''
        assert self.duration() != ''

    def test_already_at_target_shown_in_results(self):
        """Charging past 80% reports that, rather than '0 minutes'."""
        self.gui.current_var.set("90")
        self.gui.update_calculations()

        assert self.duration(0) == 'Already at target charge'
        assert self.completion(0) == 'Already at target charge'
        assert self.duration(1) != 'Already at target charge'


class TestGuiPresetsAndTargets:
    """Presets, configurable targets and the taper toggle in the GUI."""

    def setup_method(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.gui = NissanLeafGUI(self.root)

    def teardown_method(self):
        if self.root:
            self.root.destroy()

    def duration(self, index=0):
        return self.gui.result_rows[index * 2].cget('text')

    def test_preset_dropdown_lists_both_presets(self):
        values = self.gui.preset_combo.cget('values')
        assert 'Home overnight' in values
        assert 'Workplace top-up' in values
        assert self.gui.preset_var.get() == 'Custom'

    def test_preset_dropdown_is_readonly(self):
        assert str(self.gui.preset_combo.cget('state')) == 'readonly'

    def test_applying_home_preset_updates_rate_and_target(self):
        self.gui.preset_var.set('Home overnight')
        self.gui.apply_preset()
        assert self.gui.charging_var.get() == 'Level 2 (240V) 6.6kW'
        assert self.gui.targets_var.get() == '80'
        assert self.gui.charger.targets == [80.0]

    def test_applying_work_preset_updates_rate_and_target(self):
        self.gui.preset_var.set('Workplace top-up')
        self.gui.apply_preset()
        assert self.gui.charging_var.get() == 'Level 2 (240V) 3.3kW'
        assert self.gui.charger.targets == [100.0]

    def test_editing_a_preset_field_clears_the_preset_label(self):
        """The dropdown stops claiming a preset once you deviate from it."""
        self.gui.preset_var.set('Home overnight')
        self.gui.apply_preset()
        self.gui.targets_var.set('90')
        self.gui.on_manual_change()
        assert self.gui.preset_var.get() == 'Custom'
        assert self.gui.charger.targets == [90.0]

    def test_results_grid_follows_the_target_list(self):
        self.gui.targets_var.set('50, 75, 90')
        self.gui.update_calculations()
        assert self.gui.charger.targets == [50.0, 75.0, 90.0]
        # Two labels per row: duration and completion.
        assert len(self.gui.result_rows) == 6
        assert all(label.cget('text') for label in self.gui.result_rows)

    def test_invalid_target_reports_an_error(self):
        self.gui.targets_var.set('80, 150')
        self.gui.update_calculations()
        assert 'Target percentage' in self.gui.error_label.cget('text')

    def test_empty_target_list_reports_an_error(self):
        self.gui.targets_var.set('')
        self.gui.update_calculations()
        assert 'at least one target' in self.gui.error_label.cget('text')

    def test_taper_toggle_changes_the_estimate(self):
        self.gui.targets_var.set('100')
        self.gui.taper_var.set(True)
        self.gui.update_calculations()
        tapered = self.duration()

        self.gui.taper_var.set(False)
        self.gui.update_calculations()
        assert self.duration() != tapered
        assert self.gui.charger.model_taper is False

    def test_charger_from_cli_prepopulates_the_form(self):
        """A charger built from command-line flags seeds the GUI."""
        root = tk.Tk()
        root.withdraw()
        try:
            charger = NissanLeafCharger()
            charger.targets = [55.0]
            gui = NissanLeafGUI(root, charger)
            assert gui.targets_var.get() == '55'
            assert gui.charger is charger
        finally:
            root.destroy()
