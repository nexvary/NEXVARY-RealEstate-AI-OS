from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .growth_models import MediaType, PropertyMediaAsset
from .models import AuditEvent, Project, Unit, UserRole
from .omnichannel_models import ConversationSalesState, OmnichannelOutbox, OutboundKind, OutboundStatus
from .policy import RequestContext, get_request_context, require_roles, write_sales
from .property_sales_models import AdPropertyReferral, ConversationPropertyContext
from .property_sales_service import property_context_payload
from .workspace_models import InboxConversation

router = APIRouter(prefix="/api/v1/property-sales")
manage_referrals = require_roles(UserRole.owner, UserRole.admin, UserRole.sales_manager)


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    row = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


class ReferralCreate(BaseModel):
    channel: str = Field(default="whatsapp", min_length=2, max_length=40)
    campaign_id: str | None = Field(default=None, max_length=180)
    ad_id: str = Field(min_length=2, max_length=180)
    project_id: str
    unit_id: str | None = None
    label: str | None = Field(default=None, max_length=220)
    source_url: str | None = Field(default=None, max_length=2048)


class ReferralRead(BaseModel):
    id: str
    channel: str
    campaign_id: str | None
    ad_id: str
    project_id: str
    project_name: str
    unit_id: str | None
    unit_code: str | None
    label: str | None
    source_url: str | None


class MediaQueueRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1, max_length=10)
    channel_id: str | None = None


def referral_read(db: Session, row: AdPropertyReferral) -> ReferralRead:
    project = tenant_record(db, Project, row.project_id, row.tenant_id)
    unit = tenant_record(db, Unit, row.unit_id, row.tenant_id) if row.unit_id else None
    return ReferralRead(
        id=row.id,
        channel=row.channel,
        campaign_id=row.campaign_id,
        ad_id=row.ad_id,
        project_id=row.project_id,
        project_name=project.name,
        unit_id=row.unit_id,
        unit_code=unit.code if unit else None,
        label=row.label,
        source_url=row.source_url,
    )


@router.post("/ad-referrals", response_model=ReferralRead, status_code=201)
def create_ad_referral(
    payload: ReferralCreate,
    ctx: RequestContext = Depends(manage_referrals),
    db: Session = Depends(get_db),
) -> ReferralRead:
    project = tenant_record(db, Project, payload.project_id, ctx.tenant_id)
    unit = tenant_record(db, Unit, payload.unit_id, ctx.tenant_id) if payload.unit_id else None
    if unit and unit.project_id != project.id:
        raise HTTPException(status_code=409, detail="Unit belongs to a different project")

    row = AdPropertyReferral(
        tenant_id=ctx.tenant_id,
        channel=payload.channel.strip().lower(),
        campaign_id=payload.campaign_id,
        ad_id=payload.ad_id.strip(),
        project_id=project.id,
        unit_id=unit.id if unit else None,
        label=payload.label,
        source_url=payload.source_url,
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="property_sales.ad_referral.create",
            entity_type="ad_property_referral",
            entity_id=row.id,
            details=f"ad={row.ad_id};project={row.project_id};unit={row.unit_id or ''}",
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This ad is already mapped for the selected channel") from exc
    db.refresh(row)
    return referral_read(db, row)


@router.get("/ad-referrals", response_model=list[ReferralRead])
def list_ad_referrals(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[ReferralRead]:
    rows = db.scalars(
        select(AdPropertyReferral)
        .where(AdPropertyReferral.tenant_id == ctx.tenant_id)
        .order_by(AdPropertyReferral.created_at.desc())
        .limit(500)
    ).all()
    return [referral_read(db, row) for row in rows]


@router.get("/conversations/{conversation_id}/context")
def get_conversation_property_context(
    conversation_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    row = db.scalar(
        select(ConversationPropertyContext).where(
            ConversationPropertyContext.tenant_id == ctx.tenant_id,
            ConversationPropertyContext.conversation_id == conversation_id,
        )
    )
    return {"context": property_context_payload(db, row)}


def media_kind(asset: PropertyMediaAsset) -> tuple[OutboundKind, str | None, str | None]:
    if asset.media_type in {MediaType.image, MediaType.floorplan}:
        return OutboundKind.image, asset.title, asset.url
    if asset.media_type == MediaType.video:
        return OutboundKind.video, asset.title, asset.url
    if asset.media_type == MediaType.pdf:
        return OutboundKind.document, asset.title, asset.url
    return OutboundKind.text, f"{asset.title}\n{asset.url}", None


@router.post("/conversations/{conversation_id}/media-outbox", status_code=201)
def queue_property_media(
    conversation_id: str,
    payload: MediaQueueRequest,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    conversation = tenant_record(db, InboxConversation, conversation_id, ctx.tenant_id)
    context = db.scalar(
        select(ConversationPropertyContext).where(
            ConversationPropertyContext.tenant_id == ctx.tenant_id,
            ConversationPropertyContext.conversation_id == conversation.id,
        )
    )
    state = db.scalar(
        select(ConversationSalesState).where(
            ConversationSalesState.tenant_id == ctx.tenant_id,
            ConversationSalesState.conversation_id == conversation.id,
        )
    )

    unique_ids = list(dict.fromkeys(payload.asset_ids))
    assets = list(
        db.scalars(
            select(PropertyMediaAsset).where(
                PropertyMediaAsset.tenant_id == ctx.tenant_id,
                PropertyMediaAsset.id.in_(unique_ids),
            )
        ).all()
    )
    if len(assets) != len(unique_ids):
        raise HTTPException(status_code=404, detail="One or more media assets were not found")
    if any(not bool(asset.is_verified) for asset in assets):
        raise HTTPException(status_code=409, detail="Only verified property media can enter the sales outbox")

    if context and context.project_id:
        for asset in assets:
            same_unit = bool(context.unit_id and asset.unit_id == context.unit_id)
            same_project = asset.project_id == context.project_id and (asset.unit_id is None or not context.unit_id)
            if not (same_unit or same_project):
                raise HTTPException(status_code=409, detail="Media asset does not match the conversation property context")

    auto_allowed = bool(
        context
        and state
        and state.auto_reply_enabled
        and not state.handoff_required
    )
    status = OutboundStatus.approved if auto_allowed else OutboundStatus.pending_approval
    created: list[OmnichannelOutbox] = []
    for asset in assets:
        kind, body, media_url = media_kind(asset)
        row = OmnichannelOutbox(
            tenant_id=ctx.tenant_id,
            conversation_id=conversation.id,
            channel=conversation.channel.value,
            channel_id=payload.channel_id,
            kind=kind,
            body=body,
            media_url=media_url,
            grounded=1,
            source_confidence=Decimal("1.0"),
            requires_approval=0 if auto_allowed else 1,
            status=status,
            created_by_user_id=ctx.user_id,
        )
        db.add(row)
        created.append(row)

    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="property_sales.media_outbox.queue",
            entity_type="inbox_conversation",
            entity_id=conversation.id,
            details=f"assets={len(created)};auto={auto_allowed}",
        )
    )
    db.commit()
    for row in created:
        db.refresh(row)
    return [
        {
            "id": row.id,
            "conversation_id": row.conversation_id,
            "kind": row.kind.value,
            "body": row.body,
            "media_url": row.media_url,
            "grounded": bool(row.grounded),
            "status": row.status.value,
            "requires_approval": bool(row.requires_approval),
        }
        for row in created
    ]
