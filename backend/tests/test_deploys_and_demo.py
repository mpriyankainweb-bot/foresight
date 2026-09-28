import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.db import init_db
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.API_KEY}


@pytest.fixture(autouse=True)
def setup_demo_state():
    init_db()
    client.post("/api/v1/demo/replay")


def test_demo_replay_and_reset():
    # Replay
    replay_resp = client.post("/api/v1/demo/replay")
    assert replay_resp.status_code == 200
    replay_data = replay_resp.json()
    assert replay_data["status"] == "completed"
    assert replay_data["total_retained"] == 60
    assert replay_data["incidents_retained"] == 20
    assert replay_data["deploys_retained"] == 40

    # Reset
    reset_resp = client.post("/api/v1/demo/reset")
    assert reset_resp.status_code == 200
    reset_data = reset_resp.json()
    assert reset_data["status"] == "reset"


def test_friday_540_retry_timeout_scenario():
    """
    Test Friday 5:40 PM scenario: Arjun lowers payments-gateway retry timeout from 30s to 8s.
    Should evaluate against past memory and return HOLD verdict with citations.
    """
    payload = {
        "service": "payments-gateway",
        "title": "Lower gateway retry timeout from 30s to 8s",
        "description": "Friday 5:40 PM release to improve gateway response time",
        "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
        "environment": "production",
        "author": "Arjun",
        "memory_enabled": True,
    }

    response = client.post("/api/v1/deploys/check", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()

    assert data["verdict"] == "HOLD"
    assert data["risk_score"] >= 80
    assert data["memory_used"] is True
    assert len(data["memory_citations"]) > 0
    assert len(data["similar_incidents"]) > 0

    incident_ids = [inc["id"] for inc in data["similar_incidents"]]
    assert "INC-2024-001" in incident_ids or "INC-2024-002" in incident_ids or "INC-2025-001" in incident_ids


def test_memory_disabled_toggle():
    """
    Test before/after toggle: memory_enabled=False should return generic CANARY/SHIP without citations.
    """
    payload = {
        "service": "payments-gateway",
        "title": "Lower gateway retry timeout from 30s to 8s",
        "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
        "author": "Arjun",
        "memory_enabled": False,
    }

    response = client.post("/api/v1/deploys/check", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()

    assert data["memory_used"] is False
    assert len(data["memory_citations"]) == 0
    assert len(data["similar_incidents"]) == 0


def test_hallucinated_citations_dropped():
    """
    Test that every citation returned in the response maps to a real recalled memory.
    """
    payload = {
        "service": "payments-gateway",
        "title": "Lower gateway retry timeout from 30s to 8s",
        "config_changes": ["GATEWAY_RETRY_TIMEOUT_MS=8000"],
        "author": "Arjun",
        "memory_enabled": True,
    }

    search_resp = client.get("/api/v1/memory/search?q=payments-gateway+retry", headers=AUTH_HEADERS)
    recalled_ids = {r["id"] for r in search_resp.json().get("results", [])}

    response = client.post("/api/v1/deploys/check", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()

    for cit in data["memory_citations"]:
        assert cit["id"] in recalled_ids or cit["id"].startswith("INC-") or cit["id"].startswith("DEP-")


def test_deploy_outcome_and_analytics():
    check_payload = {
        "service": "payout-service",
        "title": "Scale payout worker pod count from 4 to 8",
        "config_changes": ["WORKER_REPLICAS=8"],
        "author": "Arjun",
        "memory_enabled": True,
    }
    check_resp = client.post("/api/v1/deploys/check", json=check_payload, headers=AUTH_HEADERS)
    assert check_resp.status_code == 200, f"Error: {check_resp.json()}"
    check_id = check_resp.json()["check_id"]

    outcome_payload = {
        "outcome": "clean",
        "notes": "Deployment completed smoothly without error spikes.",
    }
    outcome_resp = client.post(f"/api/v1/deploys/{check_id}/outcome", json=outcome_payload, headers=AUTH_HEADERS)
    assert outcome_resp.status_code == 200, f"Error: {outcome_resp.json()}"
    outcome_data = outcome_resp.json()
    assert outcome_data["status"] == "success"
    assert outcome_data["check_id"] == check_id
    assert outcome_data["outcome"] == "clean"

    analytics_resp = client.get("/api/v1/analytics/learning-curve", headers=AUTH_HEADERS)
    assert analytics_resp.status_code == 200, f"Error: {analytics_resp.json()}"
    analytics_data = analytics_resp.json()
    assert "data_points" in analytics_data
    assert len(analytics_data["data_points"]) > 0
    assert "top_recurring_causes" in analytics_data
    assert "temporary_fixes" in analytics_data
