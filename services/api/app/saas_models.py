from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class TenantPlan(str, enum.Enum):
    starter = "starter"
    professional = "professional"
    enterprise = "enterprise"


class TenantLifecycle(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    trial = "trial"


class PlatformAdmin(Base):
    __tablename__ = "platform_admins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TenantSaaSProfile(Base):
    __tablename__ = "tenant_saas_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    plan: Mapped[TenantPlan] = mapped_column(Enum(TenantPlan), default=TenantPlan.professional, nullable=False, index=True)
    lifecycle: Mapped[TenantLifecycle] = mapped_column(Enum(TenantLifecycle), default=TenantLifecycle.active, nullable=False, index=True)
    custom_domain: Mapped[str | None] = mapped_column(String(255), unique=True)
    max_users: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    max_projects: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_units: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    max_monthly_ai_requests: Mapped[int] = mapped_column(Integer, default=10000, nullable=False)
    powered_by_nexvary: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    logo_data_url: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    website_url: Mapped[str | None] = mapped_column(String(500))
    facebook_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    youtube_url: Mapped[str | None] = mapped_column(String(500))
    x_url: Mapped[str | None] = mapped_column(String(500))
    tiktok_url: Mapped[str | None] = mapped_column(String(500))
    feature_flags_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantUsage(Base):
    __tablename__ = "tenant_usage"
    __table_args__ = (UniqueConstraint("tenant_id", "period", name="uq_tenant_usage_period"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    ai_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inbound_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outbound_messages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantIntegration(Base):
    __tablename__ = "tenant_integrations"
    __table_args__ = (UniqueConstraint("tenant_id", "provider", name="uq_tenant_integration_provider"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    is_enabled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    public_config_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    encrypted_secret_json: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
