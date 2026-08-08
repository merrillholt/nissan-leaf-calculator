# Nissan Leaf Calculator - Claude Guidelines

## Commands
- Run with GUI (default): `python main.py`
- Run with console: `python main.py --console`
- Run with web: `python main.py --web`
- Run GUI directly: `python -m leaf_calculator.leaf_gui`
- Run console directly: `python -m leaf_calculator.leaf_console`
- Run web directly: `python -m leaf_calculator.leaf_web`
- Tests: `pytest`
- Type checking: `mypy leaf_calculator/`
- Code quality: `pylint leaf_calculator/`

## Layout
The application package is `leaf_calculator/`, with `templates/` and `static/`
inside it so Flask's defaults resolve them in both a source checkout and an
installed wheel. `main.py` at the repo root is a thin wrapper around
`leaf_calculator.cli:main`, which is also the installed console script.
`legacy/` at the repo root holds pre-refactor code for reference and is
excluded from packaging, mypy, pylint and coverage.

Use `python -m` rather than running module files by path: the modules use
relative imports (`from .leaf_core import ...`), so executing them as scripts
will not resolve.

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