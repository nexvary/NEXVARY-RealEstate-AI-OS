from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class MessageDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class MessageStatus(str, enum.Enum):
    queued = "queued"
    accepted = "accepted"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"
    received = "received"


class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_message_id", name="uq_whatsapp_message_external"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("whatsapp_channels.id"), nullable=False, index=True)
    direction: Mapped[MessageDirection] = mapped_column(Enum(MessageDirection), nullable=False, index=True)
    external_message_id: Mapped[str | None] = mapped_column(String(220), index=True)
    contact: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), nullable=False, index=True)
    content_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    error_text: Mapped[str | None] = mapped_column(Text)
    provider_timestamp: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WhatsAppWebhookEvent(Base):
    __tablename__ = "whatsapp_webhook_events"
    __table_args__ = (
        UniqueConstraint("channel_id", "event_key", name="uq_whatsapp_webhook_event_key"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("whatsapp_channels.id"), nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(220), nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
