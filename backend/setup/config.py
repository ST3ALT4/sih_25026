# config.py

import pathlib
from datetime import datetime

# Determine project root (three levels up from this file: backend/setup/config.py)
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent

# Backend, dataset, and FHIR artefacts directories relative to project root
BACKEND_DIR = PROJECT_ROOT / "backend"
DATASET_DIR = BACKEND_DIR / "dataset"
FHIR_DIR = BACKEND_DIR / "FHIR_artefacts"

# Source file paths
AYURVEDA_CSV_FILE = DATASET_DIR / "ayurveda_sample_demo.csv"
MAPPING_FILE = DATASET_DIR / "namaste_icd11_mapping_automated.csv"
CODE_SYSTEM_JSON = FHIR_DIR / "namaste_codesystem.json"
CONCEPTMAP_JSON = FHIR_DIR / "namaste_icd11_conceptmap.json"

# CodeSystem metadata
CODESYSTEM = {
    "id": "namaste-aryuveda-codes",
    "url": "https://namaste.ayush.gov.in/ayurveda",
    "version": "1.0.0",
    "name": "NAMASTE",
    "title": "National Ayurveda Morbidity Codes (NAMASTE)",
    "publisher": "Ministry of Ayush, Government of India",
    "status": "active",
    "date": datetime.now().isoformat(),
    "content": "complete"
}

# ConceptMap metadata
CONCEPTMAP = {
    "id": "namaste_ayurveda-to-icd11_TM2",
    "url": "https://example.org/fhir/ConceptMap/namaste-to-icd11",
    "version": "1.0.0",
    "source": CODESYSTEM["url"],
    "target": "http://id.who.int/icd/release/11/mms",
    "status": "active",
    "date": datetime.now().isoformat()
}

