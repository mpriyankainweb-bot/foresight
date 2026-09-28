import json
import logging
from pathlib import Path
from typing import Any

from hindsight_client import Hindsight

from backend.app.config import settings

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.mode = settings.FORESIGHT_MODE
        self.bank_id = settings.HINDSIGHT_BANK_ID
        self.api_key = settings.HINDSIGHT_API_KEY
        self.api_url = settings.HINDSIGHT_API_URL
        self._mock_memories: list[dict[str, Any]] = []

        if self.is_live():
            self.client = Hindsight(api_key=self.api_key, base_url=self.api_url)
            self._init_live_bank()
        else:
            self.client = None
            self._init_mock_bank()

    def is_live(self) -> bool:
        return self.mode == "live" and bool(self.api_key)

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
        except Exception as e:
            logger.info(f"Hindsight bank creation note (may already exist): {e}")

    def _init_mock_bank(self):
        seed_path = Path(__file__).parent.parent.parent.parent / "data" / "seed" / "incidents.json"
        if seed_path.exists():
            with open(seed_path, "r") as f:
                incidents = json.load(f)
                for inc in incidents:
                    self._mock_memories.append({
                        "id": inc["id"],
                        "content": f"{inc['title']}. Root cause: {inc['root_cause_class']}. Alert: {inc['alert_text']}",
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
        metadata: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if self.is_live():
            self.client.retain(
                bank_id=self.bank_id,
                content=content,
                document_id=document_id,
                tags=tags,
                metadata=metadata,
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
            self._mock_memories.append(mock_entry)
            return {"status": "success", "backend": "mock", "document_id": mem_id}

    def recall(self, query: str, tags: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if self.is_live():
            try:
                resp = self.client.recall(bank_id=self.bank_id, query=query, tags=tags)
                results = []
                for item in getattr(resp, "results", []):
                    results.append({
                        "id": getattr(item, "id", "mem-live"),
                        "text": getattr(item, "text", str(item)),
                        "score": getattr(item, "score", 0.9),
                        "tags": getattr(item, "tags", []),
                        "metadata": getattr(item, "metadata", {}),
                    })
                return results
            except Exception as e:
                logger.error(f"Error during Hindsight recall: {e}")
                return []
        else:
            # Simple keyword search for mock bank
            query_terms = query.lower().split()
            matched = []
            for mem in self._mock_memories:
                text = (mem["content"] + " " + " ".join(mem["tags"])).lower()
                score = sum(1.0 for term in query_terms if term in text)
                if score > 0 or "retry" in query.lower() or "timeout" in query.lower():
                    matched.append({
                        "id": mem["id"],
                        "text": mem["content"],
                        "score": round(0.7 + (score * 0.05), 2),
                        "tags": mem["tags"],
                        "metadata": mem["metadata"],
                        "fix_attempts": mem.get("fix_attempts", []),
                    })
            matched.sort(key=lambda x: x["score"], reverse=True)
            return matched[:limit]

    def search_memories(self, query: str) -> list[dict[str, Any]]:
        return self.recall(query=query, limit=20)
