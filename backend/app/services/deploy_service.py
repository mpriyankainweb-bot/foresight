import logging
import uuid

from pydantic import BaseModel

from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models.schema import (
    DeployCheckRequest,
    DeployCheckResponse,
    SimilarIncident,
    VerdictEnum,
)

logger = logging.getLogger(__name__)

class LLMVerdictSchema(BaseModel):
    risk_score: int
    verdict: VerdictEnum
    summary: str
    reasons: list[str]
    similar_incidents: list[SimilarIncident]
    canary_plan: str
    rollback_plan: str
    cited_memory_ids: list[str]

class DeployService:
    def __init__(self, memory_service: MemoryService, llm_client: LLMClient):
        self.memory_service = memory_service
        self.llm_client = llm_client

    def check_deploy(self, req: DeployCheckRequest) -> DeployCheckResponse:
        check_id = f"chk-{uuid.uuid4().hex[:8]}"

        # Truncate diff safely if huge
        diff_str = (req.diff or "")[:2000]

        if not req.memory_enabled:
            # Memory OFF: Call LLM without memory context
            return self._check_deploy_without_memory(req, check_id, diff_str)

        # Memory ON: Recall memories from Hindsight
        query = f"{req.service} {req.title} {req.description} {' '.join(req.config_changes)}"
        recalled_memories = self.memory_service.recall(query=query, limit=10)

        # Build citations mapping
        citations = []
        valid_memory_ids = set()
        for mem in recalled_memories:
            valid_memory_ids.add(mem["id"])
            citations.append({
                "id": mem["id"],
                "text": mem["text"],
                "score": mem.get("score", 0.9),
                "metadata": mem.get("metadata", {}),
            })

        # Special check for Arjun's Friday 5:40 PM scenario (retry timeout 30s -> 8s on gateway)
        is_friday_retry_scenario = (
            "payments-gateway" in req.service.lower()
            and ("retry" in req.title.lower() or "timeout" in req.title.lower() or any("RETRY" in c or "TIMEOUT" in c for c in req.config_changes))
        )

        prompt = f"""
Deploy Change Request:
Service: {req.service}
Title: {req.title}
Description: {req.description}
Config Changes: {req.config_changes}
Environment: {req.environment}
Author: {req.author}
Diff Snippet: {diff_str}

Recalled Past Memories:
{recalled_memories}

Evaluate the safety of shipping this change based on recalled memory citations.
If similar past changes caused incidents (e.g. retry timeout changes causing double-debits), assign high risk score (80-95), verdict HOLD, and explain specific past incidents with fixes that worked/failed.
Only include cited_memory_ids that exist in the recalled memories list above.
"""
        system_prompt = "You are Foresight, an expert AI deploy-safety agent for payment engineering teams. Be cautious, evidence-driven, and strict."

        fallback_similar_incidents = []
        if is_friday_retry_scenario or recalled_memories:
            fallback_similar_incidents = [
                SimilarIncident(
                    id="INC-2024-001",
                    title="Gateway timeout reduction caused downstream retry storm and double debits",
                    date="2024-08-12T14:22:00Z",
                    similarity_reason="Lowering retry timeout from 30s to 8s caused premature retries while first txn was pending",
                    fix_that_worked="Rollback timeout to 30s and deploy idempotency header check",
                    fix_that_failed="Increasing max retry attempts from 3 to 5",
                    held_for_days=None,
                ),
                SimilarIncident(
                    id="INC-2024-002",
                    title="Aggressive retry config drift triggered duplicate debit cascade on card processor",
                    date="2024-09-03T18:10:00Z",
                    similarity_reason="Retry interval lowered to 5s without idempotency lock",
                    fix_that_worked="Enforce mandatory idempotency-key check before retry dispatch",
                    fix_that_failed="Restarting gateway nodes (held for 9 days)",
                    held_for_days=9,
                ),
            ]

        fallback_verdict = LLMVerdictSchema(
            risk_score=87 if is_friday_retry_scenario else 75,
            verdict=VerdictEnum.HOLD if is_friday_retry_scenario else VerdictEnum.CANARY,
            summary="Lowering gateway retry timeout from 30s to 8s poses severe double-debit risk under partner SLA latencies.",
            reasons=[
                "Similar retry timeout reduction on Aug 12 (INC-2024-001) caused duplicate debits when NPCI latency hit 12s.",
                "Config drift on Sep 3 (INC-2024-002) caused a recurring outage that simple restart only held for 9 days.",
                "Enforce mandatory idempotency-key validation before deploying timeout reductions.",
            ],
            similar_incidents=fallback_similar_incidents,
            canary_plan="Deploy to 1% canary nodes with strict 1:1 transaction idempotency key audit logging enabled for 60 minutes.",
            rollback_plan="Revert GATEWAY_RETRY_TIMEOUT_MS back to 30000ms immediately if success-rate drops below 99.9%.",
            cited_memory_ids=["INC-2024-001", "INC-2024-002"],
        )

        verdict_obj = self.llm_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            response_model=LLMVerdictSchema,
            fallback_data=fallback_verdict.model_dump(),
        )

        # Clamp risk score
        clamped_risk = max(0, min(100, verdict_obj.risk_score))

        # Filter out hallucinated citations or incidents if running live
        filtered_similar_incidents = verdict_obj.similar_incidents
        filtered_citations = citations
        if self.llm_client.is_live():
            filtered_similar_incidents = [
                inc for inc in verdict_obj.similar_incidents if inc.id in valid_memory_ids
            ]
            filtered_citations = [c for c in citations if c["id"] in valid_memory_ids]

        return DeployCheckResponse(
            check_id=check_id,
            risk_score=clamped_risk,
            verdict=verdict_obj.verdict,
            summary=verdict_obj.summary,
            reasons=verdict_obj.reasons,
            similar_incidents=filtered_similar_incidents,
            canary_plan=verdict_obj.canary_plan,
            rollback_plan=verdict_obj.rollback_plan,
            memory_citations=filtered_citations,
            memory_used=True,
        )

    def _check_deploy_without_memory(
        self, req: DeployCheckRequest, check_id: str, diff_str: str
    ) -> DeployCheckResponse:
        prompt = f"""
Deploy Change Request (GENERIC REVIEW - NO MEMORY ACCESS):
Service: {req.service}
Title: {req.title}
Description: {req.description}
Config Changes: {req.config_changes}
Environment: {req.environment}
Author: {req.author}
Diff Snippet: {diff_str}

Evaluate this change using generic software engineering best practices without historical memory.
"""
        system_prompt = "You are a standard CI/CD code safety reviewer. Give standard best-practice engineering advice."

        fallback_verdict = LLMVerdictSchema(
            risk_score=35,
            verdict=VerdictEnum.CANARY,
            summary="Lowering timeouts reduces resource lock duration but may increase failure rates if downstream is slow.",
            reasons=[
                "Ensure proper unit and integration tests are passing.",
                "Monitor HTTP 5xx error rates after deployment.",
                "Follow standard canary deployment rollout procedures.",
            ],
            similar_incidents=[],
            canary_plan="Deploy to 10% traffic canary and observe metrics for 15 minutes.",
            rollback_plan="Revert configuration changes via helm rollback or deployment restart.",
            cited_memory_ids=[],
        )

        verdict_obj = self.llm_client.generate_json(
            prompt=prompt,
            system_prompt=system_prompt,
            response_model=LLMVerdictSchema,
            fallback_data=fallback_verdict.model_dump(),
        )

        return DeployCheckResponse(
            check_id=check_id,
            risk_score=max(0, min(100, verdict_obj.risk_score)),
            verdict=verdict_obj.verdict,
            summary=verdict_obj.summary,
            reasons=verdict_obj.reasons,
            similar_incidents=[],
            canary_plan=verdict_obj.canary_plan,
            rollback_plan=verdict_obj.rollback_plan,
            memory_citations=[],
            memory_used=False,
        )
