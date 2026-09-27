from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Project, Unit, User
from .saas_models import TenantLifecycle, TenantPlan, TenantSaaSProfile, TenantUsage


PLAN_DEFAULTS = {
    TenantPlan.starter: dict(max_users=8, max_projects=15, max_units=750, max_monthly_ai_requests=1500),
    TenantPlan.professional: dict(max_users=25, max_projects=100, max_units=5000, max_monthly_ai_requests=10000),
    TenantPlan.enterprise: dict(max_users=250, max_projects=1000, max_units=100000, max_monthly_ai_requests=200000),
}


def ensure_profile(db: Session, tenant_id: str) -> TenantSaaSProfile:
    profile = db.scalar(select(TenantSaaSProfile).where(TenantSaaSProfile.tenant_id == tenant_id))
    if profile is None:
        defaults = PLAN_DEFAULTS[TenantPlan.professional]
        profile = TenantSaaSProfile(
            tenant_id=tenant_id,
            plan=TenantPlan.professional,
            lifecycle=TenantLifecycle.active,
            **defaults,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def assert_tenant_active(db: Session, tenant_id: str) -> TenantSaaSProfile:
    profile = ensure_profile(db, tenant_id)
    if profile.lifecycle == TenantLifecycle.suspended:
        raise HTTPException(status_code=403, detail="Company workspace is suspended")
    return profile


def _count(db: Session, model, tenant_id: str) -> int:
    return int(db.scalar(select(func.count()).select_from(model).where(model.tenant_id == tenant_id)) or 0)


def enforce_entity_limit(db: Session, tenant_id: str, entity: str) -> None:
    profile = assert_tenant_active(db, tenant_id)
    mapping = {
        "users": (User, profile.max_users),
        "projects": (Project, profile.max_projects),
        "units": (Unit, profile.max_units),
    }
    model, limit = mapping[entity]
    if _count(db, model, tenant_id) >= limit:
        raise HTTPException(status_code=409, detail=f"{entity} plan limit reached")


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def consume_ai_request(db: Session, tenant_id: str) -> TenantUsage:
    profile = assert_tenant_active(db, tenant_id)
    period = current_period()
    usage = db.scalar(
        select(TenantUsage).where(
            TenantUsage.tenant_id == tenant_id,
            TenantUsage.period == period,
        )
    )
    if usage is None:
        usage = TenantUsage(tenant_id=tenant_id, period=period)
        db.add(usage)
        db.flush()

    if usage.ai_requests >= profile.max_monthly_ai_requests:
        raise HTTPException(status_code=429, detail="Monthly AI request limit reached")

    usage.ai_requests += 1
    db.commit()
    db.refresh(usage)
    return usage
