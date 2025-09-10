from pydantic import BaseModel, Field
from typing import List, Optional

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
