
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.llm.client import LLMClient
from backend.app.memory.service import MemoryService

memory_service = MemoryService()
llm_client = LLMClient()

def verify_api_key(x_api_key: str | None = Header(None)):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or missing X-API-Key header"}},
        )
    return x_api_key

app = FastAPI(
    title="Foresight API",
    description="AI deploy-safety agent backend for fintech engineering teams",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.routers.demo_analytics import (
    analytics_router,
    demo_router,
)
from backend.app.routers.deploys import router as deploys_router

app.include_router(deploys_router)
app.include_router(demo_router)
app.include_router(analytics_router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "mode": settings.FORESIGHT_MODE,
        "memory_backend": "hindsight" if memory_service.is_live() else "mock",
        "llm_backend": "groq" if llm_client.is_live() else "mock",
        "version": "0.1.0",
    }

@app.get("/api/v1/memory/search", dependencies=[Depends(verify_api_key)])
def search_memory(q: str = Query(..., min_length=1, description="Search query string")):
    try:
        results = memory_service.search_memories(query=q)
        return {
            "query": q,
            "count": len(results),
            "memory_backend": "hindsight" if memory_service.is_live() else "mock",
            "results": results,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "MEMORY_SEARCH_ERROR", "message": str(e)}},
        )

@app.exception_handler(HTTPException)
def custom_http_exception_handler(request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )
