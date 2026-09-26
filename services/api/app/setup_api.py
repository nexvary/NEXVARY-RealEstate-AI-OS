import hmac
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Annotated

from .config import get_settings
from .db import get_db
from .models import AuditEvent, Tenant, User, UserRole
from .security import create_access_token, hash_password

router = APIRouter(prefix="/api/v1")


class SetupStatus(BaseModel):
    needs_setup: bool
    tenant_count: int
    desktop_mode: bool


class BootstrapRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    company_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$")
    brand_name: str | None = None
    primary_color: str = "#0B1F33"
    owner_name: str = Field(min_length=2, max_length=160)
    owner_email: str = Field(min_length=5, max_length=255)
    owner_password: str = Field(min_length=10, max_length=200)


class BootstrapResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    tenant_id: str
    tenant_slug: str
    user_id: str
    user_email: str
    user_name: str
    role: str


@router.get("/setup/status", response_model=SetupStatus)
def setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    count = db.scalar(select(func.count()).select_from(Tenant)) or 0
    settings = get_settings()
    return SetupStatus(
        needs_setup=count == 0,
        tenant_count=count,
        desktop_mode=settings.app_env == "desktop",
    )


@router.post("/auth/bootstrap", response_model=BootstrapResponse, status_code=201)
def bootstrap_first_owner(payload: BootstrapRequest, db: Session = Depends(get_db)) -> BootstrapResponse:
    count = db.scalar(select(func.count()).select_from(Tenant)) or 0
    if count != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial setup is already complete")

    settings = get_settings()
    tenant = Tenant(
        name=payload.company_name,
        slug=payload.company_slug.lower(),
        brand_name=payload.brand_name or payload.company_name,
        primary_color=payload.primary_color,
    )
    db.add(tenant)
    try:
        db.flush()
        owner = User(
            tenant_id=tenant.id,
            email=payload.owner_email.lower(),
            display_name=payload.owner_name,
            role=UserRole.owner,
            password_hash=hash_password(payload.owner_password),
        )
        db.add(owner)
        db.flush()
        db.add(
            AuditEvent(
                tenant_id=tenant.id,
                actor=owner.email,
                action="tenant.bootstrap",
                entity_type="tenant",
                entity_id=tenant.id,
                details=tenant.slug,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company or owner already exists") from exc

    token = create_access_token(user_id=owner.id, tenant_id=tenant.id, role=owner.role.value)
    return BootstrapResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_ttl_minutes,
        tenant_id=tenant.id,
        tenant_slug=tenant.slug,
        user_id=owner.id,
        user_email=owner.email,
        user_name=owner.display_name,
        role=owner.role.value,
    )
