"""Flask web interface for Nissan Leaf Charging Calculator.

This module provides a web-based interface optimized for iSH Alpine on iOS.
It reuses the core calculation logic from leaf_core.py and provides a
mobile-friendly, touch-optimized interface.
"""

from datetime import datetime
from typing import Dict, List, Mapping, Optional, Tuple

from flask import Flask, render_template, request, jsonify

from .leaf_core import (
  DEFAULT_TARGETS,
  PRESETS,
  NissanLeafCharger,
  summarize,
  validate_battery_capacity,
  validate_battery_health,
  validate_charging_rate,
  validate_current_charge,
  validate_target_percentage,
)

# templates/ and static/ sit inside this package, which is where Flask looks
# by default -- so they resolve correctly whether the app runs from a source
# checkout or an installed wheel.
app = Flask(__name__)


def parse_targets(raw: Optional[str]) -> List[float]:
  """Parse a comma-separated list of target percentages.

  Args:
    raw: Raw form value; blank or missing yields the defaults.

  Returns:
    Validated target percentages.

  Raises:
    ValueError: If any entry is not a valid percentage.
  """
  if not raw or not raw.strip():
    return list(DEFAULT_TARGETS)

  targets = [
    validate_target_percentage(part)
    for part in raw.split(',') if part.strip()
  ]
  if not targets:
    return list(DEFAULT_TARGETS)
  return targets


def read_taper_flag(form_data: Mapping[str, str]) -> bool:
  """Read the charge-taper toggle from submitted form data.

  The form pairs a hidden 'off' field with the checkbox so that unchecking
  it submits something rather than nothing; the last value wins. Callers
  that omit the field entirely (the JSON clients) get the default, which is
  to model the taper.

  Args:
    form_data: Submitted form values.

  Returns:
    True if the taper should be modelled.
  """
  if hasattr(form_data, 'getlist'):
    values = form_data.getlist('model_taper')
  else:
    raw = form_data.get('model_taper')
    values = [raw] if raw is not None else []

  if not values:
    return True
  return bool(values[-1] != 'off')


def validate_form_input(
  form_data: Mapping[str, str]
) -> Tuple[bool, Optional[str], Dict]:
  """Validate all form inputs.

  Delegates every range and choice check to the shared validators in
  leaf_core, so the web form accepts exactly what the other front ends do.

  Args:
    form_data: Dictionary containing form field values.

  Returns:
    Tuple of (is_valid, error_message, cleaned_data):
      - is_valid: True if all inputs are valid
      - error_message: Error description if invalid, None otherwise
      - cleaned_data: Dictionary with validated and converted values

  Raises:
    None: All errors returned as part of the tuple.
  """
  preset_key = (form_data.get('preset') or '').strip().lower()

  try:
    cleaned = {
      'battery_capacity': validate_battery_capacity(
        form_data.get('battery_capacity', '')
      ),
      'battery_health': validate_battery_health(
        form_data.get('battery_health', '')
      ),
      'charging_rate': validate_charging_rate(
        form_data.get('charging_rate', '')
      ),
      'current_charge': validate_current_charge(
        form_data.get('current_charge', '')
      ),
      'targets': parse_targets(form_data.get('targets')),
      'model_taper': read_taper_flag(form_data),
      'preset': preset_key,
    }
  except ValueError as exc:
    return (False, str(exc), {})

  if preset_key and preset_key not in PRESETS:
    options = ', '.join(sorted(PRESETS))
    return (False, f'Preset must be one of: {options}', {})

  return (True, None, cleaned)


def build_charger(cleaned_data: Dict) -> NissanLeafCharger:
  """Build a charger from validated form data.

  The preset is applied first so explicit form fields win over it, matching
  how the command line resolves the same conflict.

  Args:
    cleaned_data: Dictionary with validated input values.

  Returns:
    A configured NissanLeafCharger.
  """
  charger = NissanLeafCharger()
  if cleaned_data.get('preset'):
    charger.apply_preset(cleaned_data['preset'])

  charger.battery_capacity = cleaned_data['battery_capacity']
  charger.battery_health = cleaned_data['battery_health']
  charger.charging_rate = cleaned_data['charging_rate']
  charger.current_charge = cleaned_data['current_charge']
  charger.model_taper = cleaned_data['model_taper']
  charger.targets = cleaned_data['targets']
  return charger


def perform_calculation(cleaned_data: Dict) -> Dict:
  """Execute calculation and format results.

  Args:
    cleaned_data: Dictionary with validated input values.

  Returns:
    Dictionary containing:
      - start_time: Calculation timestamp
      - results: One entry per target, each with target, duration and
        completion keys
      - duration_80 / completion_80 / duration_100 / completion_100: kept
        for the 80% and 100% targets so existing clients keep working

  Raises:
    ValueError: If calculation fails due to invalid inputs.
  """
  charger = build_charger(cleaned_data)
  start_time = datetime.now()
  rows = summarize(charger, start_time)

  results: Dict = {
    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
    'model_taper': charger.model_taper,
    'results': [
      {
        'target': row['target'],
        'duration': row.get('duration', row.get('error')),
        'completion': row.get('completion', row.get('error')),
      }
      for row in rows
    ],
  }

  # Flat keys for the standard targets, preserving the original response
  # shape for the AJAX client and anything else already parsing it.
  for row in rows:
    if row['target'] in (80.0, 100.0):
      suffix = f'{row["target"]:g}'
      results[f'duration_{suffix}'] = row.get('duration', row.get('error'))
      results[f'completion_{suffix}'] = row.get(
        'completion', row.get('error')
      )

  return results


@app.route('/', methods=['GET', 'POST'])
def index():
  """Main route: display form and results.

  Handles both GET (initial page load) and POST (form submission).

  Returns:
    Rendered HTML template with form and optional results.
  """
  results = None
  error = None
  form_data: Mapping[str, str] = {}

  if request.method == 'POST':
    is_valid, error_msg, cleaned_data = validate_form_input(request.form)

    # Always echo back exactly what the user submitted, so the repopulated
    # form shows '90' rather than the parsed '90.0'.
    form_data = request.form

    if is_valid:
      try:
        results = perform_calculation(cleaned_data)
      except ValueError as e:
        error = f'Calculation error: {str(e)}'
    else:
      error = error_msg

  return render_template(
    'index.html',
    results=results,
    error=error,
    form_data=form_data,
    presets=list(PRESETS.values()),
    default_targets=', '.join(f'{t:g}' for t in DEFAULT_TARGETS)
  )


@app.route('/calculate', methods=['POST'])
def calculate():
  """AJAX endpoint for progressive enhancement.

  Returns:
    JSON response with calculation results or error message.
  """
  is_valid, error_msg, cleaned_data = validate_form_input(request.form)

  if not is_valid:
    return jsonify({'error': error_msg}), 400

  try:
    results = perform_calculation(cleaned_data)
    return jsonify(results), 200
  except ValueError as e:
    # The calculator only raises ValueError for out-of-range inputs, so this
    # is a bad request, not a server fault.
    return jsonify({'error': f'Calculation error: {str(e)}'}), 400


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000, debug=False)
