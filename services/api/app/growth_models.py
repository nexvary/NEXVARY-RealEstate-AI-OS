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


class CampaignStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    paused = "paused"
    completed = "completed"


class MediaType(str, enum.Enum):
    image = "image"
    video = "video"
    pdf = "pdf"
    floorplan = "floorplan"
    virtual_tour = "virtual_tour"


class MediaSourceKind(str, enum.Enum):
    company = "company"
    developer = "developer"
    verified = "verified"
    generated = "generated"


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_campaign_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    channel: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    objective: Mapped[str | None] = mapped_column(String(180))
    status: Mapped[CampaignStatus] = mapped_column(Enum(CampaignStatus), default=CampaignStatus.draft, nullable=False, index=True)
    budget: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    spend: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EGP", nullable=False)
    utm_source: Mapped[str | None] = mapped_column(String(120))
    utm_medium: Mapped[str | None] = mapped_column(String(120))
    utm_campaign: Mapped[str | None] = mapped_column(String(180))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CustomerJourneyEvent(Base):
    __tablename__ = "customer_journey_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    campaign_id: Mapped[str | None] = mapped_column(ForeignKey("marketing_campaigns.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("inbox_conversations.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    channel: Mapped[str | None] = mapped_column(String(80), index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AudienceSegment(Base):
    __tablename__ = "audience_segments"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_audience_segment_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    rules_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PropertyMediaAsset(Base):
    __tablename__ = "property_media_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"), index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    source_kind: Mapped[MediaSourceKind] = mapped_column(Enum(MediaSourceKind), default=MediaSourceKind.company, nullable=False)
    is_verified: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SalesPlaybook(Base):
    __tablename__ = "sales_playbooks"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_sales_playbook_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    trigger_stage: Mapped[str | None] = mapped_column(String(80), index=True)
    steps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CustomerFeedback(Base):
    __tablename__ = "customer_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("inbox_conversations.id"), index=True)
    channel: Mapped[str | None] = mapped_column(String(80), index=True)
    category: Mapped[str] = mapped_column(String(100), default="general", nullable=False, index=True)
    rating: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
