from datetime import datetime
from typing import Dict, Any

from fhir.resources.condition import Condition
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference

from FHIR.models import DiagnosisInput

#FHIR thing to get what thype of coding we are using in the record
def get_system_url(system_name: str) -> str:
    """system URL mapping"""
    system_mapping = {
        "icd-11": "https://icd.who.int/browse/2025-01/mms/en",
        "namaste": "https://namaste.ayush.gov.in/", 
    }
    
    return system_mapping.get(system_name.lower(), "urn:oid:2.16.840.1.113883.6.96")

def create_fhir_condition(diagnosis_data: DiagnosisInput) -> Dict[str, Any]:
    """Enhanced FHIR Condition creation"""
    
    # Create the coding for the diagnosis
    diagnosis_coding = Coding.construct(
        system=get_system_url(diagnosis_data.system),
        code=diagnosis_data.code,
        display=diagnosis_data.display
    )
    
    # Create CodeableConcept
    condition_code = CodeableConcept.construct(
        coding=[diagnosis_coding],
        text=diagnosis_data.display
    )
    
    # Clinical status coding
    clinical_status = CodeableConcept.construct(
        coding=[Coding.construct(
            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
            code=diagnosis_data.clinical_status
        )]
    )
    
    # Verification status coding
    verification_status = CodeableConcept.construct(
        coding=[Coding.construct(
            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
            code=diagnosis_data.verification_status
        )]
    )
    
    # Patient reference
    patient_reference = Reference.construct(reference=f"Patient/{diagnosis_data.patient_id}")
    
    # Create the Condition resource
    condition = Condition.construct(
        clinicalStatus=clinical_status,
        verificationStatus=verification_status,
        code=condition_code,
        subject=patient_reference,
        recordedDate=datetime.now().isoformat()
    )

    return condition.dict()
    
