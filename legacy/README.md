# Legacy Code

This directory contains the original implementation files that have been superseded by the modular architecture.

## Files

- **Leaf.py**: Original monolithic implementation combining core logic and console interface
- **NissanLeafCharger.py**: Original implementation combining core logic and GUI interface

These files are kept for reference purposes only and are not part of the active codebase.

## Current Architecture

The current modular architecture splits functionality into:
- `leaf_core.py` - Core calculation logic
- `leaf_gui.py` - GUI interface
- `leaf_console.py` - Console interface
- `../main.py` - Entry point with CLI argument parsing
