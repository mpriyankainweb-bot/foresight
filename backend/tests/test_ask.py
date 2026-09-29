import json

from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.db import init_db
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.API_KEY}


def setup_function():
    init_db()


def test_ask_foresight_unauthorized():
    resp = client.post("/api/v1/ask", json={"question": "What broke last time?"})
    assert resp.status_code == 401


def test_ask_foresight_streaming():
    resp = client.post(
        "/api/v1/ask",
        json={"question": "What broke last time we changed retry timeouts?"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 200

    lines = [line.strip() for line in resp.text.strip().split("\n") if line.strip()]
    assert len(lines) >= 2

    # First event should contain citations
    first_event = json.loads(lines[0])
    assert first_event["type"] == "citations"
    assert "citations" in first_event

    # Intermediate events should contain deltas
    delta_events = [json.loads(line) for line in lines[1:] if json.loads(line).get("type") == "delta"]
    assert len(delta_events) > 0
    full_text = "".join([e["text"] for e in delta_events])
    assert "retry" in full_text.lower() or "timeout" in full_text.lower() or "paynest" in full_text.lower()

    # Final event should be done
    last_event = json.loads(lines[-1])
    assert last_event["type"] == "done"
