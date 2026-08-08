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
- Provides estimates for both 80% and 100% charging targets
- Available with GUI, console, or web interface
- Comprehensive test suite with 100 tests

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
- **Result**: 7 hours 51 minutes to complete

## Testing

The project includes a comprehensive test suite with 100 tests covering:

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
  - `cli.py` - Command-line argument handling and interface selection
  - `leaf_core.py` - Core calculation logic and utilities
  - `leaf_gui.py` - GUI interface using tkinter
  - `leaf_console.py` - Console interface
  - `leaf_web.py` - Flask web interface (mobile-friendly, optimized for iSH on iOS)
  - `templates/` - HTML templates for the web interface
  - `static/` - CSS and JavaScript for the web interface
- `legacy/` - Original implementations, kept for reference only
- `tests/` - Comprehensive test suite
  - `test_leaf_core.py` - Core calculation tests
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

1. **Core Logic** (`leaf_core.py`): Pure calculation functions, no UI dependencies
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
