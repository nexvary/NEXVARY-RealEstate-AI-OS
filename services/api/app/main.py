from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .config import get_settings
from .db import Base, engine
from .security import validate_production_secrets

settings = get_settings()
validate_production_secrets()
app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="Transactional real-estate core with AI/RAG orchestration boundaries.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_dev_schema() -> None:
    if settings.app_env == "development":
        Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "nexvary-realestate-api", "version": "0.3.0"}


app.include_router(router)
