# Future Enhancements

## Outstanding

1. **Output reports**: Allow exporting a summary of inputs and computed finish times to text or CSV for record keeping.
2. **Configurable inefficiency factor**: Surface the 10% energy overhead as a user-adjustable setting to account for charger efficiency differences. It is currently the class constant `NissanLeafCharger.INEFFICIENCY_FACTOR`, so the plumbing exists — it just is not exposed in any interface.
3. **More scenario presets**: Only `home` and `work` exist. A road-trip / DC fast-charge preset would need CHAdeMO support in `CHARGING_RATES` first, along with a much steeper taper curve than the AC one.

## Done

- **Improve CLI flow** — `--battery`, `--health`, `--current`, `--rate`, `--target` and `--preset` are accepted by `leaf_calculator/cli.py`. Supplying any of them prints a one-shot estimate with no prompts; combining them with an interface flag pre-populates that interface instead.
- **Shared validation helpers** — the validators live in `leaf_core.py` and are used by all four front ends. Range and choice checks are now defined exactly once.
- **Scenario presets** — `home` (6.6 kW to 80%) and `work` (3.3 kW to 100%), in `leaf_core.PRESETS`. Selectable from the command line, console menu, GUI dropdown and web form. Presets set rate and target only; battery capacity, health and current charge describe the car, not the scenario.
- **Charge taper modeling** — `NissanLeafCharger` models the BMS slowdown as a linear rate decline from `TAPER_START_PERCENT` (80%) to `TAPER_END_RATE_FRACTION` (25%) at 100%, integrated logarithmically. On by default; `--no-taper` or the interface toggles restore the constant-rate behaviour. Targets at or below 80% are unaffected.
- **Automated tests** — 171 tests across core, CLI, console, GUI, web and integration.
