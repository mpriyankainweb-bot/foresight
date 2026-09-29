from fastapi.testclient import TestClient
from pydantic import BaseModel

from backend.app import main as main_module
from backend.app.config import settings
from backend.app.llm.client import LLMClient
from backend.app.main import app
from backend.app.memory.service import MemoryService

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

def test_health_reports_missing_provider_keys(monkeypatch):
    monkeypatch.setattr(settings, "FORESIGHT_MODE", "live")
    monkeypatch.setattr(main_module.memory_service, "mode", "live")
    monkeypatch.setattr(main_module.memory_service, "api_key", None)
    monkeypatch.setattr(main_module.memory_service, "initialization_error", None)
    monkeypatch.setattr(main_module.llm_client, "mode", "live")
    monkeypatch.setattr(main_module.llm_client, "api_key", None)

    response = client.get("/health")
    data = response.json()
    assert data["status"] == "degraded"
    assert data["memory_backend"] == "mock"
    assert data["llm_backend"] == "mock"
    assert any("HINDSIGHT_API_KEY" in warning for warning in data["warnings"])
    assert any("GROQ_API_KEY" in warning for warning in data["warnings"])

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
    assert data["bank_id"] == "offline-demo"
    assert data["results"][0]["content"]

def test_llm_client_offline_fallback():
    llm = LLMClient()
    fallback = {"message": "hello world", "code": 200}
    result = llm.generate_json(
        prompt="Say hello",
        system_prompt="You are a helper",
        response_model=SampleModel,
        fallback_data=fallback,
    )
    assert result.message == "hello world"
    assert result.code == 200

def test_memory_service_offline():
    mem = MemoryService()
    recalled = mem.recall("retry timeout")
    assert len(recalled) > 0
    assert any("retry" in r["text"].lower() for r in recalled)
