from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.db import get_session
from backend.app.memory.service import MemoryService
from backend.app.models import AnalyticsResponse
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

memory_service = MemoryService()
analytics_service = AnalyticsService(memory_service=memory_service)


@router.get("/learning-curve", response_model=AnalyticsResponse)
def get_learning_curve(session: Session = Depends(get_session)):
    return analytics_service.get_learning_curve(db_session=session)
