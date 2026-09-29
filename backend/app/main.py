import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

from backend.app.config import settings
from backend.app.db import get_session, init_db
from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService
from backend.app.models import ApiKeyRecord
from backend.app.routers.analytics import router as analytics_router
from backend.app.routers.ask import router as ask_router
from backend.app.routers.demo import router as demo_router
from backend.app.routers.deploys import router as deploys_router
from backend.app.routers.incidents import router as incidents_router
from backend.app.routers.keys import router as keys_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Foresight API",
    description="AI deploy-safety agent backend for fintech engineering teams",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS setup
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_service = MemoryService()
llm_client = LLMClient()


def verify_api_key(
    x_api_key: str | None = Header(None),
    session: Session = Depends(get_session),  # noqa: B008 - FastAPI dependency injection.
):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Missing X-API-Key header"}},
        )

    # Check default master key from config
    if settings.API_KEY and x_api_key == settings.API_KEY:
        return x_api_key

    # Check database keys
    db_key = session.exec(
        select(ApiKeyRecord).where(ApiKeyRecord.key == x_api_key, ApiKeyRecord.is_active == True)
    ).first()

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or inactive X-API-Key"}},
        )

    return x_api_key


@app.get("/")
def root():
    return {
        "message": "Foresight Deploy Safety API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "mode": settings.FORESIGHT_MODE,
        "version": "0.1.0",
    }


@app.get("/health")
def health_check():
    warnings = []
    if settings.FORESIGHT_MODE == "live":
        if not memory_service.is_live():
            warnings.append("HINDSIGHT_API_KEY is missing; memory is using the offline seed bank")
        if memory_service.initialization_error:
            warnings.append(f"Hindsight bank initialization failed: {memory_service.initialization_error}")
        if not llm_client.is_live():
            warnings.append("GROQ_API_KEY is missing; LLM is using the offline fallback")
    return {
        "status": "degraded" if warnings else "ok",
        "mode": settings.FORESIGHT_MODE,
        "memory_backend": "hindsight" if memory_service.is_live() else "mock",
        "llm_backend": "groq" if llm_client.is_live() else "mock",
        "memory_bank_id": memory_service.bank_id if memory_service.is_live() else "offline-demo",
        "warnings": warnings,
        "version": "0.1.0",
    }


# Demo & Keys routes (unprotected per SPEC for key generation and demo)
app.include_router(demo_router)
app.include_router(keys_router)

# Protected API routes
app.include_router(deploys_router, dependencies=[Depends(verify_api_key)])
app.include_router(incidents_router, dependencies=[Depends(verify_api_key)])
app.include_router(analytics_router, dependencies=[Depends(verify_api_key)])
app.include_router(ask_router, dependencies=[Depends(verify_api_key)])


@app.get("/api/v1/memory/search", dependencies=[Depends(verify_api_key)])
def search_memory(q: str = Query(..., min_length=1, description="Search query string")):
    try:
        results = memory_service.search_memories(query=q)
        formatted_results = []
        for item in results:
            metadata = item.get("metadata") or {}
            text = item.get("content") or item.get("text") or ""
            formatted_results.append({
                **item,
                "content": text,
                "created_at": metadata.get("created_at") or metadata.get("date") or "",
                "tags": item.get("tags") or [],
                "score": float(item.get("score") or 0.0),
            })
        return {
            "query": q,
            "count": len(formatted_results),
            "memory_backend": "hindsight" if memory_service.is_live() else "mock",
            "bank_id": memory_service.bank_id if memory_service.is_live() else "offline-demo",
            "results": formatted_results,
        }
    except Exception as e:  # noqa: BLE001 - convert provider errors into an API response.
        logger.error("Memory search failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE if memory_service.is_live() else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "HINDSIGHT_RECALL_FAILED" if memory_service.is_live() else "MEMORY_SEARCH_ERROR", "message": str(e)}},
        )


@app.exception_handler(HTTPException)
def custom_http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = errors[0].get("msg", "Validation error") if errors else "Invalid request data"
    code = "INPUT_TOO_LARGE" if "maximum allowed limit" in msg else "VALIDATION_ERROR"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": code, "message": msg}},
    )
