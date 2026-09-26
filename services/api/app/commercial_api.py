from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from urllib.parse import urljoin

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .commercial_models import (
    BillingCycle,
    BillingInvoice,
    InvoiceStatus,
    SaaSSubscription,
    SEOEntityPage,
    SEOPageStatus,
    SubscriptionStatus,
    TenantTemplate,
    WhatsAppChannel,
    WhatsAppChannelStatus,
)
from .db import get_db
from .integration_crypto import decrypt_secret_map, encrypt_secret_map
from .models import AuditEvent, Project, Tenant, Unit, UnitStatus, User, UserRole
from .platform_policy import PlatformContext, get_platform_context
from .policy import RequestContext, get_request_context, manage_users
from .quota import PLAN_DEFAULTS
from .saas_models import TenantIntegration, TenantLifecycle, TenantPlan, TenantSaaSProfile
from .security import hash_password
from .seo_models import SEOProject

platform_router = APIRouter(prefix="/api/v1/platform")
tenant_router = APIRouter(prefix="/api/v1")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def next_period(start: datetime, cycle: BillingCycle) -> datetime:
    if cycle == BillingCycle.yearly:
        try:
            return start.replace(year=start.year + 1)
        except ValueError:
            return start.replace(year=start.year + 1, day=28)
    if cycle == BillingCycle.monthly:
        month = start.month + 1
        year = start.year
        if month == 13:
            month = 1
            year += 1
        day = min(start.day, 28)
        return start.replace(year=year, month=month, day=day)
    return start + timedelta(days=30)


def normalize_domain(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    normalized = value.strip().lower().rstrip(".")
    if "://" in normalized or "/" in normalized or " " in normalized or "." not in normalized:
        raise HTTPException(status_code=422, detail="Custom domain must be a hostname such as crm.company.com")
    return normalized


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u0600-\u06ff]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized[:180] or "page"


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    record = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record


class SubscriptionRead(BaseModel):
    id: str
    tenant_id: str
    plan: str
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    amount: Decimal
    currency: str
    started_at: datetime
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    provider: str
    external_subscription_id: str | None


class SubscriptionUpsert(BaseModel):
    plan: TenantPlan
    status: SubscriptionStatus = SubscriptionStatus.active
    billing_cycle: BillingCycle = BillingCycle.monthly
    amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)
    provider: str = Field(default="manual", min_length=2, max_length=60)
    external_subscription_id: str | None = Field(default=None, max_length=180)
    cancel_at_period_end: bool = False
    apply_plan_limits: bool = True


class InvoiceCreate(BaseModel):
    subtotal: Decimal = Field(gt=0)
    tax_amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)
    due_at: datetime | None = None
    description: str | None = Field(default=None, max_length=1200)
    status: InvoiceStatus = InvoiceStatus.open


class InvoiceRead(BaseModel):
    id: str
    tenant_id: str
    subscription_id: str | None
    number: str
    status: InvoiceStatus
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str
    description: str | None
    due_at: datetime | None
    paid_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    plan: TenantPlan = TenantPlan.professional
    primary_color: str = Field(default="#0B1F33", pattern=r"^#[0-9A-Fa-f]{6}$")
    powered_by_nexvary: bool = True
    feature_flags: dict[str, bool] = Field(default_factory=dict)
    integration_providers: list[str] = Field(default_factory=lambda: ["whatsapp", "google-search-console"])
    subscription_amount: Decimal = Field(default=0, ge=0)
    subscription_currency: str = Field(default="USD", min_length=3, max_length=8)
    billing_cycle: BillingCycle = BillingCycle.monthly


class TemplateRead(BaseModel):
    id: str
    name: str
    description: str | None
    plan: str
    primary_color: str
    powered_by_nexvary: bool
    max_users: int
    max_projects: int
    max_units: int
    max_monthly_ai_requests: int
    feature_flags: dict[str, bool]
    integration_providers: list[str]
    subscription_amount: Decimal
    subscription_currency: str
    billing_cycle: BillingCycle
    created_at: datetime


class ProvisionFromTemplate(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    company_slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$")
    brand_name: str | None = Field(default=None, max_length=160)
    owner_name: str = Field(min_length=2, max_length=160)
    owner_email: str = Field(min_length=5, max_length=255)
    owner_password: str = Field(min_length=10, max_length=200)
    custom_domain: str | None = Field(default=None, max_length=255)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=500)


class ProvisionResult(BaseModel):
    tenant_id: str
    company_slug: str
    owner_user_id: str
    subscription_id: str
    integrations_created: list[str]


class WhatsAppChannelCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=160)
    phone_number_id: str = Field(min_length=2, max_length=120)
    waba_id: str | None = Field(default=None, max_length=120)
    business_phone: str | None = Field(default=None, max_length=40)
    graph_api_version: str = Field(default="v23.0", min_length=2, max_length=20)
    access_token: str | None = Field(default=None, max_length=10000)
    app_secret: str | None = Field(default=None, max_length=10000)
    is_default: bool = False
    enabled: bool = True


class WhatsAppChannelRead(BaseModel):
    id: str
    display_name: str
    phone_number_id: str
    waba_id: str | None
    business_phone: str | None
    graph_api_version: str
    status: WhatsAppChannelStatus
    is_default: bool
    configured_secret_keys: list[str]
    created_at: datetime
    updated_at: datetime


class WhatsAppChannelUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=160)
    business_phone: str | None = Field(default=None, max_length=40)
    graph_api_version: str | None = Field(default=None, min_length=2, max_length=20)
    access_token: str | None = Field(default=None, max_length=10000)
    app_secret: str | None = Field(default=None, max_length=10000)
    is_default: bool | None = None
    enabled: bool | None = None


class SEOPageRead(BaseModel):
    id: str
    seo_project_id: str
    entity_type: str
    entity_id: str
    slug: str
    page_url: str
    title: str
    meta_description: str
    body: dict[str, Any]
    structured_data: dict[str, Any]
    status: SEOPageStatus
    source_hash: str
    generated_at: datetime
    updated_at: datetime


def subscription_read(row: SaaSSubscription) -> SubscriptionRead:
    return SubscriptionRead(
        id=row.id,
        tenant_id=row.tenant_id,
        plan=row.plan,
        status=row.status,
        billing_cycle=row.billing_cycle,
        amount=row.amount,
        currency=row.currency,
        started_at=row.started_at,
        current_period_start=row.current_period_start,
        current_period_end=row.current_period_end,
        cancel_at_period_end=bool(row.cancel_at_period_end),
        provider=row.provider,
        external_subscription_id=row.external_subscription_id,
    )


def template_read(row: TenantTemplate) -> TemplateRead:
    return TemplateRead(
        id=row.id,
        name=row.name,
        description=row.description,
        plan=row.plan,
        primary_color=row.primary_color,
        powered_by_nexvary=bool(row.powered_by_nexvary),
        max_users=row.max_users,
        max_projects=row.max_projects,
        max_units=row.max_units,
        max_monthly_ai_requests=row.max_monthly_ai_requests,
        feature_flags=json.loads(row.feature_flags_json or "{}"),
        integration_providers=json.loads(row.integration_providers_json or "[]"),
        subscription_amount=row.subscription_amount,
        subscription_currency=row.subscription_currency,
        billing_cycle=row.billing_cycle,
        created_at=row.created_at,
    )


@platform_router.get("/tenants/{tenant_id}/subscription", response_model=SubscriptionRead | None)
def get_subscription(
    tenant_id: str,
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
):
    row = db.scalar(select(SaaSSubscription).where(SaaSSubscription.tenant_id == tenant_id))
    return subscription_read(row) if row else None


@platform_router.put("/tenants/{tenant_id}/subscription", response_model=SubscriptionRead)
def upsert_subscription(
    tenant_id: str,
    payload: SubscriptionUpsert,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> SubscriptionRead:
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    now = utcnow()
    row = db.scalar(select(SaaSSubscription).where(SaaSSubscription.tenant_id == tenant_id))
    if row is None:
        row = SaaSSubscription(
            tenant_id=tenant_id,
            plan=payload.plan.value,
            started_at=now,
            current_period_start=now,
            current_period_end=next_period(now, payload.billing_cycle),
        )
        db.add(row)
    elif row.billing_cycle != payload.billing_cycle:
        row.current_period_start = now
        row.current_period_end = next_period(now, payload.billing_cycle)

    row.plan = payload.plan.value
    row.status = payload.status
    row.billing_cycle = payload.billing_cycle
    row.amount = payload.amount
    row.currency = payload.currency.upper()
    row.provider = payload.provider
    row.external_subscription_id = payload.external_subscription_id
    row.cancel_at_period_end = 1 if payload.cancel_at_period_end else 0

    profile = db.scalar(select(TenantSaaSProfile).where(TenantSaaSProfile.tenant_id == tenant_id))
    if profile:
        profile.plan = payload.plan
        if payload.apply_plan_limits:
            for key, value in PLAN_DEFAULTS[payload.plan].items():
                setattr(profile, key, value)

    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor=f"platform:{ctx.email}",
            action="billing.subscription.update",
            entity_type="subscription",
            entity_id=row.id,
            details=f"plan={payload.plan.value};status={payload.status.value};cycle={payload.billing_cycle.value}",
        )
    )
    db.commit()
    db.refresh(row)
    return subscription_read(row)


@platform_router.get("/tenants/{tenant_id}/invoices", response_model=list[InvoiceRead])
def list_invoices(
    tenant_id: str,
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> list[BillingInvoice]:
    return list(
        db.scalars(
            select(BillingInvoice)
            .where(BillingInvoice.tenant_id == tenant_id)
            .order_by(BillingInvoice.created_at.desc())
        ).all()
    )


@platform_router.post("/tenants/{tenant_id}/invoices", response_model=InvoiceRead, status_code=201)
def create_invoice(
    tenant_id: str,
    payload: InvoiceCreate,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> BillingInvoice:
    tenant = db.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Company not found")
    subscription = db.scalar(select(SaaSSubscription).where(SaaSSubscription.tenant_id == tenant_id))
    total = (payload.subtotal + payload.tax_amount).quantize(Decimal("0.01"))
    number = f"INV-{utcnow().strftime('%Y%m%d')}-{tenant.slug[:20].upper()}-{uuid.uuid4().hex[:6].upper()}"
    row = BillingInvoice(
        tenant_id=tenant_id,
        subscription_id=subscription.id if subscription else None,
        number=number,
        status=payload.status,
        subtotal=payload.subtotal,
        tax_amount=payload.tax_amount,
        total=total,
        currency=payload.currency.upper(),
        description=payload.description,
        due_at=payload.due_at,
    )
    db.add(row)
    db.add(
        AuditEvent(
            tenant_id=tenant_id,
            actor=f"platform:{ctx.email}",
            action="billing.invoice.create",
            entity_type="billing_invoice",
            entity_id=row.id,
            details=f"{number};total={total}",
        )
    )
    db.commit()
    db.refresh(row)
    return row


@platform_router.post("/invoices/{invoice_id}/pay", response_model=InvoiceRead)
def mark_invoice_paid(
    invoice_id: str,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> BillingInvoice:
    row = db.scalar(select(BillingInvoice).where(BillingInvoice.id == invoice_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if row.status == InvoiceStatus.void:
        raise HTTPException(status_code=409, detail="Voided invoice cannot be paid")
    row.status = InvoiceStatus.paid
    row.paid_at = utcnow()
    db.add(
        AuditEvent(
            tenant_id=row.tenant_id,
            actor=f"platform:{ctx.email}",
            action="billing.invoice.paid",
            entity_type="billing_invoice",
            entity_id=row.id,
            details=row.number,
        )
    )
    db.commit()
    db.refresh(row)
    return row


@platform_router.post("/invoices/{invoice_id}/void", response_model=InvoiceRead)
def void_invoice(
    invoice_id: str,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> BillingInvoice:
    row = db.scalar(select(BillingInvoice).where(BillingInvoice.id == invoice_id))
    if row is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if row.status == InvoiceStatus.paid:
        raise HTTPException(status_code=409, detail="Paid invoice cannot be voided")
    row.status = InvoiceStatus.void
    db.add(
        AuditEvent(
            tenant_id=row.tenant_id,
            actor=f"platform:{ctx.email}",
            action="billing.invoice.void",
            entity_type="billing_invoice",
            entity_id=row.id,
            details=row.number,
        )
    )
    db.commit()
    db.refresh(row)
    return row


@platform_router.get("/templates", response_model=list[TemplateRead])
def list_templates(
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> list[TemplateRead]:
    return [template_read(row) for row in db.scalars(select(TenantTemplate).order_by(TenantTemplate.created_at.desc())).all()]


@platform_router.post("/templates", response_model=TemplateRead, status_code=201)
def create_template(
    payload: TemplateCreate,
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> TemplateRead:
    defaults = PLAN_DEFAULTS[payload.plan]
    providers = [item.strip().lower() for item in payload.integration_providers if item.strip()]
    row = TenantTemplate(
        name=payload.name.strip(),
        description=payload.description,
        plan=payload.plan.value,
        primary_color=payload.primary_color,
        powered_by_nexvary=1 if payload.powered_by_nexvary else 0,
        max_users=defaults["max_users"],
        max_projects=defaults["max_projects"],
        max_units=defaults["max_units"],
        max_monthly_ai_requests=defaults["max_monthly_ai_requests"],
        feature_flags_json=json.dumps(payload.feature_flags, ensure_ascii=False),
        integration_providers_json=json.dumps(providers, ensure_ascii=False),
        subscription_amount=payload.subscription_amount,
        subscription_currency=payload.subscription_currency.upper(),
        billing_cycle=payload.billing_cycle,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Template name already exists") from exc
    db.refresh(row)
    return template_read(row)


@platform_router.post("/templates/{template_id}/provision", response_model=ProvisionResult, status_code=201)
def provision_template(
    template_id: str,
    payload: ProvisionFromTemplate,
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> ProvisionResult:
    template = db.scalar(select(TenantTemplate).where(TenantTemplate.id == template_id))
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    now = utcnow()
    plan = TenantPlan(template.plan)
    tenant = Tenant(
        name=payload.company_name,
        slug=payload.company_slug.lower(),
        brand_name=payload.brand_name or payload.company_name,
        primary_color=template.primary_color,
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
            plan=plan,
            lifecycle=TenantLifecycle.active,
            custom_domain=normalize_domain(payload.custom_domain),
            powered_by_nexvary=template.powered_by_nexvary,
            contact_email=payload.contact_email,
            website_url=payload.website_url,
            max_users=template.max_users,
            max_projects=template.max_projects,
            max_units=template.max_units,
            max_monthly_ai_requests=template.max_monthly_ai_requests,
            feature_flags_json=template.feature_flags_json,
        )
        subscription = SaaSSubscription(
            tenant_id=tenant.id,
            plan=template.plan,
            status=SubscriptionStatus.active,
            billing_cycle=template.billing_cycle,
            amount=template.subscription_amount,
            currency=template.subscription_currency,
            started_at=now,
            current_period_start=now,
            current_period_end=next_period(now, template.billing_cycle),
        )
        db.add_all([owner, profile, subscription])
        db.flush()

        providers = json.loads(template.integration_providers_json or "[]")
        integrations_created: list[str] = []
        for provider in providers:
            safe = str(provider).strip().lower()
            if not safe:
                continue
            db.add(
                TenantIntegration(
                    tenant_id=tenant.id,
                    provider=safe,
                    display_name=safe.replace("-", " ").title(),
                    is_enabled=0,
                    public_config_json="{}",
                )
            )
            integrations_created.append(safe)

        db.add(
            AuditEvent(
                tenant_id=tenant.id,
                actor=f"platform:{ctx.email}",
                action="tenant.template_provision",
                entity_type="tenant",
                entity_id=tenant.id,
                details=f"template={template.name};plan={template.plan}",
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company slug, domain or owner account already exists") from exc

    return ProvisionResult(
        tenant_id=tenant.id,
        company_slug=tenant.slug,
        owner_user_id=owner.id,
        subscription_id=subscription.id,
        integrations_created=integrations_created,
    )


def whatsapp_read(db: Session, row: WhatsAppChannel) -> WhatsAppChannelRead:
    integration = None
    if row.integration_id:
        integration = db.scalar(select(TenantIntegration).where(TenantIntegration.id == row.integration_id))
    secrets = decrypt_secret_map(integration.encrypted_secret_json) if integration else {}
    return WhatsAppChannelRead(
        id=row.id,
        display_name=row.display_name,
        phone_number_id=row.phone_number_id,
        waba_id=row.waba_id,
        business_phone=row.business_phone,
        graph_api_version=row.graph_api_version,
        status=row.status,
        is_default=bool(row.is_default),
        configured_secret_keys=sorted(secrets.keys()),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@tenant_router.get("/whatsapp/channels", response_model=list[WhatsAppChannelRead])
def list_whatsapp_channels(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[WhatsAppChannelRead]:
    rows = db.scalars(
        select(WhatsAppChannel)
        .where(WhatsAppChannel.tenant_id == ctx.tenant_id)
        .order_by(WhatsAppChannel.is_default.desc(), WhatsAppChannel.created_at.asc())
    ).all()
    return [whatsapp_read(db, row) for row in rows]


@tenant_router.post("/whatsapp/channels", response_model=WhatsAppChannelRead, status_code=201)
def create_whatsapp_channel(
    payload: WhatsAppChannelCreate,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> WhatsAppChannelRead:
    integration = db.scalar(
        select(TenantIntegration).where(
            TenantIntegration.tenant_id == ctx.tenant_id,
            TenantIntegration.provider == "whatsapp",
        )
    )
    if integration is None:
        integration = TenantIntegration(
            tenant_id=ctx.tenant_id,
            provider="whatsapp",
            display_name="WhatsApp Business",
            is_enabled=1 if payload.enabled else 0,
            public_config_json="{}",
        )
        db.add(integration)
        db.flush()

    public_config = {
        "phone_number_id": payload.phone_number_id,
        "waba_id": payload.waba_id,
        "business_phone": payload.business_phone,
        "graph_api_version": payload.graph_api_version,
    }
    integration.is_enabled = 1 if payload.enabled else 0
    integration.public_config_json = json.dumps(public_config, ensure_ascii=False)
    existing_secrets = decrypt_secret_map(integration.encrypted_secret_json)
    if payload.access_token:
        existing_secrets["access_token"] = payload.access_token
    if payload.app_secret:
        existing_secrets["app_secret"] = payload.app_secret
    if existing_secrets:
        integration.encrypted_secret_json = encrypt_secret_map(existing_secrets)

    if payload.is_default:
        db.query(WhatsAppChannel).filter(
            WhatsAppChannel.tenant_id == ctx.tenant_id
        ).update({WhatsAppChannel.is_default: 0})

    ready = bool(existing_secrets.get("access_token")) and payload.enabled
    row = WhatsAppChannel(
        tenant_id=ctx.tenant_id,
        integration_id=integration.id,
        display_name=payload.display_name,
        phone_number_id=payload.phone_number_id,
        waba_id=payload.waba_id,
        business_phone=payload.business_phone,
        graph_api_version=payload.graph_api_version,
        status=WhatsAppChannelStatus.ready if ready else WhatsAppChannelStatus.draft,
        is_default=1 if payload.is_default else 0,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This WhatsApp phone number ID already exists") from exc
    db.refresh(row)
    return whatsapp_read(db, row)


@tenant_router.patch("/whatsapp/channels/{channel_id}", response_model=WhatsAppChannelRead)
def update_whatsapp_channel(
    channel_id: str,
    payload: WhatsAppChannelUpdate,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> WhatsAppChannelRead:
    row = tenant_record(db, WhatsAppChannel, channel_id, ctx.tenant_id)
    integration = db.scalar(select(TenantIntegration).where(TenantIntegration.id == row.integration_id)) if row.integration_id else None
    if integration is None:
        raise HTTPException(status_code=409, detail="WhatsApp integration is missing")

    values = payload.model_dump(exclude_unset=True)
    for key in ("display_name", "business_phone", "graph_api_version"):
        if key in values:
            setattr(row, key, values[key])

    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    if values.get("access_token"):
        secrets["access_token"] = values["access_token"]
    if values.get("app_secret"):
        secrets["app_secret"] = values["app_secret"]
    if secrets:
        integration.encrypted_secret_json = encrypt_secret_map(secrets)

    if "enabled" in values:
        integration.is_enabled = 1 if values["enabled"] else 0
    if values.get("is_default"):
        db.query(WhatsAppChannel).filter(
            WhatsAppChannel.tenant_id == ctx.tenant_id,
            WhatsAppChannel.id != row.id,
        ).update({WhatsAppChannel.is_default: 0})
        row.is_default = 1
    elif values.get("is_default") is False:
        row.is_default = 0

    ready = bool(secrets.get("access_token")) and bool(integration.is_enabled)
    row.status = WhatsAppChannelStatus.ready if ready else WhatsAppChannelStatus.draft
    public_config = json.loads(integration.public_config_json or "{}")
    public_config.update(
        {
            "phone_number_id": row.phone_number_id,
            "waba_id": row.waba_id,
            "business_phone": row.business_phone,
            "graph_api_version": row.graph_api_version,
        }
    )
    integration.public_config_json = json.dumps(public_config, ensure_ascii=False)
    db.commit()
    db.refresh(row)
    return whatsapp_read(db, row)


@tenant_router.get("/whatsapp/channels/{channel_id}/readiness")
def whatsapp_readiness(
    channel_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    row = tenant_record(db, WhatsAppChannel, channel_id, ctx.tenant_id)
    integration = db.scalar(select(TenantIntegration).where(TenantIntegration.id == row.integration_id)) if row.integration_id else None
    secrets = decrypt_secret_map(integration.encrypted_secret_json) if integration else {}
    checks = {
        "channel_enabled": bool(integration and integration.is_enabled),
        "phone_number_id": bool(row.phone_number_id),
        "access_token": bool(secrets.get("access_token")),
        "waba_id": bool(row.waba_id),
    }
    return {
        "channel_id": row.id,
        "ready": checks["channel_enabled"] and checks["phone_number_id"] and checks["access_token"],
        "checks": checks,
        "secret_values_exposed": False,
    }


def page_read(row: SEOEntityPage) -> SEOPageRead:
    return SEOPageRead(
        id=row.id,
        seo_project_id=row.seo_project_id,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        slug=row.slug,
        page_url=row.page_url,
        title=row.title,
        meta_description=row.meta_description,
        body=json.loads(row.body_json),
        structured_data=json.loads(row.structured_data_json),
        status=row.status,
        source_hash=row.source_hash,
        generated_at=row.generated_at,
        updated_at=row.updated_at,
    )


def _source_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _upsert_seo_page(
    db: Session,
    ctx: RequestContext,
    seo_project: SEOProject,
    entity_type: str,
    entity_id: str,
    source: dict[str, Any],
    title: str,
    meta: str,
    body: dict[str, Any],
    structured: dict[str, Any],
    slug: str,
) -> SEOEntityPage:
    digest = _source_hash(source)
    page_url = urljoin(seo_project.site_url.rstrip("/") + "/", slug.lstrip("/"))
    row = db.scalar(
        select(SEOEntityPage).where(
            SEOEntityPage.tenant_id == ctx.tenant_id,
            SEOEntityPage.seo_project_id == seo_project.id,
            SEOEntityPage.entity_type == entity_type,
            SEOEntityPage.entity_id == entity_id,
        )
    )
    if row is None:
        row = SEOEntityPage(
            tenant_id=ctx.tenant_id,
            seo_project_id=seo_project.id,
            entity_type=entity_type,
            entity_id=entity_id,
            slug=slug,
            page_url=page_url,
            title=title,
            meta_description=meta,
            body_json=json.dumps(body, ensure_ascii=False, default=str),
            structured_data_json=json.dumps(structured, ensure_ascii=False, default=str),
            status=SEOPageStatus.ready,
            source_hash=digest,
        )
        db.add(row)
    elif row.source_hash != digest:
        row.slug = slug
        row.page_url = page_url
        row.title = title
        row.meta_description = meta
        row.body_json = json.dumps(body, ensure_ascii=False, default=str)
        row.structured_data_json = json.dumps(structured, ensure_ascii=False, default=str)
        row.status = SEOPageStatus.ready
        row.source_hash = digest
        row.updated_at = utcnow()
    db.flush()
    return row


def _project_page(db: Session, ctx: RequestContext, seo_project: SEOProject, project: Project) -> SEOEntityPage:
    source = {
        "id": project.id,
        "name": project.name,
        "city": project.city,
        "developer": project.developer,
        "description": project.description,
    }
    title = f"{project.name} — {project.city}"
    meta = (project.description or f"{project.name} real-estate project in {project.city}.").strip()[:500]
    slug = f"projects/{slugify(project.name)}"
    body = {
        "heading": project.name,
        "city": project.city,
        "developer": project.developer,
        "description": project.description,
        "source": "transactional_database",
    }
    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": meta,
        "url": urljoin(seo_project.site_url.rstrip("/") + "/", slug),
        "mainEntity": {
            "@type": "Place",
            "name": project.name,
            "address": {"@type": "PostalAddress", "addressLocality": project.city},
        },
    }
    if project.developer:
        structured["mainEntity"]["provider"] = {"@type": "Organization", "name": project.developer}
    return _upsert_seo_page(db, ctx, seo_project, "project", project.id, source, title, meta, body, structured, slug)


def _unit_page(db: Session, ctx: RequestContext, seo_project: SEOProject, unit: Unit) -> SEOEntityPage:
    project = tenant_record(db, Project, unit.project_id, ctx.tenant_id)
    source = {
        "id": unit.id,
        "project_id": project.id,
        "project_name": project.name,
        "city": project.city,
        "code": unit.code,
        "unit_type": unit.unit_type,
        "bedrooms": unit.bedrooms,
        "area_sqm": str(unit.area_sqm),
        "price": str(unit.price),
        "currency": unit.currency,
        "status": unit.status.value,
    }
    bedrooms_text = f", {unit.bedrooms} bedrooms" if unit.bedrooms is not None else ""
    title = f"{unit.unit_type} {unit.code} in {project.name}"
    meta = (
        f"{unit.unit_type} {unit.code} in {project.name}, {project.city}{bedrooms_text}, "
        f"{unit.area_sqm} m², {unit.currency} {unit.price}. Status: {unit.status.value}."
    )[:500]
    slug = f"projects/{slugify(project.name)}/units/{slugify(unit.code)}"
    availability = "https://schema.org/InStock" if unit.status == UnitStatus.available else "https://schema.org/SoldOut"
    body = {
        "heading": title,
        "project": project.name,
        "city": project.city,
        "unit_code": unit.code,
        "unit_type": unit.unit_type,
        "bedrooms": unit.bedrooms,
        "area_sqm": str(unit.area_sqm),
        "price": str(unit.price),
        "currency": unit.currency,
        "availability": unit.status.value,
        "source": "transactional_database",
    }
    structured = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": meta,
        "url": urljoin(seo_project.site_url.rstrip("/") + "/", slug),
        "mainEntity": {
            "@type": "Offer",
            "price": str(unit.price),
            "priceCurrency": unit.currency,
            "availability": availability,
            "itemOffered": {
                "@type": "Residence",
                "name": title,
                "floorSize": {"@type": "QuantitativeValue", "value": str(unit.area_sqm), "unitCode": "MTK"},
            },
        },
    }
    return _upsert_seo_page(db, ctx, seo_project, "unit", unit.id, source, title, meta, body, structured, slug)


@tenant_router.get("/seo/real-estate/pages", response_model=list[SEOPageRead])
def list_real_estate_seo_pages(
    seo_project_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[SEOPageRead]:
    query = select(SEOEntityPage).where(SEOEntityPage.tenant_id == ctx.tenant_id)
    if seo_project_id:
        query = query.where(SEOEntityPage.seo_project_id == seo_project_id)
    rows = db.scalars(query.order_by(SEOEntityPage.updated_at.desc())).all()
    return [page_read(row) for row in rows]


@tenant_router.post("/seo/real-estate/projects/{project_id}/generate", response_model=SEOPageRead)
def generate_project_page(
    project_id: str,
    seo_project_id: str,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> SEOPageRead:
    project = tenant_record(db, Project, project_id, ctx.tenant_id)
    seo_project = tenant_record(db, SEOProject, seo_project_id, ctx.tenant_id)
    row = _project_page(db, ctx, seo_project, project)
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="seo.realestate.project_page.generate",
            entity_type="project",
            entity_id=project.id,
            details=row.page_url,
        )
    )
    db.commit()
    db.refresh(row)
    return page_read(row)


@tenant_router.post("/seo/real-estate/units/{unit_id}/generate", response_model=SEOPageRead)
def generate_unit_page(
    unit_id: str,
    seo_project_id: str,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> SEOPageRead:
    unit = tenant_record(db, Unit, unit_id, ctx.tenant_id)
    seo_project = tenant_record(db, SEOProject, seo_project_id, ctx.tenant_id)
    row = _unit_page(db, ctx, seo_project, unit)
    db.commit()
    db.refresh(row)
    return page_read(row)


@tenant_router.post("/seo/real-estate/projects/{project_id}/sync-all")
def sync_project_and_units(
    project_id: str,
    seo_project_id: str,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    project = tenant_record(db, Project, project_id, ctx.tenant_id)
    seo_project = tenant_record(db, SEOProject, seo_project_id, ctx.tenant_id)
    project_page = _project_page(db, ctx, seo_project, project)
    units = db.scalars(
        select(Unit).where(Unit.tenant_id == ctx.tenant_id, Unit.project_id == project.id)
    ).all()
    unit_pages = [_unit_page(db, ctx, seo_project, unit) for unit in units]
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="seo.realestate.sync_all",
            entity_type="project",
            entity_id=project.id,
            details=f"pages={1 + len(unit_pages)}",
        )
    )
    db.commit()
    return {
        "project_id": project.id,
        "seo_project_id": seo_project.id,
        "project_page_id": project_page.id,
        "unit_pages": len(unit_pages),
        "source": "transactional_database",
        "hallucinated_fields": 0,
    }
