// js/main.js

import { searchTerminology } from './api.js';
import { displaySearchResults, showLoading } from './ui.js';

// Get references to interactive elements from the DOM
const searchButton = document.getElementById('searchButton');
const searchInput = document.getElementById('terminologySearch');
const namasteCheck = document.getElementById('namasteCheck');
const tm2Check = document.getElementById('tm2Check');
const biomedicineCheck = document.getElementById('biomedicineCheck');

async function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    // Determine which systems are selected
    const systems = [];
    if (namasteCheck.checked) systems.push('NAMASTE');
    if (tm2Check.checked) systems.push('ICD-11 TM2');
    if (biomedicineCheck.checked) systems.push('ICD-11');

    showLoading(true);
    try {
        const results = await searchTerminology(query, systems);
        displaySearchResults(results);
    } catch (error) {
        // Here you would call a UI function to show an error message
        console.error("Failed to display search results:", error);
    } finally {
        showLoading(false);
    }
}

// Add the primary event listener
searchButton.addEventListener('click', handleSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});
