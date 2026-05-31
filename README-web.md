# Nissan Leaf Calculator - Web Interface

Flask-based web interface optimized for iSH Alpine on iOS iPhone.

## Features

- Mobile-friendly, touch-optimized design
- Works on iOS Safari in iSH Alpine
- All calculation features from GUI/console versions
- Progressive enhancement with AJAX
- Graceful degradation without JavaScript
- Lightweight and fast (minimal dependencies)

## Prerequisites

### On iSH Alpine (iOS)

1. Update package manager:
   ```sh
   apk update
   apk upgrade
   ```

2. Install Python 3 and pip:
   ```sh
   apk add python3 py3-pip
   ```

3. Install Flask:
   ```sh
   pip3 install Flask
   ```

### On Other Systems

1. Ensure Python 3.8+ is installed:
   ```sh
   python3 --version
   ```

2. Install Flask:
   ```sh
   pip3 install Flask
   ```

   Or using the requirements file:
   ```sh
   pip3 install -r requirements.txt
   ```

## Running the Web Interface

### Method 1: Using main.py (Recommended)

```sh
python3 main.py --web
```

Or using the short flag:
```sh
python3 main.py -w
```

### Method 2: Running leaf_web.py directly

```sh
cd "Python Modules"
python3 leaf_web.py
```

## Accessing the Interface

1. After starting the server, you'll see:
   ```
   Starting Nissan Leaf Calculator web server...
   Access the calculator at: http://localhost:5000
   Press Ctrl+C to stop the server
   ```

2. Open Safari on your iOS device and navigate to:
   ```
   http://localhost:5000
   ```

3. (Optional) Add to Home Screen for an app-like experience:
   - Tap the Share button in Safari
   - Select "Add to Home Screen"
   - Name it "Leaf Calculator"
   - Tap "Add"

## Using the Calculator

### Input Fields

1. **Battery Capacity**: Select 40 kWh or 62 kWh
2. **Battery Health**: Enter percentage (0-100%)
3. **Charging Rate**: Select charging level:
   - Level 1 (120V): 1.4 kW
   - Level 2 (240V): 3.3 kW or 6.6 kW
4. **Current Charge**: Enter current battery percentage (0-100%)

### Calculating Charging Times

1. Fill in all form fields
2. Tap "Calculate Charging Time"
3. View results showing:
   - Time to reach 80% charge (recommended)
   - Time to reach 100% charge (full)
   - Estimated completion times

### Progressive Enhancement

The interface uses AJAX for smoother calculations without page reload.
If JavaScript is disabled or unavailable, it falls back to traditional
form submission with page reload.

## Performance Tips for iSH Alpine

### Memory Management

- Close other apps to free memory
- Avoid opening multiple browser tabs
- Use WiFi instead of cellular for localhost access

### Flask Server

- The server runs in production mode (debug=False) for better performance
- Single-process mode minimizes resource usage
- Static assets are cached for faster subsequent loads

### Browser Tips

- Use Safari's private browsing mode to prevent cache buildup
- Clear Safari cache periodically: Settings > Safari > Clear History
- Enable Safari's "Request Desktop Website" for larger touch targets

## Troubleshooting

### Port Already in Use

**Error**: `Address already in use`

**Solutions**:
1. Kill the process using port 5000:
   ```sh
   kill $(lsof -ti:5000)
   ```

2. Or use a different port (requires modifying `leaf_web.py`):
   ```python
   app.run(host='127.0.0.1', port=5001, debug=False)
   ```

### Flask Not Found

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**: Install Flask:
```sh
pip3 install Flask
```

### Slow Performance

**Symptoms**: Server responds slowly, calculations take too long

**Solutions**:
1. Ensure iSH has sufficient resources:
   - Close other apps
   - Restart iSH if it's been running for a long time

2. Check available memory:
   ```sh
   free -h
   ```

3. Disable JavaScript if AJAX is causing issues:
   - Safari Settings > Advanced > JavaScript (toggle off)

### CSS/JavaScript Not Loading

**Symptoms**: Page loads but looks unstyled, or AJAX doesn't work

**Solutions**:
1. Check that static files exist:
   ```sh
   ls static/
   # Should show: style.css  app.js
   ```

2. Clear browser cache and reload

3. Check Flask logs for 404 errors

### Template Not Found

**Error**: `TemplateNotFound: index.html`

**Solution**: Ensure templates directory exists:
```sh
ls templates/
# Should show: index.html
```

### Calculation Errors

**Symptoms**: Error messages about invalid inputs

**Common Issues**:
- Battery health must be 0-100%
- Current charge must be less than 80% (can't calculate to 80% if already above)
- Only specific charging rates are supported (1.4, 3.3, 6.6 kW)
- Only specific battery capacities are supported (40, 62 kWh)

## Testing

### Running Tests

```sh
pytest tests/test_leaf_web.py -v
```

### Test Coverage

The test suite covers:
- Route accessibility (GET /)
- Form submission (POST /)
- Input validation (invalid ranges)
- Calculation correctness
- Error handling (400/500 responses)
- AJAX endpoint (/calculate)
- Form state preservation on errors

### Running Specific Tests

```sh
# Test routes only
pytest tests/test_leaf_web.py::TestRoutes -v

# Test validation only
pytest tests/test_leaf_web.py::TestInputValidation -v

# Test AJAX endpoint
pytest tests/test_leaf_web.py::TestAjaxEndpoint -v
```

## Technical Details

### Architecture

- **Backend**: Flask 2.3+ (Python web framework)
- **Frontend**: HTML5, CSS3, vanilla JavaScript
- **Calculation Engine**: Reuses `leaf_core.py` (same as GUI/console)
- **Template Engine**: Jinja2 (built-in with Flask)

### File Structure

```
nissan-leaf-calculator/
├── Python Modules/
│   ├── leaf_core.py       # Core calculation logic (shared)
│   ├── leaf_web.py         # Flask application
│   ├── leaf_gui.py         # GUI interface (tkinter)
│   └── leaf_console.py     # Console interface
├── templates/
│   └── index.html          # Main HTML template
├── static/
│   ├── style.css           # Mobile-first responsive CSS
│   └── app.js              # AJAX progressive enhancement
├── tests/
│   └── test_leaf_web.py    # Flask route tests
├── main.py                 # Entry point with --web flag
└── README-web.md           # This file
```

### URL Routes

- `GET /`: Display calculation form
- `POST /`: Process form and display results
- `POST /calculate`: AJAX endpoint (returns JSON)

### Response Formats

**HTML Response** (traditional POST):
```html
<section class="results">
  <h2>Charging Time Estimates</h2>
  <table>...</table>
</section>
```

**JSON Response** (AJAX endpoint):
```json
{
  "start_time": "2024-01-01 10:00:00",
  "duration_80": "4 hours 48 minutes",
  "completion_80": "2024-01-01 14:48:00",
  "duration_100": "6 hours 40 minutes",
  "completion_100": "2024-01-01 16:40:00"
}
```

**Error Response** (validation failure):
```json
{
  "error": "Battery health must be between 0 and 100%"
}
```

## Code Style

The web interface follows the same code style as the rest of the project:

- **Indentation**: 2 spaces
- **Type hints**: Full typing annotations
- **Docstrings**: Google style with Args/Returns/Raises
- **Imports**: Grouped (stdlib, third-party, local)
- **Line length**: 80 characters

## Security Considerations

### Input Validation

- All inputs validated server-side (never trust client)
- Type coercion with exception handling
- Range checks enforced (0-100 for percentages)

### XSS Protection

- Flask auto-escapes Jinja2 templates
- JavaScript uses `textContent` instead of `innerHTML` where possible
- All user input is sanitized before display

### CSRF Protection

Not implemented (stateless application, no user accounts).
If adding user authentication, consider using Flask-WTF for CSRF tokens.

## Future Enhancements

Possible improvements for future versions:

1. **PWA Support**: Service worker for offline functionality
2. **Dark Mode Toggle**: User-controlled theme switching
3. **Charging Presets**: Quick buttons for common scenarios
4. **History**: Local storage of previous calculations
5. **Charts**: Visual graph showing charge over time
6. **Multi-language**: Internationalization support
7. **API Mode**: RESTful JSON API for external integrations

## Support

For issues or questions:

1. Check this README's Troubleshooting section
2. Verify you're using Python 3.8+ and Flask 2.3+
3. Ensure all files are in the correct locations
4. Check Flask logs for error messages

## License

Same license as the main Nissan Leaf Calculator project.

## Credits

- Web interface optimized for iSH Alpine on iOS
- Reuses core calculation logic from the original calculator
- Mobile-first design with progressive enhancement
- Nissan brand colors and styling
