from contextlib import asynccontextmanager

from pathlib import Path
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
    session: Session = Depends(get_session),
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
    return {
        "status": "ok",
        "mode": settings.FORESIGHT_MODE,
        "memory_backend": "hindsight" if memory_service.is_live() else "mock",
        "llm_backend": "groq" if llm_client.is_live() else "mock",
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

# Mount Next.js static build if frontend/out directory exists (for single web service deployment on Render)
static_frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "out"
if static_frontend_dir.exists():
    app.mount("/_next", StaticFiles(directory=static_frontend_dir / "_next"), name="next-static")

    @app.get("/{full_path:path}")
    async def serve_spa_frontend(full_path: str):
        # Exclude API and Health routes from SPA fallback
        if full_path.startswith("api/") or full_path == "health" or full_path == "docs" or full_path == "openapi.json":
            raise HTTPException(status_code=404, detail="Not Found")

        target_file = static_frontend_dir / full_path
        if target_file.is_file():
            return FileResponse(target_file)

        html_file = static_frontend_dir / f"{full_path}.html"
        if html_file.is_file():
            return FileResponse(html_file)

        index_file = static_frontend_dir / "index.html"
        if index_file.is_file():
            return FileResponse(index_file)

        raise HTTPException(status_code=404, detail="Not Found")
