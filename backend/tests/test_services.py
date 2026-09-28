from fastapi.testclient import TestClient
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.main import app

client = TestClient(app)

class SampleModel(BaseModel):
    message: str
    code: int

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "mode" in data
    assert "memory_backend" in data

def test_memory_search_unauthorized():
    response = client.get("/api/v1/memory/search?q=retry")
    assert response.status_code == 401

def test_memory_search_authorized():
    headers = {"X-API-Key": settings.API_KEY}
    response = client.get("/api/v1/memory/search?q=retry", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0

def test_friday_scenario_check_hold():
    headers = {"X-API-Key": settings.API_KEY}
    payload = {
        "service": "payments-gateway",
        "title": "Lower gateway retry timeout from 30s to 8s",
        "description": "Lower retry timeout for faster failure recovery",
        "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
        "environment": "production",
        "author": "Arjun",
        "memory_enabled": True,
    }
    response = client.post("/api/v1/deploys/check", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "HOLD"
    assert data["risk_score"] >= 80
    assert data["memory_used"] is True
    assert len(data["memory_citations"]) > 0
    assert len(data["similar_incidents"]) > 0

def test_memory_disabled_toggle():
    headers = {"X-API-Key": settings.API_KEY}
    payload = {
        "service": "payments-gateway",
        "title": "Lower gateway retry timeout from 30s to 8s",
        "description": "Lower retry timeout for faster failure recovery",
        "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
        "environment": "production",
        "author": "Arjun",
        "memory_enabled": False,
    }
    response = client.post("/api/v1/deploys/check", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["memory_used"] is False
    assert len(data["memory_citations"]) == 0
    assert len(data["similar_incidents"]) == 0

def test_record_outcome():
    headers = {"X-API-Key": settings.API_KEY}
    payload = {"outcome": "degraded", "notes": "Observed slight latency spike in UPI"}
    response = client.post("/api/v1/deploys/chk-12345/outcome", headers=headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["check_id"] == "chk-12345"
    assert data["outcome"] == "degraded"
    assert data["retained"] is True

def test_demo_replay_and_reset():
    replay_resp = client.post("/api/v1/demo/replay")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert replay_data["status"] == "success"
    assert replay_data["incidents_retained"] == 20
    assert replay_data["deploys_retained"] == 40

    reset_resp = client.post("/api/v1/demo/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "success"

def test_analytics_learning_curve():
    response = client.get("/api/v1/analytics/learning-curve")
    assert response.status_code == 200
    data = response.json()
    assert "series" in data
    assert len(data["series"]) > 0
    assert data["current_accuracy"] > 90
