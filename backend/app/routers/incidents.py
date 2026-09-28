from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.app.db import get_session
from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models import (
    CreateIncidentRequest,
    CreateIncidentResponse,
    LogFixAttemptRequest,
    LogFixAttemptResponse,
    ResolveIncidentRequest,
    ResolveIncidentResponse,
)
from backend.app.services.incident_service import IncidentService

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])

memory_service = MemoryService()
llm_client = LLMClient()
incident_service = IncidentService(memory_service=memory_service, llm_client=llm_client)


@router.post("", response_model=CreateIncidentResponse)
def create_incident(
    request: CreateIncidentRequest,
    session: Session = Depends(get_session),
):
    try:
        return incident_service.create_incident(request=request, db_session=session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "CREATE_INCIDENT_ERROR", "message": str(e)}},
        )


@router.post("/{id}/fix-attempts", response_model=LogFixAttemptResponse)
def log_fix_attempt(
    id: str,
    request: LogFixAttemptRequest,
    session: Session = Depends(get_session),
):
    return incident_service.log_fix_attempt(incident_id=id, request=request, db_session=session)


@router.post("/{id}/resolve", response_model=ResolveIncidentResponse)
def resolve_incident(
    id: str,
    request: ResolveIncidentRequest,
    session: Session = Depends(get_session),
):
    return incident_service.resolve_incident(incident_id=id, request=request, db_session=session)
