import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import router
from .config import get_settings
from .db import Base, engine
from .security import validate_production_secrets
from .setup_api import router as setup_router

settings = get_settings()
validate_production_secrets()

app = FastAPI(
    title=settings.app_name,
    version="0.4.0",
    description="Transactional real-estate core with AI/RAG orchestration boundaries.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_schema() -> None:
    if settings.app_env in {"development", "test", "desktop"}:
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexvary-realestate-api", "version": "0.4.0"}


app.include_router(setup_router)
app.include_router(router)

static_dir = os.getenv("NEXVARY_STATIC_DIR")
if static_dir:
    static_path = Path(static_dir)
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="web")
