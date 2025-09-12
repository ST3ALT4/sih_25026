import csv
import time
import re
import pandas as pd
from dotenv import load_dotenv

from setup.icd_client import IcdApiClient
from setup.mapping_algorithm import MappingSuggester
from setup.config import AYURVEDA_CSV_FILE, MAPPING_FILE, PROJECT_ROOT

def setup_environment():
    """Loads environment variables from a .env file for standalone script execution."""
    dotenv_path = PROJECT_ROOT / '.env'
    if dotenv_path.exists():
        print(f"Loading environment variables from: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print("WARN: .env file not found. Make sure ICD credentials are set in your system environment.")

def extract_namaste_id(namc_code):
    """Extract NAMASTE ID from codes like 'SR11 (AAA-1)' -> 'AAA-1'"""
    if pd.isna(namc_code):
        return namc_code
    match = re.search(r'\(([^)]+)\)', str(namc_code))
    return match.group(1) if match else str(namc_code)

def extract_icd_mapping(namc_code):
    """Extract ICD mapping code from codes like 'SR11 (AAA-1)' -> 'SR11'"""
    if pd.isna(namc_code):
        return None
    match = re.search(r'^([^(]+)', str(namc_code).strip())
    if match:
        icd_part = match.group(1).strip()
        if any(icd_part.startswith(prefix) for prefix in ['SR','SK','SM','SL','SN','SP','SQ']):
            return icd_part
    return None

def load_namaste_concepts_from_csv():
    """Load NAMASTE codes, terms, and definitions from the CSV file."""
    if not AYURVEDA_CSV_FILE.exists():
        print(f"ERROR: CSV file not found at {AYURVEDA_CSV_FILE}")
        return []
    df = pd.read_csv(AYURVEDA_CSV_FILE)
    df['NAMASTE_ID'] = df['NAMC_CODE'].apply(extract_namaste_id)
    df['ICD_MAPPING'] = df['NAMC_CODE'].apply(extract_icd_mapping)
    concepts = []
    for _, row in df.iterrows():
        concepts.append({
            "code": row['NAMASTE_ID'],
            "original_namc_code": row['NAMC_CODE'],
            "term": row.get('NAMC_term', "") or "",
            "definition": row.get('Long_definition', "") or "",
            "existing_icd_mapping": row['ICD_MAPPING'],
            "has_existing_mapping": pd.notna(row['ICD_MAPPING'])
        })
    return concepts

def determine_equivalence(score: float) -> str:
    """Determine FHIR equivalence based on the confidence score."""
    if score >= 0.85:
        return "equivalent"
    if score >= 0.75:
        return "equal"
    if score >= 0.60:
        return "wider"
    return "relatedto"

def save_mappings_to_csv(mappings: list):
    """Save the generated mappings to a CSV file."""
    if not mappings:
        print("No mappings to save.")
        return
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "namaste_code", "namaste_term", "icd_code", "icd_term",
        "equivalence", "confidence_score", "mapping_source", "original_namc_code"
    ]
    with open(MAPPING_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    print(f"💾 Automated mapping saved to {MAPPING_FILE}")

def get_icd_term_for_existing_mapping(icd_client, icd_code):
    """Get the ICD term for an existing ICD code mapping."""
    try:
        search_results = icd_client.search_code(icd_code)
        entity_id = search_results.get("stemId").split('/')[-1]
        return icd_client.get_entity_details(entity_id).get("title").get("@value", "Nan")
    except Exception as e:
        print(f" ⚠️ Could not fetch ICD term for {icd_code}: {e}")
        return "Unknown ICD Term"

def create_mapping_file(icd_client: IcdApiClient):
    """Main function to generate the entire mapping file."""
    print("--- Starting Enhanced NAMASTE to ICD-11 Mapping Generation ---")
    setup_environment()
    mapper = MappingSuggester(icd_client)
    namaste_concepts = load_namaste_concepts_from_csv()
    if not namaste_concepts:
        print("Could not load NAMASTE concepts. Aborting.")
        return
    print(f"Loaded {len(namaste_concepts)} NAMASTE concepts.")
    existing_mappings = [c for c in namaste_concepts if c['has_existing_mapping']]
    needs_mapping = [c for c in namaste_concepts if not c['has_existing_mapping']]
    print(f"📋 {len(existing_mappings)} concepts have existing ICD mappings")
    print(f"🔍 {len(needs_mapping)} concepts need new ICD mappings")
    final_mappings = []

    print("\n--- Processing Existing Mappings ---")
    for i, concept in enumerate(existing_mappings, 1):
        print(f"[{i}/{len(existing_mappings)}] Using existing mapping: {concept['term']} -> {concept['existing_icd_mapping']}")
        icd_term = get_icd_term_for_existing_mapping(icd_client, concept['existing_icd_mapping'])
        final_mappings.append({
            "namaste_code": concept['code'],
            "namaste_term": concept['term'],
            "icd_code": concept['existing_icd_mapping'],
            "icd_term": icd_term,
            "equivalence": "equivalent",
            "confidence_score": 1.0,
            "mapping_source": "existing",
            "original_namc_code": concept['original_namc_code']
        })
        time.sleep(0.2)

    print(f"\n--- Generating New Mappings for {len(needs_mapping)} concepts ---")
    for i, concept in enumerate(needs_mapping, 1):
        if not concept['term'].strip():
            continue
        print(f"[{i}/{len(needs_mapping)}] Processing: {concept['term']} ({concept['code']})...")
        suggestions = mapper.suggest_mappings(
            namaste_term=concept['term'],
            namaste_definition=concept['definition']
        )
        if suggestions:
            top = suggestions[0]
            score = top['score']
            final_mappings.append({
                "namaste_code": concept['code'],
                "namaste_term": concept['term'],
                "icd_code": top['icd_code'],
                "icd_term": top['icd_term'],
                "equivalence": determine_equivalence(score),
                "confidence_score": round(score, 4),
                "mapping_source": "generated",
                "original_namc_code": concept['original_namc_code']
            })
            print(f" ✅ Mapped to '{top['icd_term']}' with score {score:.4f}")
        else:
            print(f" ❌ No suitable mapping found for '{concept['term']}'")
        time.sleep(0.5)

    save_mappings_to_csv(final_mappings)
    print(f"\n--- Mapping Generation Summary ---")
    print(f"✅ Total mappings created: {len(final_mappings)}")
    print(f"📋 Existing mappings used: {len([m for m in final_mappings if m['mapping_source']=='existing'])}")
    print(f"🔍 New mappings generated: {len([m for m in final_mappings if m['mapping_source']=='generated'])}")
    print("\n--- Enhanced Automated Mapping Generation Finished ---")

if __name__ == "__main__":
    # Example usage:
    # icd_client = IcdApiClient()
    # create_mapping_file(icd_client)
    pass

