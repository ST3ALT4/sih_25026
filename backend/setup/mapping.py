import json
import csv
import pathlib
from rapidfuzz import process, fuzz
from functools import lru_cache

from setup.icd_client import IcdApiClient

# Paths
AYURVEDA_FILE = pathlib.Path("FHIR_artefacts/namaste_codesystem.json")
MAPPING_FILE = pathlib.Path("dataset/namaste_icd11_mapping.csv")

def load_namaste_terms():
    """Load NAMASTE codes + terms from CodeSystem JSON."""
    with open(AYURVEDA_FILE, "r", encoding="utf-8") as f:
        cs = json.load(f)

    terms = []
    for concept in cs.get("concept", []):
        terms.append((concept["code"], concept["display"]))
    return terms

def fetch_icd_terms(icd_client: IcdApiClient, limit: int = 500):
    """Fetch some ICD-11 terms via API."""
    terms = []
    # Example: pull a batch of terms for common letters
    for letter in ["a", "b", "c", "d"]:
        results = icd_client.search_conditions(letter, limit=limit)
        for entity in results.get("destinationEntities", []):
            terms.append({
                "code": entity.get("theCode"),
                "title": entity.get("title", ""),
                "definition": entity.get("definition", "")
            })
    return terms

def auto_map(namaste_terms, icd_terms, batch_size: int = 100):
    """Optimized fuzzy matching with batching and caching."""
    icd_lookup = {t["title"]: t for t in icd_terms}
    icd_titles = list(icd_lookup.keys())
    
    mappings = []
    
    # Process in batches to manage memory
    for i in range(0, len(namaste_terms), batch_size):
        batch = namaste_terms[i:i + batch_size]
        
        for code, term in batch:
            matches = process.extract(
                term, 
                icd_titles, 
                scorer=fuzz.WRatio,
                limit=3,  # Get top 3 matches
                score_cutoff=60  # Only consider matches above 60%
            )
            
            if matches:
                best_match, score, _ = matches[0]
                icd = icd_lookup[best_match]
                
                mappings.append({
                    "namaste_code": code,
                    "namaste_term": term,
                    "icd_code": icd.get("code"),
                    "icd_term": icd.get("title"),
                    "equivalence": determine_equivalence(score),
                    "confidence": score,
                    "alternative_matches": [
                        {"term": m, "score": m} 
                        for m in matches[1:3]
                    ]
                })
    
    return mappings

def determine_equivalence(score: float) -> str:
    """Determine FHIR equivalence based on confidence score."""
    if score >= 95:
        return "equivalent"
    elif score >= 80:
        return "equal"
    elif score >= 60:
        return "wider"
    else:
        return "relatedto"
def save_to_csv(mappings):
    """Save mappings to CSV."""
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MAPPING_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["namaste_code", "namaste_term", "icd_code", "icd_term", "equivalence", "confidence", "alternative_matches"]
        )
        writer.writeheader()
        writer.writerows(mappings)
    print(f"💾 Mapping saved to {MAPPING_FILE}")

def map(icd_client):

    namaste_terms = load_namaste_terms()
    print(f"Loaded {len(namaste_terms)} NAMASTE terms")

    icd_terms = fetch_icd_terms(icd_client)
    print(f"Fetched {len(icd_terms)} ICD-11 terms")

    mappings = auto_map(namaste_terms, icd_terms)
    print(f"Generated {len(mappings)} mappings")

    save_to_csv(mappings)

