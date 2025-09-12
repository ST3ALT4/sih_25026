import json
import logging
import pathlib
from datetime import datetime
from typing import List, Dict

import pandas as pd
from fhir.resources.conceptmap import ConceptMap

from setup.config import DATASET_DIR, FHIR_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("conceptmap_generator.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class Config:
    dataset_file: pathlib.Path = DATASET_DIR / "namaste_icd11_mapping_automated.csv"
    output_dir: pathlib.Path = FHIR_DIR
    output_file: pathlib.Path = FHIR_DIR / "namaste_icd11_conceptmap.json"
    conceptmap_id: str = "namaste_ayurveda-to-icd11_TM2"
    conceptmap_url: str = "https://example.org/fhir/ConceptMap/namaste-to-icd11"
    conceptmap_version: str = "1.0.0"
    source_system: str = "https://namaste.ayush.gov.in/ayurveda"
    target_system: str = "http://id.who.int/icd/release/11/mms"

class ConceptMapGenerator:
    def __init__(self, config: Config = Config()):
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

    def load_mapping(self) -> pd.DataFrame:
        df = pd.read_csv(self.config.dataset_file)
        required = ["namaste_code","namaste_term","icd_code","icd_term","equivalence"]
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column: {col}")
        logger.info(f"Loaded {len(df)} mapping rows from {self.config.dataset_file}")
        return df

    def generate_conceptmap(self) -> ConceptMap:
        df = self.load_mapping()
        group = {
            "source": self.config.source_system,
            "target": self.config.target_system,
            "element": []
        }
        for _, row in df.iterrows():
            element = {
                "code": str(row["namaste_code"]),
                "display": str(row["namaste_term"]),
                "target": [{
                    "code": str(row["icd_code"]),
                    "display": str(row["icd_term"]),
                    "equivalence": str(row["equivalence"] or "relatedto")
                }]
            }
            group["element"].append(element)
        cm = ConceptMap.construct(
            resourceType="ConceptMap",
            id=self.config.conceptmap_id,
            url=self.config.conceptmap_url,
            version=self.config.conceptmap_version,
            status="active",
            date=datetime.now().isoformat(),
            sourceUri=self.config.source_system,
            targetUri=self.config.target_system,
            group=[group]
        )
        logger.info(f"✅ Generated ConceptMap with {len(group['element'])} mappings")
        return cm

    def save_conceptmap(self, conceptmap: ConceptMap):
        data = conceptmap.dict(by_alias=True)
        with open(self.config.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 ConceptMap saved to {self.config.output_file}")

def create_conceptmap():
    gen = ConceptMapGenerator()
    cm = gen.generate_conceptmap()
    gen.save_conceptmap(cm)
    print("🎉 ConceptMap generation completed successfully!")

