# Nissan Leaf Calculator - Claude Guidelines

## Commands
- Run with GUI (default): `python main.py`
- Run with console: `python main.py --console`
- Run GUI directly: `python "Python Modules/leaf_gui.py"`
- Run console directly: `python "Python Modules/leaf_console.py"`
- Type checking: `mypy "Python Modules/"`
- Code quality: `pylint "Python Modules/"`

## Code Style
- **Indentation**: 2 spaces for NissanLeafCharger.py, 4 spaces for Leaf.py
- **Imports**: Group in order: standard library, third-party, local modules
- **Type hints**: Always use typing annotations (Dict, Tuple, Optional, etc.)
- **Docstrings**: Google style docstrings with Args/Returns/Raises sections
- **Naming**: 
  - Classes: PascalCase
  - Methods/functions: snake_case
  - Constants: UPPER_CASE
- **Error handling**: Use try/except blocks with specific exception types
- **Formatting**: Maintain 80 character line length
- **Constants**: Define class-level constants for configuration values
- **Comments**: Add comments for complex logic, not obvious implementations

Create unit tests for new features and run before submitting changes.