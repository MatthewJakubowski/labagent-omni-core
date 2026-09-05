from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import hashlib

from core.engine import UltimateClinicalAuditor, FullFHIRBundleExporter
from core.synthesizer import ClinicalGroundedSynthesizer, API_KEY_PLACEHOLDER

app = FastAPI(
    title="LabAgent-Omni Core API",
    description="Stateless Sidecar Clinical Engine for Laboratory Autovalidation & FHIR Generation",
    version="1.0.0"
)

class PatientModel(BaseModel):
    age: int = Field(40, ge=0, le=125, description="Wiek pacjenta")
    sex: str = Field("M", pattern="^(M|F)$", description="Płeć (M/F)")
    patient_id: Optional[str] = Field("ANON_SAMPLE", description="Identyfikator anonimizowany hashem SHA-256")

class AuditRequest(BaseModel):
    patient: PatientModel
    current_results: Dict[str, Any]
    previous_results: Optional[Dict[str, Any]] = {}
    custom_api_key: Optional[str] = Field(API_KEY_PLACEHOLDER, description="Opcjonalny klucz API do LLM (domyślnie placeholder)")

@app.get("/health", tags=["System"])
def health():
    return {"status": "HEALTHY", "service": "LabAgent-Omni Core", "version": "1.0.0"}

@app.post("/api/v1/audit", tags=["Clinical Engine"])
def execute_audit(req: AuditRequest):
    # Hashowanie identyfikatora (Zero-Data Retention)
    pt_hash = hashlib.sha256(req.patient.patient_id.encode()).hexdigest()
    pt_info = {"hash": pt_hash, "age": req.patient.age, "sex": req.patient.sex}

    # Deterministyczny audyt laboratoryjny
    audit_res = UltimateClinicalAuditor.execute_god_mode_audit(
        pt_info,
        req.current_results,
        req.previous_results
    )
    return audit_res

@app.post("/api/v1/fhir-bundle", tags=["Interoperability"])
def export_fhir(req: AuditRequest):
    pt_hash = hashlib.sha256(req.patient.patient_id.encode()).hexdigest()
    pt_info = {"hash": pt_hash, "age": req.patient.age, "sex": req.patient.sex}

    audit_res = UltimateClinicalAuditor.execute_god_mode_audit(
        pt_info,
        req.current_results,
        req.previous_results
    )

    if not audit_res["preanalytical"]["passed"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Krytyczna blokada przedanalityczna: {audit_res['preanalytical']['reason']}"
        )

    bundle = FullFHIRBundleExporter.export(audit_res)
    return bundle

@app.post("/api/v1/synthesize", tags=["Grounded AI Synthesis"])
def synthesize_report(req: AuditRequest):
    pt_hash = hashlib.sha256(req.patient.patient_id.encode()).hexdigest()
    pt_info = {"hash": pt_hash, "age": req.patient.age, "sex": req.patient.sex}

    audit_res = UltimateClinicalAuditor.execute_god_mode_audit(
        pt_info,
        req.current_results,
        req.previous_results
    )

    synthesis = ClinicalGroundedSynthesizer.generate_sbar_and_patient_view(
        audit_res,
        api_key=req.custom_api_key
    )
    return synthesis
