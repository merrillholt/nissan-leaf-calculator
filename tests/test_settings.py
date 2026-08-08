"""Tests for persistent user settings.

The isolated_settings fixture in conftest.py redirects the config file to a
temporary path, so nothing here touches the real ~/.config.
"""

import json
import os

import pytest

from leaf_calculator import settings
from leaf_calculator.cli import build_parser, configure_charger, main


class TestConfigPath:
    """Where the settings file lives."""

    def test_explicit_override_wins(self, tmp_path, monkeypatch):
        target = tmp_path / 'custom.json'
        monkeypatch.setenv(settings.CONFIG_ENV_VAR, str(target))
        assert settings.config_path() == target

    def test_falls_back_to_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.delenv(settings.CONFIG_ENV_VAR, raising=False)
        monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
        assert settings.config_path() == (
            tmp_path / settings.APP_DIR_NAME / settings.CONFIG_FILE_NAME
        )

    def test_falls_back_to_dot_config(self, tmp_path, monkeypatch):
        monkeypatch.delenv(settings.CONFIG_ENV_VAR, raising=False)
        monkeypatch.delenv('XDG_CONFIG_HOME', raising=False)
        monkeypatch.setattr(settings.Path, 'home', staticmethod(lambda: tmp_path))
        assert settings.config_path() == (
            tmp_path / '.config' / settings.APP_DIR_NAME
            / settings.CONFIG_FILE_NAME
        )

    def test_config_lives_outside_the_project_tree(self, monkeypatch):
        """The repo is kept on pCloud; sync would corrupt an in-tree file."""
        monkeypatch.delenv(settings.CONFIG_ENV_VAR, raising=False)
        assert 'nissan-leaf-calculator/leaf_calculator' not in str(
            settings.config_path()
        )


class TestRoundTrip:
    """Reading back what was written."""

    def test_default_when_nothing_stored(self):
        assert settings.load_battery_health() == 100.0

    def test_saved_value_is_read_back(self):
        assert settings.save_battery_health(87.5) is True
        assert settings.load_battery_health() == 87.5

    def test_creates_parent_directories(self, isolated_settings):
        assert not isolated_settings.parent.exists()
        settings.save_battery_health(90)
        assert isolated_settings.exists()

    def test_file_is_readable_json(self, isolated_settings):
        settings.save_battery_health(72)
        data = json.loads(isolated_settings.read_text())
        assert data == {'battery_health': 72.0}

    def test_unrelated_keys_are_preserved(self, isolated_settings):
        isolated_settings.parent.mkdir(parents=True)
        isolated_settings.write_text('{"something_else": "keep me"}')
        settings.save_battery_health(65)
        data = json.loads(isolated_settings.read_text())
        assert data['something_else'] == 'keep me'
        assert data['battery_health'] == 65.0

    def test_repeated_save_of_same_value_is_a_no_op(self, isolated_settings):
        settings.save_battery_health(80)
        first = isolated_settings.stat().st_mtime_ns
        assert settings.save_battery_health(80) is True
        assert isolated_settings.stat().st_mtime_ns == first

    def test_invalid_value_is_rejected(self):
        for bad in (0, -5, 101, 'abc'):
            with pytest.raises(ValueError):
                settings.save_battery_health(bad)


class TestResilience:
    """A bad config file must never break the calculator."""

    def test_missing_file(self):
        assert settings.load_settings() == {}
        assert settings.load_battery_health() == 100.0

    def test_malformed_json(self, isolated_settings):
        isolated_settings.parent.mkdir(parents=True)
        isolated_settings.write_text('{not json at all')
        assert settings.load_settings() == {}
        assert settings.load_battery_health() == 100.0

    def test_json_that_is_not_an_object(self, isolated_settings):
        isolated_settings.parent.mkdir(parents=True)
        isolated_settings.write_text('[1, 2, 3]')
        assert settings.load_settings() == {}
        assert settings.load_battery_health() == 100.0

    def test_out_of_range_stored_value_falls_back(self, isolated_settings):
        """A hand-edited value must not wedge the app."""
        isolated_settings.parent.mkdir(parents=True)
        isolated_settings.write_text('{"battery_health": 500}')
        assert settings.load_battery_health() == 100.0

    def test_non_numeric_stored_value_falls_back(self, isolated_settings):
        isolated_settings.parent.mkdir(parents=True)
        isolated_settings.write_text('{"battery_health": "ninety"}')
        assert settings.load_battery_health() == 100.0

    def test_unwritable_location_reports_rather_than_raises(
            self, tmp_path, monkeypatch
    ):
        blocked = tmp_path / 'blocked'
        blocked.mkdir()
        blocked.chmod(0o500)
        monkeypatch.setenv(
            settings.CONFIG_ENV_VAR, str(blocked / 'sub' / 'config.json')
        )
        try:
            assert settings.save_settings({'battery_health': 90}) is False
            assert settings.remember_battery_health(90) is not None
        finally:
            blocked.chmod(0o700)

    def test_no_temporary_files_left_behind(self, isolated_settings):
        settings.save_battery_health(88)
        leftovers = [
            name for name in os.listdir(isolated_settings.parent)
            if name != isolated_settings.name
        ]
        assert leftovers == []


class TestCliIntegration:
    """Battery health persists across command-line runs."""

    def test_health_flag_is_remembered(self):
        main(['--health', '85', '--current', '10'])
        assert settings.load_battery_health() == 85.0

    def test_remembered_health_is_used_next_run(self):
        settings.save_battery_health(78)
        charger = configure_charger(build_parser().parse_args([]))
        assert charger.battery_health == 78.0

    def test_remembered_health_shows_in_the_report(self, capsys):
        settings.save_battery_health(83)
        main(['--current', '20'])
        assert 'Battery Health:   83%' in capsys.readouterr().out

    def test_no_save_leaves_the_stored_value_alone(self):
        """One-off what-if queries must not clobber the real value."""
        settings.save_battery_health(90)
        main(['--health', '50', '--current', '10', '--no-save'])
        assert settings.load_battery_health() == 90.0

    def test_no_save_still_uses_the_supplied_value(self, capsys):
        settings.save_battery_health(90)
        main(['--health', '50', '--current', '10', '--no-save'])
        assert 'Battery Health:   50%' in capsys.readouterr().out

    def test_explicit_health_overrides_the_stored_value(self):
        settings.save_battery_health(70)
        charger = configure_charger(
            build_parser().parse_args(['--health', '95'])
        )
        assert charger.battery_health == 95.0

    def test_no_save_is_not_a_charge_flag(self, capsys):
        """--no-save alone must not trigger a one-shot report."""
        args = build_parser().parse_args(['--no-save'])
        assert args.no_save is True
        assert args.health is None


class TestWebIntegration:
    """Battery health persists across web submissions."""

    @pytest.fixture
    def client(self):
        from leaf_calculator.leaf_web import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    BASE = {
        'battery_capacity': '40',
        'charging_rate': '6.6',
        'current_charge': '0',
    }

    def test_submission_is_remembered(self, client):
        client.post('/', data={**self.BASE, 'battery_health': '82'})
        assert settings.load_battery_health() == 82.0

    def test_fresh_form_shows_the_remembered_value(self, client):
        settings.save_battery_health(76)
        response = client.get('/')
        assert b'value="76"' in response.data

    def test_fresh_form_defaults_to_100_when_nothing_stored(self, client):
        response = client.get('/')
        assert b'value="100"' in response.data

    def test_invalid_submission_is_not_remembered(self, client):
        settings.save_battery_health(88)
        client.post('/', data={**self.BASE, 'battery_health': '150'})
        assert settings.load_battery_health() == 88.0

    def test_fresh_form_keeps_its_other_defaults(self, client):
        """Seeding health must not break the other field defaults."""
        response = client.get('/')
        assert b'<option value="40" selected>40 kWh</option>' in response.data
        assert b'value="6.6" selected' in response.data


class TestConsoleIntegration:
    """Battery health persists across console sessions."""

    def test_setting_health_is_remembered(self):
        from unittest.mock import patch
        from leaf_calculator.leaf_console import ConsoleInterface

        console = ConsoleInterface()
        with patch('builtins.input', side_effect=['92']):
            with patch('builtins.print'):
                console._set_battery_health()

        assert console.charger.battery_health == 92.0
        assert settings.load_battery_health() == 92.0

    def test_quitting_the_prompt_stores_nothing(self):
        from unittest.mock import patch
        from leaf_calculator.leaf_console import ConsoleInterface

        settings.save_battery_health(60)
        console = ConsoleInterface()
        with patch('builtins.input', side_effect=['q']):
            with patch('builtins.print'):
                console._set_battery_health()

        assert settings.load_battery_health() == 60.0
