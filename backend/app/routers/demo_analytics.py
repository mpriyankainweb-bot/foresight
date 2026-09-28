from fastapi import APIRouter, HTTPException, status

from backend.app.main import memory_service
from backend.app.models.schema import (
    DemoReplayResponse,
    DemoResetResponse,
    LearningCurveResponse,
)
from backend.app.services.demo_service import DemoService

demo_router = APIRouter(prefix="/api/v1/demo", tags=["Demo Mode"])
analytics_router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

demo_service = DemoService(memory_service=memory_service)

# Note: Demo routes do NOT require X-API-Key as per spec
@demo_router.post("/replay", response_model=DemoReplayResponse)
def replay_demo():
    try:
        return demo_service.replay_seed_data()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DEMO_REPLAY_ERROR", "message": str(e)}},
        )

@demo_router.post("/reset", response_model=DemoResetResponse)
def reset_demo():
    try:
        return demo_service.reset_demo()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "DEMO_RESET_ERROR", "message": str(e)}},
        )

@analytics_router.get("/learning-curve", response_model=LearningCurveResponse)
def get_learning_curve():
    try:
        return demo_service.get_learning_curve()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "ANALYTICS_ERROR", "message": str(e)}},
        )
