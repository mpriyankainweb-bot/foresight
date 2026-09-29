import pytest
from pydantic import BaseModel

from backend.app.llm.client import LLMClient
from backend.app.memory import service as memory_module
from backend.app.memory.service import MemoryService


class SampleModel(BaseModel):
    message: str


class FailingHindsightClient:
    def recall(self, **kwargs):
        raise RuntimeError("401 Unauthorized: token secret-test-key")

    def retain(self, **kwargs):
        raise RuntimeError("401 Unauthorized: token secret-test-key")


def live_memory_service() -> MemoryService:
    service = MemoryService.__new__(MemoryService)
    service.mode = "live"
    service.bank_id = "test-bank"
    service.api_key = "secret-test-key"
    service.api_url = "https://api.hindsight.vectorize.io"
    service.client = FailingHindsightClient()
    service.initialization_error = None
    service._mock_memories = []
    return service


def test_live_hindsight_recall_error_is_not_empty_results():
    service = live_memory_service()
    with pytest.raises(RuntimeError, match="Hindsight recall failed") as error:
        service.recall("test query")
    assert "secret-test-key" not in str(error.value)
    assert "[REDACTED]" in str(error.value)


def test_live_hindsight_retain_error_is_not_reported_as_success():
    service = live_memory_service()
    with pytest.raises(RuntimeError, match="Hindsight retain failed") as error:
        service.retain("test memory", document_id="test-doc")
    assert "secret-test-key" not in str(error.value)
    assert "[REDACTED]" in str(error.value)


def test_hindsight_client_initialization_error_is_reported_without_crashing(monkeypatch):
    monkeypatch.setattr(memory_module.settings, "FORESIGHT_MODE", "live")
    monkeypatch.setattr(memory_module.settings, "HINDSIGHT_API_KEY", "secret-test-key")
    monkeypatch.setattr(memory_module.settings, "HINDSIGHT_API_URL", "https://bad.example")
    monkeypatch.setattr(memory_module.settings, "HINDSIGHT_BANK_ID", "test-bank")

    def broken_client(**kwargs):
        raise ValueError("invalid configuration secret-test-key")

    monkeypatch.setattr(memory_module, "Hindsight", broken_client)
    service = MemoryService()

    assert service.is_live()
    assert service.client is None
    assert service.initialization_error == "invalid configuration [REDACTED]"


def test_live_groq_error_does_not_return_deterministic_fallback(monkeypatch):
    client = LLMClient()
    client.mode = "live"
    client.api_key = "secret-groq-key"
    client.primary_model = "primary-model"
    client.fallback_model = "fallback-model"

    def fail_request(model, prompt, system_prompt):
        raise RuntimeError("provider rejected secret-groq-key")

    monkeypatch.setattr(client, "_call_groq", fail_request)
    with pytest.raises(RuntimeError, match="Live Groq JSON generation failed") as error:
        client.generate_json(
            prompt="prompt",
            system_prompt="return JSON",
            response_model=SampleModel,
            fallback_data={"message": "mock answer"},
        )
    assert "secret-groq-key" not in str(error.value)
    assert "mock answer" not in str(error.value)


def test_live_groq_text_uses_fallback_model_after_primary_failure(monkeypatch):
    client = LLMClient()
    client.mode = "live"
    client.api_key = "test-groq-key"
    client.primary_model = "primary-model"
    client.fallback_model = "fallback-model"
    attempted_models = []

    def call_model(model, prompt, system_prompt):
        attempted_models.append(model)
        if model == "primary-model":
            raise RuntimeError("primary unavailable")
        return "A live Groq answer based on the supplied evidence."

    monkeypatch.setattr(client, "_call_groq", call_model)
    answer = client.generate_text("question", "system")
    assert answer.startswith("A live Groq answer")
    assert attempted_models == ["primary-model", "fallback-model"]
