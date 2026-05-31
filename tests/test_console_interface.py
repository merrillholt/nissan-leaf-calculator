import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the Python Modules directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "Python Modules"))

from leaf_console import ConsoleInterface


class TestConsoleInterface:
    """Test cases for the ConsoleInterface class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.console = ConsoleInterface()

    def test_init(self):
        """Test console interface initialization."""
        assert self.console.charger is not None
        assert self.console.start_time is not None

    @patch('builtins.input')
    def test_get_valid_number_valid_input(self, mock_input):
        """Test get_valid_number with valid input."""
        mock_input.return_value = "50.5"
        result = self.console.get_valid_number("Enter number: ", 0, 100)
        assert result == 50.5

    @patch('builtins.input')
    def test_get_valid_number_quit(self, mock_input):
        """Test get_valid_number with quit input."""
        mock_input.return_value = "q"
        result = self.console.get_valid_number("Enter number: ", 0, 100)
        assert result is None

    @patch('builtins.input')
    def test_get_valid_number_out_of_range_then_valid(self, mock_input):
        """Test get_valid_number with out of range then valid input."""
        mock_input.side_effect = ["150", "50"]
        with patch('builtins.print'):
            result = self.console.get_valid_number("Enter number: ", 0, 100)
        assert result == 50.0

    @patch('builtins.input')
    def test_get_valid_number_invalid_then_valid(self, mock_input):
        """Test get_valid_number with invalid then valid input."""
        mock_input.side_effect = ["abc", "50"]
        with patch('builtins.print'):
            result = self.console.get_valid_number("Enter number: ", 0, 100)
        assert result == 50.0

    @patch('builtins.input')
    def test_display_menu_valid(self, mock_input):
        """Test display_menu with valid input."""
        options = {'1': ('Option 1', 10), '2': ('Option 2', 20)}
        mock_input.return_value = "1"
        with patch('builtins.print'):
            result = self.console.display_menu(options, "Choose")
        assert result == "1"

    @patch('builtins.input')
    def test_display_menu_quit(self, mock_input):
        """Test display_menu with quit input."""
        options = {'1': ('Option 1', 10), '2': ('Option 2', 20)}
        mock_input.return_value = "q"
        with patch('builtins.print'):
            result = self.console.display_menu(options, "Choose")
        assert result == "q"

    @patch('builtins.input')
    def test_display_menu_invalid_then_valid(self, mock_input):
        """Test display_menu with invalid then valid input."""
        options = {'1': ('Option 1', 10), '2': ('Option 2', 20)}
        mock_input.side_effect = ["3", "1"]
        with patch('builtins.print'):
            result = self.console.display_menu(options, "Choose")
        assert result == "1"

    def test_display_results(self):
        """Test display_results method."""
        self.console.charger.battery_capacity = 40
        self.console.charger.battery_health = 90
        self.console.charger.current_charge = 20
        self.console.charger.charging_rate = 6.6

        with patch('builtins.print') as mock_print:
            self.console.display_results()

        # Verify that print was called multiple times
        assert mock_print.call_count > 5

        # Check that some expected output was printed (less specific checks)
        calls = [str(call) for call in mock_print.call_args_list]
        assert any("Charging Time Estimates" in call for call in calls)
        assert any("To 80% charge" in call for call in calls)
        assert any("To 100% charge" in call for call in calls)

    @patch('builtins.input')
    def test_run_complete_flow_quit_early(self, mock_input):
        """Test complete run flow with early quit."""
        mock_input.return_value = "q"

        with patch('builtins.print'):
            result = self.console.run()

        # Should return without completing full flow
        assert result is None

    @patch('builtins.input')
    def test_run_complete_flow_success(self, mock_input):
        """Test complete successful run flow."""
        # Simulate user inputs: battery selection, health=90%, current=20%, calculate, then quit
        mock_input.side_effect = ["1", "1", "3", "90", "4", "20", "5", "q"]

        with patch('builtins.print') as mock_print:
            result = self.console.run()

        # Verify that configuration was set correctly
        assert self.console.charger.battery_capacity == 40
        assert self.console.charger.battery_health == 90
        assert self.console.charger.current_charge == 20

        # Verify results were displayed
        assert mock_print.call_count > 10

    def test_edge_case_zero_health(self):
        """Test behavior with zero battery health."""
        self.console.charger.battery_health = 0
        self.console.charger.current_charge = 0

        with patch('builtins.print'):
            self.console.display_results()

        # Should handle zero health gracefully

    def test_edge_case_full_battery(self):
        """Test behavior with full battery."""
        self.console.charger.current_charge = 100

        with patch('builtins.print'):
            self.console.display_results()

        # Should handle full battery gracefully