import json
import logging
import time
from pathlib import Path
from typing import Any

try:
    from hindsight_client import Hindsight
except ImportError:  # The Hindsight SDK is installed only for live mode.
    Hindsight = None  # type: ignore[assignment,misc]

from backend.app.config import settings

logger = logging.getLogger(__name__)


def _safe_hindsight_error(exc: BaseException, api_key: str | None) -> str:
    message = str(exc).strip() or type(exc).__name__
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message[:1000]


class MemoryService:
    def __init__(self):
        self.mode = settings.FORESIGHT_MODE
        self.bank_id = settings.HINDSIGHT_BANK_ID
        self.api_key = settings.HINDSIGHT_API_KEY
        self.api_url = settings.HINDSIGHT_API_URL
        self._mock_memories: list[dict[str, Any]] = []
        self.initialization_error: str | None = None

        if self.is_live():
            if Hindsight is None:
                raise RuntimeError("Live mode requires the Hindsight SDK; install foresight with the 'live' extra")
            try:
                self.client = Hindsight(api_key=self.api_key, base_url=self.api_url, timeout=30.0)
            except Exception as exc:  # noqa: BLE001 - SDK construction errors are provider/configuration failures.
                self.client = None
                self.initialization_error = _safe_hindsight_error(exc, self.api_key)
                logger.error("Hindsight client initialization failed: %s", self.initialization_error)
            else:
                self._init_live_bank()
        else:
            self.client = None
            self._init_mock_bank()

    def is_live(self) -> bool:
        return self.mode == "live" and bool(self.api_key and self.api_key.strip())

    def _bank_already_exists(self, exc: BaseException) -> bool:
        status_code = getattr(exc, "status_code", None)
        if status_code is None:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
        message = str(exc).lower()
        return status_code == 409 or "already exists" in message or "bank exists" in message

    def _init_live_bank(self):
        try:
            self.client.create_bank(
                bank_id=self.bank_id,
                name="Foresight PayNest Safety Bank",
                mission="Remember deploys, incidents, root causes, fixes attempted, whether each fix worked, whether it held, and engineering context around them. Prioritize causal links between changes and outages.",
                background="PayNest UPI and card payments platform handling 2M txns/day.",
                retain_mission="Extract root causes, retry parameters, timeout configs, idempotency checks, and fix efficacy.",
                reflect_mission="Produce cautious, evidence-driven risk briefs citing past incidents and temporary fixes.",
            )
            logger.info(f"Initialized live Hindsight bank: {self.bank_id}")
        except Exception as e:  # noqa: BLE001 - SDK errors differ across auth, conflict, and network failures.
            if self._bank_already_exists(e):
                logger.info("Hindsight bank already exists | bank_id=%s", self.bank_id)
                return
            self.initialization_error = _safe_hindsight_error(e, self.api_key)
            logger.error(
                "Hindsight bank initialization failed | bank_id=%s | error=%s",
                self.bank_id,
                self.initialization_error,
            )

    def _init_mock_bank(self):
        seed_path = Path(__file__).parent.parent.parent.parent / "data" / "seed" / "incidents.json"
        if seed_path.exists():
            with open(seed_path, "r", encoding="utf-8") as f:
                incidents = json.load(f)
                for inc in incidents:
                    self._mock_memories.append({
                        "id": inc["id"],
                        "content": f"{inc['title']}. Root cause: {inc['root_cause_class']}. Service: {inc['service']}. Alert: {inc['alert_text']}. Error logs: {inc.get('error_logs', '')}. Slack: {inc.get('slack_excerpt', '')}",
                        "tags": [inc["service"], inc["severity"], inc["root_cause_class"]],
                        "metadata": {
                            "title": inc["title"],
                            "date": inc["date"],
                            "service": inc["service"],
                            "severity": inc["severity"],
                            "root_cause_class": inc["root_cause_class"],
                        },
                        "fix_attempts": inc.get("fix_attempts", []),
                    })

    def retain(
        self,
        content: str,
        document_id: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.is_live():
            try:
                self.client.retain(
                    bank_id=self.bank_id,
                    content=content,
                    document_id=document_id,
                    tags=tags,
                    metadata=metadata,
                )
            except Exception as e:  # noqa: BLE001 - surface every Hindsight retain failure.
                detail = _safe_hindsight_error(e, self.api_key)
                logger.error(
                    "Hindsight retain failed | bank_id=%s | document_id=%s | error=%s",
                    self.bank_id,
                    document_id,
                    detail,
                )
                raise RuntimeError(f"Hindsight retain failed for bank '{self.bank_id}': {detail}") from None
            logger.info(
                "Hindsight retain succeeded | bank_id=%s | document_id=%s",
                self.bank_id,
                document_id,
            )
            return {"status": "success", "backend": "hindsight", "document_id": document_id}
        else:
            mem_id = document_id or f"mock-mem-{len(self._mock_memories) + 1}"
            mock_entry = {
                "id": mem_id,
                "content": content,
                "tags": tags or [],
                "metadata": metadata or {},
            }
            if "fix_attempts" in (metadata or {}):
                mock_entry["fix_attempts"] = metadata["fix_attempts"]

            # Avoid duplicates if document_id already exists
            existing_idx = next((i for i, m in enumerate(self._mock_memories) if m["id"] == mem_id), None)
            if existing_idx is not None:
                self._mock_memories[existing_idx] = mock_entry
            else:
                self._mock_memories.append(mock_entry)
            return {"status": "success", "backend": "mock", "document_id": mem_id}

    def recall(self, query: str, tags: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if self.is_live():
            started_at = time.monotonic()
            try:
                import asyncio
                import concurrent.futures

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        def _do_async_recall():
                            return asyncio.run(self.client.arecall(bank_id=self.bank_id, query=query, tags=tags))
                        resp = pool.submit(_do_async_recall).result(timeout=35.0)
                else:
                    resp = self.client.recall(bank_id=self.bank_id, query=query, tags=tags)

                results = []
                for item in getattr(resp, "results", []):
                    results.append({
                        "id": getattr(item, "id", getattr(item, "document_id", "mem-live")),
                        "text": getattr(item, "text", getattr(item, "content", str(item))),
                        "score": getattr(item, "score", 0.9),
                        "tags": getattr(item, "tags", []),
                        "metadata": getattr(item, "metadata", {}),
                    })
                logger.info(
                    "Hindsight recall succeeded | bank_id=%s | result_count=%d | latency_ms=%.1f",
                    self.bank_id,
                    len(results[:limit]),
                    (time.monotonic() - started_at) * 1000,
                )
                return results[:limit]
            except Exception as e:  # noqa: BLE001 - surface every Hindsight recall failure.
                detail = _safe_hindsight_error(e, self.api_key)
                logger.error(
                    "Hindsight recall failed | bank_id=%s | error=%s",
                    self.bank_id,
                    detail,
                )
                raise RuntimeError(f"Hindsight recall failed for bank '{self.bank_id}': {detail}") from None
        else:
            query_lower = query.lower()
            query_terms = [t for t in query_lower.split() if len(t) > 2]
            matched = []

            for mem in self._mock_memories:
                text = (mem["content"] + " " + " ".join(mem["tags"]) + " " + str(mem.get("metadata", {}))).lower()
                matches = sum(1 for term in query_terms if term in text)
                score = 0.0

                if matches > 0:
                    score = min(0.95, 0.65 + (matches * 0.08))

                # Boost score for specific keyword matches
                if ("retry" in query_lower or "timeout" in query_lower) and ("retry" in text or "timeout" in text):
                    score = max(score, 0.88)

                if score > 0.3 or matches > 0:
                    matched.append({
                        "id": mem["id"],
                        "text": mem["content"],
                        "score": round(score, 2),
                        "tags": mem["tags"],
                        "metadata": mem.get("metadata", {}),
                        "fix_attempts": mem.get("fix_attempts", []),
                    })

            matched.sort(key=lambda x: x["score"], reverse=True)
            return matched[:limit]

    def search_memories(self, query: str) -> list[dict[str, Any]]:
        return self.recall(query=query, limit=20)

    def reset(self):
        self._mock_memories.clear()
        if not self.is_live():
            self._init_mock_bank()

    def get_count(self) -> int:
        return len(self._mock_memories)
