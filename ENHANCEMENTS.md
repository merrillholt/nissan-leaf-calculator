# Future Enhancements

1. **Improve CLI flow**: Accept optional charge parameters via command-line flags (e.g., `--battery`, `--health`, `--current`, `--target`) so presets can be supplied without prompts.
2. **Shared validation helpers**: Move duplicated numeric validation logic from the console and GUI front ends into shared utilities inside `leaf_core.py` or a helper module.
3. **Scenario presets**: Offer common charging profiles (home overnight, workplace top-up, road trip fast charge) selectable from both interfaces to pre-populate rates and targets.
4. **Output reports**: Allow exporting a summary of inputs and computed finish times to text or CSV for record keeping.
5. **Configurable inefficiency factor**: Surface the 10% energy overhead as a user-adjustable setting to account for charger efficiency differences.
6. **Automated tests**: Add pytest coverage for the core calculations, especially percentage validation and no-rate edge cases.
