import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import router
from .admin_api import router as admin_router
from .branding_api import router as branding_router
from .commercial_api import platform_router as commercial_platform_router, tenant_router as commercial_tenant_router
from .ai_api import router as ai_router
from .automation_api import router as automation_router
from .config import get_settings
from .db import Base, engine
from .security import validate_production_secrets
from .seo_api import router as seo_router
from .setup_api import router as setup_router
from .finance_api import router as finance_router
from .growth_api import router as growth_router
from .platform_api import router as platform_router
from .workspace_api import router as workspace_router

settings = get_settings()
validate_production_secrets()

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "test", "desktop"}:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.7.0",
    description="Transactional real-estate core with grounded AI/RAG orchestration boundaries.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexvary-realestate-api", "version": "1.7.0"}


app.include_router(setup_router)
app.include_router(router)
app.include_router(workspace_router)
app.include_router(finance_router)
app.include_router(growth_router)
app.include_router(ai_router)
app.include_router(automation_router)
app.include_router(admin_router)
app.include_router(platform_router)
app.include_router(branding_router)
app.include_router(seo_router)
app.include_router(commercial_platform_router)
app.include_router(commercial_tenant_router)

static_dir = os.getenv("NEXVARY_STATIC_DIR")
if static_dir:
    static_path = Path(static_dir)
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="web")
