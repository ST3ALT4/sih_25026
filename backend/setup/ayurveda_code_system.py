import json
import logging
import pathlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import pandas as pd
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept

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
    """Configuration class for the CodeSystem generator."""
    current_dir: pathlib.Path = pathlib.Path(__file__).parent
    backend_dir: pathlib.Path = current_dir.parent
    dataset_file: pathlib.Path = backend_dir / 'dataset' / 'ayurveda_morbidity_code.csv'
    output_dir: pathlib.Path = backend_dir / 'FHIR_artefacts'
    output_file: pathlib.Path = output_dir / 'namaste_codesystem.json'
    
    # CodeSystem metadata
    codesystem_id: str = "namaste-aryuveda-codes"
    codesystem_url: str = "https://namaste.ayush.gov.in/ayurveda"
    codesystem_version: str = "1.0.0"
    codesystem_name: str = "NAMASTE"
    codesystem_title: str = "National Ayurveda Morbidity Codes (NAMASTE)"
    codesystem_publisher: str = "Ministry of Ayush, Government of India"
    
    # CSV column names
    code_column: str = 'NAMC_CODE'
    term_column: str = 'NAMC_term'
    definition_column: str = 'Long_definition'


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    valid_concepts: List[Dict[str, Any]]


class NAMASTECodeSystemGenerator:
    """
    Generator class for NAMASTE CodeSystem FHIR resources.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the generator with configuration."""
        self.config = config or Config()
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """Ensure output directory exists."""
        try:
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory ensured: {self.config.output_dir}")
        except Exception as e:
            logger.error(f"Failed to create output directory: {e}")
            raise

    def _validate_csv_data(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate CSV data and return validation results.
        
        Args:
            df: Pandas DataFrame containing the CSV data
            
        Returns:
            ValidationResult object with validation status and details
        """
        errors = []
        warnings = []
        valid_concepts = []
        
        # Check if required columns exist
        required_columns = [self.config.code_column, self.config.term_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            return ValidationResult(False, errors, warnings, valid_concepts)
        
        # Check for empty DataFrame
        if df.empty:
            errors.append("CSV file is empty")
            return ValidationResult(False, errors, warnings, valid_concepts)
        
        # Validate each row
        for index, row in df.iterrows():
            row_errors = []
            
            # Check for required fields
            code_value = row.get(self.config.code_column, None)
            term_value = row.get(self.config.term_column, None)
            if code_value is None or pd.isna(code_value) or str(code_value).strip() == '':
                row_errors.append(f"Row {index}: Missing or empty code")
                continue

            if term_value is None or pd.isna(term_value) or str(term_value).strip() == '':
                row_errors.append(f"Row {index}: Missing or empty term")
                continue

            # Validate code format (basic validation)
            code_str = str(code_value).strip()
            if len(code_str) > 50:  # Reasonable limit for codes
                warnings.append(f"Row {index}: Code '{code_str}' is unusually long")
            
            # If we get here, the row is valid
            concept_data = {
                "code": code_str,
                "display": str(term_value).strip()
            }
            
            # Add definition if present
            definition_value = row.get(self.config.definition_column)
            if definition_value is not None and str(definition_value).strip():
                concept_data["definition"] = str(definition_value).strip()
            
            valid_concepts.append(concept_data)
            
            if row_errors:
                errors.extend(row_errors)
        
        is_valid = len(errors) == 0 and len(valid_concepts) > 0
        
        return ValidationResult(is_valid, errors, warnings, valid_concepts)
    
    def _create_fhir_concepts(self, concept_data_list: List[Dict[str, Any]]) -> List[CodeSystemConcept]:
        """
        Create FHIR CodeSystemConcept objects from concept data.
        
        Args:
            concept_data_list: List of concept dictionaries
            
        Returns:
            List of CodeSystemConcept objects
        """
        concepts = []
        
        for concept_data in concept_data_list:
            try:
                concept = CodeSystemConcept.construct(**concept_data)
                concepts.append(concept)
                logger.debug(f"Created concept: {concept_data.get('code')}")
            except Exception as e:
                logger.error(f"Failed to create concept {concept_data.get('code')}: {e}")
                raise
        
        return concepts
    
    def _create_codesystem(self, concepts: List[CodeSystemConcept]) -> CodeSystem:
        """
        Create FHIR CodeSystem resource.
        
        Args:
            concepts: List of CodeSystemConcept objects
            
        Returns:
            CodeSystem object
        """
        description = (
            "This code system defines the National Ayurveda Morbidity Codes (NAMASTE) "
            "for documenting clinical conditions in Ayurveda"
        )
        
        try:
            code_system = CodeSystem.construct(
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
            
            logger.info(f"Created CodeSystem with {len(concepts)} concepts")
            return code_system
            
        except Exception as e:
            logger.error(f"Failed to create CodeSystem: {e}")
            raise
    
    def _save_codesystem(self, code_system: CodeSystem) -> None:
        """
        Save CodeSystem to JSON file.
        
        Args:
            code_system: CodeSystem object to save
        """
        try:
            # Convert to dict with FHIR-compliant field names
            json_data = code_system.dict(by_alias=True)
            
            # Write to file with proper formatting
            with open(self.config.output_file, 'w', encoding='utf-8') as outfile:
                json.dump(json_data, outfile, indent=2, ensure_ascii=False)
            
            logger.info(f"CodeSystem saved to: {self.config.output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save CodeSystem: {e}")
            raise
    
    def load_csv_data(self) -> pd.DataFrame:
        """
        Load CSV data from file.
        
        Returns:
            Pandas DataFrame containing the CSV data
        """
        if not self.config.dataset_file.exists():
            raise FileNotFoundError(f"Dataset file not found: {self.config.dataset_file}")
        
        try:
            # Load CSV with error handling for encoding issues
            df = pd.read_csv(self.config.dataset_file, encoding='utf-8')
            logger.info(f"Loaded CSV with {len(df)} rows from {self.config.dataset_file}")
            return df
            
        except UnicodeDecodeError:
            # Try alternative encoding
            logger.warning("UTF-8 encoding failed, trying latin-1")
            df = pd.read_csv(self.config.dataset_file, encoding='latin-1')
            logger.info(f"Loaded CSV with {len(df)} rows using latin-1 encoding")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load CSV file: {e}")
            raise
    
    def generate_codesystem(self) -> bool:
        """
        Main method to generate the NAMASTE CodeSystem.
        
        Returns:
            Boolean indicating success
        """
        logger.info("Starting NAMASTE CodeSystem generation...")
        
        try:
            # Load and validate data
            df = self.load_csv_data()
            validation_result = self._validate_csv_data(df)
            
            # Report validation results
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(warning)
            
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    logger.error(error)
                logger.error("Data validation failed. CodeSystem generation aborted.")
                return False
            
            if not validation_result.valid_concepts:
                logger.warning("No valid concepts found in the CSV file.")
                return False
            
            # Create FHIR concepts
            concepts = self._create_fhir_concepts(validation_result.valid_concepts)
            
            # Create CodeSystem
            code_system = self._create_codesystem(concepts)
            
            # Save to file
            self._save_codesystem(code_system)
            
            # Success summary
            logger.info("✅ NAMASTE CodeSystem generation completed successfully!")
            logger.info(f"📊 Total concepts: {len(concepts)}")
            logger.info(f"⚠️  Warnings: {len(validation_result.warnings)}")
            logger.info(f"💾 Output file: {self.config.output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ CodeSystem generation failed: {e}")
            return False


def create_ayurveda_code():
    """Main entry point."""
    try:
        generator = NAMASTECodeSystemGenerator()
        success = generator.generate_codesystem()
        
        if success:
            print("\n🎉 CodeSystem generation completed successfully!")
        else:
            print("\n💥 CodeSystem generation failed. Check the logs for details.")
            exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        print(f"\n💥 Unexpected error: {e}")
        exit(1)
