/**
 * Nissan Leaf Charging Calculator - Progressive Enhancement
 * AJAX form submission for smoother UX with graceful degradation
 */

(function() {
  'use strict';

  // Feature detection - only enhance if browser supports required features
  if (!('fetch' in window) || !('FormData' in window)) {
    // Fall back to traditional form submission
    return;
  }

  // Get form element
  const form = document.getElementById('calculator-form');
  if (!form) {
    return;
  }

  // Add submit event listener
  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Get form elements
    const button = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);

    // Set loading state
    const originalButtonText = button.textContent;
    button.disabled = true;
    button.textContent = 'Calculating...';
    button.classList.add('loading');

    try {
      // Send AJAX request to calculate endpoint
      const response = await fetch('/calculate', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle error response
        displayError(data.error || 'Calculation failed');
        return;
      }

      // Update results without page reload
      updateResults(data);
      clearError();

    } catch (error) {
      // Network error or other failure - fall back to traditional submit
      console.error('AJAX request failed:', error);
      form.submit();
    } finally {
      // Reset button state
      button.disabled = false;
      button.textContent = originalButtonText;
      button.classList.remove('loading');
    }
  });

  /**
   * Update results section with calculation data
   * @param {Object} data - Calculation results
   */
  function updateResults(data) {
    // Check if results section exists
    let resultsSection = document.querySelector('.results');

    if (!resultsSection) {
      // Create results section if it doesn't exist
      resultsSection = createResultsSection();
      document.querySelector('.container').appendChild(resultsSection);
    }

    // Update start time
    const startTimeEl = document.querySelector('.start-time');
    if (startTimeEl) {
      startTimeEl.innerHTML = '<strong>Calculation Time:</strong> <time>' +
        escapeHtml(data.start_time) + '</time>';
      startTimeEl.style.display = 'block';
    } else {
      // Create start time element
      const newStartTime = document.createElement('div');
      newStartTime.className = 'start-time';
      newStartTime.innerHTML = '<strong>Calculation Time:</strong> <time>' +
        escapeHtml(data.start_time) + '</time>';
      form.parentNode.insertBefore(newStartTime, form.nextSibling);
    }

    // Rebuild the table body: the number of targets is user-configurable,
    // so the row count is not fixed at two.
    const tbody = resultsSection.querySelector('tbody');
    if (tbody) {
      tbody.textContent = '';
      (data.results || []).forEach(function(row) {
        const tr = document.createElement('tr');
        [formatTarget(row.target) + '% charge', row.duration, row.completion]
          .forEach(function(value) {
            const td = document.createElement('td');
            td.textContent = value;
            tr.appendChild(td);
          });
        tbody.appendChild(tr);
      });
    }

    updateTaperNote(resultsSection, data.model_taper);

    // Show results section with animation
    resultsSection.style.display = 'block';
  }

  /**
   * Trim trailing zeros from a target percentage for display
   * @param {number} target - Target percentage
   * @returns {string} Display string
   */
  function formatTarget(target) {
    return String(Number(target));
  }

  /**
   * Show or hide the note warning that taper is not modelled
   * @param {HTMLElement} section - Results section
   * @param {boolean} modelTaper - Whether taper was modelled
   */
  function updateTaperNote(section, modelTaper) {
    let note = section.querySelector('.hint');
    if (modelTaper === false) {
      if (!note) {
        note = document.createElement('p');
        note.className = 'hint';
        section.appendChild(note);
      }
      note.textContent = 'Charge taper not modelled — estimates near ' +
        '100% will run optimistic.';
    } else if (note) {
      note.remove();
    }
  }

  /**
   * Create results section HTML structure
   * @returns {HTMLElement} Results section element
   */
  function createResultsSection() {
    const section = document.createElement('section');
    section.className = 'results';
    section.innerHTML = `
      <h2>Charging Time Estimates</h2>
      <table>
        <thead>
          <tr>
            <th>Target</th>
            <th>Duration</th>
            <th>Completion Time</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    `;
    return section;
  }

  /**
   * Display error message
   * @param {string} message - Error message to display
   */
  function displayError(message) {
    // Remove existing error if present
    clearError();

    // Create error element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.innerHTML = '<strong>Error:</strong> ' + escapeHtml(message);

    // Insert before form
    form.parentNode.insertBefore(errorDiv, form);
  }

  /**
   * Clear error message
   */
  function clearError() {
    const errorDiv = document.querySelector('.error');
    if (errorDiv) {
      errorDiv.remove();
    }
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
})();
