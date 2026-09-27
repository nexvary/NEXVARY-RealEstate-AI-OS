from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .integration_crypto import decrypt_secret_map, encrypt_secret_map
from .models import AuditEvent, Lead, Project, Tenant, Unit, User, UserRole
from .platform_policy import PlatformContext, get_platform_context
from .quota import PLAN_DEFAULTS, current_period, ensure_profile
from .saas_models import (
    PlatformAdmin,
    TenantIntegration,
    TenantLifecycle,
    TenantPlan,
    TenantSaaSProfile,
    TenantUsage,
)
from .security import create_platform_token, hash_password, verify_password

router = APIRouter(prefix="/api/v1/platform")


class PlatformStatus(BaseModel):
    configured: bool
    admin_count: int


class PlatformLogin(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=10, max_length=200)


class PlatformClaim(BaseModel):
    tenant_slug: str = Field(min_length=3, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=10, max_length=200)


class PlatformAdminRead(BaseModel):
    id: str
    email: str
    display_name: str
    model_config = ConfigDict(from_attributes=True)


class PlatformToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    admin: PlatformAdminRead


class PlatformOverview(BaseModel):
    tenants_total: int
    tenants_active: int
    tenants_trial: int
    tenants_suspended: int
    users_total: int
    projects_total: int
    units_total: int
    ai_requests_current_month: int


class TenantCreate(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    company_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$")
    brand_name: str | None = Field(default=None, max_length=160)
    primary_color: str = Field(default="#0B1F33", pattern=r"^#[0-9A-Fa-f]{6}$")
    owner_name: str = Field(min_length=2, max_length=160)
    owner_email: str = Field(min_length=5, max_length=255)
    owner_password: str = Field(min_length=10, max_length=200)
    plan: TenantPlan = TenantPlan.professional
    lifecycle: TenantLifecycle = TenantLifecycle.active
    custom_domain: str | None = Field(default=None, max_length=255)
    powered_by_nexvary: bool = True
    logo_data_url: str | None = Field(default=None, max_length=1500000)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    youtube_url: str | None = Field(default=None, max_length=500)
    x_url: str | None = Field(default=None, max_length=500)
    tiktok_url: str | None = Field(default=None, max_length=500)


class TenantPlatformUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    plan: TenantPlan | None = None
    lifecycle: TenantLifecycle | None = None
    custom_domain: str | None = Field(default=None, max_length=255)
    powered_by_nexvary: bool | None = None
    logo_data_url: str | None = Field(default=None, max_length=1500000)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    youtube_url: str | None = Field(default=None, max_length=500)
    x_url: str | None = Field(default=None, max_length=500)
    tiktok_url: str | None = Field(default=None, max_length=500)
    max_users: int | None = Field(default=None, ge=1, le=10000)
    max_projects: int | None = Field(default=None, ge=1, le=100000)
    max_units: int | None = Field(default=None, ge=1, le=10000000)
    max_monthly_ai_requests: int | None = Field(default=None, ge=0, le=100000000)
    apply_plan_defaults: bool = False


class TenantPlatformRead(BaseModel):
    id: str
    name: str
    slug: str
    brand_name: str | None
    primary_color: str
    created_at: datetime
    plan: TenantPlan
    lifecycle: TenantLifecycle
    custom_domain: str | None
    powered_by_nexvary: bool
    logo_data_url: str | None
    contact_email: str | None
    website_url: str | None
    facebook_url: str | None
    linkedin_url: str | None
    youtube_url: str | None
    x_url: str | None
    tiktok_url: str | None
    max_users: int
    max_projects: int
    max_units: int
    max_monthly_ai_requests: int
    users_count: int
    projects_count: int
    units_count: int
    leads_count: int
    ai_requests_current_month: int


class IntegrationUpsert(BaseModel):
    display_name: str = Field(min_length=2, max_length=160)
    is_enabled: bool = False
    public_config: dict[str, Any] = Field(default_factory=dict)
    secrets: dict[str, Any] | None = None


class IntegrationRead(BaseModel):
    id: str
    tenant_id: str
    provider: str
    display_name: str
    is_enabled: bool
    public_config: dict[str, Any]
    secret_keys: list[str]
    updated_at: datetime


def _normalized_domain(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    normalized = value.strip().lower().rstrip(".")
    if "://" in normalized or "/" in normalized or " " in normalized or "." not in normalized:
        raise HTTPException(status_code=422, detail="Custom domain must be a hostname such as crm.company.com")
    return normalized


def _validated_logo(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    allowed = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
    if not value.startswith(allowed):
        raise HTTPException(status_code=422, detail="Logo must be PNG, JPEG or WEBP data URL")
    if len(value) > 1_500_000:
        raise HTTPException(status_code=413, detail="Logo is too large")
    return value


def _tenant_read(db: Session, tenant: Tenant) -> TenantPlatformRead:
    profile = ensure_profile(db, tenant.id)
    usage = db.scalar(
        select(TenantUsage).where(
            TenantUsage.tenant_id == tenant.id,
            TenantUsage.period == current_period(),
        )
    )
    return TenantPlatformRead(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        brand_name=tenant.brand_name,
        primary_color=tenant.primary_color,
        created_at=tenant.created_at,
        plan=profile.plan,
        lifecycle=profile.lifecycle,
        custom_domain=profile.custom_domain,
        powered_by_nexvary=bool(profile.powered_by_nexvary),
        logo_data_url=profile.logo_data_url,
        contact_email=profile.contact_email,
        website_url=profile.website_url,
        facebook_url=profile.facebook_url,
        linkedin_url=profile.linkedin_url,
        youtube_url=profile.youtube_url,
        x_url=profile.x_url,
        tiktok_url=profile.tiktok_url,
        max_users=profile.max_users,
        max_projects=profile.max_projects,
        max_units=profile.max_units,
        max_monthly_ai_requests=profile.max_monthly_ai_requests,
        users_count=int(db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id)) or 0),
        projects_count=int(db.scalar(select(func.count()).select_from(Project).where(Project.tenant_id == tenant.id)) or 0),
        units_count=int(db.scalar(select(func.count()).select_from(Unit).where(Unit.tenant_id == tenant.id)) or 0),
        leads_count=int(db.scalar(select(func.count()).select_from(Lead).where(Lead.tenant_id == tenant.id)) or 0),
        ai_requests_current_month=usage.ai_requests if usage else 0,
    )


@router.get("/status", response_model=PlatformStatus)
def platform_status(db: Session = Depends(get_db)) -> PlatformStatus:
    count = int(db.scalar(select(func.count()).select_from(PlatformAdmin)) or 0)
    return PlatformStatus(configured=count > 0, admin_count=count)


@router.post("/auth/login", response_model=PlatformToken)
def platform_login(payload: PlatformLogin, db: Session = Depends(get_db)) -> PlatformToken:
    admin = db.scalar(
        select(PlatformAdmin).where(
            func.lower(PlatformAdmin.email) == payload.email.lower(),
            PlatformAdmin.is_active == 1,
        )
    )
    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid platform administrator credentials")

    settings = get_settings()
    return PlatformToken(
        access_token=create_platform_token(admin_id=admin.id),
        expires_in_minutes=settings.jwt_ttl_minutes,
        admin=admin,
    )


@router.post("/auth/claim", response_model=PlatformToken, status_code=201)
def claim_platform_admin(payload: PlatformClaim, db: Session = Depends(get_db)) -> PlatformToken:
    count = int(db.scalar(select(func.count()).select_from(PlatformAdmin)) or 0)
    if count:
        raise HTTPException(status_code=409, detail="Platform administration is already configured")

    tenant = db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug.lower()))
    if tenant is None:
        raise HTTPException(status_code=401, detail="Invalid owner credentials")
    owner = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            func.lower(User.email) == payload.email.lower(),
            User.role == UserRole.owner,
            User.is_active == 1,
        )
    )
    if owner is None or not verify_password(payload.password, owner.password_hash):
        raise HTTPException(status_code=401, detail="Invalid owner credentials")

    admin = PlatformAdmin(
        email=owner.email,
        display_name=owner.display_name,
        password_hash=hash_password(payload.password),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    settings = get_settings()
    return PlatformToken(
        access_token=create_platform_token(admin_id=admin.id),
        expires_in_minutes=settings.jwt_ttl_minutes,
        admin=admin,
    )


@router.get("/overview", response_model=PlatformOverview)
def platform_overview(
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> PlatformOverview:
    tenants = list(db.scalars(select(Tenant)).all())
    profiles = [ensure_profile(db, tenant.id) for tenant in tenants]
    return PlatformOverview(
        tenants_total=len(tenants),
        tenants_active=sum(1 for p in profiles if p.lifecycle == TenantLifecycle.active),
        tenants_trial=sum(1 for p in profiles if p.lifecycle == TenantLifecycle.trial),
        tenants_suspended=sum(1 for p in profiles if p.lifecycle == TenantLifecycle.suspended),
        users_total=int(db.scalar(select(func.count()).select_from(User)) or 0),
        projects_total=int(db.scalar(select(func.count()).select_from(Project)) or 0),
        units_total=int(db.scalar(select(func.count()).select_from(Unit)) or 0),
        ai_requests_current_month=int(
            db.scalar(
                select(func.coalesce(func.sum(TenantUsage.ai_requests), 0))
                .where(TenantUsage.period == current_period())
            )
            or 0
        ),
    )


@router.get("/tenants", response_model=list[TenantPlatformRead])
def list_tenants(
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> list[TenantPlatformRead]:
    tenants = list(db.scalars(select(Tenant).order_by(Tenant.created_at.desc())).all())
    return [_tenant_read(db, tenant) for tenant in tenants]


@router.post("/tenants", response_model=TenantPlatformRead, status_code=201)
def create_tenant(
    payload: TenantCreate,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> TenantPlatformRead:
    defaults = PLAN_DEFAULTS[payload.plan]
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
        profile = TenantSaaSProfile(
            tenant_id=tenant.id,
            plan=payload.plan,
            lifecycle=payload.lifecycle,
            custom_domain=_normalized_domain(payload.custom_domain),
            powered_by_nexvary=1 if payload.powered_by_nexvary else 0,
            logo_data_url=_validated_logo(payload.logo_data_url),
            contact_email=payload.contact_email,
            website_url=payload.website_url,
            facebook_url=payload.facebook_url,
            linkedin_url=payload.linkedin_url,
            youtube_url=payload.youtube_url,
            x_url=payload.x_url,
            tiktok_url=payload.tiktok_url,
            **defaults,
        )
        db.add_all([owner, profile])
        db.add(
            AuditEvent(
                tenant_id=tenant.id,
                actor=f"platform:{ctx.email}",
                action="tenant.platform_create",
                entity_type="tenant",
                entity_id=tenant.id,
                details=f"plan={payload.plan.value}",
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company slug, domain or owner account already exists") from exc
    db.refresh(tenant)
    return _tenant_read(db, tenant)


@router.patch("/tenants/{tenant_id}", response_model=TenantPlatformRead)
def update_tenant(
    tenant_id: str,
    payload: TenantPlatformUpdate,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> TenantPlatformRead:
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = ensure_profile(db, tenant.id)

    values = payload.model_dump(exclude_unset=True)
    if values.pop("apply_plan_defaults", False) and payload.plan is not None:
        for key, value in PLAN_DEFAULTS[payload.plan].items():
            setattr(profile, key, value)

    for key in ("brand_name", "primary_color"):
        if key in values and values[key] is not None:
            setattr(tenant, key, values.pop(key))

    if "powered_by_nexvary" in values:
        profile.powered_by_nexvary = 1 if values.pop("powered_by_nexvary") else 0
    if "logo_data_url" in values:
        profile.logo_data_url = _validated_logo(values.pop("logo_data_url"))
    if "custom_domain" in values:
        profile.custom_domain = _normalized_domain(values.pop("custom_domain"))

    for key, value in values.items():
        setattr(profile, key, value)

    db.add(
        AuditEvent(
            tenant_id=tenant.id,
            actor=f"platform:{ctx.email}",
            action="tenant.platform_update",
            entity_type="tenant",
            entity_id=tenant.id,
            details=",".join(payload.model_dump(exclude_unset=True).keys()),
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Custom domain is already assigned") from exc
    db.refresh(tenant)
    return _tenant_read(db, tenant)


@router.get("/tenants/{tenant_id}/integrations", response_model=list[IntegrationRead])
def list_integrations(
    tenant_id: str,
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> list[IntegrationRead]:
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    rows = list(db.scalars(select(TenantIntegration).where(TenantIntegration.tenant_id == tenant_id)).all())
    return [
        IntegrationRead(
            id=row.id,
            tenant_id=row.tenant_id,
            provider=row.provider,
            display_name=row.display_name,
            is_enabled=bool(row.is_enabled),
            public_config=json.loads(row.public_config_json or "{}"),
            secret_keys=sorted(decrypt_secret_map(row.encrypted_secret_json).keys()),
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.put("/tenants/{tenant_id}/integrations/{provider}", response_model=IntegrationRead)
def upsert_integration(
    tenant_id: str,
    provider: str,
    payload: IntegrationUpsert,
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> IntegrationRead:
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    safe_provider = provider.strip().lower()
    if not safe_provider or len(safe_provider) > 80 or not all(ch.isalnum() or ch in "-_" for ch in safe_provider):
        raise HTTPException(status_code=422, detail="Invalid integration provider")

    row = db.scalar(
        select(TenantIntegration).where(
            TenantIntegration.tenant_id == tenant_id,
            TenantIntegration.provider == safe_provider,
        )
    )
    if row is None:
        row = TenantIntegration(tenant_id=tenant_id, provider=safe_provider, display_name=payload.display_name)
        db.add(row)

    row.display_name = payload.display_name
    row.is_enabled = 1 if payload.is_enabled else 0
    row.public_config_json = json.dumps(payload.public_config, ensure_ascii=False)
    if payload.secrets is not None:
        row.encrypted_secret_json = encrypt_secret_map(payload.secrets)

    db.commit()
    db.refresh(row)
    return IntegrationRead(
        id=row.id,
        tenant_id=row.tenant_id,
        provider=row.provider,
        display_name=row.display_name,
        is_enabled=bool(row.is_enabled),
        public_config=json.loads(row.public_config_json or "{}"),
        secret_keys=sorted(decrypt_secret_map(row.encrypted_secret_json).keys()),
        updated_at=row.updated_at,
    )
