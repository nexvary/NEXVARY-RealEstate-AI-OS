from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .commercial_models import (
    BillingInvoice,
    InvoiceStatus,
    SaaSSubscription,
    SubscriptionStatus,
    WhatsAppChannel,
    WhatsAppChannelStatus,
)
from .db import get_db
from .integration_crypto import decrypt_secret_map, encrypt_secret_map
from .models import AuditEvent
from .platform_policy import PlatformContext, get_platform_context
from .policy import RequestContext, get_request_context, manage_users
from .production_models import MessageDirection, MessageStatus, WhatsAppMessage, WhatsAppWebhookEvent
from .saas_models import TenantIntegration

platform_router = APIRouter(prefix="/api/v1/platform")
tenant_router = APIRouter(prefix="/api/v1")
public_router = APIRouter(prefix="/api/v1")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def channel_for_tenant(db: Session, channel_id: str, tenant_id: str) -> WhatsAppChannel:
    row = db.scalar(
        select(WhatsAppChannel).where(
            WhatsAppChannel.id == channel_id,
            WhatsAppChannel.tenant_id == tenant_id,
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")
    return row


def channel_integration(db: Session, row: WhatsAppChannel) -> TenantIntegration:
    integration = None
    if row.integration_id:
        integration = db.scalar(select(TenantIntegration).where(TenantIntegration.id == row.integration_id))
    if integration is None:
        raise HTTPException(status_code=409, detail="WhatsApp integration is missing")
    return integration


class BillingReconcileResult(BaseModel):
    invoices_marked_overdue: int
    subscriptions_marked_past_due: int
    subscriptions_cancelled: int
    checked_at: datetime


class BillingSummary(BaseModel):
    subscriptions: dict[str, int]
    invoices: dict[str, int]


@platform_router.get("/billing/summary", response_model=BillingSummary)
def billing_summary(
    _: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> BillingSummary:
    subscriptions: dict[str, int] = {status.value: 0 for status in SubscriptionStatus}
    invoices: dict[str, int] = {status.value: 0 for status in InvoiceStatus}

    for status, count in db.execute(
        select(SaaSSubscription.status, func.count(SaaSSubscription.id)).group_by(SaaSSubscription.status)
    ).all():
        subscriptions[status.value if hasattr(status, "value") else str(status)] = int(count)

    for status, count in db.execute(
        select(BillingInvoice.status, func.count(BillingInvoice.id)).group_by(BillingInvoice.status)
    ).all():
        invoices[status.value if hasattr(status, "value") else str(status)] = int(count)

    return BillingSummary(subscriptions=subscriptions, invoices=invoices)


@platform_router.post("/billing/reconcile", response_model=BillingReconcileResult)
def reconcile_billing(
    ctx: PlatformContext = Depends(get_platform_context),
    db: Session = Depends(get_db),
) -> BillingReconcileResult:
    now = utcnow()
    overdue_count = 0
    past_due_count = 0
    cancelled_count = 0

    invoices = db.scalars(
        select(BillingInvoice).where(BillingInvoice.status == InvoiceStatus.open)
    ).all()
    for invoice in invoices:
        due_at = as_utc(invoice.due_at)
        if due_at is not None and due_at < now:
            invoice.status = InvoiceStatus.overdue
            overdue_count += 1
            db.add(
                AuditEvent(
                    tenant_id=invoice.tenant_id,
                    actor=f"platform:{ctx.email}",
                    action="billing.invoice.overdue",
                    entity_type="billing_invoice",
                    entity_id=invoice.id,
                    details=invoice.number,
                )
            )

    subscriptions = db.scalars(select(SaaSSubscription)).all()
    for subscription in subscriptions:
        period_end = as_utc(subscription.current_period_end)
        if period_end is None or period_end > now:
            continue

        if bool(subscription.cancel_at_period_end) and subscription.status != SubscriptionStatus.cancelled:
            subscription.status = SubscriptionStatus.cancelled
            cancelled_count += 1
            db.add(
                AuditEvent(
                    tenant_id=subscription.tenant_id,
                    actor=f"platform:{ctx.email}",
                    action="billing.subscription.cancelled",
                    entity_type="subscription",
                    entity_id=subscription.id,
                    details="cancel_at_period_end reached",
                )
            )
            continue

        unpaid = db.scalar(
            select(BillingInvoice).where(
                BillingInvoice.subscription_id == subscription.id,
                BillingInvoice.status.in_([InvoiceStatus.open, InvoiceStatus.overdue]),
            )
        )
        if (unpaid is not None or subscription.status == SubscriptionStatus.trial) and subscription.status != SubscriptionStatus.past_due:
            subscription.status = SubscriptionStatus.past_due
            past_due_count += 1
            db.add(
                AuditEvent(
                    tenant_id=subscription.tenant_id,
                    actor=f"platform:{ctx.email}",
                    action="billing.subscription.past_due",
                    entity_type="subscription",
                    entity_id=subscription.id,
                    details="billing period ended without a confirmed renewal payment",
                )
            )

    db.commit()
    return BillingReconcileResult(
        invoices_marked_overdue=overdue_count,
        subscriptions_marked_past_due=past_due_count,
        subscriptions_cancelled=cancelled_count,
        checked_at=now,
    )


class WebhookConfig(BaseModel):
    verify_token: str = Field(min_length=12, max_length=500)


class MessageSend(BaseModel):
    to: str = Field(min_length=6, max_length=80)
    message_type: str = Field(default="text", pattern=r"^(text|image|video|document)$")
    text: str | None = Field(default=None, max_length=4096)
    media_url: str | None = Field(default=None, max_length=2048)
    caption: str | None = Field(default=None, max_length=1024)


class MessageRead(BaseModel):
    id: str
    channel_id: str
    direction: MessageDirection
    external_message_id: str | None
    contact: str
    message_type: str
    status: MessageStatus
    content: dict[str, Any]
    error_text: str | None
    provider_timestamp: str | None
    created_at: datetime
    updated_at: datetime


def message_read(row: WhatsAppMessage) -> MessageRead:
    return MessageRead(
        id=row.id,
        channel_id=row.channel_id,
        direction=row.direction,
        external_message_id=row.external_message_id,
        contact=row.contact,
        message_type=row.message_type,
        status=row.status,
        content=json.loads(row.content_json or "{}"),
        error_text=row.error_text,
        provider_timestamp=row.provider_timestamp,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@tenant_router.put("/whatsapp/channels/{channel_id}/webhook-config")
def configure_whatsapp_webhook(
    channel_id: str,
    payload: WebhookConfig,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    row = channel_for_tenant(db, channel_id, ctx.tenant_id)
    integration = channel_integration(db, row)
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    if not secrets.get("app_secret"):
        raise HTTPException(status_code=409, detail="Configure the Meta app secret before enabling webhooks")
    secrets["webhook_verify_token"] = payload.verify_token
    integration.encrypted_secret_json = encrypt_secret_map(secrets)
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.user_id,
            action="whatsapp.webhook.configure",
            entity_type="whatsapp_channel",
            entity_id=row.id,
            details="verify token configured; secret values not exposed",
        )
    )
    db.commit()
    return {
        "channel_id": row.id,
        "configured": True,
        "callback_path": f"/api/v1/whatsapp/webhook/{row.id}",
        "secret_values_exposed": False,
    }


@tenant_router.get("/whatsapp/messages", response_model=list[MessageRead])
def list_whatsapp_messages(
    channel_id: str | None = None,
    limit: int = 100,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[MessageRead]:
    safe_limit = max(1, min(limit, 250))
    query = select(WhatsAppMessage).where(WhatsAppMessage.tenant_id == ctx.tenant_id)
    if channel_id:
        channel_for_tenant(db, channel_id, ctx.tenant_id)
        query = query.where(WhatsAppMessage.channel_id == channel_id)
    rows = db.scalars(query.order_by(WhatsAppMessage.created_at.desc()).limit(safe_limit)).all()
    return [message_read(row) for row in rows]


def outbound_body(payload: MessageSend) -> dict[str, Any]:
    body: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": payload.to.strip(),
        "type": payload.message_type,
    }
    if payload.message_type == "text":
        if not payload.text:
            raise HTTPException(status_code=422, detail="text is required for text messages")
        body["text"] = {"preview_url": False, "body": payload.text}
    else:
        if not payload.media_url or not payload.media_url.startswith("https://"):
            raise HTTPException(status_code=422, detail="A public HTTPS media_url is required for media messages")
        media: dict[str, Any] = {"link": payload.media_url}
        if payload.caption and payload.message_type in {"image", "video", "document"}:
            media["caption"] = payload.caption
        body[payload.message_type] = media
    return body


@tenant_router.post("/whatsapp/channels/{channel_id}/messages", response_model=MessageRead, status_code=201)
def send_whatsapp_message(
    channel_id: str,
    payload: MessageSend,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> MessageRead:
    row = channel_for_tenant(db, channel_id, ctx.tenant_id)
    integration = channel_integration(db, row)
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    token = secrets.get("access_token")
    if not integration.is_enabled or row.status != WhatsAppChannelStatus.ready or not token:
        raise HTTPException(status_code=409, detail="WhatsApp channel is not ready for live sending")

    body = outbound_body(payload)
    url = f"https://graph.facebook.com/{row.graph_api_version}/{row.phone_number_id}/messages"
    record = WhatsAppMessage(
        tenant_id=ctx.tenant_id,
        channel_id=row.id,
        direction=MessageDirection.outbound,
        contact=payload.to.strip(),
        message_type=payload.message_type,
        status=MessageStatus.queued,
        content_json=json.dumps(body, ensure_ascii=False),
    )
    db.add(record)
    db.flush()

    response: httpx.Response | None = None
    try:
        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=20.0,
        )
        response.raise_for_status()
        result = response.json()
        messages = result.get("messages") or []
        record.external_message_id = messages[0].get("id") if messages else None
        record.status = MessageStatus.accepted
        record.error_text = None
    except (httpx.HTTPError, ValueError) as exc:
        record.status = MessageStatus.failed
        safe_detail = f"provider request failed: {type(exc).__name__}"
        if response is not None:
            safe_detail += f"; HTTP {response.status_code}"
        record.error_text = safe_detail
        row.status = WhatsAppChannelStatus.error
        row.last_error = safe_detail
        db.add(
            AuditEvent(
                tenant_id=ctx.tenant_id,
                actor=ctx.user_id,
                action="whatsapp.message.failed",
                entity_type="whatsapp_message",
                entity_id=record.id,
                details=safe_detail,
            )
        )
        db.commit()
        db.refresh(record)
        raise HTTPException(status_code=502, detail="WhatsApp provider rejected or failed the message request") from exc

    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.user_id,
            action="whatsapp.message.accepted",
            entity_type="whatsapp_message",
            entity_id=record.id,
            details=f"type={payload.message_type};external_id={record.external_message_id or 'unknown'}",
        )
    )
    db.commit()
    db.refresh(record)
    return message_read(record)


@public_router.get("/whatsapp/webhook/{channel_id}", response_class=PlainTextResponse)
def verify_whatsapp_webhook(
    channel_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PlainTextResponse:
    row = db.scalar(select(WhatsAppChannel).where(WhatsAppChannel.id == channel_id))
    if row is None:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")
    integration = channel_integration(db, row)
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    expected = secrets.get("webhook_verify_token")
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode != "subscribe" or not expected or not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=403, detail="Webhook verification failed")
    return PlainTextResponse(challenge or "")


def valid_meta_signature(raw: bytes, signature: str | None, app_secret: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature[7:], expected)


@public_router.post("/whatsapp/webhook/{channel_id}")
async def receive_whatsapp_webhook(
    channel_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    row = db.scalar(select(WhatsAppChannel).where(WhatsAppChannel.id == channel_id))
    if row is None:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")
    integration = channel_integration(db, row)
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    app_secret = secrets.get("app_secret")
    if not app_secret:
        raise HTTPException(status_code=503, detail="Webhook signing secret is not configured")

    raw = await request.body()
    if not valid_meta_signature(raw, request.headers.get("x-hub-signature-256"), app_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook payload") from exc

    payload_hash = hashlib.sha256(raw).hexdigest()
    event = WhatsAppWebhookEvent(
        tenant_id=row.tenant_id,
        channel_id=row.id,
        event_key=payload_hash,
        event_type="meta_webhook",
        payload_hash=payload_hash,
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"status": "duplicate", "messages_received": 0, "statuses_updated": 0}

    messages_received = 0
    statuses_updated = 0

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            metadata = value.get("metadata") or {}
            incoming_phone_id = metadata.get("phone_number_id")
            if incoming_phone_id and incoming_phone_id != row.phone_number_id:
                continue

            for message in value.get("messages", []) or []:
                external_id = message.get("id")
                sender = message.get("from") or "unknown"
                message_type = message.get("type") or "unknown"
                if external_id:
                    existing = db.scalar(
                        select(WhatsAppMessage).where(
                            WhatsAppMessage.tenant_id == row.tenant_id,
                            WhatsAppMessage.external_message_id == external_id,
                        )
                    )
                    if existing:
                        continue
                db.add(
                    WhatsAppMessage(
                        tenant_id=row.tenant_id,
                        channel_id=row.id,
                        direction=MessageDirection.inbound,
                        external_message_id=external_id,
                        contact=sender,
                        message_type=message_type,
                        status=MessageStatus.received,
                        content_json=json.dumps(message, ensure_ascii=False),
                        provider_timestamp=message.get("timestamp"),
                    )
                )
                messages_received += 1

            for status in value.get("statuses", []) or []:
                external_id = status.get("id")
                if not external_id:
                    continue
                message_row = db.scalar(
                    select(WhatsAppMessage).where(
                        WhatsAppMessage.tenant_id == row.tenant_id,
                        WhatsAppMessage.external_message_id == external_id,
                    )
                )
                if message_row is None:
                    continue
                provider_status = status.get("status") or ""
                try:
                    message_row.status = MessageStatus(provider_status)
                except ValueError:
                    pass
                message_row.provider_timestamp = status.get("timestamp") or message_row.provider_timestamp
                errors = status.get("errors") or []
                if errors:
                    first = errors[0]
                    message_row.error_text = str(first.get("title") or first.get("message") or "provider status error")[:1000]
                statuses_updated += 1

    db.commit()
    return {
        "status": "processed",
        "messages_received": messages_received,
        "statuses_updated": statuses_updated,
    }
