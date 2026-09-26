from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class SubscriptionStatus(str, enum.Enum):
    trial = "trial"
    active = "active"
    past_due = "past_due"
    cancelled = "cancelled"


class BillingCycle(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"
    custom = "custom"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    void = "void"
    overdue = "overdue"


class WhatsAppChannelStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    disabled = "disabled"
    error = "error"


class SEOPageStatus(str, enum.Enum):
    draft = "draft"
    ready = "ready"
    published = "published"


class SaaSSubscription(Base):
    __tablename__ = "saas_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    plan: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.active, nullable=False, index=True)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle), default=BillingCycle.monthly, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider: Mapped[str] = mapped_column(String(60), default="manual", nullable=False)
    external_subscription_id: Mapped[str | None] = mapped_column(String(180))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class BillingInvoice(Base):
    __tablename__ = "billing_invoices"
    __table_args__ = (UniqueConstraint("tenant_id", "number", name="uq_billing_invoice_tenant_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    subscription_id: Mapped[str | None] = mapped_column(ForeignKey("saas_subscriptions.id"), index=True)
    number: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.open, nullable=False, index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_invoice_id: Mapped[str | None] = mapped_column(String(180))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class TenantTemplate(Base):
    __tablename__ = "tenant_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[str] = mapped_column(String(40), nullable=False)
    primary_color: Mapped[str] = mapped_column(String(20), default="#0B1F33", nullable=False)
    powered_by_nexvary: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_users: Mapped[int] = mapped_column(Integer, nullable=False)
    max_projects: Mapped[int] = mapped_column(Integer, nullable=False)
    max_units: Mapped[int] = mapped_column(Integer, nullable=False)
    max_monthly_ai_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    feature_flags_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    integration_providers_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    subscription_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    subscription_currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    billing_cycle: Mapped[BillingCycle] = mapped_column(Enum(BillingCycle), default=BillingCycle.monthly, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WhatsAppChannel(Base):
    __tablename__ = "whatsapp_channels"
    __table_args__ = (UniqueConstraint("tenant_id", "phone_number_id", name="uq_whatsapp_tenant_phone_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    integration_id: Mapped[str | None] = mapped_column(ForeignKey("tenant_integrations.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone_number_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    waba_id: Mapped[str | None] = mapped_column(String(120))
    business_phone: Mapped[str | None] = mapped_column(String(40))
    graph_api_version: Mapped[str] = mapped_column(String(20), default="v23.0", nullable=False)
    status: Mapped[WhatsAppChannelStatus] = mapped_column(Enum(WhatsAppChannelStatus), default=WhatsAppChannelStatus.draft, nullable=False, index=True)
    is_default: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SEOEntityPage(Base):
    __tablename__ = "seo_entity_pages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "entity_type", "entity_id", "seo_project_id", name="uq_seo_entity_page"),
        UniqueConstraint("tenant_id", "seo_project_id", "slug", name="uq_seo_page_slug"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    seo_project_id: Mapped[str] = mapped_column(ForeignKey("seo_projects.id"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False)
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meta_description: Mapped[str] = mapped_column(String(500), nullable=False)
    body_json: Mapped[str] = mapped_column(Text, nullable=False)
    structured_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SEOPageStatus] = mapped_column(Enum(SEOPageStatus), default=SEOPageStatus.ready, nullable=False, index=True)
    source_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
