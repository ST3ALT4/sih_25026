# backend/namaste_data.py

import csv
from typing import Dict, List

NAMASTE_DATA: List[Dict[str, str]] = []

def load_namaste_data():
    """Loads the NAMASTE data from the CSV file."""
    global NAMASTE_DATA
    with open('../../dataset/ayurveda_morbidity_code.csv', mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            NAMASTE_DATA.append(row)

def search_namaste_by_term(term: str) -> List[Dict[str, str]]:
    """Searches for a NAMASTE code by its term."""
    results = []
    for row in NAMASTE_DATA:
        if term.lower() in row.get('NAMC_term', '').lower():
            results.append({
                "namaste_code": row.get('NAMC_CODE'),
                "namaste_term": row.get('NAMC_term')
            })
    return results
