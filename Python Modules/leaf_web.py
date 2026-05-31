"""Flask web interface for Nissan Leaf Charging Calculator.

This module provides a web-based interface optimized for iSH Alpine on iOS.
It reuses the core calculation logic from leaf_core.py and provides a
mobile-friendly, touch-optimized interface.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple

from flask import Flask, render_template, request, jsonify

# Handle imports when running directly or via main.py
try:
  from leaf_core import NissanLeafCharger, ChargingTimeCalculator
except ImportError:
  current_dir = os.path.dirname(os.path.abspath(__file__))
  sys.path.insert(0, current_dir)
  from leaf_core import NissanLeafCharger, ChargingTimeCalculator

# Flask app initialization
app = Flask(
  __name__,
  template_folder=os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'templates'
  ),
  static_folder=os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'static'
  )
)


def validate_form_input(
  form_data: Dict
) -> Tuple[bool, Optional[str], Dict]:
  """Validate all form inputs.

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
  cleaned = {}

  try:
    # Validate battery capacity
    battery_capacity = float(form_data.get('battery_capacity', 0))
    if battery_capacity not in NissanLeafCharger.BATTERY_CAPACITIES.values():
      return (
        False,
        'Battery capacity must be 40 or 62 kWh',
        {}
      )
    cleaned['battery_capacity'] = battery_capacity

    # Validate battery health
    battery_health = float(form_data.get('battery_health', 0))
    if not 0 <= battery_health <= 100:
      return (
        False,
        'Battery health must be between 0 and 100%',
        {}
      )
    cleaned['battery_health'] = battery_health

    # Validate charging rate
    charging_rate = float(form_data.get('charging_rate', 0))
    if charging_rate not in NissanLeafCharger.CHARGING_RATES.values():
      return (
        False,
        'Charging rate must be 1.4, 3.3, or 6.6 kW',
        {}
      )
    cleaned['charging_rate'] = charging_rate

    # Validate current charge
    current_charge = float(form_data.get('current_charge', 0))
    if not 0 <= current_charge <= 100:
      return (
        False,
        'Current charge must be between 0 and 100%',
        {}
      )
    cleaned['current_charge'] = current_charge

    return (True, None, cleaned)

  except (ValueError, TypeError) as e:
    return (False, f'Invalid input: {str(e)}', {})


def perform_calculation(cleaned_data: Dict) -> Dict:
  """Execute calculation and format results.

  Args:
    cleaned_data: Dictionary with validated input values.

  Returns:
    Dictionary containing:
      - start_time: Calculation timestamp
      - duration_80: Formatted time to 80% charge
      - completion_80: Datetime when 80% charge completes
      - duration_100: Formatted time to 100% charge
      - completion_100: Datetime when 100% charge completes

  Raises:
    ValueError: If calculation fails due to invalid inputs.
  """
  # Create charger instance
  charger = NissanLeafCharger()
  charger.battery_capacity = cleaned_data['battery_capacity']
  charger.battery_health = cleaned_data['battery_health']
  charger.charging_rate = cleaned_data['charging_rate']
  charger.current_charge = cleaned_data['current_charge']

  # Get start time
  start_time = datetime.now()

  # Calculate charging times
  time_to_80 = charger.calculate_charging_time(80.0)
  time_to_100 = charger.calculate_charging_time(100.0)

  # Format results
  calculator = ChargingTimeCalculator()

  results = {
    'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
    'duration_80': calculator.format_time(time_to_80),
    'completion_80': calculator.calculate_completion_time(
      start_time,
      time_to_80
    ),
    'duration_100': calculator.format_time(time_to_100),
    'completion_100': calculator.calculate_completion_time(
      start_time,
      time_to_100
    )
  }

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
  form_data = {}

  if request.method == 'POST':
    # Validate inputs
    is_valid, error_msg, cleaned_data = validate_form_input(
      request.form
    )

    if is_valid:
      try:
        # Perform calculation
        results = perform_calculation(cleaned_data)
        # Preserve form data for display
        form_data = cleaned_data
      except ValueError as e:
        error = f'Calculation error: {str(e)}'
        form_data = request.form
    else:
      error = error_msg
      form_data = request.form

  return render_template(
    'index.html',
    results=results,
    error=error,
    form_data=form_data
  )


@app.route('/calculate', methods=['POST'])
def calculate():
  """AJAX endpoint for progressive enhancement.

  Returns:
    JSON response with calculation results or error message.
  """
  # Validate inputs
  is_valid, error_msg, cleaned_data = validate_form_input(request.form)

  if not is_valid:
    return jsonify({'error': error_msg}), 400

  try:
    # Perform calculation
    results = perform_calculation(cleaned_data)
    return jsonify(results), 200
  except ValueError as e:
    return jsonify({'error': f'Calculation error: {str(e)}'}), 500


if __name__ == '__main__':
  app.run(host='127.0.0.1', port=5000, debug=False)
