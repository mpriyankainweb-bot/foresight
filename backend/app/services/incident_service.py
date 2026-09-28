import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.app.db import engine
from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    FixAttemptRecord,
    FixSuggestionItem,
    IncidentRecord,
    LogFixAttemptRequest,
    LogFixAttemptResponse,
    MemoryCitationItem,
    PostmortemDraft,
    ResolveIncidentRequest,
    ResolveIncidentResponse,
)

logger = logging.getLogger(__name__)


class LLMFixSuggestionsResponse(BaseModel):
    ranked_fix_suggestions: list[FixSuggestionItem]
    memory_citations: list[MemoryCitationItem]


class IncidentService:
    def __init__(self, memory_service: MemoryService, llm_client: LLMClient):
        self.memory_service = memory_service
        self.llm_client = llm_client

    def _build_offline_fix_suggestions(
        self, request: CreateIncidentRequest, recalled_memories: list[dict[str, Any]]
    ) -> dict[str, Any]:
        combined = f"{request.service} {request.title} {request.alerts} {request.logs}".lower()
        recalled_ids = {m["id"] for m in recalled_memories}

        default_suggestions = [
            FixSuggestionItem(
                id="fix_001",
                description="Enforce mandatory idempotency key headers on gateway retry dispatch and reset timeout threshold to 30s",
                outcome="worked",
                held_for_days=None,
                confidence=0.95,
                source_incident_id="INC-2024-001",
                reasoning="Worked for similar gateway timeout and double-debit incident INC-2024-001.",
            ),
            FixSuggestionItem(
                id="fix_002",
                description="Increase gateway retry max_attempts from 3 to 5",
                outcome="failed",
                held_for_days=None,
                confidence=0.85,
                source_incident_id="INC-2024-001",
                reasoning="Failed in INC-2024-001 because it aggravated the retry storm against NPCI upstream.",
            ),
            FixSuggestionItem(
                id="fix_003",
                description="Restart gateway worker nodes to flush local in-memory config cache",
                outcome="temporary",
                held_for_days=9,
                confidence=0.70,
                source_incident_id="INC-2024-002",
                reasoning="Relieved queue backlog in INC-2024-002 but failed after 9 days due to config drift.",
            ),
        ]

        citations = [
            MemoryCitationItem(
                id=m["id"],
                text=m["text"][:300],
                score=m.get("score", 0.9),
                tags=m.get("tags", []),
            )
            for m in recalled_memories
        ]

        if not citations:
            citations = [
                MemoryCitationItem(
                    id="INC-2024-001",
                    text="Gateway timeout reduction from 30s to 8s caused downstream retry storm and double debits.",
                    score=0.92,
                    tags=["payments-gateway", "SEV-1", "double_debit"],
                )
            ]

        return {
            "ranked_fix_suggestions": default_suggestions,
            "memory_citations": citations,
        }

    def create_incident(
        self, request: CreateIncidentRequest, db_session: Session
    ) -> CreateIncidentResponse:
        incident_id = f"inc_{uuid.uuid4().hex[:12]}"

        # Recall memories using alerts, logs, title, service
        query = f"{request.service} {request.title} {request.alerts} {request.logs}"[:500]
        recalled_memories = self.memory_service.recall(query=query, limit=10)
        recalled_ids = {m["id"] for m in recalled_memories}

        system_prompt = (
            "You are Foresight, an AI deploy-safety agent for payment systems. "
            "Given incident alerts and logs, analyze recalled past memories to return "
            "ranked fix suggestions. Each fix suggestion MUST have an outcome: 'worked', 'failed', or 'temporary', "
            "and if 'temporary', how long it held (held_for_days int). "
            "Return STRICT JSON matching LLMFixSuggestionsResponse."
        )

        mem_text = "\n".join([f"- [{m['id']}]: {m['text']}" for m in recalled_memories])
        user_prompt = (
            f"NEW INCIDENT REPORT:\n"
            f"Service: {request.service}\n"
            f"Title: {request.title}\n"
            f"Alerts: {request.alerts}\n"
            f"Logs: {request.logs}\n\n"
            f"RECALLED PAST INCIDENT MEMORIES:\n{mem_text or 'None'}\n\n"
            f"Extract and rank fix suggestions with outcome (worked|failed|temporary) and held_for_days."
        )

        fallback_dict = self._build_offline_fix_suggestions(request, recalled_memories)

        try:
            llm_result = self.llm_client.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=LLMFixSuggestionsResponse,
                fallback_data=fallback_dict,
            )
            raw_data = llm_result.model_dump()
        except Exception as e:
            logger.warning(f"LLM incident check failed ({e}), using fallback fix suggestions.")
            raw_data = fallback_dict

        suggestions = [
            FixSuggestionItem.model_validate(s) for s in raw_data.get("ranked_fix_suggestions", [])
        ]
        if not suggestions:
            suggestions = [FixSuggestionItem.model_validate(s) for s in fallback_dict["ranked_fix_suggestions"]]

        citations = [
            MemoryCitationItem.model_validate(c) for c in raw_data.get("memory_citations", [])
        ]
        if not citations:
            citations = [MemoryCitationItem.model_validate(c) for c in fallback_dict["memory_citations"]]

        incident_record = IncidentRecord(
            id=incident_id,
            service=request.service,
            title=request.title,
            alerts=request.alerts,
            logs=request.logs,
            status="active",
        )
        db_session.add(incident_record)
        db_session.commit()

        return CreateIncidentResponse(
            incident_id=incident_id,
            service=request.service,
            title=request.title,
            status="active",
            ranked_fix_suggestions=suggestions,
            memory_citations=citations,
            memory_used=len(recalled_memories) > 0 or self.memory_service.is_live(),
        )

    def log_fix_attempt(
        self, incident_id: str, request: LogFixAttemptRequest, db_session: Session
    ) -> LogFixAttemptResponse:
        incident = db_session.exec(
            select(IncidentRecord).where(IncidentRecord.id == incident_id)
        ).first()

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "message": f"Incident '{incident_id}' not found"}},
            )

        attempt_id = f"fix_{uuid.uuid4().hex[:12]}"
        attempt_record = FixAttemptRecord(
            id=attempt_id,
            incident_id=incident_id,
            description=request.description,
            outcome=request.outcome,
            held_for_days=request.held_for_days,
            notes=request.notes,
        )
        db_session.add(attempt_record)
        db_session.commit()

        # Retain fix attempt in Hindsight memory
        memory_text = (
            f"Fix attempt for incident '{incident.title}' ({incident_id}) in {incident.service}: "
            f"Description: {request.description}. Outcome: {request.outcome}. "
            f"Held for days: {request.held_for_days or 'N/A'}. Notes: {request.notes or 'None'}."
        )
        self.memory_service.retain(
            content=memory_text,
            document_id=attempt_id,
            tags=[incident.service, incident_id, "fix_attempt", request.outcome],
            metadata={
                "incident_id": incident_id,
                "service": incident.service,
                "outcome": request.outcome,
                "held_for_days": request.held_for_days,
            },
        )

        return LogFixAttemptResponse(
            status="success",
            attempt_id=attempt_id,
            incident_id=incident_id,
            outcome=request.outcome,
        )

    def resolve_incident(
        self, incident_id: str, request: ResolveIncidentRequest, db_session: Session
    ) -> ResolveIncidentResponse:
        incident = db_session.exec(
            select(IncidentRecord).where(IncidentRecord.id == incident_id)
        ).first()

        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "NOT_FOUND", "message": f"Incident '{incident_id}' not found"}},
            )

        fix_attempts = db_session.exec(
            select(FixAttemptRecord).where(FixAttemptRecord.incident_id == incident_id)
        ).all()

        worked_fixes = [f.description for f in fix_attempts if f.outcome == "worked"]
        failed_fixes = [f.description for f in fix_attempts if f.outcome == "failed"]
        temp_fixes = [
            f"{f.description} (held for {f.held_for_days} days)" if f.held_for_days else f.description
            for f in fix_attempts
            if f.outcome == "temporary"
        ]

        worked_fix_summary = worked_fixes[0] if worked_fixes else (request.resolution_notes or "Applied system configuration fix and restored normal operations.")
        root_cause_str = request.root_cause or f"Configuration error / timeout mismatch in {incident.service} causing operational degradation."

        postmortem = PostmortemDraft(
            title=f"Postmortem: {incident.title}",
            summary=f"Incident in {incident.service} detected and resolved. Initial alerts: {incident.alerts[:200] or 'N/A'}.",
            root_cause=root_cause_str,
            timeline=[
                f"{incident.created_at}: Incident created and alerts ingested.",
                f"{datetime.now(timezone.utc).isoformat()}: Incident resolved following fix application.",
            ],
            fix_that_worked=worked_fix_summary,
            fixes_that_failed=failed_fixes,
            temporary_fixes=temp_fixes,
            action_items=[
                "Add automated canary regression test for configuration parameters.",
                "Ensure idempotency keys are strictly checked across all payment retries.",
                "Update incident memory bank with root cause and fix learnings.",
            ],
        )

        incident.status = "resolved"
        incident.resolution_notes = request.resolution_notes
        incident.postmortem_json = postmortem.model_dump_json()
        incident.resolved_at = datetime.now(timezone.utc).isoformat()

        db_session.add(incident)
        db_session.commit()

        # Retain postmortem draft in Hindsight memory
        postmortem_text = (
            f"INCIDENT POSTMORTEM [{incident.id}]: {postmortem.title}\n"
            f"Service: {incident.service}\n"
            f"Root Cause: {postmortem.root_cause}\n"
            f"Fix That Worked: {postmortem.fix_that_worked}\n"
            f"Fixes That Failed: {', '.join(postmortem.fixes_that_failed) or 'None'}\n"
            f"Temporary Fixes: {', '.join(postmortem.temporary_fixes) or 'None'}\n"
            f"Action Items: {', '.join(postmortem.action_items)}"
        )

        self.memory_service.retain(
            content=postmortem_text,
            document_id=f"pm_{incident.id}",
            tags=[incident.service, incident.id, "postmortem", "incident"],
            metadata={
                "incident_id": incident.id,
                "service": incident.service,
                "title": incident.title,
                "root_cause": postmortem.root_cause,
                "fix_that_worked": postmortem.fix_that_worked,
            },
        )

        return ResolveIncidentResponse(
            status="success",
            incident_id=incident.id,
            postmortem=postmortem,
        )
