import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .api import router
from .admin_api import router as admin_router
from .branding_api import router as branding_router
from .commercial_api import platform_router as commercial_platform_router, tenant_router as commercial_tenant_router
from .crm_api import router as enterprise_crm_router
from .ai_api import router as ai_router
from .automation_api import router as automation_router
from .config import get_settings
from .db import Base, engine
from .security import validate_production_secrets
from .seo_api import router as seo_router
from .setup_api import router as setup_router
from .finance_api import router as finance_router
from .growth_api import router as growth_router
from .omnichannel_api import router as omnichannel_router
from .property_sales_api import router as property_sales_router
from .platform_api import router as platform_router
from .workspace_api import router as workspace_router
from .license_api import router as license_router
from .license_core import current_license_status

settings = get_settings()
validate_production_secrets()

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env in {"development", "test", "desktop"}:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="2.1.0",
    description="White-label real-estate business workspace.",
    lifespan=lifespan,
)


@app.middleware("http")
async def enforce_desktop_license(request, call_next):
    path = request.url.path
    allowed = path == "/health" or path.startswith("/api/v1/license")
    if settings.app_env == "desktop" and path.startswith("/api/v1") and not allowed:
        if not current_license_status().get("valid"):
            return JSONResponse(
                status_code=402,
                content={"detail": "A valid license is required", "code": "license_required"},
            )
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "real-estate-business-service", "version": "2.1.0"}


app.include_router(setup_router)
app.include_router(license_router)
app.include_router(router)
app.include_router(workspace_router)
app.include_router(finance_router)
app.include_router(enterprise_crm_router)
app.include_router(growth_router)
app.include_router(omnichannel_router)
app.include_router(property_sales_router)
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
