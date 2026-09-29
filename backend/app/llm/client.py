import json
import logging
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _should_retry_groq(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    return isinstance(exc, httpx.HTTPStatusError) and (
        exc.response.status_code == 429 or exc.response.status_code >= 500
    )


class LLMClient:
    def __init__(self):
        self.mode = settings.FORESIGHT_MODE
        self.primary_model = settings.GROQ_PRIMARY_MODEL
        self.fallback_model = settings.GROQ_FALLBACK_MODEL
        self.api_key = settings.GROQ_API_KEY
        self._cache: dict[str, Any] = {}

    def is_live(self) -> bool:
        return self.mode == "live" and bool(self.api_key and self.api_key.strip())

    def _safe_error(self, exc: BaseException) -> str:
        message = str(exc).strip() or type(exc).__name__
        if self.api_key:
            message = message.replace(self.api_key, "[REDACTED]")
        return message[:1000]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.TransportError) | retry_if_exception(_should_retry_groq),
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

        start_time = time.monotonic()
        timeout = httpx.Timeout(60.0, connect=10.0)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            if response.is_error:
                try:
                    error_body = response.json()
                    error_detail = error_body.get("error", {}).get("message", response.text)
                except (ValueError, AttributeError):
                    error_detail = response.text
                if self.api_key:
                    error_detail = str(error_detail).replace(self.api_key, "[REDACTED]")
                error_detail = str(error_detail).strip()[:800] or response.reason_phrase
                logger.error(
                    "Groq API request failed | model=%s | status=%s | error=%s",
                    model,
                    response.status_code,
                    error_detail,
                )
                raise httpx.HTTPStatusError(
                    f"Groq API returned HTTP {response.status_code}: {error_detail}",
                    request=response.request,
                    response=response,
                )
            data = response.json()

        latency_ms = (time.monotonic() - start_time) * 1000
        usage = data.get("usage", {})
        logger.info(
            "Groq API call succeeded | model=%s | latency_ms=%.1f | tokens=%s",
            model,
            latency_ms,
            usage.get("total_tokens", 0),
        )
        return data["choices"][0]["message"]["content"]

    def _models_to_try(self) -> list[str]:
        return list(dict.fromkeys(model for model in (self.primary_model, self.fallback_model) if model))

    def generate_text(self, prompt: str, system_prompt: str) -> str:
        if not self.is_live():
            raise RuntimeError("Groq is not configured for live mode")

        last_error: BaseException | None = None
        for model in self._models_to_try():
            try:
                return self._call_groq(model=model, prompt=prompt, system_prompt=system_prompt)
            except Exception as exc:  # noqa: BLE001 - provider failures trigger configured model failover.
                last_error = exc
                logger.warning(
                    "Groq text generation failed | model=%s | error=%s",
                    model,
                    self._safe_error(exc),
                )

        detail = self._safe_error(last_error) if last_error else "no Groq model is configured"
        raise RuntimeError(f"Groq text generation failed for all configured models: {detail}") from last_error

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
            if fallback_data is not None:
                return response_model.model_validate(fallback_data)
            raise RuntimeError("Groq is offline or GROQ_API_KEY is missing and no fallback data was provided")

        last_error: BaseException | None = None
        for model in self._models_to_try():
            try:
                content = self._call_groq(model, prompt, system_prompt)
                parsed_json = json.loads(content)
                obj = response_model.model_validate(parsed_json)
                self._cache[cache_key] = obj.model_dump()
                return obj
            except Exception as exc:  # noqa: BLE001 - provider, JSON, and schema errors trigger model failover.
                logger.warning(
                    "Groq JSON generation failed | model=%s | error=%s; trying a repair request",
                    model,
                    self._safe_error(exc),
                )
                try:
                    repair_prompt = (
                        f"{prompt}\n\nYour previous response failed validation with error: "
                        f"{self._safe_error(exc)}.\nPlease output STRICT JSON matching schema: "
                        f"{response_model.model_json_schema()}"
                    )
                    content = self._call_groq(model, repair_prompt, system_prompt)
                    parsed_json = json.loads(content)
                    obj = response_model.model_validate(parsed_json)
                    self._cache[cache_key] = obj.model_dump()
                    return obj
                except Exception as repair_error:  # noqa: BLE001 - report any repair/model/schema failure.
                    logger.error(
                        "Groq repair request failed | model=%s | error=%s",
                        model,
                        self._safe_error(repair_error),
                    )
                    last_error = repair_error

        detail = self._safe_error(last_error) if last_error else "no Groq model is configured"
        raise RuntimeError(f"Live Groq JSON generation failed for all configured models: {detail}") from last_error
