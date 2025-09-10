import csv
import sqlite3
import pathlib
import json
import re
from tqdm import tqdm
from thefuzz import fuzz
from icd_client import IcdApiClient

# --- Configuration ---
# Define file paths relative to the script's location
CURRENT_DIR = pathlib.Path(__file__).parent
BACKEND_DIR = CURRENT_DIR.parent
DATASET_FILE = BACKEND_DIR.parent / 'dataset' / 'ayurveda_morbidity_code.csv'
DB_FILE = BACKEND_DIR / 'namaste_icd_mapping.db'
# Set a threshold for how similar terms should be to be considered a match (0-100)
CONFIDENCE_THRESHOLD = 70

def initialize_database():
    """Creates the SQLite database and the mapping table if they don't exist."""
    print(f"Initializing database at: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Drop the table if it exists to start fresh each time
    cursor.execute('DROP TABLE IF EXISTS code_mappings')
    cursor.execute('''
        CREATE TABLE code_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            namaste_code TEXT NOT NULL,
            namaste_term TEXT NOT NULL,
            icd_code TEXT NOT NULL,
            icd_title TEXT NOT NULL,
            credibility_score INTEGER NOT NULL,
            UNIQUE(namaste_code, icd_code)
        )
    ''')
    conn.commit()
    return conn, cursor

def run_mapping_algorithm():
    """
    Main function to run the mapping from NAMASTE codes to ICD-11 codes.
    """
    print("Starting the mapping process. This may take several minutes...")
    
    # Initialize the ICD API client and the database
    icd_client = IcdApiClient()
    conn, cursor = initialize_database()
    
    # Read the NAMASTE codes from the CSV
    with open(DATASET_FILE, mode='r', encoding='utf-8') as infile:
        reader = list(csv.DictReader(infile))
        
        # Use tqdm for a progress bar
        for row in tqdm(reader, desc="Processing NAMASTE Terms"):
            namaste_code = row.get('NAMC_CODE')
            namaste_term = row.get('NAMC_term')

            if not namaste_term or not namaste_code:
                continue

            try:
                # Search the ICD API for the NAMASTE term
                search_results = icd_client.search_conditions(namaste_term,1)

                for result in search_results['destinationEntities']:
                    icd_title = result.get("title", {}).get("@value", "")
                    # Extract the ICD code from the ID URL
                    icd_id = result.get("id", "")
                    icd_code = icd_id.split('/')[-1] if icd_id else None

                    if not icd_title or not icd_code:
                        continue
                
                    # Calculate the credibility score
                    score = fuzz.token_sort_ratio(namaste_term.lower(), icd_title.lower())

                    # If the score is above our threshold, save it to the database
                    if score >= CONFIDENCE_THRESHOLD:
                        try:
                            cursor.execute('''
                                INSERT INTO code_mappings (
                                    namaste_code, namaste_term, icd_code, icd_title, credibility_score
                                ) VALUES (?, ?, ?, ?, ?)
                            ''', (namaste_code, namaste_term, icd_code, icd_title, score))
                        except sqlite3.IntegrityError:
                            # This handles cases where a NAMASTE-ICD pair is found multiple times
                            pass

            except Exception as e:
                print(f"\nAn error occurred while processing '{namaste_term}': {e}")

    # Commit all changes and close the connection
    conn.commit()
    conn.close()
    print("\nMapping database created successfully!")
    print(f"Database saved to: {DB_FILE}")


if __name__ == "__main__":
    run_mapping_algorithm()
