from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class VerdictEnum(str, Enum):
    SHIP = "SHIP"
    CANARY = "CANARY"
    HOLD = "HOLD"

class DeployOutcomeEnum(str, Enum):
    CLEAN = "clean"
    DEGRADED = "degraded"
    INCIDENT = "incident"

class SimilarIncident(BaseModel):
    id: str
    title: str
    date: str
    similarity_reason: str
    fix_that_worked: str
    fix_that_failed: str | None = None
    held_for_days: int | None = None

class DeployCheckRequest(BaseModel):
    service: str
    title: str
    description: str
    diff: str | None = None
    config_changes: list[str] = Field(default_factory=list)
    environment: str = "production"
    author: str = "Arjun"
    memory_enabled: bool = True

class DeployCheckResponse(BaseModel):
    check_id: str
    risk_score: int = Field(ge=0, le=100)
    verdict: VerdictEnum
    summary: str
    reasons: list[str]
    similar_incidents: list[SimilarIncident] = Field(default_factory=list)
    canary_plan: str
    rollback_plan: str
    memory_citations: list[dict[str, Any]] = Field(default_factory=list)
    memory_used: bool

class DeployOutcomeRequest(BaseModel):
    outcome: DeployOutcomeEnum
    notes: str | None = None

class DeployOutcomeResponse(BaseModel):
    check_id: str
    outcome: DeployOutcomeEnum
    retained: bool
    status: str

class DemoReplayResponse(BaseModel):
    status: str
    incidents_retained: int
    deploys_retained: int
    memory_backend: str

class DemoResetResponse(BaseModel):
    status: str
    message: str

class LearningCurveDataPoint(BaseModel):
    date: str
    accuracy: float
    mttr_minutes: float
    memories_count: int

class LearningCurveResponse(BaseModel):
    series: list[LearningCurveDataPoint]
    current_accuracy: float
    current_mttr: float
    total_memories: int
