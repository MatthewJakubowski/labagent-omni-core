import pytest
import hashlib
from core.engine import UltimateClinicalAuditor, FullFHIRBundleExporter

@pytest.fixture
def base_patient():
    return {
        "hash": hashlib.sha256(b"TEST-PATIENT-001").hexdigest(),
        "age": 40,
        "sex": "M"
    }

def test_ckd_epi_2021_calculation():
    # Mężczyzna, 40 lat, kreatynina 0.94 mg/dL
    egfr_m = UltimateClinicalAuditor.calculate_ckd_epi(0.94, 40, "M")
    assert egfr_m > 90.0, f"eGFR powinien być > 90 ml/min, otrzymano: {egfr_m}"

    # Kobieta, 50 lat, kreatynina 1.10 mg/dL
    egfr_f = UltimateClinicalAuditor.calculate_ckd_epi(1.10, 50, "F")
    assert 55.0 <= egfr_f <= 75.0, f"eGFR poza zakresem oczekiwanym: {egfr_f}"

def test_preanalytical_edta_contamination_block(base_patient):
    # K+ > 7.5 przy Ca < 1.1 = twarda blokada EDTA
    contaminated_cur = {
        "K_POTASSIUM": 8.2,
        "CA_CALCIUM": 0.85,
        "H_INDEX": 0.04
    }
    res = UltimateClinicalAuditor.execute_god_mode_audit(base_patient, contaminated_cur, {})
    assert res["preanalytical"]["passed"] is False
    assert res["preanalytical"]["status"] == "REJECT_EDTA"

def test_preanalytical_hemolysis_block(base_patient):
    # H-Index > 0.50 g/L = odrzucenie z powodu hemolizy
    hemolyzed_cur = {
        "K_POTASSIUM": 4.4,
        "CA_CALCIUM": 2.35,
        "H_INDEX": 0.65
    }
    res = UltimateClinicalAuditor.execute_god_mode_audit(base_patient, hemolyzed_cur, {})
    assert res["preanalytical"]["passed"] is False
    assert res["preanalytical"]["status"] == "REJECT_HEMOLYSIS"

def test_full_pipeline_and_fhir_export(base_patient):
    valid_cur = {
        "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.04,
        "WBC": 5.8, "HGB": 15.6, "MCV": 88.4, "RDW_CV": 12.1, "PLT": 242.0,
        "GLUCOSE": 92.0, "INSULIN": 10.4, "HBA1C": 5.2,
        "CHOL_TOTAL": 188.0, "HDL": 55.0, "TRIGLYCERIDES": 162.0, "APOB": 84.0,
        "HS_TROPONIN": 4.2, "NT_PROBNP": 48.0, "D_DIMER": 280.0,
        "ALT": 46.0, "AST": 27.0, "ALP": 56.0, "GGTP": 24.0,
        "CREATININE": 0.94, "CYSTATIN_C": 0.82,
        "IRON": 112.0, "UIBC": 212.0, "FERRITIN": 145.0, "HS_CRP": 0.48, "HOMOCYSTEINE": 8.4,
        "TSH": 2.05, "FT4": 1.22, "FT3": 3.25, "ANTI_TPO": 10.4, "ANTI_CCP": 1.8,
        "TESTOSTERONE": 640.0, "SHBG": 35.0, "VIT_D3": 46.5, "PSA_TOTAL": 0.78, "CA125": 12.1
    }
    
    audit_res = UltimateClinicalAuditor.execute_god_mode_audit(base_patient, valid_cur, {})
    assert audit_res["preanalytical"]["passed"] is True
    assert len(audit_res["axes"]) == 10

    # Eksport do FHIR Bundle
    bundle = FullFHIRBundleExporter.export(audit_res)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["total"] > 30
    assert len(bundle["entry"]) == bundle["total"]
