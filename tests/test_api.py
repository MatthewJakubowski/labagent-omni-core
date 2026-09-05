from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

def test_api_audit_endpoint():
    payload = {
        "patient": {"age": 40, "sex": "M", "patient_id": "TEST_001"},
        "current_results": {
            "K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.04,
            "ALT": 46.0, "AST": 27.0, "CREATININE": 0.94
        }
    }
    res = client.post("/api/v1/audit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["preanalytical"]["passed"] is True
    assert len(data["axes"]) > 0

def test_api_synthesize_endpoint_with_placeholder():
    payload = {
        "patient": {"age": 40, "sex": "M"},
        "current_results": {"K_POTASSIUM": 4.4, "CA_CALCIUM": 2.38, "H_INDEX": 0.04}
    }
    res = client.post("/api/v1/synthesize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SYNTHESIZED_LOCAL_FALLBACK"
    assert "patient_view" in data
    assert "physician_sbar" in data
