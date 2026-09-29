import json
import logging
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self):
        self.mode = settings.FORESIGHT_MODE
        self.primary_model = settings.GROQ_PRIMARY_MODEL
        self.fallback_model = settings.GROQ_FALLBACK_MODEL
        self.api_key = settings.GROQ_API_KEY
        self._cache: dict[str, Any] = {}

    def is_live(self) -> bool:
        return self.mode == "live" and bool(self.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def _call_groq(self, model: str, prompt: str, system_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is missing")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Ensure system or user message includes the word 'json' when response_format is json_object
        formatted_sys_prompt = system_prompt
        if "json" not in system_prompt.lower() and "json" not in prompt.lower():
            formatted_sys_prompt = f"{system_prompt}\n\nPlease respond in valid JSON format."

        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": formatted_sys_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if "json" in formatted_sys_prompt.lower() or "json" in prompt.lower():
            payload["response_format"] = {"type": "json_object"}

        start_time = time.time()
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        latency_ms = (time.time() - start_time) * 1000
        usage = data.get("usage", {})
        logger.info(
            f"Groq API call succeeded | Model: {model} | Latency: {latency_ms:.1f}ms | Tokens: {usage.get('total_tokens', 0)}"
        )
        return data["choices"][0]["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        response_model: type[T],
        fallback_data: dict[str, Any] | None = None,
    ) -> T:
        cache_key = f"{prompt}:{system_prompt}:{response_model.__name__}"
        if cache_key in self._cache:
            return response_model.model_validate(self._cache[cache_key])

        if not self.is_live():
            if fallback_data:
                return response_model.model_validate(fallback_data)
            raise RuntimeError("LLM is in offline mode and no fallback mock data was provided")

        models_to_try = [self.primary_model, self.fallback_model]
        last_error = None

        for model in models_to_try:
            try:
                content = self._call_groq(model, prompt, system_prompt)
                parsed_json = json.loads(content)
                obj = response_model.model_validate(parsed_json)
                self._cache[cache_key] = obj.model_dump()
                return obj
            except Exception as e:
                logger.warning(f"Failed LLM generation on model {model}: {e}. Retrying with repair prompt...")
                try:
                    repair_prompt = (
                        f"{prompt}\n\nYour previous response failed validation with error: {e}.\n"
                        f"Please output STRICT JSON matching schema: {response_model.model_json_schema()}"
                    )
                    content = self._call_groq(model, repair_prompt, system_prompt)
                    parsed_json = json.loads(content)
                    obj = response_model.model_validate(parsed_json)
                    self._cache[cache_key] = obj.model_dump()
                    return obj
                except Exception as repair_err:
                    logger.error(f"Repair attempt failed on model {model}: {repair_err}")
                    last_error = repair_err

        if fallback_data:
            logger.warning(f"All LLM models failed. Returning fallback response: {last_error}")
            return response_model.model_validate(fallback_data)

        raise RuntimeError(f"LLM generation completely failed: {last_error}")
