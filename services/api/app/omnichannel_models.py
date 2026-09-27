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


class CustomerReplyPreference(str, enum.Enum):
    unset = "unset"
    text = "text"
    voice = "voice"


class SalesJourneyStage(str, enum.Enum):
    new = "new"
    asked_price = "asked_price"
    interested = "interested"
    explained = "explained"
    qualified = "qualified"
    viewing_requested = "viewing_requested"
    high_intent = "high_intent"
    reservation_requested = "reservation_requested"
    won = "won"
    lost = "lost"


class OutboundKind(str, enum.Enum):
    text = "text"
    image = "image"
    video = "video"
    document = "document"


class OutboundStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    sending = "sending"
    sent = "sent"
    failed = "failed"
    rejected = "rejected"


class AttributionEventType(str, enum.Enum):
    conversation = "conversation"
    qualified = "qualified"
    viewing = "viewing"
    reservation = "reservation"
    contract = "contract"
    revenue = "revenue"


class ConversationSalesState(Base):
    __tablename__ = "conversation_sales_states"
    __table_args__ = (UniqueConstraint("tenant_id", "conversation_id", name="uq_sales_state_conversation"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("inbox_conversations.id"), nullable=False, index=True)
    reply_preference: Mapped[CustomerReplyPreference] = mapped_column(
        Enum(CustomerReplyPreference), default=CustomerReplyPreference.unset, nullable=False
    )
    journey_stage: Mapped[SalesJourneyStage] = mapped_column(
        Enum(SalesJourneyStage), default=SalesJourneyStage.new, nullable=False, index=True
    )
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    campaign_id: Mapped[str | None] = mapped_column(String(180), index=True)
    ad_id: Mapped[str | None] = mapped_column(String(180), index=True)
    auto_reply_enabled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    handoff_required: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    handoff_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class InboundMessageReceipt(Base):
    __tablename__ = "inbound_message_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "external_message_id", name="uq_inbound_external_message"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("inbox_conversations.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    external_message_id: Mapped[str] = mapped_column(String(220), nullable=False, index=True)
    message_id: Mapped[str] = mapped_column(ForeignKey("inbox_messages.id"), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class OmnichannelOutbox(Base):
    __tablename__ = "omnichannel_outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("inbox_conversations.id"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    channel_id: Mapped[str | None] = mapped_column(String(36), index=True)
    kind: Mapped[OutboundKind] = mapped_column(Enum(OutboundKind), default=OutboundKind.text, nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    media_url: Mapped[str | None] = mapped_column(String(2048))
    grounded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=0, nullable=False)
    requires_approval: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[OutboundStatus] = mapped_column(Enum(OutboundStatus), default=OutboundStatus.pending_approval, nullable=False, index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    approved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    external_message_id: Mapped[str | None] = mapped_column(String(220), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MarketingAttributionEvent(Base):
    __tablename__ = "marketing_attribution_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    conversation_id: Mapped[str | None] = mapped_column(ForeignKey("inbox_conversations.id"), index=True)
    lead_id: Mapped[str | None] = mapped_column(ForeignKey("leads.id"), index=True)
    campaign_id: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    ad_id: Mapped[str | None] = mapped_column(String(180), index=True)
    event_type: Mapped[AttributionEventType] = mapped_column(Enum(AttributionEventType), nullable=False, index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EGP", nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
