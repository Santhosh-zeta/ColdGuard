"""
Tests for ColdGuard FastAPI REST wrapper.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test GET /health returns ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == __import__("core").__version__


def test_vaccines_endpoint(client):
    """Test GET /vaccines returns all 12 UIP vaccines."""
    response = client.get("/vaccines")
    assert response.status_code == 200
    data = response.json()

    assert data["count"] == 12
    assert len(data["vaccines"]) == 12

    vaccine_keys = {v["key"] for v in data["vaccines"]}
    expected = {"DPT", "OPV", "MMR", "BCG", "HepB", "IPV", "Rotavirus", "PCV", "YF", "JE", "Typhoid", "MenA"}
    assert vaccine_keys == expected

    # Verify freeze sensitivity is set
    dpt = next((v for v in data["vaccines"] if v["key"] == "DPT"), None)
    assert dpt is not None
    assert dpt["freeze_sensitive"] is True


def test_analyse_valid_dpt(client):
    """Test POST /analyse with valid DPT data."""
    payload = {
        "vaccine": "DPT",
        "timestamps": [1694592000, 1694595600],
        "temperatures_c": [5.2, 6.1],
        "n_mc_samples": 100,
    }
    response = client.post("/analyse", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["vaccine"] == "DPT"
    assert data["vaccine_name"] == "DPT (Diphtheria-Pertussis-Tetanus)"
    assert data["decision_output"]["decision"] in ["USE", "INVESTIGATE", "DISCARD"]
    assert 0 <= data["decision_output"]["confidence"] <= 1
    assert isinstance(data["decision_output"]["ci_90"], list)
    assert len(data["decision_output"]["ci_90"]) == 2
    assert data["decision_output"]["ci_90"][0] <= data["decision_output"]["ci_90"][1]


def test_analyse_min_readings(client):
    """Test POST /analyse with only 1 reading fails."""
    payload = {
        "vaccine": "DPT",
        "timestamps": [1694592000],
        "temperatures_c": [5.2],
    }
    response = client.post("/analyse", json=payload)
    assert response.status_code == 422  # Validation error


def test_analyse_invalid_vaccine(client):
    """Test POST /analyse with unknown vaccine fails."""
    payload = {
        "vaccine": "UNKNOWN",
        "timestamps": [1694592000, 1694595600],
        "temperatures_c": [5.2, 6.1],
    }
    response = client.post("/analyse", json=payload)
    assert response.status_code == 422


def test_analyse_temp_out_of_range(client):
    """Test POST /analyse with temperature out of range fails."""
    payload = {
        "vaccine": "DPT",
        "timestamps": [1694592000, 1694595600],
        "temperatures_c": [5.2, 100.0],  # 100°C is out of range
    }
    response = client.post("/analyse", json=payload)
    assert response.status_code == 422


def test_analyse_non_finite_readings(client):
    """Test POST /analyse rejects NaN/inf readings with 422."""
    import json

    headers = {"content-type": "application/json"}
    payload = {
        "vaccine": "DPT",
        "timestamps": [1694592000, 1694595600, 1694599200],
        "temperatures_c": [5.2, float("nan"), 5.0],
    }
    # json.dumps keeps the bare NaN token, which is what a data logger emits.
    response = client.post("/analyse", content=json.dumps(payload), headers=headers)
    assert response.status_code == 422
    assert "non-finite values at index 1" in response.json()["detail"]

    payload["temperatures_c"] = [5.2, 5.0, 5.0]
    payload["timestamps"] = [1694592000, float("nan"), 1694599200]
    response = client.post("/analyse", content=json.dumps(payload), headers=headers)
    assert response.status_code == 422
    assert "non-finite values at index 1" in response.json()["detail"]


def test_analyse_mismatched_lengths(client):
    """Test POST /analyse with mismatched timestamps/temperatures fails."""
    payload = {
        "vaccine": "DPT",
        "timestamps": [1694592000, 1694595600],
        "temperatures_c": [5.2],  # Only 1 temp but 2 timestamps
    }
    response = client.post("/analyse", json=payload)
    assert response.status_code == 422


def test_analyse_all_vaccines(client):
    """Test POST /analyse works for all 12 vaccines."""
    vaccines = ["DPT", "OPV", "MMR", "BCG", "HepB", "IPV", "Rotavirus", "PCV", "YF", "JE", "Typhoid", "MenA"]

    for vaccine in vaccines:
        payload = {
            "vaccine": vaccine,
            "timestamps": [1694592000, 1694595600],
            "temperatures_c": [5.0, 6.0],
            "n_mc_samples": 100,
        }
        response = client.post("/analyse", json=payload)
        assert response.status_code == 200, f"Failed for vaccine {vaccine}"
        data = response.json()
        assert data["vaccine"] == vaccine


def test_root_endpoint(client):
    """Test GET / returns API documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "docs" in data
    assert data["docs"] == "/docs"


def test_docs_endpoint(client):
    """Test that Swagger docs are available at /docs."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()


# ---------------------------------------------------------------------------
# POST /batch-analyse
# ---------------------------------------------------------------------------

GOOD_CSV = "timestamp,temperature_celsius\n" + "\n".join(
    f"{1694592000 + i * 3600},{4 + (i % 3)}" for i in range(24)
)


def test_batch_valid(client):
    body = {"batch": [{"vaccine": "DPT", "csv_data": GOOD_CSV},
                      {"vaccine": "BCG", "csv_data": GOOD_CSV, "label": "lot-2"}],
            "n_mc_samples": 200}
    r = client.post("/batch-analyse", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["total"] == 2
    assert data["summary"]["errors"] == 0
    assert data["audit_id"].startswith("batch-")
    assert [x["vaccine"] for x in data["results"]] == ["DPT", "BCG"]
    assert data["results"][1]["label"] == "lot-2"


def test_batch_partial_errors(client):
    body = {"batch": [{"vaccine": "DPT", "csv_data": GOOD_CSV},
                      {"vaccine": "NOPE", "csv_data": GOOD_CSV},
                      {"vaccine": "DPT", "csv_data": "garbage\n1"}],
            "n_mc_samples": 200}
    r = client.post("/batch-analyse", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["summary"]["errors"] == 2
    assert [x["status"] for x in data["results"]] == ["ok", "error", "error"]


def test_batch_large(client):
    body = {"batch": [{"vaccine": "DPT", "csv_data": GOOD_CSV}] * 25, "n_mc_samples": 100}
    r = client.post("/batch-analyse", json=body)
    assert r.status_code == 200
    assert r.json()["summary"]["total"] == 25


def test_batch_empty_rejected(client):
    assert client.post("/batch-analyse", json={"batch": []}).status_code == 422


def test_export_dhis2_endpoint(client):
    body = {"vaccine": "DPT", "timestamps": [1694592000, 1694595600, 1694599200],
            "temperatures_c": [5.0, 5.5, 5.0], "n_mc_samples": 100,
            "org_unit": "FAC123", "period": "20260115"}
    r = client.post("/export/dhis2", json=body)
    assert r.status_code == 200
    assert len(r.json()["dataValues"]) == 6
    body["period"] = "bad"
    assert client.post("/export/dhis2", json=body).status_code == 422


def test_export_dhis2_non_finite_reading(client):
    """POST /export/dhis2 returns the same 422 as /analyse for bad readings."""
    import json

    headers = {"content-type": "application/json"}
    body = {"vaccine": "DPT", "timestamps": [1694592000, 1694595600],
            "temperatures_c": [5.0, float("nan")], "n_mc_samples": 100,
            "org_unit": "FAC123"}
    response = client.post("/export/dhis2", content=json.dumps(body), headers=headers)
    assert response.status_code == 422
    assert "non-finite values at index 1" in response.json()["detail"]


def test_batch_accepts_semicolon_decimal_comma_csv(client):
    """In-memory CSV text in a European locale must work through /batch-analyse."""
    csv = "timestamp;temperature_celsius\n" + "\n".join(
        f"{1694592000 + i * 3600};{4 + (i % 3)},5" for i in range(24))
    r = client.post("/batch-analyse", json={"batch": [{"vaccine": "DPT", "csv_data": csv}],
                                            "n_mc_samples": 100})
    assert r.status_code == 200
    assert r.json()["results"][0]["status"] == "ok"
