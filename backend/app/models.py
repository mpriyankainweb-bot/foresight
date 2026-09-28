from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
from sqlmodel import Field as SQLField, SQLModel

MAX_TEXT_LENGTH = 50000  # 50KB character limit per text field


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


class IncidentRecord(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    created_at: str = SQLField(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    service: str
    title: str
    alerts: str = ""
    logs: str = ""
    status: str = "active"  # active | resolved
    resolution_notes: Optional[str] = None
    postmortem_json: Optional[str] = None
    resolved_at: Optional[str] = None


class FixAttemptRecord(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    incident_id: str = SQLField(index=True)
    created_at: str = SQLField(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    description: str
    outcome: str  # worked | failed | temporary
    held_for_days: Optional[int] = None
    notes: Optional[str] = None


class ApiKeyRecord(SQLModel, table=True):
    id: str = SQLField(primary_key=True)
    created_at: str = SQLField(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    key: str = SQLField(index=True, unique=True)
    name: str = "default"
    is_active: bool = True


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

    @field_validator("description", "diff", mode="before")
    @classmethod
    def validate_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Input text exceeds maximum allowed limit of {MAX_TEXT_LENGTH} characters.")
        return v


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


# Incident Schemas

class FixSuggestionItem(BaseModel):
    id: str
    description: str
    outcome: str  # worked | failed | temporary
    held_for_days: Optional[int] = None
    confidence: float = 0.9
    source_incident_id: Optional[str] = None
    reasoning: str = ""


class CreateIncidentRequest(BaseModel):
    service: str
    title: str
    alerts: str = ""
    logs: str = ""

    @field_validator("alerts", "logs", "title", mode="before")
    @classmethod
    def validate_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Input exceeds maximum allowed limit of {MAX_TEXT_LENGTH} characters.")
        return v


class CreateIncidentResponse(BaseModel):
    incident_id: str
    service: str
    title: str
    status: str
    ranked_fix_suggestions: list[FixSuggestionItem]
    memory_citations: list[MemoryCitationItem]
    memory_used: bool


class LogFixAttemptRequest(BaseModel):
    description: str
    outcome: str  # worked | failed | temporary
    held_for_days: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v: str) -> str:
        v_lower = v.lower()
        if v_lower not in ("worked", "failed", "temporary"):
            raise ValueError("outcome must be one of: 'worked', 'failed', 'temporary'")
        return v_lower

    @field_validator("description", "notes", mode="before")
    @classmethod
    def validate_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Input exceeds maximum allowed limit of {MAX_TEXT_LENGTH} characters.")
        return v


class LogFixAttemptResponse(BaseModel):
    status: str
    attempt_id: str
    incident_id: str
    outcome: str


class ResolveIncidentRequest(BaseModel):
    root_cause: str = ""
    resolution_notes: str = ""

    @field_validator("root_cause", "resolution_notes", mode="before")
    @classmethod
    def validate_length(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) > MAX_TEXT_LENGTH:
            raise ValueError(f"Input exceeds maximum allowed limit of {MAX_TEXT_LENGTH} characters.")
        return v


class PostmortemDraft(BaseModel):
    title: str
    summary: str
    root_cause: str
    timeline: list[str] = Field(default_factory=list)
    fix_that_worked: str
    fixes_that_failed: list[str] = Field(default_factory=list)
    temporary_fixes: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)


class ResolveIncidentResponse(BaseModel):
    status: str
    incident_id: str
    postmortem: PostmortemDraft


# API Key Schemas

class GenerateApiKeyRequest(BaseModel):
    name: str = "default"


class GenerateApiKeyResponse(BaseModel):
    api_key: str
    name: str
    created_at: str


# Demo & Analytics Schemas

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
