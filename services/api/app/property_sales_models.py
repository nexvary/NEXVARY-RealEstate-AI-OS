from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class AdPropertyReferral(Base):
    __tablename__ = "ad_property_referrals"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "ad_id", name="uq_ad_property_referral"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(180), index=True)
    ad_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"), index=True)
    label: Mapped[str | None] = mapped_column(String(220))
    source_url: Mapped[str | None] = mapped_column(String(2048))
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ConversationPropertyContext(Base):
    __tablename__ = "conversation_property_contexts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "conversation_id", name="uq_conversation_property_context"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("inbox_conversations.id"), nullable=False, index=True)
    referral_id: Mapped[str | None] = mapped_column(ForeignKey("ad_property_referrals.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(ForeignKey("units.id"), index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(180), index=True)
    ad_id: Mapped[str | None] = mapped_column(String(180), index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
