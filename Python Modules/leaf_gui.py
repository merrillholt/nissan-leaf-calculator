"""GUI interface for Nissan Leaf Charging Calculator.

This module provides a tkinter-based graphical user interface for calculating
Nissan Leaf charging times with real-time updates.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

# Import from the same directory with a path-based fallback
try:
    from leaf_core import NissanLeafCharger, ChargingTimeCalculator
except ImportError:
    import importlib.util
    from pathlib import Path

    core_path = Path(__file__).with_name('leaf_core.py')
    spec = importlib.util.spec_from_file_location('leaf_core', core_path)
    if spec is not None:
        leaf_core = importlib.util.module_from_spec(spec)
        if spec.loader:
            spec.loader.exec_module(leaf_core)
            NissanLeafCharger = leaf_core.NissanLeafCharger  # type: ignore
            ChargingTimeCalculator = leaf_core.ChargingTimeCalculator  # type: ignore
        else:
            raise ImportError("Cannot load leaf_core module")
    else:
        raise ImportError("Cannot create spec for leaf_core module")


class NissanLeafGUI:
    """GUI class for the Nissan Leaf Charging Calculator."""

    def __init__(self, root):
        """Initialize the GUI.

        Args:
            root: tkinter root window
        """
        self.root = root
        self.charger = NissanLeafCharger()
        self.start_time = datetime.now()
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI elements."""
        self.root.title('Nissan Leaf Charging Calculator')
        self.root.geometry('600x400')

        main_frame = ttk.Frame(self.root, padding='10')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights to allow expansion
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Start Time Display - make it span full width
        self.time_frame = ttk.LabelFrame(
            main_frame, text='Calculation Start Time', padding='5'
        )
        self.time_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5
        )
        self.time_frame.columnconfigure(0, weight=1)
        start_time_str = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        self.start_time_label = ttk.Label(self.time_frame, text=start_time_str)
        self.start_time_label.grid(row=0, column=0, sticky=tk.W)

        # Input fields - adjust column widths
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        input_frame.columnconfigure(1, weight=1)

        # Battery Capacity Selection
        ttk.Label(input_frame, text='Battery Capacity:').grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.battery_var = tk.StringVar(value='40 kWh')
        battery_combo = ttk.Combobox(
            input_frame,
            textvariable=self.battery_var,
            values=list(NissanLeafCharger.BATTERY_CAPACITIES.keys()),
            width=30
        )
        battery_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        battery_combo.bind('<<ComboboxSelected>>', self.update_calculations)

        # Charging Rate Selection
        ttk.Label(input_frame, text='Charging Rate:').grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.charging_var = tk.StringVar(value='Level 2 (240V) 6.6kW')
        charging_combo = ttk.Combobox(
            input_frame,
            textvariable=self.charging_var,
            values=list(NissanLeafCharger.CHARGING_RATES.keys()),
            width=30
        )
        charging_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        charging_combo.bind('<<ComboboxSelected>>', self.update_calculations)

        # Battery Health
        ttk.Label(input_frame, text='Battery Health (%):').grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.health_var = tk.StringVar(value='100')
        health_entry = ttk.Entry(input_frame, textvariable=self.health_var, width=30)
        health_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        health_entry.bind('<KeyRelease>', self.validate_and_update)

        # Current Charge
        ttk.Label(input_frame, text='Current Charge (%):').grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.current_var = tk.StringVar(value='0')
        current_entry = ttk.Entry(input_frame, textvariable=self.current_var, width=30)
        current_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        current_entry.bind('<KeyRelease>', self.validate_and_update)

        # Results Frame
        results_frame = ttk.LabelFrame(
            main_frame, text='Charging Time Estimates', padding='10'
        )
        results_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20
        )
        results_frame.columnconfigure(1, weight=1)
        results_frame.columnconfigure(2, weight=1)

        self._setup_results_grid(results_frame)
        self.update_calculations()

    def _setup_results_grid(self, frame):
        """Set up the results display grid.

        Args:
            frame: Frame to contain the results grid
        """
        # Column Headers with consistent spacing
        headers = ['Target', 'Duration', 'Completion Time']
        for col, header in enumerate(headers):
            ttk.Label(frame, text=header).grid(
                row=0, column=col, sticky=tk.W, padx=(5, 15)
            )

        # Results Labels for 80%
        ttk.Label(frame, text='To 80% charge:').grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(5, 15)
        )
        self.time_80_label = ttk.Label(frame, text='')
        self.time_80_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 15))
        self.completion_80_label = ttk.Label(frame, text='')
        self.completion_80_label.grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)

        # Results Labels for 100%
        ttk.Label(frame, text='To 100% charge:').grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(5, 15)
        )
        self.time_100_label = ttk.Label(frame, text='')
        self.time_100_label.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(5, 15))
        self.completion_100_label = ttk.Label(frame, text='')
        self.completion_100_label.grid(row=2, column=2, sticky=tk.W, pady=5, padx=5)

    def validate_number(self, value: str) -> float:
        """Validate and convert string input to float.

        Args:
            value: String value to validate

        Returns:
            Float value, or 0.0 if invalid
        """
        if not value.strip():
            return 0.0

        try:
            return float(value.strip())
        except ValueError:
            return 0.0

    def validate_and_update(self, *args):  # pylint: disable=unused-argument
        """Validate input before updating calculations."""
        health = self.validate_number(self.health_var.get())
        if health < 0 or health > 100:
            self.health_var.set('100')

        current = self.validate_number(self.current_var.get())
        if current < 0 or current > 100:
            self.current_var.set('0')

        self.update_calculations()

    def update_calculations(self, *args):  # pylint: disable=unused-argument
        """Update charging time calculations and display."""
        self.start_time = datetime.now()
        try:
            self.charger.battery_capacity = NissanLeafCharger.BATTERY_CAPACITIES[
                self.battery_var.get()
            ]
            self.charger.charging_rate = NissanLeafCharger.CHARGING_RATES[
                self.charging_var.get()
            ]

            self.charger.battery_health = self.validate_number(self.health_var.get())
            self.charger.current_charge = self.validate_number(self.current_var.get())

            if not 0 <= self.charger.battery_health <= 100:
                raise ValueError('Battery health must be between 0 and 100')
            if not 0 <= self.charger.current_charge <= 100:
                raise ValueError('Current charge must be between 0 and 100')

            time_80 = self.charger.calculate_charging_time(80)
            time_100 = self.charger.calculate_charging_time(100)

            self.time_80_label.config(
                text=ChargingTimeCalculator.format_time(time_80)
            )
            self.time_100_label.config(
                text=ChargingTimeCalculator.format_time(time_100)
            )

            self.completion_80_label.config(
                text=ChargingTimeCalculator.calculate_completion_time(
                    self.start_time, time_80
                )
            )
            self.completion_100_label.config(
                text=ChargingTimeCalculator.calculate_completion_time(
                    self.start_time, time_100
                )
            )

        except (ValueError, KeyError):
            # Clear all result labels on error (invalid input or missing dictionary key)
            for label in [
                self.time_80_label,
                self.time_100_label,
                self.completion_80_label,
                self.completion_100_label
            ]:
                label.config(text='')
            # Optionally log the error for debugging
            # print(f"Calculation error: {e}")


def main():
    """Main entry point of the application."""
    root = tk.Tk()
    NissanLeafGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
