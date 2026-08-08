"""Persistent user settings.

Battery health is a property of a particular car that changes slowly over
years, so it is remembered between runs rather than re-entered every session.
Settings live in the user's config directory, deliberately outside the project
tree -- this repository is kept on pCloud, and sync conflicts would corrupt a
file stored alongside the code.

Every function here is best-effort: a missing, unreadable or malformed config
file falls back to the default, and a failed write is reported but never
raises. Losing a remembered preference must not break the calculator.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from .leaf_core import validate_battery_health

# Environment variable that overrides the config file location outright.
CONFIG_ENV_VAR = 'LEAF_CALCULATOR_CONFIG'

APP_DIR_NAME = 'nissan-leaf-calculator'
CONFIG_FILE_NAME = 'config.json'

DEFAULT_BATTERY_HEALTH = 100.0


def config_path() -> Path:
    """Return the path of the settings file.

    Honours LEAF_CALCULATOR_CONFIG for an explicit override, then
    XDG_CONFIG_HOME, then falls back to ~/.config.

    Returns:
        Path to the JSON settings file. It may not exist yet.
    """
    override = os.environ.get(CONFIG_ENV_VAR)
    if override:
        return Path(override).expanduser()

    xdg = os.environ.get('XDG_CONFIG_HOME')
    base = Path(xdg).expanduser() if xdg else Path.home() / '.config'
    return base / APP_DIR_NAME / CONFIG_FILE_NAME


def load_settings() -> Dict[str, Any]:
    """Read the settings file.

    Returns:
        The stored settings, or an empty dict if the file is missing,
        unreadable or not a JSON object.
    """
    path = config_path()
    try:
        with path.open(encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        # Missing, unreadable, or malformed: fall back to defaults.
        return {}

    if not isinstance(data, dict):
        return {}
    return data


def save_settings(settings: Dict[str, Any]) -> bool:
    """Write the settings file atomically.

    The write goes to a temporary file in the same directory and is then
    renamed, so an interrupted run cannot leave a half-written config behind.

    Args:
        settings: Values to store.

    Returns:
        True if the file was written, False if it could not be.
    """
    path = config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            mode='w',
            encoding='utf-8',
            dir=path.parent,
            prefix=f'.{path.name}.',
            suffix='.tmp',
            delete=False
        )
        try:
            with handle:
                json.dump(settings, handle, indent=2, sort_keys=True)
                handle.write('\n')
            os.replace(handle.name, path)
        except BaseException:
            # Never leave the temporary file behind on failure.
            try:
                os.unlink(handle.name)
            except OSError:
                pass
            raise
    except OSError:
        return False
    return True


def load_battery_health(
        default: float = DEFAULT_BATTERY_HEALTH
) -> float:
    """Read the remembered battery health.

    Args:
        default: Value to use when nothing valid is stored.

    Returns:
        The stored battery health, or the default if absent or invalid.
    """
    stored = load_settings().get('battery_health')
    if stored is None:
        return default

    try:
        return validate_battery_health(stored)
    except ValueError:
        # A hand-edited or corrupted value should not wedge the app.
        return default


def save_battery_health(value: float) -> bool:
    """Remember the battery health for future runs.

    Args:
        value: Battery health percentage; validated before being stored.

    Returns:
        True if the value was written, False otherwise.

    Raises:
        ValueError: If the value is not a valid battery health percentage.
    """
    health = validate_battery_health(value)
    settings = load_settings()
    if settings.get('battery_health') == health:
        # Nothing changed; skip the write entirely.
        return True

    settings['battery_health'] = health
    return save_settings(settings)


def remember_battery_health(value: float) -> Optional[str]:
    """Persist battery health, converting any problem into a message.

    Convenience wrapper for interfaces that want to report a failure inline
    rather than handle exceptions.

    Args:
        value: Battery health percentage.

    Returns:
        None on success, or a short message explaining why it was not saved.
    """
    try:
        if save_battery_health(value):
            return None
    except ValueError as exc:
        return str(exc)
    return f'Could not save battery health to {config_path()}'
