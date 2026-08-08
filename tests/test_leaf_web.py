"""Unit tests for the Flask web interface.

Tests cover route accessibility, form submission, input validation,
calculation correctness, error handling, and AJAX endpoint.
"""

import sys
import os
import pytest

# Add the modules directory to path
modules_dir = os.path.join(
  os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
  "Python Modules"
)
sys.path.insert(0, modules_dir)

from leaf_web import app


@pytest.fixture
def client():
  """Create a test client for the Flask application.

  Returns:
    Flask test client for making requests.
  """
  app.config['TESTING'] = True
  with app.test_client() as client:
    yield client


class TestRoutes:
  """Test suite for Flask route accessibility."""

  def test_index_get(self, client):
    """Test GET request to index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Nissan Leaf Charging Calculator' in response.data
    assert b'Battery Configuration' in response.data
    assert b'Charging Configuration' in response.data
    assert b'Calculate Charging Time' in response.data

  def test_index_get_contains_form(self, client):
    """Test that index page contains form elements."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'battery_capacity' in response.data
    assert b'battery_health' in response.data
    assert b'charging_rate' in response.data
    assert b'current_charge' in response.data


class TestFormSubmission:
  """Test suite for form submission with valid data."""

  def test_calculate_post_valid_40kwh(self, client):
    """Test POST with valid 40 kWh battery data."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data
    assert b'80% charge' in response.data
    assert b'100% charge' in response.data

  def test_calculate_post_valid_62kwh(self, client):
    """Test POST with valid 62 kWh battery data."""
    response = client.post('/', data={
      'battery_capacity': '62',
      'battery_health': '90',
      'charging_rate': '3.3',
      'current_charge': '25'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data

  def test_calculate_post_partial_charge(self, client):
    """Test POST with partial initial charge."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '50'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data

  def test_calculate_post_degraded_battery(self, client):
    """Test POST with degraded battery health."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '80',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data

  def test_calculate_post_slow_charging(self, client):
    """Test POST with Level 1 (slow) charging."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '1.4',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data


class TestInputValidation:
  """Test suite for input validation and error handling."""

  def test_invalid_battery_capacity(self, client):
    """Test POST with invalid battery capacity."""
    response = client.post('/', data={
      'battery_capacity': '50',  # Invalid
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Error:' in response.data
    assert b'Battery capacity' in response.data

  def test_battery_health_too_high(self, client):
    """Test POST with battery health > 100%."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '150',  # Invalid
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Error:' in response.data
    assert b'Battery health' in response.data

  def test_battery_health_negative(self, client):
    """Test POST with negative battery health."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '-10',  # Invalid
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Error:' in response.data

  def test_battery_health_zero_rejected(self, client):
    """Zero battery health is rejected, not reported as '0 minutes'."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '0',  # Invalid: a 0 kWh pack
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Error:' in response.data
    assert b'0 minutes' not in response.data

  def test_battery_health_zero_preserved_in_form(self, client):
    """A submitted health of 0 is echoed back, not silently reset to 100."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '0',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert b'id="battery_health"' in response.data
    assert b'value="100"' not in response.data

  def test_invalid_charging_rate(self, client):
    """Test POST with invalid charging rate."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '5.0',  # Invalid
      'current_charge': '0'
    })
    assert response.status_code == 200
    assert b'Error:' in response.data
    assert b'Charging rate' in response.data

  def test_current_charge_too_high(self, client):
    """Test POST with current charge > 100%."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '150'  # Invalid
    })
    assert response.status_code == 200
    assert b'Error:' in response.data

  def test_current_charge_negative(self, client):
    """Test POST with negative current charge."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '-5'  # Invalid
    })
    assert response.status_code == 200
    assert b'Error:' in response.data

  def test_current_charge_above_80(self, client):
    """Test POST with current charge above 80% — valid, calculates time to 100%."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '85'
    })
    assert response.status_code == 200
    assert b'Charging Time Estimates' in response.data


class TestAjaxEndpoint:
  """Test suite for AJAX calculation endpoint."""

  def test_calculate_endpoint_valid(self, client):
    """Test /calculate endpoint with valid data."""
    response = client.post('/calculate', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'start_time' in data
    assert 'duration_80' in data
    assert 'completion_80' in data
    assert 'duration_100' in data
    assert 'completion_100' in data

  def test_calculate_endpoint_invalid(self, client):
    """Test /calculate endpoint with invalid data."""
    response = client.post('/calculate', data={
      'battery_capacity': '40',
      'battery_health': '150',  # Invalid
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

  def test_calculate_endpoint_json_format(self, client):
    """Test that /calculate returns proper JSON."""
    response = client.post('/calculate', data={
      'battery_capacity': '62',
      'battery_health': '90',
      'charging_rate': '3.3',
      'current_charge': '25'
    })
    assert response.status_code == 200
    assert response.content_type == 'application/json'

  def test_calculate_endpoint_already_at_target(self, client):
    """Charging past the 80% target reports it instead of a past timestamp."""
    response = client.post('/calculate', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '90'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['duration_80'] == 'Already at target charge'
    assert data['completion_80'] == 'Already at target charge'
    # The 100% target is still ahead, so it gets a real estimate.
    assert data['duration_100'] != 'Already at target charge'


class TestFormStatePreservation:
  """Test suite for form state preservation on errors."""

  def test_form_preserves_values_on_error(self, client):
    """Test that form values are preserved after validation error."""
    response = client.post('/', data={
      'battery_capacity': '40',
      'battery_health': '150',  # Invalid
      'charging_rate': '6.6',
      'current_charge': '25'
    })
    assert response.status_code == 200
    # Check that valid values are still in the form
    assert b'value="40"' in response.data or b'selected>40 kWh' in response.data
    assert b'value="6.6"' in response.data or b'selected>Level 2 (240V) - 6.6 kW' in response.data


class TestCalculationAccuracy:
  """Test suite for calculation accuracy."""

  def test_calculation_with_known_values(self, client):
    """Test calculation with known expected results."""
    # 40 kWh battery, 100% health, 6.6 kW charging, 0% to 80%
    # Expected: ~4.8 hours
    response = client.post('/calculate', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    data = response.get_json()

    # Check that duration is reasonable (should be around 4-5 hours)
    assert 'hour' in data['duration_80'].lower()

  def test_calculation_results_differ_by_target(self, client):
    """Test that 80% and 100% targets give different results."""
    response = client.post('/calculate', data={
      'battery_capacity': '40',
      'battery_health': '100',
      'charging_rate': '6.6',
      'current_charge': '0'
    })
    assert response.status_code == 200
    data = response.get_json()

    # 100% should take longer than 80%
    assert data['duration_80'] != data['duration_100']


if __name__ == '__main__':
  pytest.main([__file__, '-v'])
