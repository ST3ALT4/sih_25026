import json
import logging
import pathlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import pandas as pd
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept

from setup.config import DATASET_DIR, FHIR_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('namaste_codesystem.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    dataset_file: pathlib.Path = DATASET_DIR / 'ayurveda_sample_demo.csv'
    output_dir: pathlib.Path = FHIR_DIR
    output_file: pathlib.Path = FHIR_DIR / 'namaste_codesystem.json'
    codesystem_id: str = "namaste-aryuveda-codes"
    codesystem_url: str = "https://namaste.ayush.gov.in/ayurveda"
    codesystem_version: str = "1.0.0"
    codesystem_name: str = "NAMASTE"
    codesystem_title: str = "National Ayurveda Morbidity Codes (NAMASTE)"
    codesystem_publisher: str = "Ministry of Ayush, Government of India"
    code_column: str = 'NAMC_CODE'
    term_column: str = 'NAMC_term'
    definition_column: str = 'Long_definition'

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    valid_concepts: List[Dict[str, Any]]

class NAMASTECodeSystemGenerator:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {self.config.output_dir}")

    def _insert_concept(self, root_list, concept):
        code = concept["code"]
        if "-" in code:
            parent_code = code.rsplit("-", 1)[0]
            parent = self._find_parent(root_list, parent_code)
            if parent:
                parent.setdefault("concept", []).append(concept)
                return
        root_list.append(concept)

    def _find_parent(self, concepts, pcode):
        for c in concepts:
            if c["code"] == pcode:
                return c
            if "concept" in c:
                found = self._find_parent(c["concept"], pcode)
                if found:
                    return found
        return None

    def _validate_csv_data(self, df: pd.DataFrame) -> ValidationResult:
        errors, warnings = [], []
        root_concepts: List[Dict[str, Any]] = []
        required = [self.config.code_column, self.config.term_column]
        missing = [c for c in required if c not in df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            return ValidationResult(False, errors, warnings, [])
        if df.empty:
            errors.append("CSV file is empty")
            return ValidationResult(False, errors, warnings, [])
        for idx, row in df.iterrows():
            code_val = row.get(self.config.code_column)
            term_val = row.get(self.config.term_column)
            if not code_val or pd.isna(code_val) or not str(code_val).strip():
                errors.append(f"Row {idx}: Missing or empty code")
                continue
            if not term_val or pd.isna(term_val) or not str(term_val).strip():
                errors.append(f"Row {idx}: Missing or empty term")
                continue
            cd = str(code_val).strip()
            concept = {"code": cd, "display": str(term_val).strip()}
            defn = row.get(self.config.definition_column)
            if defn and str(defn).strip():
                concept["definition"] = str(defn).strip()
            self._insert_concept(root_concepts, concept)
        is_valid = not errors and bool(root_concepts)
        return ValidationResult(is_valid, errors, warnings, root_concepts)

    def _create_fhir_concepts(self, data_list):
        concepts = []
        for entry in data_list:
            children = entry.pop("concept", [])
            cs_concept = CodeSystemConcept.construct(**entry)
            if children:
                cs_concept.concept = self._create_fhir_concepts(children)
            concepts.append(cs_concept)
        return concepts

    def _create_codesystem(self, concepts):
        description = (
            "This code system defines the National Ayurveda Morbidity Codes (NAMASTE) "
            "for documenting clinical conditions in Ayurveda"
        )
        cs = CodeSystem.construct(
            id=self.config.codesystem_id,
            url=self.config.codesystem_url,
            version=self.config.codesystem_version,
            name=self.config.codesystem_name,
            title=self.config.codesystem_title,
            status="active",
            experimental=False,
            date=datetime.now().isoformat(),
            publisher=self.config.codesystem_publisher,
            description=description,
            caseSensitive=True,
            content="complete",
            concept=concepts
        )
        logger.info(f"Created CodeSystem with {len(concepts)} top-level concepts")
        return cs

    def _save_codesystem(self, code_system):
        json_data = code_system.dict(by_alias=True)
        with open(self.config.output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.info(f"CodeSystem saved to: {self.config.output_file}")

    def load_csv_data(self):
        df = pd.read_csv(self.config.dataset_file, encoding='utf-8')
        logger.info(f"Loaded CSV with {len(df)} rows from {self.config.dataset_file}")
        return df

    def generate_codesystem(self) -> bool:
        logger.info("Starting NAMASTE CodeSystem generation...")
        df = self.load_csv_data()
        res = self._validate_csv_data(df)
        if not res.is_valid:
            for e in res.errors:
                logger.error(e)
            logger.error("Data validation failed. Aborting.")
            return False
        concepts = self._create_fhir_concepts(res.valid_concepts)
        cs = self._create_codesystem(concepts)
        self._save_codesystem(cs)
        logger.info("✅ NAMASTE CodeSystem generation completed successfully!")
        return True

def create_ayurveda_code():
    success = NAMASTECodeSystemGenerator().generate_codesystem()
    if success:
        print("\n🎉 CodeSystem generation completed successfully!")
    else:
        print("\n💥 CodeSystem generation failed. Check the logs for details.")
        exit(1)

