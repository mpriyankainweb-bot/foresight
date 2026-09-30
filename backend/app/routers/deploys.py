from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.app.db import get_session
from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models import (
    DeployCheckRequest,
    DeployCheckResponse,
    DeployOutcomeRequest,
    DeployOutcomeResponse,
)
from backend.app.services.deploy_service import DeployService

router = APIRouter(prefix="/api/v1/deploys", tags=["deploys"])

memory_service = MemoryService()
llm_client = LLMClient()
deploy_service = DeployService(memory_service=memory_service, llm_client=llm_client)


@router.post("/check", response_model=DeployCheckResponse)
async def check_deploy(
    request: DeployCheckRequest,
    session: Session = Depends(get_session),
):
    try:
        return await deploy_service.check_deploy(request=request, db_session=session)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DEPLOY_CHECK_ERROR", "message": str(e)}},
        )


@router.post("/{check_id}/outcome", response_model=DeployOutcomeResponse)
def record_outcome(
    check_id: str,
    request: DeployOutcomeRequest,
    session: Session = Depends(get_session),
):
    return deploy_service.record_outcome(check_id=check_id, request=request, db_session=session)
