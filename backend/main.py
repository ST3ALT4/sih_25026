# main.py (full file)
from fastapi import FastAPI
from pydantic import BaseModel

# Import FHIR resources
from fhir.resources.condition import Condition
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference

# --- Pydantic Model for Input Data ---
class DiagnosisInput(BaseModel):
    patient_id: str
    code: str
    system: str  # e.g., "icd-11" or "namaste"
    display: str

# --- FastAPI App Instance ---
app = FastAPI(
    title="Health Data Integration API",
    description="An API to translate medical codes into FHIR resources."
)

# --- Helper function for FHIR system URL ---
def get_system_url(system_name: str):
    if system_name.lower() == "icd-11":
        return "http://id.who.int/icd/release/11/mms"
    if system_name.lower() == "namaste":
        return "https://www.namaste.gov.in/codes" # Placeholder URL
    return "urn:oid:2.16.840.1.113883.6.96" # Default to SNOMED-CT or other

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the FHIR Integration API!"}


@app.post("/record-diagnosis")
def create_diagnosis_record(data: DiagnosisInput):
    """
    Receives diagnosis data and converts it into a FHIR Condition resource.
    """
    # 1. Create the Coding for the diagnosis
    diagnosis_coding = Coding.construct(
        system=get_system_url(data.system),
        code=data.code,
        display=data.display
    )

    # 2. Create a CodeableConcept to hold the coding
    condition_code = CodeableConcept.construct(
        coding=[diagnosis_coding],
        text=data.display
    )

    # 3. Create a reference to the Patient
    patient_reference = Reference.construct(reference=f"Patient/{data.patient_id}")

    # 4. Assemble the final Condition resource
    condition = Condition.construct(
        clinicalStatus=CodeableConcept.construct(
            coding=[Coding.construct(system="http://terminology.hl7.org/CodeSystem/condition-clinical", code="active")]
        ),
        code=condition_code,
        subject=patient_reference
    )
    
    # 5. Return the created FHIR resource as JSON
    # In a real app, you would now POST this to the EMR.
    # For the hackathon, returning it is a great first step.
    return condition.dict()
