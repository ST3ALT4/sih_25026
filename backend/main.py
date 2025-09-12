import json
from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List
from datetime import datetime

from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from fhir.resources.diagnosticreport import DiagnosticReport

from FHIR.models import ICDSearchResult, DiagnosticReportInput, SymptomSearchRequest, DiagnosisInput
from FHIR.report_record import create_fhir_condition
from setup.icd_client import IcdApiClient
from setup.ayurveda_code_system import create_ayurveda_code
from setup.auto_mapping import create_mapping_file  
from setup.conceptmap_generator import create_conceptmap 
# --- FastAPI App Setup ---

app = FastAPI(
    title="Enhanced Health Data Integration API",
    description="API to search ICD-11 conditions and create FHIR resources",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

icd_client = IcdApiClient()
def get_icd_client():
    global icd_client
    return icd_client

create_ayurveda_code() 
create_mapping_file(icd_client)
create_conceptmap()

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

@app.get("/ayurveda")
async def ayurveda_code(): 

    try:
        with open('FHIR_artefacts/namaste_codesystem.json', 'r', encoding='utf-8') as infile:
            data = json.load(infile)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')

@app.get("/mapped")
async def mapped():
    try:
        with open('FHIR_artefacts/namaste_icd11_conceptmap.json', 'r', encoding='utf-8') as infile:
            data = json.load(infile)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{e}')

@app.get("/icd/search", response_model=List[ICDSearchResult])
async def search_icd_conditions(
    q: str = Query(..., description="Search query for medical conditions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    icd_client: IcdApiClient = Depends(get_icd_client)
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
    icd_client: IcdApiClient = Depends(get_icd_client)
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
    icd_client: IcdApiClient = Depends(get_icd_client)
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
async def get_icd_categories(icd_client: IcdApiClient = Depends(get_icd_client)):
    """Get main ICD-11 categories/chapters"""
    
    try:
        categories = icd_client.get_root_categories()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.get("/health")
async def health_check(icd_client: IcdApiClient = Depends(get_icd_client)):
    """Comprehensive health check"""
    
    # Check ICD API health
    icd_health = icd_client.health_check()
    
    return {
        "api_status": "healthy",
        "icd_api": icd_health,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }
