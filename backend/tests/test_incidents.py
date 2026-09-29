from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.API_KEY}


def test_api_key_auth_enforcement():
    # Unauthenticated request to protected endpoint should fail
    response = client.post("/api/v1/incidents", json={"service": "payments", "title": "Test Incident"})
    assert response.status_code == 401
    json_data = response.json()
    assert "error" in json_data
    assert json_data["error"]["code"] == "UNAUTHORIZED"

    # Invalid API key should fail
    response = client.post(
        "/api/v1/incidents",
        headers={"X-API-Key": "invalid-key"},
        json={"service": "payments", "title": "Test Incident"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_key_generation_and_auth():
    # Generate new API key
    gen_response = client.post("/api/v1/keys", json={"name": "ci-test-key"})
    assert gen_response.status_code == 200
    data = gen_response.json()
    assert "api_key" in data
    assert data["name"] == "ci-test-key"

    new_key = data["api_key"]

    # Use generated key for protected endpoint
    response = client.get("/api/v1/memory/search?q=gateway", headers={"X-API-Key": new_key})
    assert response.status_code == 200
    assert "results" in response.json()


def test_input_size_limit_validation():
    # Input exceeding MAX_TEXT_LENGTH (50,000 chars)
    huge_text = "A" * 50001
    response = client.post(
        "/api/v1/incidents",
        headers=AUTH_HEADERS,
        json={"service": "payments", "title": "Test", "logs": huge_text},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "INPUT_TOO_LARGE"


def test_incidents_full_lifecycle():
    # 1. Create Incident
    create_payload = {
        "service": "payments-gateway",
        "title": "UPI transaction timeout spike during peak load",
        "alerts": "504 Gateway Timeout rate > 5% on payments-gateway",
        "logs": "2025-02-21T18:00:00Z ERROR payment_client: Timeout waiting for NPCI response after 8000ms",
    }
    response = client.post("/api/v1/incidents", headers=AUTH_HEADERS, json=create_payload)
    assert response.status_code == 200
    inc_data = response.json()
    assert "incident_id" in inc_data
    incident_id = inc_data["incident_id"]
    assert inc_data["status"] == "active"
    assert len(inc_data["ranked_fix_suggestions"]) > 0

    # Verify fix suggestion attributes
    suggestion = inc_data["ranked_fix_suggestions"][0]
    assert suggestion["outcome"] in ("worked", "failed", "temporary")

    # 2. Log Fix Attempt (failed)
    fix_payload_1 = {
        "description": "Increase gateway retry max_attempts from 3 to 5",
        "outcome": "failed",
        "notes": "Triggered retry storm against upstream payment provider",
    }
    fix_res_1 = client.post(
        f"/api/v1/incidents/{incident_id}/fix-attempts",
        headers=AUTH_HEADERS,
        json=fix_payload_1,
    )
    assert fix_res_1.status_code == 200
    assert fix_res_1.json()["outcome"] == "failed"

    # 3. Log Fix Attempt (worked)
    fix_payload_2 = {
        "description": "Reset timeout to 30s and mandate Idempotency-Key header on all retries",
        "outcome": "worked",
        "notes": "Success rate restored to 99.98%",
    }
    fix_res_2 = client.post(
        f"/api/v1/incidents/{incident_id}/fix-attempts",
        headers=AUTH_HEADERS,
        json=fix_payload_2,
    )
    assert fix_res_2.status_code == 200
    assert fix_res_2.json()["outcome"] == "worked"

    # 4. Resolve Incident
    resolve_payload = {
        "root_cause": "Timeout lowered prematurely without upstream SLA alignment",
        "resolution_notes": "Reverted timeout and enforced mandatory idempotency key header",
    }
    resolve_res = client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        headers=AUTH_HEADERS,
        json=resolve_payload,
    )
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "success"
    assert res_data["incident_id"] == incident_id
    postmortem = res_data["postmortem"]
    assert postmortem["root_cause"] == resolve_payload["root_cause"]
    assert "Reset timeout to 30s" in postmortem["fix_that_worked"]
    assert "Increase gateway retry max_attempts" in postmortem["fixes_that_failed"][0]
