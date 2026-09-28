import hmac
import json
import os
import secrets
from pathlib import Path
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Annotated

from .config import get_settings
from .db import get_db
from .models import AuditEvent, Tenant, User, UserRole
from .quota import PLAN_DEFAULTS
from .saas_models import PlatformAdmin, TenantLifecycle, TenantPlan, TenantSaaSProfile
from .security import create_access_token, hash_password
from .license_core import current_license_status

router = APIRouter(prefix="/api/v1")

WHITE_LABEL_SLUG = "workspace"
LEGACY_DEVELOPMENT_SLUG = "nexvary-dev"
LEGACY_FG_SLUG = "fg-machines"


class SetupStatus(BaseModel):
    needs_setup: bool
    tenant_count: int
    desktop_mode: bool
    development_workspace: bool = False


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
    development_workspace = db.scalar(
        select(func.count()).select_from(Tenant).where(
            Tenant.slug.in_((WHITE_LABEL_SLUG, LEGACY_DEVELOPMENT_SLUG, LEGACY_FG_SLUG))
        )
    ) or 0
    return SetupStatus(
        needs_setup=count == 0,
        tenant_count=count,
        desktop_mode=settings.app_env == "desktop",
        development_workspace=bool(development_workspace),
    )


@router.post("/auth/bootstrap", response_model=BootstrapResponse, status_code=201)
def bootstrap_first_owner(payload: BootstrapRequest, db: Session = Depends(get_db)) -> BootstrapResponse:
    count = db.scalar(select(func.count()).select_from(Tenant)) or 0
    if count != 0:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial setup is already complete")

    settings = get_settings()
    licensed_company = str(current_license_status().get("company") or "").strip()
    company_name = licensed_company or payload.company_name
    tenant = Tenant(
        name=company_name,
        slug=payload.company_slug.lower(),
        brand_name=payload.brand_name or company_name,
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
            PlatformAdmin(
                email=owner.email,
                display_name=owner.display_name,
                password_hash=hash_password(payload.owner_password),
            )
        )
        db.add(
            TenantSaaSProfile(
                tenant_id=tenant.id,
                plan=TenantPlan.professional,
                lifecycle=TenantLifecycle.active,
                **PLAN_DEFAULTS[TenantPlan.professional],
            )
        )
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


def _write_development_marker() -> None:
    data_dir = os.getenv("NEXVARY_DATA_DIR")
    if not data_dir:
        return
    marker = Path(data_dir) / "development-profile.json"
    marker.write_text(
        json.dumps(
            {
                "enabled": True,
                "schema_generation": os.getenv("NEXVARY_SCHEMA_GENERATION", "v1.5"),
                "workspace_slug": WHITE_LABEL_SLUG,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _apply_neutral_identity(db: Session, tenant: Tenant, owner: User) -> None:
    """Upgrade legacy desktop workspaces without exposing an upstream brand."""
    legacy_identity = (
        tenant.slug in {LEGACY_DEVELOPMENT_SLUG, LEGACY_FG_SLUG}
        or "nexvary" in (tenant.name or "").lower()
        or "fg machines" in (tenant.name or "").lower()
        or "nexvary" in (tenant.brand_name or "").lower()
        or "fg machines" in (tenant.brand_name or "").lower()
    )
    licensed_company = str(current_license_status().get("company") or "").strip()
    neutral_name = licensed_company or "Your Company"
    tenant.name = neutral_name
    tenant.brand_name = neutral_name
    tenant.slug = WHITE_LABEL_SLUG
    if owner.display_name in {"Development Owner", "NEXVARY Development Owner", "FG Machines Owner"}:
        owner.display_name = "Workspace Owner"

    profile = db.scalar(
        select(TenantSaaSProfile).where(TenantSaaSProfile.tenant_id == tenant.id)
    )
    if profile is not None:
        profile.powered_by_nexvary = 0
        for field in (
            "contact_email",
            "website_url",
            "facebook_url",
            "linkedin_url",
            "youtube_url",
            "x_url",
            "tiktok_url",
        ):
            value = getattr(profile, field, None)
            if legacy_identity or (value and "nexvary" in value.lower()):
                setattr(profile, field, None)
    db.commit()
    db.refresh(tenant)
    db.refresh(owner)


@router.post("/auth/bootstrap-development", response_model=BootstrapResponse, status_code=201)
def bootstrap_development_workspace(db: Session = Depends(get_db)) -> BootstrapResponse:
    settings = get_settings()
    if settings.app_env not in {"desktop", "development", "test"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Development setup is not available")

    existing = db.scalar(
        select(Tenant).where(Tenant.slug.in_((WHITE_LABEL_SLUG, LEGACY_DEVELOPMENT_SLUG, LEGACY_FG_SLUG)))
    )
    if existing is not None:
        owner = db.scalar(
            select(User).where(
                User.tenant_id == existing.id,
                User.role == UserRole.owner,
                User.is_active == 1,
            )
        )
        if owner is None:
            raise HTTPException(status_code=409, detail="Development workspace owner is missing")
        _apply_neutral_identity(db, existing, owner)
        token = create_access_token(user_id=owner.id, tenant_id=existing.id, role=owner.role.value)
        _write_development_marker()
        return BootstrapResponse(
            access_token=token,
            expires_in_minutes=settings.jwt_ttl_minutes,
            tenant_id=existing.id,
            tenant_slug=existing.slug,
            user_id=owner.id,
            user_email=owner.email,
            user_name=owner.display_name,
            role=owner.role.value,
        )

    licensed_company = str(current_license_status().get("company") or "").strip()
    tenant = Tenant(
        name=licensed_company or "Demo Workspace",
        slug=WHITE_LABEL_SLUG,
        brand_name=licensed_company or "Demo Workspace",
        primary_color="#128FE7",
    )
    db.add(tenant)
    try:
        db.flush()
        generated_password = secrets.token_urlsafe(48)
        owner = User(
            tenant_id=tenant.id,
            email="owner@workspace.local",
            display_name="Workspace Owner",
            role=UserRole.owner,
            password_hash=hash_password(generated_password),
        )
        db.add(owner)
        db.flush()
        db.add(
            PlatformAdmin(
                email=owner.email,
                display_name=owner.display_name,
                password_hash=hash_password(generated_password),
            )
        )
        db.add(
            TenantSaaSProfile(
                tenant_id=tenant.id,
                plan=TenantPlan.professional,
                lifecycle=TenantLifecycle.active,
                powered_by_nexvary=0,
                **PLAN_DEFAULTS[TenantPlan.professional],
            )
        )
        db.add(
            AuditEvent(
                tenant_id=tenant.id,
                actor=owner.email,
                action="tenant.development_bootstrap",
                entity_type="tenant",
                entity_id=tenant.id,
                details="desktop-development-skip",
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Development workspace could not be created") from exc

    _write_development_marker()
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


@router.post("/auth/development-session", response_model=BootstrapResponse)
def development_session(db: Session = Depends(get_db)) -> BootstrapResponse:
    settings = get_settings()
    if settings.app_env not in {"desktop", "development", "test"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Desktop development session is not available")
    tenant = db.scalar(
        select(Tenant).where(Tenant.slug.in_((WHITE_LABEL_SLUG, LEGACY_DEVELOPMENT_SLUG, LEGACY_FG_SLUG)))
    )
    if tenant is None:
        raise HTTPException(status_code=404, detail="Development workspace not found")
    owner = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            User.role == UserRole.owner,
            User.is_active == 1,
        )
    )
    if owner is None:
        raise HTTPException(status_code=404, detail="Development owner not found")
    _apply_neutral_identity(db, tenant, owner)
    _write_development_marker()
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
