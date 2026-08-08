# Nissan Leaf Calculator - Claude Guidelines

## Commands
- Run with GUI (default): `python main.py`
- Run with console: `python main.py --console`
- Run with web: `python main.py --web`
- Run GUI directly: `python "Python Modules/leaf_gui.py"`
- Run console directly: `python "Python Modules/leaf_console.py"`
- Run web directly: `python "Python Modules/leaf_web.py"`
- Tests: `pytest`
- Type checking: `mypy "Python Modules/"`
- Code quality: `pylint "Python Modules/"`

All tool configuration lives in `pyproject.toml`. There is no `pytest.ini` — adding
one back would silently shadow the `[tool.pytest.ini_options]` block.

## Code Style
- **Indentation**: 4 spaces for leaf_console.py and leaf_gui.py; 2 spaces for leaf_web.py
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