from __future__ import annotations

from datetime import date, datetime, timezone
import json
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from .automation_models import AutomationApproval, AutomationEdge, AutomationNode, AutomationNodeRun, AutomationRun, AutomationWorkflow
from .commercial_models import BankTransferSubmission, BillingInvoice, SaaSSubscription, SEOEntityPage, TenantTemplate, WhatsAppChannel
from .crm_models import Expense, Invoice, Payment, Proposal, Reminder, SupportTicket
from .db import get_db
from .finance_models import BrokerCommission, Contract, Installment
from .growth_models import AudienceSegment, CustomerFeedback, CustomerJourneyEvent, MarketingCampaign, PropertyMediaAsset, SalesPlaybook
from .omnichannel_models import ConversationSalesState, InboundMessageReceipt, MarketingAttributionEvent, OmnichannelOutbox
from .property_sales_models import AdPropertyReferral, ConversationPropertyContext
from .models import (
    Appointment,
    AuditEvent,
    Building,
    Lead,
    PaymentPlan,
    Project,
    Reservation,
    Tenant,
    Unit,
    User,
)
from .policy import RequestContext, get_request_context, manage_users
from .quota import ensure_profile
from .saas_models import TenantIntegration, TenantSaaSProfile
from .seo_models import SEOChangeDraft, SEOProject, SEOSnapshot
from .workspace_models import FollowUpTask, InboxConversation, InboxMessage, KnowledgeDocument

router = APIRouter(prefix="/api/v1")


class TenantSettingsRead(BaseModel):
    id: str
    name: str
    slug: str
    brand_name: str | None
    primary_color: str
    logo_data_url: str | None
    cover_data_url: str | None
    contact_email: str | None
    website_url: str | None
    facebook_url: str | None
    linkedin_url: str | None
    youtube_url: str | None
    x_url: str | None
    tiktok_url: str | None
    custom_domain: str | None
    powered_by_nexvary: bool
    plan: str
    lifecycle: str


class TenantSettingsUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    logo_data_url: str | None = Field(default=None, max_length=1500000)
    cover_data_url: str | None = Field(default=None, max_length=4500000)
    contact_email: str | None = Field(default=None, max_length=255)
    website_url: str | None = Field(default=None, max_length=500)
    facebook_url: str | None = Field(default=None, max_length=500)
    linkedin_url: str | None = Field(default=None, max_length=500)
    youtube_url: str | None = Field(default=None, max_length=500)
    x_url: str | None = Field(default=None, max_length=500)
    tiktok_url: str | None = Field(default=None, max_length=500)

    @field_validator("website_url", "facebook_url", "linkedin_url", "youtube_url", "x_url", "tiktok_url")
    @classmethod
    def validate_public_url(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        normalized = value.strip()
        parsed = urlsplit(normalized)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("Public links must begin with https://")
        return normalized


class AuditRead(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str | None
    details: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def serializable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def row_dict(row: Any, excluded: set[str] | None = None) -> dict[str, Any]:
    excluded = excluded or set()
    return {
        column.name: serializable(getattr(row, column.name))
        for column in row.__table__.columns
        if column.name not in excluded
    }


def validate_logo(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    allowed = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
    if not value.startswith(allowed):
        raise HTTPException(status_code=422, detail="Logo must be PNG, JPEG or WEBP data URL")
    if len(value) > 1_500_000:
        raise HTTPException(status_code=413, detail="Logo is too large")
    return value


def profile_feature_flags(profile: TenantSaaSProfile) -> dict[str, Any]:
    try:
        value = json.loads(profile.feature_flags_json or "{}")
        return value if isinstance(value, dict) else {}
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def validate_cover(value: str | None) -> str | None:
    if value in (None, ""):
        return None
    allowed = ("data:image/png;base64,", "data:image/jpeg;base64,", "data:image/webp;base64,")
    if not value.startswith(allowed):
        raise HTTPException(status_code=422, detail="Cover must be PNG, JPEG or WEBP data URL")
    if len(value) > 4_500_000:
        raise HTTPException(status_code=413, detail="Cover image is too large")
    return value


def settings_payload(tenant: Tenant, profile: TenantSaaSProfile) -> TenantSettingsRead:
    flags = profile_feature_flags(profile)
    return TenantSettingsRead(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        brand_name=tenant.brand_name,
        primary_color=tenant.primary_color,
        logo_data_url=profile.logo_data_url,
        cover_data_url=flags.get("branding_cover_data_url"),
        contact_email=profile.contact_email,
        website_url=profile.website_url,
        facebook_url=profile.facebook_url,
        linkedin_url=profile.linkedin_url,
        youtube_url=profile.youtube_url,
        x_url=profile.x_url,
        tiktok_url=profile.tiktok_url,
        custom_domain=profile.custom_domain,
        powered_by_nexvary=bool(profile.powered_by_nexvary),
        plan=profile.plan.value,
        lifecycle=profile.lifecycle.value,
    )


@router.get("/tenant/settings", response_model=TenantSettingsRead)
def tenant_settings(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> TenantSettingsRead:
    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    profile = ensure_profile(db, tenant.id)
    return settings_payload(tenant, profile)


@router.patch("/tenant/settings", response_model=TenantSettingsRead)
def update_tenant_settings(
    payload: TenantSettingsUpdate,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> TenantSettingsRead:
    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    profile = ensure_profile(db, tenant.id)

    changes = payload.model_dump(exclude_unset=True)
    for key in ("brand_name", "primary_color"):
        if key in changes and changes[key] is not None:
            setattr(tenant, key, changes.pop(key))
    if "logo_data_url" in changes:
        profile.logo_data_url = validate_logo(changes.pop("logo_data_url"))
    if "cover_data_url" in changes:
        cover = validate_cover(changes.pop("cover_data_url"))
        flags = profile_feature_flags(profile)
        if cover:
            flags["branding_cover_data_url"] = cover
        else:
            flags.pop("branding_cover_data_url", None)
        profile.feature_flags_json = json.dumps(flags, ensure_ascii=False, separators=(",", ":"))
    for key, value in changes.items():
        setattr(profile, key, value)

    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="tenant.settings.update",
            entity_type="tenant",
            entity_id=tenant.id,
            details=",".join(payload.model_dump(exclude_unset=True).keys()),
        )
    )
    db.commit()
    db.refresh(tenant)
    db.refresh(profile)
    return settings_payload(tenant, profile)


@router.get("/audit", response_model=list[AuditRead])
def audit_log(
    limit: int = 200,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    safe_limit = max(1, min(limit, 1000))
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == ctx.tenant_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(safe_limit)
        ).all()
    )


@router.get("/backup/export")
def export_backup(
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    models = {
        "users": (User, {"password_hash"}),
        "projects": (Project, set()),
        "buildings": (Building, set()),
        "payment_plans": (PaymentPlan, set()),
        "units": (Unit, set()),
        "leads": (Lead, set()),
        "appointments": (Appointment, set()),
        "reservations": (Reservation, set()),
        "contracts": (Contract, set()),
        "installments": (Installment, set()),
        "broker_commissions": (BrokerCommission, set()),
        "crm_proposals": (Proposal, set()),
        "crm_invoices": (Invoice, set()),
        "crm_payments": (Payment, set()),
        "crm_expenses": (Expense, set()),
        "crm_support_tickets": (SupportTicket, set()),
        "crm_reminders": (Reminder, set()),
        "knowledge_documents": (KnowledgeDocument, {"content"}),
        "inbox_conversations": (InboxConversation, set()),
        "inbox_messages": (InboxMessage, set()),
        "followup_tasks": (FollowUpTask, set()),
        "automation_workflows": (AutomationWorkflow, set()),
        "automation_nodes": (AutomationNode, set()),
        "automation_edges": (AutomationEdge, set()),
        "automation_runs": (AutomationRun, set()),
        "automation_node_runs": (AutomationNodeRun, set()),
        "automation_approvals": (AutomationApproval, set()),
        "marketing_campaigns": (MarketingCampaign, set()),
        "customer_journey_events": (CustomerJourneyEvent, set()),
        "audience_segments": (AudienceSegment, set()),
        "property_media_assets": (PropertyMediaAsset, set()),
        "sales_playbooks": (SalesPlaybook, set()),
        "customer_feedback": (CustomerFeedback, set()),
        "conversation_sales_states": (ConversationSalesState, set()),
        "inbound_message_receipts": (InboundMessageReceipt, set()),
        "omnichannel_outbox": (OmnichannelOutbox, set()),
        "marketing_attribution_events": (MarketingAttributionEvent, set()),
        "ad_property_referrals": (AdPropertyReferral, set()),
        "conversation_property_contexts": (ConversationPropertyContext, set()),
        "tenant_saas_profiles": (TenantSaaSProfile, set()),
        "tenant_integrations": (TenantIntegration, {"encrypted_secret_json"}),
        "saas_subscriptions": (SaaSSubscription, set()),
        "billing_invoices": (BillingInvoice, set()),
        "bank_transfer_submissions": (BankTransferSubmission, set()),
        "whatsapp_channels": (WhatsAppChannel, set()),
        "seo_entity_pages": (SEOEntityPage, set()),
        "seo_projects": (SEOProject, set()),
        "seo_snapshots": (SEOSnapshot, set()),
        "seo_change_drafts": (SEOChangeDraft, set()),
        "audit_events": (AuditEvent, set()),
    }

    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    data: dict[str, Any] = {
        "format": "Real-Estate-Business-OS-backup",
        "version": "2.2.1",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tenant": row_dict(tenant),
        "tables": {},
    }
    for name, (model, excluded) in models.items():
        rows = db.scalars(select(model).where(model.tenant_id == ctx.tenant_id)).all()
        data["tables"][name] = [row_dict(row, excluded) for row in rows]
    return data
