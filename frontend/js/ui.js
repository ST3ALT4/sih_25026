// js/ui.js

// Get references to all the important DOM elements
const searchInput = document.getElementById('terminologySearch');
const searchButton = document.getElementById('searchButton');
const resultsContainer = document.getElementById('searchResults');
const resultsSpinner = document.getElementById('resultsSpinner');
const resultsSection = document.getElementById('resultsSection');
// ... other elements

/**
 * Renders the search results on the page.
 * @param {Object[]} results - The array of result objects from the API.
 */
export function displaySearchResults(results) {
    resultsContainer.innerHTML = ''; // Clear previous results
    if (!results || results.length === 0) {
        resultsContainer.innerHTML = `<div class="alert alert-warning">No results found.</div>`;
        return;
    }
    
    for (const item of results) {
        const systemClass = item.system.replace(/\s+/g, '-').toLowerCase();
        const resultCard = `
            <div class="card concept-card">
              <div class="card-body">
                <h5 class="card-title">${item.display}</h5>
                <p class="card-text">${item.definition}</p>
                </div>
            </div>`;
        resultsContainer.insertAdjacentHTML('beforeend', resultCard);
    }
}

/**
 * Shows or hides the main loading spinner.
 * @param {boolean} isLoading - Whether to show the spinner.
 */
export function showLoading(isLoading) {
    if (isLoading) {
        resultsSection.classList.remove('d-none');
        resultsSpinner.style.display = 'inline-block';
    } else {
        resultsSpinner.style.display = 'none';
    }
}

// You would add more functions here like showToast(), setupEventListeners(), etc.
