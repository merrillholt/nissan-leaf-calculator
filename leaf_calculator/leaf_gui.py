"""GUI interface for Nissan Leaf Charging Calculator.

This module provides a tkinter-based graphical user interface for calculating
Nissan Leaf charging times with real-time updates.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import List, Optional

from .leaf_core import (
    PRESETS,
    NissanLeafCharger,
    summarize,
    validate_battery_health,
    validate_current_charge,
    validate_target_percentage,
)

NO_PRESET = 'Custom'


class NissanLeafGUI:
    """GUI class for the Nissan Leaf Charging Calculator."""

    def __init__(self, root, charger: Optional[NissanLeafCharger] = None):
        """Initialize the GUI.

        Args:
            root: tkinter root window
            charger: Pre-configured calculator, e.g. one built from
                command-line flags. A default one is created if omitted.
        """
        self.root = root
        self.charger = charger if charger is not None else NissanLeafCharger()
        self.start_time = datetime.now()
        # Widgets are built by setup_gui; declared here so the full set of
        # instance attributes is visible in one place.
        self.results_frame: ttk.LabelFrame
        self.error_label: ttk.Label
        self.start_time_label: ttk.Label
        self.preset_var: tk.StringVar
        self.battery_var: tk.StringVar
        self.charging_var: tk.StringVar
        self.health_var: tk.StringVar
        self.current_var: tk.StringVar
        self.targets_var: tk.StringVar
        self.taper_var: tk.BooleanVar
        self.preset_combo: ttk.Combobox
        self.battery_combo: ttk.Combobox
        self.charging_combo: ttk.Combobox
        self.result_rows: List[ttk.Label] = []
        self.setup_gui()

    def setup_gui(self):
        """Set up the GUI elements."""
        self.root.title('Nissan Leaf Charging Calculator')
        self.root.geometry('640x520')

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
        self._setup_input_fields(input_frame)

        # Results Frame
        self.results_frame = ttk.LabelFrame(
            main_frame, text='Charging Time Estimates', padding='10'
        )
        self.results_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=20
        )
        self.results_frame.columnconfigure(1, weight=1)
        self.results_frame.columnconfigure(2, weight=1)

        self.error_label = ttk.Label(main_frame, text='', foreground='red')
        self.error_label.grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5)
        )

        self._sync_charger_from_form()
        self._rebuild_results_grid()
        self.update_calculations()

    def _setup_input_fields(self, input_frame):
        """Build the input widgets.

        Args:
            input_frame: Frame that holds the labelled inputs.
        """
        # Scenario Preset Selection
        ttk.Label(input_frame, text='Scenario:').grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.preset_var = tk.StringVar(value=NO_PRESET)
        self.preset_combo = ttk.Combobox(
            input_frame,
            textvariable=self.preset_var,
            values=[NO_PRESET] + [p.label for p in PRESETS.values()],
            width=30,
            state='readonly'
        )
        self.preset_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.apply_preset)

        # Battery Capacity Selection
        ttk.Label(input_frame, text='Battery Capacity:').grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.battery_var = tk.StringVar(value='40 kWh')
        self.battery_combo = ttk.Combobox(
            input_frame,
            textvariable=self.battery_var,
            values=list(NissanLeafCharger.BATTERY_CAPACITIES.keys()),
            width=30,
            state='readonly'
        )
        self.battery_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.battery_combo.bind('<<ComboboxSelected>>', self.update_calculations)

        # Charging Rate Selection
        ttk.Label(input_frame, text='Charging Rate:').grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.charging_var = tk.StringVar(value='Level 2 (240V) 6.6kW')
        self.charging_combo = ttk.Combobox(
            input_frame,
            textvariable=self.charging_var,
            values=list(NissanLeafCharger.CHARGING_RATES.keys()),
            width=30,
            state='readonly'
        )
        self.charging_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        self.charging_combo.bind(
            '<<ComboboxSelected>>', self.on_manual_change
        )

        # Battery Health
        ttk.Label(input_frame, text='Battery Health (%):').grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.health_var = tk.StringVar(value='100')
        health_entry = ttk.Entry(
            input_frame, textvariable=self.health_var, width=30
        )
        health_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        health_entry.bind('<KeyRelease>', self.validate_and_update)

        # Current Charge
        ttk.Label(input_frame, text='Current Charge (%):').grid(
            row=4, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.current_var = tk.StringVar(value='0')
        current_entry = ttk.Entry(
            input_frame, textvariable=self.current_var, width=30
        )
        current_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        current_entry.bind('<KeyRelease>', self.validate_and_update)

        # Target charge levels
        ttk.Label(input_frame, text='Targets (%):').grid(
            row=5, column=0, sticky=tk.W, pady=5, padx=(0, 10)
        )
        self.targets_var = tk.StringVar(
            value=', '.join(f'{t:g}' for t in self.charger.targets)
        )
        targets_entry = ttk.Entry(
            input_frame, textvariable=self.targets_var, width=30
        )
        targets_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        targets_entry.bind('<KeyRelease>', self.on_manual_change)

        # Charge taper toggle
        self.taper_var = tk.BooleanVar(value=self.charger.model_taper)
        taper_check = ttk.Checkbutton(
            input_frame,
            text='Model charge taper (slower as the pack fills)',
            variable=self.taper_var,
            command=self.update_calculations
        )
        taper_check.grid(
            row=6, column=0, columnspan=2, sticky=tk.W, pady=(5, 0)
        )

    def _rebuild_results_grid(self):
        """Rebuild the results rows to match the configured targets."""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.result_rows = []

        headers = ['Target', 'Duration', 'Completion Time']
        for col, header in enumerate(headers):
            ttk.Label(self.results_frame, text=header).grid(
                row=0, column=col, sticky=tk.W, padx=(5, 15)
            )

        for index, target in enumerate(self.charger.targets, start=1):
            ttk.Label(
                self.results_frame, text=f'To {target:g}% charge:'
            ).grid(row=index, column=0, sticky=tk.W, pady=5, padx=(5, 15))

            duration = ttk.Label(self.results_frame, text='')
            duration.grid(
                row=index, column=1, sticky=tk.W, pady=5, padx=(5, 15)
            )
            completion = ttk.Label(self.results_frame, text='')
            completion.grid(row=index, column=2, sticky=tk.W, pady=5, padx=5)
            self.result_rows.append(duration)
            self.result_rows.append(completion)

    def apply_preset(self, *args):  # pylint: disable=unused-argument
        """Apply the selected scenario preset to the form."""
        label = self.preset_var.get()
        preset = next(
            (p for p in PRESETS.values() if p.label == label), None
        )
        if preset is None:
            return

        rate_name = next(
            name for name, value in NissanLeafCharger.CHARGING_RATES.items()
            if value == preset.charging_rate
        )
        self.charging_var.set(rate_name)
        self.targets_var.set(f'{preset.target:g}')
        self.update_calculations()

    def on_manual_change(self, *args):  # pylint: disable=unused-argument
        """Drop the preset label when the user edits its fields directly."""
        self.preset_var.set(NO_PRESET)
        self.update_calculations()

    def parse_targets(self) -> List[float]:
        """Parse the targets entry into a list of percentages.

        Returns:
            Validated target percentages.

        Raises:
            ValueError: If any entry is not a valid percentage, or the field
                is empty.
        """
        raw = self.targets_var.get().strip()
        if not raw:
            raise ValueError('Enter at least one target percentage')
        return [
            validate_target_percentage(part)
            for part in raw.split(',') if part.strip()
        ]

    def validate_and_update(self, *args):  # pylint: disable=unused-argument
        """Validate input before updating calculations."""
        self.update_calculations()

    def _sync_charger_from_form(self):
        """Copy the form values onto the charger.

        Raises:
            ValueError: If any field is invalid.
            KeyError: If a dropdown holds an unknown key.
        """
        self.charger.battery_capacity = NissanLeafCharger.BATTERY_CAPACITIES[
            self.battery_var.get()
        ]
        self.charger.charging_rate = NissanLeafCharger.CHARGING_RATES[
            self.charging_var.get()
        ]
        self.charger.battery_health = validate_battery_health(
            self.health_var.get().strip()
        )
        self.charger.current_charge = validate_current_charge(
            self.current_var.get().strip()
        )
        self.charger.model_taper = self.taper_var.get()
        self.charger.targets = self.parse_targets()

    def update_calculations(self, *args):  # pylint: disable=unused-argument
        """Update charging time calculations and display."""
        self.start_time = datetime.now()
        self.start_time_label.config(
            text=self.start_time.strftime('%Y-%m-%d %H:%M:%S')
        )

        previous_targets = list(self.charger.targets)
        try:
            self._sync_charger_from_form()
        except (ValueError, KeyError) as exc:
            self._show_error(str(exc).strip("'"))
            return

        if self.charger.targets != previous_targets:
            self._rebuild_results_grid()

        rows = summarize(self.charger, self.start_time)
        errors = [row['error'] for row in rows if 'error' in row]
        if errors:
            self._show_error(str(errors[0]))
            return

        for index, row in enumerate(rows):
            self.result_rows[index * 2].config(text=row['duration'])
            self.result_rows[index * 2 + 1].config(text=row['completion'])
        self.error_label.config(text='')

    def _show_error(self, message: str):
        """Blank the results and explain why they could not be computed.

        Args:
            message: Text shown to the user.
        """
        for label in self.result_rows:
            label.config(text='')
        self.error_label.config(text=message)


def main():
    """Main entry point of the application."""
    root = tk.Tk()
    NissanLeafGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
