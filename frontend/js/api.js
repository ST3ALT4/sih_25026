// js/api.js

const API_BASE_URL = 'http://127.0.0.1:8000'; // Define a base URL for your API

/**
 * Searches the terminology API.
 * @param {string} query - The search term.
 * @param {string[]} systems - The systems to search in (e.g., ['NAMASTE', 'ICD-11']).
 * @returns {Promise<Object[]>} - A promise that resolves to the search results.
 */
export async function searchTerminology(query, systems) {
    try {
        const response = await fetch(`${API_BASE_URL}/terminology/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, systems })
        });
        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Search failed:', error);
        throw error; // Re-throw to be caught by the UI layer
    }
}

/**
 * Fetches mappings for a specific code.
 * @param {string} code - The code to get mappings for.
 * @param {string} system - The system the code belongs to.
 * @returns {Promise<Object>} - A promise that resolves to the mapping data.
 */
export async function getMappings(code, system) {
    // Implementation for fetching mappings...
}
