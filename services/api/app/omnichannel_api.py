from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .commercial_models import WhatsAppChannel
from .db import get_db
from .integration_crypto import decrypt_secret_map
from .models import AuditEvent, Lead, Project, Unit, UnitStatus, User, UserRole
from .omnichannel_models import (
    AttributionEventType,
    ConversationSalesState,
    CustomerReplyPreference,
    InboundMessageReceipt,
    MarketingAttributionEvent,
    OmnichannelOutbox,
    OutboundKind,
    OutboundStatus,
    SalesJourneyStage,
)
from .policy import RequestContext, get_request_context, require_roles, write_sales
from .saas_models import TenantIntegration
from .workspace_models import (
    ConversationChannel,
    FollowUpTask,
    InboxConversation,
    InboxMessage,
    MessageDirection,
    KnowledgeChunk,
    KnowledgeDocument,
)

router = APIRouter(prefix="/api/v1/omnichannel")
approve_sales = require_roles(UserRole.owner, UserRole.admin, UserRole.sales_manager)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    row = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


def get_or_create_state(db: Session, conversation: InboxConversation) -> ConversationSalesState:
    row = db.scalar(
        select(ConversationSalesState).where(
            ConversationSalesState.tenant_id == conversation.tenant_id,
            ConversationSalesState.conversation_id == conversation.id,
        )
    )
    if row is None:
        row = ConversationSalesState(
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
        )
        db.add(row)
        db.flush()
    return row


def tokens(value: str) -> set[str]:
    return {
        item
        for item in re.findall(r"[A-Za-z0-9]+|[\u0621-\u063A\u0641-\u064A]+", value.casefold())
        if len(item) > 2
    }


class InboundIntake(BaseModel):
    channel: ConversationChannel
    external_message_id: str = Field(min_length=2, max_length=220)
    external_contact: str = Field(min_length=2, max_length=180)
    display_name: str | None = Field(default=None, max_length=180)
    body: str = Field(min_length=1, max_length=10000)
    lead_id: str | None = None
    campaign_id: str | None = Field(default=None, max_length=180)
    ad_id: str | None = Field(default=None, max_length=180)


class InboundResult(BaseModel):
    duplicate: bool
    conversation_id: str
    message_id: str
    state_id: str


class SalesStatePatch(BaseModel):
    reply_preference: CustomerReplyPreference | None = None
    journey_stage: SalesJourneyStage | None = None
    lead_score: int | None = Field(default=None, ge=0, le=100)
    assigned_user_id: str | None = None
    campaign_id: str | None = Field(default=None, max_length=180)
    ad_id: str | None = Field(default=None, max_length=180)
    auto_reply_enabled: bool | None = None


class SalesStateRead(BaseModel):
    id: str
    conversation_id: str
    reply_preference: CustomerReplyPreference
    journey_stage: SalesJourneyStage
    lead_score: int
    assigned_user_id: str | None
    campaign_id: str | None
    ad_id: str | None
    auto_reply_enabled: bool
    handoff_required: bool
    handoff_reason: str | None


class GroundedReplyRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    city: str | None = Field(default=None, max_length=120)
    max_price: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=30)
    unit_type: str | None = Field(default=None, max_length=80)
    source_confidence: Decimal = Field(default=Decimal("1.0"), ge=0, le=1)
    channel_id: str | None = None


class OutboxRead(BaseModel):
    id: str
    conversation_id: str
    channel: str
    channel_id: str | None
    kind: OutboundKind
    body: str | None
    media_url: str | None
    grounded: bool
    source_confidence: Decimal
    requires_approval: bool
    status: OutboundStatus
    external_message_id: str | None
    attempts: int
    last_error: str | None
    sent_at: datetime | None
    created_at: datetime


class GroundedReplyResult(BaseModel):
    answer: str
    grounded: bool
    requires_handoff: bool
    approval_required: bool
    outbox: OutboxRead
    voice_plan: dict[str, Any] | None
    units: list[dict[str, Any]]
    evidence: list[dict[str, Any]]


class HandoffRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=1000)
    assign_to_user_id: str | None = None


class AttributionRecord(BaseModel):
    campaign_id: str = Field(min_length=1, max_length=180)
    ad_id: str | None = Field(default=None, max_length=180)
    event_type: AttributionEventType
    value: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)
    lead_id: str | None = None
    conversation_id: str | None = None
    entity_id: str | None = None


def state_read(row: ConversationSalesState) -> SalesStateRead:
    return SalesStateRead(
        id=row.id,
        conversation_id=row.conversation_id,
        reply_preference=row.reply_preference,
        journey_stage=row.journey_stage,
        lead_score=row.lead_score,
        assigned_user_id=row.assigned_user_id,
        campaign_id=row.campaign_id,
        ad_id=row.ad_id,
        auto_reply_enabled=bool(row.auto_reply_enabled),
        handoff_required=bool(row.handoff_required),
        handoff_reason=row.handoff_reason,
    )


def outbox_read(row: OmnichannelOutbox) -> OutboxRead:
    return OutboxRead(
        id=row.id,
        conversation_id=row.conversation_id,
        channel=row.channel,
        channel_id=row.channel_id,
        kind=row.kind,
        body=row.body,
        media_url=row.media_url,
        grounded=bool(row.grounded),
        source_confidence=row.source_confidence,
        requires_approval=bool(row.requires_approval),
        status=row.status,
        external_message_id=row.external_message_id,
        attempts=row.attempts,
        last_error=row.last_error,
        sent_at=row.sent_at,
        created_at=row.created_at,
    )


@router.post("/inbound", response_model=InboundResult, status_code=201)
def ingest_inbound(
    payload: InboundIntake,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> InboundResult:
    existing = db.scalar(
        select(InboundMessageReceipt).where(
            InboundMessageReceipt.tenant_id == ctx.tenant_id,
            InboundMessageReceipt.channel == payload.channel.value,
            InboundMessageReceipt.external_message_id == payload.external_message_id,
        )
    )
    if existing:
        state = get_or_create_state(
            db,
            tenant_record(db, InboxConversation, existing.conversation_id, ctx.tenant_id),
        )
        db.commit()
        return InboundResult(
            duplicate=True,
            conversation_id=existing.conversation_id,
            message_id=existing.message_id,
            state_id=state.id,
        )

    if payload.lead_id:
        tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)

    conversation = db.scalar(
        select(InboxConversation).where(
            InboxConversation.tenant_id == ctx.tenant_id,
            InboxConversation.channel == payload.channel,
            InboxConversation.external_contact == payload.external_contact,
        )
    )
    if conversation is None:
        conversation = InboxConversation(
            tenant_id=ctx.tenant_id,
            lead_id=payload.lead_id,
            channel=payload.channel,
            external_contact=payload.external_contact,
            display_name=payload.display_name,
        )
        db.add(conversation)
        db.flush()
    else:
        if payload.display_name:
            conversation.display_name = payload.display_name
        if payload.lead_id and not conversation.lead_id:
            conversation.lead_id = payload.lead_id

    message = InboxMessage(
        tenant_id=ctx.tenant_id,
        conversation_id=conversation.id,
        direction=MessageDirection.inbound,
        sender=payload.display_name or payload.external_contact,
        body=payload.body,
    )
    conversation.last_message_at = utcnow()
    db.add(message)
    db.flush()

    digest = hashlib.sha256(
        json.dumps(payload.model_dump(mode="json"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    receipt = InboundMessageReceipt(
        tenant_id=ctx.tenant_id,
        conversation_id=conversation.id,
        channel=payload.channel.value,
        external_message_id=payload.external_message_id,
        message_id=message.id,
        payload_hash=digest,
    )
    db.add(receipt)

    state = get_or_create_state(db, conversation)
    if payload.campaign_id:
        state.campaign_id = payload.campaign_id
    if payload.ad_id:
        state.ad_id = payload.ad_id
    if payload.campaign_id:
        db.add(
            MarketingAttributionEvent(
                tenant_id=ctx.tenant_id,
                conversation_id=conversation.id,
                lead_id=conversation.lead_id,
                campaign_id=payload.campaign_id,
                ad_id=payload.ad_id,
                event_type=AttributionEventType.conversation,
            )
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(InboundMessageReceipt).where(
                InboundMessageReceipt.tenant_id == ctx.tenant_id,
                InboundMessageReceipt.channel == payload.channel.value,
                InboundMessageReceipt.external_message_id == payload.external_message_id,
            )
        )
        if existing is None:
            raise
        state = get_or_create_state(
            db,
            tenant_record(db, InboxConversation, existing.conversation_id, ctx.tenant_id),
        )
        db.commit()
        return InboundResult(
            duplicate=True,
            conversation_id=existing.conversation_id,
            message_id=existing.message_id,
            state_id=state.id,
        )

    return InboundResult(
        duplicate=False,
        conversation_id=conversation.id,
        message_id=message.id,
        state_id=state.id,
    )


@router.get("/conversations/{conversation_id}/sales-state", response_model=SalesStateRead)
def get_sales_state(
    conversation_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> SalesStateRead:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    row = get_or_create_state(db, conversation)
    db.commit()
    return state_read(row)


@router.patch("/conversations/{conversation_id}/sales-state", response_model=SalesStateRead)
def update_sales_state(
    conversation_id: str,
    payload: SalesStatePatch,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> SalesStateRead:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    row = get_or_create_state(db, conversation)
    values = payload.model_dump(exclude_unset=True)
    if values.get("assigned_user_id"):
        tenant_record(db, User, values["assigned_user_id"], ctx.tenant_id)
    for key, value in values.items():
        if key == "auto_reply_enabled" and value is not None:
            value = 1 if value else 0
        setattr(row, key, value)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return state_read(row)


def grounded_inventory(
    db: Session,
    tenant_id: str,
    payload: GroundedReplyRequest,
) -> list[tuple[Unit, Project]]:
    query = (
        select(Unit, Project)
        .join(Project, Project.id == Unit.project_id)
        .where(
            Unit.tenant_id == tenant_id,
            Project.tenant_id == tenant_id,
            Unit.status == UnitStatus.available,
        )
    )
    if payload.city:
        query = query.where(func.lower(Project.city) == payload.city.lower())
    if payload.max_price is not None:
        query = query.where(Unit.price <= payload.max_price)
    if payload.bedrooms is not None:
        query = query.where(Unit.bedrooms == payload.bedrooms)
    if payload.unit_type:
        query = query.where(func.lower(Unit.unit_type) == payload.unit_type.lower())
    return list(db.execute(query.order_by(Unit.price.asc()).limit(5)).all())


def grounded_evidence(db: Session, tenant_id: str, question: str) -> list[dict[str, Any]]:
    query_terms = tokens(question)
    if not query_terms:
        return []
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .where(KnowledgeChunk.tenant_id == tenant_id)
    ).all()
    scored: list[dict[str, Any]] = []
    for chunk, document in rows:
        haystack = f"{document.title} {document.source_name or ''} {chunk.text}".casefold()
        score = sum(10 for term in query_terms if term in haystack)
        if score:
            scored.append(
                {
                    "document_title": document.title,
                    "source_name": document.source_name,
                    "chunk_position": chunk.position,
                    "text": chunk.text,
                    "score": score,
                }
            )
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:4]


def build_answer(rows: list[tuple[Unit, Project]], evidence: list[dict[str, Any]], arabic: bool) -> str:
    if rows:
        if arabic:
            intro = f"وجدت {len(rows)} وحدة متاحة حاليًا من قاعدة البيانات:"
            items = [
                f"{project.name} — {unit.code}: {unit.unit_type}، {unit.area_sqm} م²، {unit.price} {unit.currency}"
                for unit, project in rows[:3]
            ]
            suffix = "السعر والتوافر المذكوران أعلاه من قاعدة البيانات الحالية."
            if evidence:
                suffix += " توجد أيضًا معلومات مساندة في قاعدة المعرفة."
            return "\n".join([intro, *items, suffix])
        intro = f"I found {len(rows)} currently available units in the database:"
        items = [
            f"{project.name} — {unit.code}: {unit.unit_type}, {unit.area_sqm} m², {unit.price} {unit.currency}"
            for unit, project in rows[:3]
        ]
        suffix = "The pricing and availability above come from the current transactional database."
        if evidence:
            suffix += " Related supporting knowledge is also available."
        return "\n".join([intro, *items, suffix])
    return (
        "لم أجد وحدة متاحة مطابقة للطلب الحالي. سأحوّل المحادثة لموظف للتأكد من البدائل."
        if arabic
        else "I found no available unit matching the current request. A staff member should verify alternatives."
    )


@router.post("/conversations/{conversation_id}/grounded-reply", response_model=GroundedReplyResult)
def prepare_grounded_reply(
    conversation_id: str,
    payload: GroundedReplyRequest,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> GroundedReplyResult:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    state = get_or_create_state(db, conversation)
    rows = grounded_inventory(db, ctx.tenant_id, payload)
    evidence = grounded_evidence(db, ctx.tenant_id, payload.question)
    arabic = bool(re.search(r"[\u0600-\u06FF]", payload.question))
    answer = build_answer(rows, evidence, arabic)

    grounded = bool(rows or evidence)
    requires_handoff = not bool(rows)
    confidence = Decimal(payload.source_confidence)
    auto_allowed = bool(state.auto_reply_enabled) and grounded and not requires_handoff and confidence >= Decimal("0.82")
    status = OutboundStatus.approved if auto_allowed else OutboundStatus.pending_approval
    outbox = OmnichannelOutbox(
        tenant_id=ctx.tenant_id,
        conversation_id=conversation.id,
        channel=conversation.channel.value,
        channel_id=payload.channel_id,
        kind=OutboundKind.text,
        body=answer,
        grounded=1 if grounded else 0,
        source_confidence=confidence,
        requires_approval=0 if auto_allowed else 1,
        status=status,
        created_by_user_id=ctx.user_id,
    )
    db.add(outbox)

    if requires_handoff:
        state.handoff_required = 1
        state.handoff_reason = "No currently available unit matched the grounded request."
        db.add(
            FollowUpTask(
                tenant_id=ctx.tenant_id,
                lead_id=conversation.lead_id,
                assigned_user_id=state.assigned_user_id or ctx.user_id,
                title="Human handoff required",
                notes=f"Conversation {conversation.id}: {state.handoff_reason}",
            )
        )

    voice_plan = None
    if state.reply_preference == CustomerReplyPreference.voice:
        segments = [item.strip() for item in answer.split("\n") if item.strip()][:3]
        voice_plan = {
            "locale": "ar-EG" if arabic else "en-US",
            "gender": "female",
            "style": "professional",
            "max_messages": 3,
            "segments": segments,
            "synthesis_required": True,
        }

    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="omnichannel.grounded_reply.prepare",
            entity_type="inbox_conversation",
            entity_id=conversation.id,
            details=f"grounded={grounded};handoff={requires_handoff};auto={auto_allowed}",
        )
    )
    db.commit()
    db.refresh(outbox)

    unit_payload = [
        {
            "unit_id": unit.id,
            "project_id": project.id,
            "project_name": project.name,
            "code": unit.code,
            "unit_type": unit.unit_type,
            "bedrooms": unit.bedrooms,
            "area_sqm": str(unit.area_sqm),
            "price": str(unit.price),
            "currency": unit.currency,
            "status": unit.status.value,
        }
        for unit, project in rows
    ]
    return GroundedReplyResult(
        answer=answer,
        grounded=grounded,
        requires_handoff=requires_handoff,
        approval_required=not auto_allowed,
        outbox=outbox_read(outbox),
        voice_plan=voice_plan,
        units=unit_payload,
        evidence=evidence,
    )


@router.post("/conversations/{conversation_id}/handoff")
def request_handoff(
    conversation_id: str,
    payload: HandoffRequest,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    state = get_or_create_state(db, conversation)
    if payload.assign_to_user_id:
        tenant_record(db, User, payload.assign_to_user_id, ctx.tenant_id)
        state.assigned_user_id = payload.assign_to_user_id
    state.handoff_required = 1
    state.handoff_reason = payload.reason
    task = FollowUpTask(
        tenant_id=ctx.tenant_id,
        lead_id=conversation.lead_id,
        assigned_user_id=state.assigned_user_id or ctx.user_id,
        title="Customer handoff",
        notes=f"{payload.reason}\nConversation: {conversation.id}",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"handoff_required": True, "reason": payload.reason, "task_id": task.id}


@router.get("/outbox", response_model=list[OutboxRead])
def list_outbox(
    status: OutboundStatus | None = Query(default=None),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[OutboxRead]:
    query = select(OmnichannelOutbox).where(OmnichannelOutbox.tenant_id == ctx.tenant_id)
    if status:
        query = query.where(OmnichannelOutbox.status == status)
    rows = db.scalars(query.order_by(OmnichannelOutbox.created_at.desc()).limit(500)).all()
    return [outbox_read(row) for row in rows]


@router.post("/outbox/{outbox_id}/approve", response_model=OutboxRead)
def approve_outbox(
    outbox_id: str,
    ctx: RequestContext = Depends(approve_sales),
    db: Session = Depends(get_db),
) -> OutboxRead:
    row = tenant_record(db, OmnichannelOutbox, outbox_id, ctx.tenant_id)
    if row.status != OutboundStatus.pending_approval:
        raise HTTPException(status_code=409, detail="Message is not pending approval")
    row.status = OutboundStatus.approved
    row.approved_by_user_id = ctx.user_id
    db.commit()
    db.refresh(row)
    return outbox_read(row)


@router.post("/outbox/{outbox_id}/reject", response_model=OutboxRead)
def reject_outbox(
    outbox_id: str,
    ctx: RequestContext = Depends(approve_sales),
    db: Session = Depends(get_db),
) -> OutboxRead:
    row = tenant_record(db, OmnichannelOutbox, outbox_id, ctx.tenant_id)
    if row.status != OutboundStatus.pending_approval:
        raise HTTPException(status_code=409, detail="Message is not pending approval")
    row.status = OutboundStatus.rejected
    row.approved_by_user_id = ctx.user_id
    db.commit()
    db.refresh(row)
    return outbox_read(row)


def whatsapp_payload(row: OmnichannelOutbox, to: str) -> dict[str, Any]:
    base: dict[str, Any] = {"messaging_product": "whatsapp", "to": to}
    if row.kind == OutboundKind.text:
        base.update({"type": "text", "text": {"body": row.body or ""}})
    elif row.kind == OutboundKind.image:
        base.update({"type": "image", "image": {"link": row.media_url}})
    elif row.kind == OutboundKind.video:
        base.update({"type": "video", "video": {"link": row.media_url}})
    else:
        base.update({"type": "document", "document": {"link": row.media_url}})
    return base


@router.post("/outbox/{outbox_id}/dispatch", response_model=OutboxRead)
def dispatch_outbox(
    outbox_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> OutboxRead:
    row = tenant_record(db, OmnichannelOutbox, outbox_id, ctx.tenant_id)
    if row.status != OutboundStatus.approved:
        raise HTTPException(status_code=409, detail="Only approved messages can be dispatched")
    conversation = tenant_record(db, InboxConversation, row.conversation_id, ctx.tenant_id)
    if row.channel != ConversationChannel.whatsapp.value:
        raise HTTPException(status_code=409, detail="Official transport is currently implemented for WhatsApp only")

    channel_query = select(WhatsAppChannel).where(
        WhatsAppChannel.tenant_id == ctx.tenant_id,
        WhatsAppChannel.status == "ready",
    )
    if row.channel_id:
        channel_query = channel_query.where(WhatsAppChannel.id == row.channel_id)
    else:
        channel_query = channel_query.order_by(WhatsAppChannel.is_default.desc(), WhatsAppChannel.created_at.asc())
    channel = db.scalar(channel_query.limit(1))
    if channel is None or not channel.integration_id:
        raise HTTPException(status_code=409, detail="No ready WhatsApp channel is configured")

    integration = db.scalar(
        select(TenantIntegration).where(
            TenantIntegration.id == channel.integration_id,
            TenantIntegration.tenant_id == ctx.tenant_id,
            TenantIntegration.is_enabled == 1,
        )
    )
    if integration is None:
        raise HTTPException(status_code=409, detail="WhatsApp integration is disabled")
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    token = str(secrets.get("access_token") or "").strip()
    if not token:
        raise HTTPException(status_code=409, detail="WhatsApp access token is missing")

    row.status = OutboundStatus.sending
    row.attempts += 1
    db.commit()

    endpoint = f"https://graph.facebook.com/{channel.graph_api_version}/{channel.phone_number_id}/messages"
    try:
        response = httpx.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=whatsapp_payload(row, conversation.external_contact),
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json() if response.content else {}
        messages = data.get("messages") if isinstance(data, dict) else None
        external_id = ""
        if isinstance(messages, list) and messages and isinstance(messages[0], dict):
            external_id = str(messages[0].get("id") or "")
        row.status = OutboundStatus.sent
        row.external_message_id = external_id or None
        row.sent_at = utcnow()
        row.last_error = None
        db.add(
            InboxMessage(
                tenant_id=ctx.tenant_id,
                conversation_id=conversation.id,
                direction=MessageDirection.outbound,
                sender=ctx.actor,
                body=row.body or f"[{row.kind.value}] {row.media_url or ''}".strip(),
            )
        )
        conversation.last_message_at = utcnow()
    except (httpx.HTTPError, ValueError) as exc:
        row.status = OutboundStatus.failed
        row.last_error = f"{type(exc).__name__}: {str(exc)[:1000]}"
    db.commit()
    db.refresh(row)
    return outbox_read(row)


@router.post("/attribution/events", status_code=201)
def record_attribution(
    payload: AttributionRecord,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if payload.lead_id:
        tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.conversation_id:
        tenant_record(db, InboxConversation, payload.conversation_id, ctx.tenant_id)
    row = MarketingAttributionEvent(
        tenant_id=ctx.tenant_id,
        **payload.model_dump(),
        currency=payload.currency.upper(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "event_type": row.event_type.value}


@router.get("/attribution/campaigns")
def campaign_attribution(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    rows = db.execute(
        select(
            MarketingAttributionEvent.campaign_id,
            MarketingAttributionEvent.event_type,
            func.count(MarketingAttributionEvent.id),
            func.coalesce(func.sum(MarketingAttributionEvent.value), 0),
        )
        .where(MarketingAttributionEvent.tenant_id == ctx.tenant_id)
        .group_by(MarketingAttributionEvent.campaign_id, MarketingAttributionEvent.event_type)
    ).all()
    grouped: dict[str, dict[str, Any]] = {}
    for campaign_id, event_type, count, value in rows:
        item = grouped.setdefault(campaign_id, {"campaign_id": campaign_id, "events": {}, "revenue": "0"})
        item["events"][event_type.value] = int(count)
        if event_type == AttributionEventType.revenue:
            item["revenue"] = str(value)
    return sorted(grouped.values(), key=lambda item: item["campaign_id"])
