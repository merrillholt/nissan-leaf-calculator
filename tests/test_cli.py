"""Tests for the command-line interface.

Covers the charge-parameter flags (ENHANCEMENTS #1) and the scenario preset
flag (ENHANCEMENTS #3), including how the two interact.
"""

import pytest

from leaf_calculator.cli import build_parser, configure_charger, main


def parse(*argv):
    """Parse arguments and return the configured charger."""
    return configure_charger(build_parser().parse_args(list(argv)))


class TestChargeFlags:
    """Charge parameters supplied without prompts."""

    def test_defaults_when_nothing_supplied(self):
        charger = parse()
        assert charger.battery_capacity == 40.0
        assert charger.battery_health == 100.0
        assert charger.current_charge == 0.0
        assert charger.charging_rate == 6.6
        assert charger.targets == [80.0, 100.0]

    def test_each_flag_is_applied(self):
        charger = parse(
            '--battery', '62', '--health', '85',
            '--current', '30', '--rate', '3.3'
        )
        assert charger.battery_capacity == 62.0
        assert charger.battery_health == 85.0
        assert charger.current_charge == 30.0
        assert charger.charging_rate == 3.3

    def test_target_is_repeatable(self):
        charger = parse('--target', '50', '--target', '80', '-t', '100')
        assert charger.targets == [50.0, 80.0, 100.0]

    def test_short_flags(self):
        charger = parse('-b', '62', '-r', '1.4', '-t', '90')
        assert charger.battery_capacity == 62.0
        assert charger.charging_rate == 1.4
        assert charger.targets == [90.0]

    def test_no_taper_flag(self):
        assert parse().model_taper is True
        assert parse('--no-taper').model_taper is False

    @pytest.mark.parametrize('argv', [
        ('--health', '0'),
        ('--health', '150'),
        ('--current', '-5'),
        ('--battery', '50'),
        ('--rate', '5.0'),
        ('--target', '101'),
        ('--target', 'abc'),
    ])
    def test_invalid_values_are_rejected(self, argv, capsys):
        with pytest.raises(SystemExit):
            build_parser().parse_args(list(argv))
        # The validator's own message reaches the user, not argparse's
        # generic "invalid <function> value".
        assert 'must be' in capsys.readouterr().err

    def test_conflicting_interfaces_rejected(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(['--console', '--web'])


class TestPresetFlag:
    """The --preset flag and its interaction with explicit flags."""

    def test_home_preset(self):
        charger = parse('--preset', 'home')
        assert charger.charging_rate == 6.6
        assert charger.targets == [80.0]

    def test_work_preset(self):
        charger = parse('-p', 'work')
        assert charger.charging_rate == 3.3
        assert charger.targets == [100.0]

    def test_explicit_flags_override_the_preset(self):
        """The preset is a starting point, not a lock."""
        charger = parse('--preset', 'work', '--rate', '6.6', '--target', '80')
        assert charger.charging_rate == 6.6
        assert charger.targets == [80.0]

    def test_preset_combines_with_car_details(self):
        charger = parse(
            '--preset', 'home', '--battery', '62', '--current', '40'
        )
        assert charger.charging_rate == 6.6
        assert charger.targets == [80.0]
        assert charger.battery_capacity == 62.0
        assert charger.current_charge == 40.0

    def test_unknown_preset_rejected(self):
        with pytest.raises(SystemExit):
            build_parser().parse_args(['--preset', 'roadtrip'])


class TestOneShotReport:
    """Charge flags with no interface flag print a report and exit."""

    def test_report_is_printed(self, capsys):
        main(['--battery', '40', '--health', '90', '--current', '25',
              '--target', '80'])
        out = capsys.readouterr().out
        assert 'Battery Capacity: 40 kWh' in out
        assert 'Battery Health:   90%' in out
        assert 'To 80% charge:' in out
        assert '3 hours 18 minutes' in out
        assert 'Completion time:' in out

    def test_report_covers_every_target(self, capsys):
        main(['--current', '0', '-t', '50', '-t', '80', '-t', '100'])
        out = capsys.readouterr().out
        for target in ('50', '80', '100'):
            assert f'To {target}% charge:' in out

    def test_report_states_whether_taper_is_modelled(self, capsys):
        main(['--current', '10'])
        assert 'Charge Taper:     modelled' in capsys.readouterr().out

        main(['--current', '10', '--no-taper'])
        assert 'Charge Taper:     ignored' in capsys.readouterr().out

    def test_preset_alone_triggers_a_report(self, capsys):
        main(['--preset', 'home'])
        out = capsys.readouterr().out
        assert 'To 80% charge:' in out
        assert 'To 100% charge:' not in out

    def test_no_taper_alone_does_not_trigger_a_report(self):
        """--no-taper is a modifier, not a charge parameter."""
        args = build_parser().parse_args(['--no-taper'])
        assert not any(
            getattr(args, name, None)
            for name in ('battery', 'health', 'current', 'target', 'preset')
        )
