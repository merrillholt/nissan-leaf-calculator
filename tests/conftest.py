"""Shared pytest fixtures.

The autouse fixture here is load-bearing: without it the persistence tests
would read and overwrite the developer's real settings file in ~/.config.
"""

import pytest

from leaf_calculator import settings


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    """Point the settings file at a temporary directory for every test.

    Yields:
        Path of the temporary settings file, which does not exist initially.
    """
    config = tmp_path / 'config' / 'config.json'
    monkeypatch.setenv(settings.CONFIG_ENV_VAR, str(config))
    yield config
