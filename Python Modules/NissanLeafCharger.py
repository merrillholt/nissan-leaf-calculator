import tkinter as tk
from tkinter import messagebox


class NissanLeafCharger:
    def __init__(self, battery_capacity_kwh=40):
        self.battery_capacity_kwh = battery_capacity_kwh
        self.charging_rates = {
            "Level 1 (120V)": 1.4,
            "Level 2 (240V) 3.3kW": 3.3,
            "Level 2 (240V) 6.6kW": 6.6
        }

    def validate_percentage(self, value, name):
        try:
            value = float(value)
            if not 0 <= value <= 100:
                raise ValueError
            return value
        except ValueError:
            raise ValueError(f"{name} must be a number between 0 and 100")

    def calculate_effective_capacity(self, health_percentage):
        return self.battery_capacity_kwh * (health_percentage / 100)

    def calculate_charging_time(self, health_percentage, current_charge, target_charge):
        """Calculate charging time to reach target percentage"""
        health_percentage = self.validate_percentage(health_percentage, "Battery health")
        current_charge = self.validate_percentage(current_charge, "Current charge")

        if current_charge >= target_charge:
            return {level: (0, 0) for level in self.charging_rates.keys()}

        effective_capacity = self.calculate_effective_capacity(health_percentage)
        remaining_percentage = target_charge - current_charge
        energy_needed = effective_capacity * (remaining_percentage / 100)

        charging_times = {}
        for level, rate in self.charging_rates.items():
            # Add 10% to account for charging inefficiency
            hours = (energy_needed * 1.1) / rate
            hours_whole = int(hours)
            minutes = int((hours - hours_whole) * 60)
            charging_times[level] = (hours_whole, minutes)

        return charging_times


class NissanLeafGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("2019 Nissan Leaf Charging Calculator")
        self.root.geometry("700x800")  # Increased height for additional information
        self.root.configure(bg='#f0f0f0')

        self.charger = NissanLeafCharger()
        self.create_widgets()

    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=20)
        tk.Label(
            title_frame,
            text="Nissan Leaf Charging Calculator",
            font=("Helvetica", 16, "bold"),
            bg='#f0f0f0'
        ).pack()

        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(padx=20, pady=10)

        # Battery capacity selection
        capacity_frame = tk.LabelFrame(
            main_frame,
            text="Battery Capacity",
            bg='#f0f0f0',
            font=("Helvetica", 10, "bold")
        )
        capacity_frame.pack(fill=tk.X, pady=10)

        self.battery_capacity = tk.StringVar(value="40")
        tk.Radiobutton(
            capacity_frame,
            text="40 kWh (Standard)",
            variable=self.battery_capacity,
            value="40",
            bg='#f0f0f0'
        ).pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(
            capacity_frame,
            text="62 kWh (e+)",
            variable=self.battery_capacity,
            value="62",
            bg='#f0f0f0'
        ).pack(side=tk.LEFT, padx=20)

        # Input frame
        input_frame = tk.LabelFrame(
            main_frame,
            text="Input Parameters",
            bg='#f0f0f0',
            font=("Helvetica", 10, "bold")
        )
        input_frame.pack(fill=tk.X, pady=10)

        # Battery Health Input
        health_frame = tk.Frame(input_frame, bg='#f0f0f0')
        health_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(
            health_frame,
            text="Battery Health (%):",
            bg='#f0f0f0'
        ).pack(side=tk.LEFT)
        self.health_var = tk.StringVar(value="100")
        tk.Spinbox(
            health_frame,
            from_=0,
            to=100,
            textvariable=self.health_var,
            width=10
        ).pack(side=tk.RIGHT)

        # Current Charge Input
        charge_frame = tk.Frame(input_frame, bg='#f0f0f0')
        charge_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(
            charge_frame,
            text="Current Charge (%):",
            bg='#f0f0f0'
        ).pack(side=tk.LEFT)
        self.charge_var = tk.StringVar(value="0")
        tk.Spinbox(
            charge_frame,
            from_=0,
            to=100,
            textvariable=self.charge_var,
            width=10
        ).pack(side=tk.RIGHT)

        # Buttons
        button_frame = tk.Frame(main_frame, bg='#f0f0f0')
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Calculate",
            command=self.calculate,
            bg='#4CAF50',  # Green
            fg='white',
            font=("Helvetica", 10, "bold"),
            width=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="Clear",
            command=self.clear_inputs,
            bg='#f44336',  # Red
            fg='white',
            font=("Helvetica", 10, "bold"),
            width=10
        ).pack(side=tk.LEFT, padx=5)

        # Results frames (separate frames for 80% and 100%)
        # 80% Results
        results_frame_80 = tk.LabelFrame(
            main_frame,
            text="Charging Time Estimates (to 80%)",
            bg='#f0f0f0',
            font=("Helvetica", 10, "bold")
        )
        results_frame_80.pack(fill=tk.BOTH, expand=True, pady=5)

        # 100% Results
        results_frame_100 = tk.LabelFrame(
            main_frame,
            text="Charging Time Estimates (to 100%)",
            bg='#f0f0f0',
            font=("Helvetica", 10, "bold")
        )
        results_frame_100.pack(fill=tk.BOTH, expand=True, pady=5)

        # Results labels
        self.result_labels_80 = {}
        self.result_labels_100 = {}

        for level in self.charger.charging_rates.keys():
            # 80% frame
            frame_80 = tk.Frame(results_frame_80, bg='#f0f0f0')
            frame_80.pack(fill=tk.X, pady=5, padx=10)
            tk.Label(
                frame_80,
                text=level + ":",
                bg='#f0f0f0'
            ).pack(side=tk.LEFT)
            self.result_labels_80[level] = tk.Label(
                frame_80,
                text="--",
                bg='#f0f0f0'
            )
            self.result_labels_80[level].pack(side=tk.RIGHT)

            # 100% frame
            frame_100 = tk.Frame(results_frame_100, bg='#f0f0f0')
            frame_100.pack(fill=tk.X, pady=5, padx=10)
            tk.Label(
                frame_100,
                text=level + ":",
                bg='#f0f0f0'
            ).pack(side=tk.LEFT)
            self.result_labels_100[level] = tk.Label(
                frame_100,
                text="--",
                bg='#f0f0f0'
            )
            self.result_labels_100[level].pack(side=tk.RIGHT)

        # Note about 80% charging
        note_frame = tk.Frame(main_frame, bg='#f0f0f0')
        note_frame.pack(fill=tk.X, pady=10)
        tk.Label(
            note_frame,
            text="Note: Charging to 80% is recommended for daily use to extend battery life.",
            bg='#f0f0f0',
            font=("Helvetica", 9, "italic"),
            fg='#666666'
        ).pack()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg='#f0f0f0',
            font=("Helvetica", 10, "italic")
        )
        self.status_bar.pack(pady=10)

    def calculate(self):
        try:
            self.charger.battery_capacity_kwh = int(self.battery_capacity.get())

            # Calculate times for both 80% and 100%
            times_80 = self.charger.calculate_charging_time(
                float(self.health_var.get()),
                float(self.charge_var.get()),
                80  # Target 80%
            )

            times_100 = self.charger.calculate_charging_time(
                float(self.health_var.get()),
                float(self.charge_var.get()),
                100  # Target 100%
            )

            # Update both sets of results
            for level, (hours, minutes) in times_80.items():
                self.result_labels_80[level].config(
                    text=f"{hours} hours and {minutes} minutes"
                )

            for level, (hours, minutes) in times_100.items():
                self.result_labels_100[level].config(
                    text=f"{hours} hours and {minutes} minutes"
                )

            self.status_var.set("Calculation completed successfully!")

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            self.status_var.set("Error in calculation. Please check inputs.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
            self.status_var.set("An unexpected error occurred.")

    def clear_inputs(self):
        self.health_var.set("100")
        self.charge_var.set("0")
        self.battery_capacity.set("40")
        for label in self.result_labels_80.values():
            label.config(text="--")
        for label in self.result_labels_100.values():
            label.config(text="--")
        self.status_var.set("Inputs cleared.")


def main():
    root = tk.Tk()
    app = NissanLeafGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()