# Nissan Leaf Charging Calculator

A Python application that calculates charging times for a Nissan Leaf electric vehicle based on various parameters including battery capacity, current charge level, and battery health.

## Features

- Supports both 40 kWh and 62 kWh battery capacities
- Calculates charging times for different charging levels:
  - Level 1 (120V)
  - Level 2 (240V) 3.3kW
  - Level 2 (240V) 6.6kW
- Takes into account:
  - Battery health percentage
  - Current charge level
- Provides estimates for both 80% and 100% charging targets
- Available with either GUI or console interface

## Requirements

- Python 3.x
- tkinter (for GUI mode only, usually comes with Python)

## Installation

No special installation is required. Simply clone the repository and run the application.

## Usage

### Command-line Options

```bash
# Run with GUI (default)
python main.py

# Run with GUI explicitly
python main.py --gui

# Run in console mode
python main.py --console
```

### Running Directly

You can also run the individual interfaces directly:

```bash
# GUI interface
python "Python Modules/leaf_gui.py"

# Console interface
python "Python Modules/leaf_console.py"
```

## Project Structure

- `main.py` - Main entry point with command-line argument handling
- `Python Modules/`
  - `leaf_core.py` - Core calculation logic
  - `leaf_gui.py` - GUI interface using tkinter
  - `leaf_console.py` - Console interface