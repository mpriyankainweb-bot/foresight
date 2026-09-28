from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field
from sqlmodel import Field as SQLField, SQLModel


# SQLModel Database Models

class DeployCheckRecord(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    created_at: str = SQLField(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    service: str
    title: str
    description: str = ""
    diff: Optional[str] = None
    config_changes_json: str = "[]"
    environment: str = "production"
    author: str = "Arjun"
    risk_score: int
    verdict: str  # SHIP | CANARY | HOLD
    summary: str
    reasons_json: str = "[]"
    similar_incidents_json: str = "[]"
    canary_plan: str
    rollback_plan: str
    memory_citations_json: str = "[]"
    memory_used: bool = True
    outcome: Optional[str] = None  # clean | degraded | incident
    outcome_notes: Optional[str] = None


class DeployOutcomeRecord(SQLModel, table=True):
    id: Optional[int] = SQLField(default=None, primary_key=True)
    check_id: str = SQLField(index=True)
    created_at: str = SQLField(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    outcome: str  # clean | degraded | incident
    notes: Optional[str] = None


# Pydantic Schemas for API Requests & Responses

class DeployCheckRequest(BaseModel):
    service: str
    title: str
    description: str = ""
    diff: Optional[str] = None
    config_changes: list[str] = Field(default_factory=list)
    environment: str = "production"
    author: str = "Arjun"
    memory_enabled: bool = True


class SimilarIncidentItem(BaseModel):
    id: str
    title: str
    date: str
    similarity_reason: str
    fix_that_worked: str
    fix_that_failed: Optional[str] = None
    held_for_days: Optional[int] = None


class MemoryCitationItem(BaseModel):
    id: str
    text: str
    score: float = 0.9
    tags: list[str] = Field(default_factory=list)


class LLMVerdictResponse(BaseModel):
    risk_score: int
    verdict: str  # SHIP | CANARY | HOLD
    summary: str
    reasons: list[str]
    similar_incidents: list[SimilarIncidentItem] = Field(default_factory=list)
    canary_plan: str
    rollback_plan: str
    memory_citations: list[MemoryCitationItem] = Field(default_factory=list)


class DeployCheckResponse(BaseModel):
    check_id: str
    risk_score: int
    verdict: str  # SHIP | CANARY | HOLD
    summary: str
    reasons: list[str]
    similar_incidents: list[SimilarIncidentItem]
    canary_plan: str
    rollback_plan: str
    memory_citations: list[MemoryCitationItem]
    memory_used: bool


class DeployOutcomeRequest(BaseModel):
    outcome: str  # clean | degraded | incident
    notes: Optional[str] = None


class DeployOutcomeResponse(BaseModel):
    status: str
    check_id: str
    outcome: str


class DemoReplayResponse(BaseModel):
    status: str
    total_retained: int
    incidents_retained: int
    deploys_retained: int
    message: str


class DemoResetResponse(BaseModel):
    status: str
    message: str


class LearningCurveDataPoint(BaseModel):
    date: str
    memory_count: int
    prediction_accuracy: float
    mttr_minutes: float


class TopRecurringCause(BaseModel):
    cause: str
    count: int


class TemporaryFixItem(BaseModel):
    incident_id: str
    description: str
    held_for_days: int


class AnalyticsResponse(BaseModel):
    data_points: list[LearningCurveDataPoint]
    current_accuracy: float
    current_mttr_minutes: float
    top_recurring_causes: list[TopRecurringCause]
    temporary_fixes: list[TemporaryFixItem]
