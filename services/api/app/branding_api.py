from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Tenant
from .quota import ensure_profile
from .saas_models import TenantSaaSProfile

router = APIRouter(prefix="/api/v1/branding")


class BrandingResolve(BaseModel):
    tenant_slug: str
    brand_name: str
    primary_color: str
    logo_data_url: str | None
    powered_by_nexvary: bool


def normalize_host(host: str) -> str:
    value = host.strip().lower()
    if ":" in value:
        value = value.split(":", 1)[0]
    return value.rstrip(".")


@router.get("/resolve", response_model=BrandingResolve)
def resolve_branding(
    host: str = Query(min_length=3, max_length=255),
    db: Session = Depends(get_db),
) -> BrandingResolve:
    normalized = normalize_host(host)
    profile = db.scalar(
        select(TenantSaaSProfile).where(TenantSaaSProfile.custom_domain == normalized)
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="No company is configured for this domain")
    tenant = db.scalar(select(Tenant).where(Tenant.id == profile.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    profile = ensure_profile(db, tenant.id)
    return BrandingResolve(
        tenant_slug=tenant.slug,
        brand_name=tenant.brand_name or tenant.name,
        primary_color=tenant.primary_color,
        logo_data_url=profile.logo_data_url,
        powered_by_nexvary=bool(profile.powered_by_nexvary),
    )
