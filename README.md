# Nissan Leaf Charging Calculator

A Python application that calculates charging times for a Nissan Leaf electric vehicle based on various parameters including battery capacity, current charge level, and battery health.

## Features

- Supports both 40 kWh and 62 kWh battery capacities
- Calculates charging times for different charging levels:
  - Level 1 (120V) - 1.4kW
  - Level 2 (240V) 3.3kW
  - Level 2 (240V) 6.6kW
- Takes into account:
  - Battery health percentage (degradation over time)
  - Current charge level
  - 10% charging inefficiency factor
  - The charge taper — the BMS slows charging as the pack fills
- Reports any number of charge targets (80% and 100% by default)
- Scenario presets for the two common cases: home overnight and workplace top-up
- Remembers your battery health between runs, shared across all interfaces
- Available with GUI, console, web, or one-shot command-line output
- Comprehensive test suite with 203 tests

## Requirements

- Python 3.10+ (tested with 3.12 and 3.14)
- tkinter (for GUI mode only, usually comes with Python)
- Flask (for web mode only — `pip install flask`)
- pytest (for running tests)

## Installation

### Basic Installation
No special installation is required for basic usage. Simply clone the repository and run the application.

### Development Installation
For development work including testing and code quality tools (uv):

```bash
# The venv lives outside the project: this tree is on pCloud, and sync renames
# pyvenv.cfg to 'pyvenv [conflicted].cfg', which silently guts an in-project venv.
uv venv --python /usr/bin/python3 ~/.venvs/pyp-nissan-leaf-calculator
VIRTUAL_ENV=~/.venvs/pyp-nissan-leaf-calculator uv pip install -r requirements.txt
```

## Usage

### Command-line Options

```bash
# Run with GUI (default)
python main.py

# Run with GUI explicitly
python main.py --gui

# Run in console mode
python main.py --console

# Run the web interface (Flask server on http://localhost:5000)
python main.py --web
```

### One-shot estimates (no prompts)

Supplying any charge parameter prints an estimate and exits, so the calculator
can be scripted or used as a quick lookup:

```bash
# A specific charge, to a specific target
python main.py --battery 40 --health 90 --current 25 --target 80

# Several targets at once
python main.py --current 20 -t 50 -t 80 -t 100

# Pick the charging rate explicitly
python main.py --current 20 --rate 1.4

# Ignore the charge taper (constant-rate estimate)
python main.py --current 20 --no-taper
```

| Flag | Meaning |
| --- | --- |
| `--battery`, `-b` | Battery capacity in kWh: 40 or 62 |
| `--health` | Battery health percentage, above 0 and up to 100 |
| `--current` | Current charge percentage, 0 to 100 |
| `--rate`, `-r` | Charging rate in kW: 1.4, 3.3 or 6.6 |
| `--target`, `-t` | Target percentage; repeat for several targets |
| `--preset`, `-p` | Scenario preset: `home` or `work` |
| `--no-taper` | Assume a constant rate instead of modelling the taper |
| `--no-save` | Do not remember `--health` from this run |

Combine a charge parameter with an interface flag to pre-populate that
interface instead of printing a report:

```bash
python main.py --console --preset home --current 30
python main.py --gui --battery 62 --current 45
```

### Remembered battery health

Battery health is a property of your particular car that changes slowly over
years, so it is stored once and reused. Setting it anywhere — the `--health`
flag, the console menu, the GUI field, or a web form submission — saves it, and
every interface reads the same value on the next run.

The setting lives in your user config directory, deliberately outside the
project tree:

```
${XDG_CONFIG_HOME:-~/.config}/nissan-leaf-calculator/config.json
```

Set `LEAF_CALCULATOR_CONFIG` to override that path entirely.

For a one-off "what if my pack were worse" query, add `--no-save` so the stored
value is left alone:

```bash
python main.py --health 50 --current 20 --no-save
```

A missing, unreadable or hand-corrupted config file falls back to 100% rather
than failing, and a config directory that cannot be written to produces a
warning rather than an error.

### Scenario presets

Presets fill in the charging rate and target for a common situation. They
describe the *scenario*, not the car, so battery capacity, health and current
charge are left alone. Anything you set explicitly overrides the preset.

| Preset | Rate | Target |
| --- | --- | --- |
| `home` — Home overnight | 6.6 kW (Level 2) | 80% |
| `work` — Workplace top-up | 3.3 kW (Level 2) | 100% |

```bash
python main.py --preset home --current 30
python main.py --preset work --battery 62 --health 95 --current 60
```

Both are also selectable from the console menu, the GUI dropdown and the web
form.

### Charge taper

A real Leaf's battery management system reduces current as the pack fills, so
the last stretch to 100% takes disproportionately longer. The calculator models
this as a linear decline from the full rate at 80% state of charge to 25% of it
at 100%, which tracks observed Leaf AC charging far better than assuming a
constant rate.

Targets at or below 80% are unaffected. Pass `--no-taper` (or untick the box in
the GUI and web form) for the older constant-rate behaviour — for a 40 kWh pack
charging 0→100% at 6.6 kW that is the difference between 7 hours 48 minutes and
6 hours 40 minutes.

The taper curve is a simplification: the real one also depends on temperature
and on whether the supply can saturate the pack at all, which Level 1 rarely
can.

### Running Directly

You can also run the individual interfaces directly:

```bash
# GUI interface
python -m leaf_calculator.leaf_gui

# Console interface
python -m leaf_calculator.leaf_console

# Web interface
python -m leaf_calculator.leaf_web
```

Use `python -m` rather than a file path: these modules import each other with
relative imports, so running them as standalone scripts will not resolve.

## Example Calculations

### Typical Home Charging Scenario
- **Battery**: 40 kWh at 90% health
- **Current charge**: 25%
- **Target**: 80%
- **Rate**: 6.6kW (Level 2)
- **Result**: 3 hours 18 minutes to complete

### Workplace Top-up Scenario
- **Battery**: 62 kWh at 95% health
- **Current charge**: 60%
- **Target**: 100%
- **Rate**: 3.3kW (Level 2)
- **Result**: 11 hours 11 minutes to complete (7 hours 51 minutes with `--no-taper`;
  this target runs well past the 80% taper threshold)

## Testing

The project includes a comprehensive test suite with 203 tests covering:

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Core calculation tests
pytest tests/test_leaf_core.py -v

# GUI interface tests
pytest tests/test_gui_interface.py -v

# Console interface tests
pytest tests/test_console_interface.py -v

# Web interface tests
pytest tests/test_leaf_web.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Development

### Code Quality Tools
```bash
# Type checking
mypy leaf_calculator/

# Code quality analysis
pylint leaf_calculator/
```

### Project Commands (as defined in CLAUDE.md)
- Run with GUI: `python main.py`
- Run with console: `python main.py --console`
- Run with web: `python main.py --web`
- Type checking: `mypy leaf_calculator/`
- Code quality: `pylint leaf_calculator/`

## Project Structure

- `main.py` - Thin wrapper so the app runs from a source checkout
- `leaf_calculator/` - The application package
  - `cli.py` - Command-line argument handling, presets and one-shot reports
  - `leaf_core.py` - Calculation logic, shared validators, presets, taper model
  - `settings.py` - Persistent user settings (remembered battery health)
  - `leaf_gui.py` - GUI interface using tkinter
  - `leaf_console.py` - Console interface
  - `leaf_web.py` - Flask web interface (mobile-friendly, optimized for iSH on iOS)
  - `templates/` - HTML templates for the web interface
  - `static/` - CSS and JavaScript for the web interface
- `legacy/` - Original implementations, kept for reference only
- `tests/` - Comprehensive test suite
  - `test_leaf_core.py` - Core calculation, validator, preset and taper tests
  - `test_cli.py` - Command-line flag and preset tests
  - `test_settings.py` - Settings persistence tests
  - `conftest.py` - Redirects the settings file to a temp path for all tests
  - `test_gui_interface.py` - GUI interface tests
  - `test_console_interface.py` - Console interface tests
  - `test_leaf_web.py` - Web interface tests
  - `test_integration.py` - End-to-end integration tests
- `requirements.txt` - Development dependencies
- `pyproject.toml` - Packaging plus pytest, mypy, pylint, black and coverage configuration
- `CLAUDE.md` - Development guidelines and commands
- `ENHANCEMENTS.md` - Planned future improvements

## Architecture

The application follows a modular architecture:

1. **Core Logic** (`leaf_core.py`): Pure calculation functions plus the input
   validators, scenario presets and result formatting every front end shares —
   no UI dependencies
2. **Interfaces**: Separate GUI, console, and web implementations that all use the core logic
3. **Main Entry Point**: Command-line argument parsing and interface selection (`--gui`, `--console`, `--web`)
4. **Comprehensive Testing**: Unit, integration, and interface tests

## Troubleshooting

### GUI Won't Start
- Ensure tkinter is installed: `python -c "import tkinter"`
- Try console mode instead: `python main.py --console`

### Import Errors
- Ensure you're running from the project root directory
- Ensure the `leaf_calculator/` package directory is intact

### Test Failures
- Ensure pytest is installed: `uv pip install pytest`
- Run tests with verbose output: `pytest tests/ -v --tb=short`
