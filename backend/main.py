# Enhanced FastAPI Integration
# Combines your existing main.py with ICD-11 search functionality

from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from datetime import datetime

# Import FHIR resources (keeping your existing imports)
from fhir.resources.condition import Condition
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.observation import Observation

# Import your enhanced ICD client
from setup.icd_client import EnhancedIcdApiClient

# --- Enhanced Pydantic Models ---

class ICDSearchResult(BaseModel):
    """Model for ICD-11 search results"""
    code: Optional[str] = Field(None, description="ICD-11 code")
    title: str = Field(..., description="Condition title")
    definition: Optional[str] = Field(None, description="Medical definition")
    uri: str = Field(..., description="ICD-11 URI")

class DiagnosisInput(BaseModel):
    """Enhanced diagnosis input model"""
    patient_id: str = Field(..., description="Patient identifier")
    code: str = Field(..., description="Medical code")
    system: str = Field(..., description="Coding system (icd-11, snomed, etc.)")
    display: str = Field(..., description="Human-readable display name")
    clinical_status: str = Field("active", description="Clinical status of condition")
    verification_status: str = Field("confirmed", description="Verification status")

class SymptomSearchRequest(BaseModel):
    """Model for symptom-based search"""
    symptoms: List[str] = Field(..., description="List of symptoms")
    patient_age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    patient_gender: Optional[str] = Field(None, description="Patient gender")
    limit: int = Field(10, ge=1, le=50, description="Maximum results to return")

class DiagnosticReportInput(BaseModel):
    """Model for creating diagnostic reports"""
    patient_id: str = Field(..., description="Patient identifier")
    practitioner_id: str = Field(..., description="Practitioner identifier")
    findings: List[DiagnosisInput] = Field(..., description="List of diagnoses/findings")
    report_status: str = Field("final", description="Report status")
    conclusion: Optional[str] = Field(None, description="Clinical conclusion")

# --- FastAPI App Setup ---

app = FastAPI(
    title="Enhanced Health Data Integration API",
    description="API to search ICD-11 conditions and create FHIR resources",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Initialize ICD Client ---

def get_icd_client() -> EnhancedIcdApiClient:
    """Dependency to get ICD client instance"""
    client_id = os.getenv("ICD_CLIENT_ID", "your_client_id")
    client_secret = os.getenv("ICD_CLIENT_SECRET", "your_client_secret")
    
    if client_id == "your_client_id" or client_secret == "your_client_secret":
        raise HTTPException(
            status_code=500, 
            detail="ICD-11 credentials not configured. Please set ICD_CLIENT_ID and ICD_CLIENT_SECRET environment variables."
        )
    
    return EnhancedIcdApiClient(client_id, client_secret)

# --- Helper Functions (Enhanced from your original) ---

def get_system_url(system_name: str) -> str:
    """Enhanced system URL mapping"""
    system_mapping = {
        "icd-11": "http://id.who.int/icd/release/11/mms",
        "icd-10": "http://hl7.org/fhir/sid/icd-10",
        "snomed": "http://snomed.info/sct",
        "namaste": "https://www.namaste.gov.in/codes",  # Your custom system
        "loinc": "http://loinc.org"
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

# --- API Endpoints ---

@app.get("/")
def read_root():
    """Root endpoint with API information"""
    return {
        "message": "Enhanced Health Data Integration API",
        "version": "2.0.0",
        "features": [
            "ICD-11 condition search",
            "FHIR resource creation",
            "Symptom-based diagnosis suggestions",
            "Diagnostic report generation"
        ],
        "endpoints": {
            "icd_search": "/icd/search?q=condition",
            "diagnosis": "/diagnosis/create",
            "symptoms": "/symptoms/search",
            "diagnostic_report": "/diagnostic-report/create",
            "health": "/health"
        }
    }

@app.get("/icd/search", response_model=List[ICDSearchResult])
async def search_icd_conditions(
    q: str = Query(..., description="Search query for medical conditions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    icd_client: EnhancedIcdApiClient = Depends(get_icd_client)
):
    """Search for medical conditions in ICD-11"""
    
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters long")
    
    try:
        # Search using your enhanced ICD client
        search_results = icd_client.search_conditions(q.strip(), limit)
        
        # Transform results to our model
        conditions = []
        for entity in search_results.get("destinationEntities", []):
            conditions.append(ICDSearchResult(
                code=entity.get("theCode"),
                title=entity.get("title", ""),
                definition=entity.get("definition"),
                uri=entity.get("id", "")
            ))
        
        return conditions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/icd/entity/{entity_id:path}")
async def get_icd_entity_details(
    entity_id: str,
    icd_client: EnhancedIcdApiClient = Depends(get_icd_client)
):
    """Get detailed information about a specific ICD-11 entity"""
    
    try:
        entity_details = icd_client.get_entity_details(entity_id)
        return entity_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity details: {str(e)}")

@app.post("/diagnosis/create")
def create_diagnosis_record(data: DiagnosisInput):
    """
    Enhanced diagnosis record creation with FHIR Condition resource
    (Builds upon your original function)
    """
    try:
        condition_resource = create_fhir_condition(data)
        
        return {
            "message": "FHIR Condition resource created successfully",
            "patient_id": data.patient_id,
            "condition": condition_resource,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create diagnosis record: {str(e)}")

@app.post("/symptoms/search")
async def search_by_symptoms(
    request: SymptomSearchRequest,
    icd_client: EnhancedIcdApiClient = Depends(get_icd_client)
):
    """Search for potential diagnoses based on symptoms"""
    
    suggestions = []
    
    # Search for each symptom
    for symptom in request.symptoms:
        try:
            results = icd_client.search_conditions(symptom, limit=5)
            
            for entity in results.get("destinationEntities", []):
                suggestion = ICDSearchResult(
                    code=entity.get("theCode"),
                    title=entity.get("title", ""),
                    definition=entity.get("definition"),
                    uri=entity.get("id", "")
                )
                
                # Avoid duplicates
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    
        except Exception:
            continue  # Skip failed searches
    
    # Limit results
    unique_suggestions = suggestions[:request.limit]
    
    return {
        "patient_info": {
            "age": request.patient_age,
            "gender": request.patient_gender,
            "symptoms": request.symptoms
        },
        "suggested_conditions": unique_suggestions,
        "total_found": len(unique_suggestions),
        "disclaimer": "This is for educational/hackathon purposes only. Always consult healthcare professionals."
    }

@app.post("/diagnostic-report/create")
def create_diagnostic_report(data: DiagnosticReportInput):
    """Create a FHIR DiagnosticReport with multiple findings"""
    
    try:
        # Create individual condition resources for each finding
        condition_resources = []
        for finding in data.findings:
            condition = create_fhir_condition(finding)
            condition_resources.append(condition)
        
        # Create references to the conditions
        result_references = [
            Reference.construct(reference=f"Condition/{i}") 
            for i in range(len(condition_resources))
        ]
        
        # Create the DiagnosticReport
        diagnostic_report = DiagnosticReport.construct(
            status=data.report_status,
            code=CodeableConcept.construct(
                coding=[Coding.construct(
                    system="http://loinc.org",
                    code="11526-1",
                    display="Pathology study"
                )]
            ),
            subject=Reference.construct(reference=f"Patient/{data.patient_id}"),
            performer=[Reference.construct(reference=f"Practitioner/{data.practitioner_id}")],
            result=result_references,
            conclusion=data.conclusion,
            effectiveDateTime=datetime.now().isoformat()
        )
        
        return {
            "message": "FHIR DiagnosticReport created successfully",
            "diagnostic_report": diagnostic_report.dict(),
            "conditions": condition_resources,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create diagnostic report: {str(e)}")

@app.get("/icd/categories")
async def get_icd_categories(icd_client: EnhancedIcdApiClient = Depends(get_icd_client)):
    """Get main ICD-11 categories/chapters"""
    
    try:
        categories = icd_client.get_root_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/health")
async def health_check(icd_client: EnhancedIcdApiClient = Depends(get_icd_client)):
    """Comprehensive health check"""
    
    # Check ICD API health
    icd_health = icd_client.health_check()
    
    return {
        "api_status": "healthy",
        "icd_api": icd_health,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
