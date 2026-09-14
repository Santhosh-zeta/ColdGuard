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
    assert data["version"] == "1.0.0"


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
