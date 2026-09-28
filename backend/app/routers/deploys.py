from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.main import llm_client, memory_service, verify_api_key
from backend.app.models.schema import (
    DeployCheckRequest,
    DeployCheckResponse,
    DeployOutcomeRequest,
    DeployOutcomeResponse,
)
from backend.app.services.demo_service import DemoService
from backend.app.services.deploy_service import DeployService

router = APIRouter(prefix="/api/v1/deploys", tags=["Deploys"])

deploy_service = DeployService(memory_service=memory_service, llm_client=llm_client)
demo_service = DemoService(memory_service=memory_service)

@router.post("/check", response_model=DeployCheckResponse, dependencies=[Depends(verify_api_key)])
def check_deploy(req: DeployCheckRequest):
    try:
        return deploy_service.check_deploy(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DEPLOY_CHECK_ERROR", "message": str(e)}},
        )

@router.post("/{check_id}/outcome", response_model=DeployOutcomeResponse, dependencies=[Depends(verify_api_key)])
def record_outcome(check_id: str, req: DeployOutcomeRequest):
    try:
        return demo_service.record_deploy_outcome(check_id=check_id, req=req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "RECORD_OUTCOME_ERROR", "message": str(e)}},
        )
