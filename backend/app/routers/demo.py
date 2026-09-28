from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.db import get_session
from backend.app.models import DemoReplayResponse, DemoResetResponse
from backend.app.memory.service import MemoryService
from backend.app.services.demo_service import DemoService

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])

# Router level dependencies can be instantiated
memory_service = MemoryService()
demo_service = DemoService(memory_service=memory_service)


@router.post("/replay", response_model=DemoReplayResponse)
def replay_demo(session: Session = Depends(get_session)):
    return demo_service.replay_demo(db_session=session)


@router.post("/reset", response_model=DemoResetResponse)
def reset_demo(session: Session = Depends(get_session)):
    return demo_service.reset_demo(db_session=session)
