from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .finance_models import Contract, ContractStatus
from .growth_models import (
    AudienceSegment,
    CampaignStatus,
    CustomerFeedback,
    CustomerJourneyEvent,
    MarketingCampaign,
    MediaSourceKind,
    MediaType,
    PropertyMediaAsset,
    SalesPlaybook,
)
from .models import Lead, LeadStatus, Project, Unit, UserRole
from .policy import RequestContext, get_request_context, require_roles, write_sales
from .workspace_models import InboxConversation

router = APIRouter(prefix="/api/v1")
growth_manage = require_roles(UserRole.owner, UserRole.admin, UserRole.sales_manager)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    row = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return row


class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    channel: str = Field(min_length=2, max_length=80)
    objective: str | None = Field(default=None, max_length=180)
    status: CampaignStatus = CampaignStatus.draft
    budget: Decimal = Field(default=0, ge=0)
    spend: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)
    utm_source: str | None = Field(default=None, max_length=120)
    utm_medium: str | None = Field(default=None, max_length=120)
    utm_campaign: str | None = Field(default=None, max_length=180)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class CampaignUpdate(BaseModel):
    objective: str | None = Field(default=None, max_length=180)
    status: CampaignStatus | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    spend: Decimal | None = Field(default=None, ge=0)
    starts_at: datetime | None = None
    ends_at: datetime | None = None


class CampaignRead(BaseModel):
    id: str
    name: str
    channel: str
    objective: str | None
    status: CampaignStatus
    budget: Decimal
    spend: Decimal
    currency: str
    utm_source: str | None
    utm_medium: str | None
    utm_campaign: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CampaignPerformance(BaseModel):
    campaign_id: str
    campaign_name: str
    channel: str
    spend: Decimal
    currency: str
    leads_touched: int
    contracts_last_touch: int
    revenue_last_touch: Decimal
    cost_per_lead: Decimal | None
    roas_last_touch: Decimal | None


class JourneyEventCreate(BaseModel):
    lead_id: str
    campaign_id: str | None = None
    conversation_id: str | None = None
    event_type: str = Field(min_length=2, max_length=100)
    channel: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


class JourneyEventRead(BaseModel):
    id: str
    lead_id: str
    campaign_id: str | None
    conversation_id: str | None
    event_type: str
    channel: str | None
    metadata: dict[str, Any]
    occurred_at: datetime


class AudienceRules(BaseModel):
    sources: list[str] = Field(default_factory=list)
    statuses: list[LeadStatus] = Field(default_factory=list)
    min_score: int | None = Field(default=None, ge=0, le=100)
    preferred_city: str | None = Field(default=None, max_length=120)
    min_budget: Decimal | None = Field(default=None, ge=0)
    max_budget: Decimal | None = Field(default=None, ge=0)


class AudienceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=1200)
    rules: AudienceRules
    is_active: bool = True


class AudienceRead(BaseModel):
    id: str
    name: str
    description: str | None
    rules: AudienceRules
    is_active: bool
    created_at: datetime


class AudiencePreview(BaseModel):
    segment_id: str
    count: int
    leads: list[dict[str, Any]]


class MediaCreate(BaseModel):
    project_id: str | None = None
    unit_id: str | None = None
    title: str = Field(min_length=2, max_length=220)
    media_type: MediaType
    url: str = Field(min_length=5, max_length=2048)
    tags: list[str] = Field(default_factory=list)
    source_kind: MediaSourceKind = MediaSourceKind.company
    is_verified: bool = False


class MediaRead(BaseModel):
    id: str
    project_id: str | None
    unit_id: str | None
    title: str
    media_type: MediaType
    url: str
    tags: list[str]
    source_kind: MediaSourceKind
    is_verified: bool
    created_at: datetime


class PlaybookCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=1200)
    trigger_stage: str | None = Field(default=None, max_length=80)
    steps: list[str] = Field(min_length=1, max_length=50)
    is_active: bool = True


class PlaybookRead(BaseModel):
    id: str
    name: str
    description: str | None
    trigger_stage: str | None
    steps: list[str]
    is_active: bool
    created_at: datetime


class FeedbackCreate(BaseModel):
    lead_id: str | None = None
    conversation_id: str | None = None
    channel: str | None = Field(default=None, max_length=80)
    category: str = Field(default="general", min_length=2, max_length=100)
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str = Field(min_length=2, max_length=5000)


class FeedbackRead(BaseModel):
    id: str
    lead_id: str | None
    conversation_id: str | None
    channel: str | None
    category: str
    rating: int | None
    comment: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def journey_read(row: CustomerJourneyEvent) -> JourneyEventRead:
    return JourneyEventRead(
        id=row.id,
        lead_id=row.lead_id,
        campaign_id=row.campaign_id,
        conversation_id=row.conversation_id,
        event_type=row.event_type,
        channel=row.channel,
        metadata=json.loads(row.metadata_json or "{}"),
        occurred_at=row.occurred_at,
    )


def audience_read(row: AudienceSegment) -> AudienceRead:
    return AudienceRead(
        id=row.id,
        name=row.name,
        description=row.description,
        rules=AudienceRules.model_validate(json.loads(row.rules_json or "{}")),
        is_active=bool(row.is_active),
        created_at=row.created_at,
    )


def media_read(row: PropertyMediaAsset) -> MediaRead:
    return MediaRead(
        id=row.id,
        project_id=row.project_id,
        unit_id=row.unit_id,
        title=row.title,
        media_type=row.media_type,
        url=row.url,
        tags=json.loads(row.tags_json or "[]"),
        source_kind=row.source_kind,
        is_verified=bool(row.is_verified),
        created_at=row.created_at,
    )


def playbook_read(row: SalesPlaybook) -> PlaybookRead:
    return PlaybookRead(
        id=row.id,
        name=row.name,
        description=row.description,
        trigger_stage=row.trigger_stage,
        steps=json.loads(row.steps_json or "[]"),
        is_active=bool(row.is_active),
        created_at=row.created_at,
    )


@router.post("/growth/campaigns", response_model=CampaignRead, status_code=201)
def create_campaign(
    payload: CampaignCreate,
    ctx: RequestContext = Depends(growth_manage),
    db: Session = Depends(get_db),
) -> MarketingCampaign:
    if payload.ends_at and payload.starts_at and payload.ends_at < payload.starts_at:
        raise HTTPException(status_code=422, detail="Campaign end must be after start")
    row = MarketingCampaign(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        **payload.model_dump(),
        currency=payload.currency.upper(),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Campaign name already exists") from exc
    db.refresh(row)
    return row


@router.get("/growth/campaigns", response_model=list[CampaignRead])
def list_campaigns(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[MarketingCampaign]:
    return list(db.scalars(
        select(MarketingCampaign)
        .where(MarketingCampaign.tenant_id == ctx.tenant_id)
        .order_by(MarketingCampaign.created_at.desc())
    ).all())


@router.patch("/growth/campaigns/{campaign_id}", response_model=CampaignRead)
def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    ctx: RequestContext = Depends(growth_manage),
    db: Session = Depends(get_db),
) -> MarketingCampaign:
    row = tenant_record(db, MarketingCampaign, campaign_id, ctx.tenant_id)
    values = payload.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(row, key, value)
    if row.ends_at and row.starts_at and row.ends_at < row.starts_at:
        raise HTTPException(status_code=422, detail="Campaign end must be after start")
    db.commit()
    db.refresh(row)
    return row


@router.post("/growth/journeys/events", response_model=JourneyEventRead, status_code=201)
def create_journey_event(
    payload: JourneyEventCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> JourneyEventRead:
    tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.campaign_id:
        tenant_record(db, MarketingCampaign, payload.campaign_id, ctx.tenant_id)
    if payload.conversation_id:
        tenant_record(db, InboxConversation, payload.conversation_id, ctx.tenant_id)
    row = CustomerJourneyEvent(
        tenant_id=ctx.tenant_id,
        lead_id=payload.lead_id,
        campaign_id=payload.campaign_id,
        conversation_id=payload.conversation_id,
        event_type=payload.event_type,
        channel=payload.channel,
        metadata_json=json.dumps(payload.metadata, ensure_ascii=False, default=str),
        occurred_at=payload.occurred_at or utcnow(),
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return journey_read(row)


@router.get("/growth/journeys/{lead_id}", response_model=list[JourneyEventRead])
def lead_journey(
    lead_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[JourneyEventRead]:
    tenant_record(db, Lead, lead_id, ctx.tenant_id)
    rows = db.scalars(
        select(CustomerJourneyEvent)
        .where(CustomerJourneyEvent.tenant_id == ctx.tenant_id, CustomerJourneyEvent.lead_id == lead_id)
        .order_by(CustomerJourneyEvent.occurred_at.asc())
    ).all()
    return [journey_read(row) for row in rows]


@router.get("/growth/attribution/campaigns", response_model=list[CampaignPerformance])
def campaign_attribution(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[CampaignPerformance]:
    campaigns = list(db.scalars(
        select(MarketingCampaign).where(MarketingCampaign.tenant_id == ctx.tenant_id)
        .order_by(MarketingCampaign.created_at.desc())
    ).all())
    touched_rows = db.execute(
        select(CustomerJourneyEvent.campaign_id, func.count(func.distinct(CustomerJourneyEvent.lead_id)))
        .where(
            CustomerJourneyEvent.tenant_id == ctx.tenant_id,
            CustomerJourneyEvent.campaign_id.is_not(None),
        )
        .group_by(CustomerJourneyEvent.campaign_id)
    ).all()
    touched = {campaign_id: int(count) for campaign_id, count in touched_rows}
    revenue: dict[str, Decimal] = {}
    contract_counts: dict[str, int] = {}

    contracts = db.scalars(
        select(Contract).where(
            Contract.tenant_id == ctx.tenant_id,
            Contract.status.in_([ContractStatus.active, ContractStatus.completed]),
        )
    ).all()
    for contract in contracts:
        last_touch = db.scalar(
            select(CustomerJourneyEvent)
            .where(
                CustomerJourneyEvent.tenant_id == ctx.tenant_id,
                CustomerJourneyEvent.lead_id == contract.lead_id,
                CustomerJourneyEvent.campaign_id.is_not(None),
                CustomerJourneyEvent.occurred_at <= contract.signed_at,
            )
            .order_by(CustomerJourneyEvent.occurred_at.desc())
            .limit(1)
        )
        if last_touch and last_touch.campaign_id:
            revenue[last_touch.campaign_id] = revenue.get(last_touch.campaign_id, Decimal("0")) + contract.total_price
            contract_counts[last_touch.campaign_id] = contract_counts.get(last_touch.campaign_id, 0) + 1

    output: list[CampaignPerformance] = []
    for campaign in campaigns:
        lead_count = touched.get(campaign.id, 0)
        campaign_revenue = revenue.get(campaign.id, Decimal("0"))
        cost_per_lead = (campaign.spend / lead_count).quantize(Decimal("0.01")) if lead_count and campaign.spend else None
        roas = (campaign_revenue / campaign.spend).quantize(Decimal("0.01")) if campaign.spend else None
        output.append(CampaignPerformance(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            channel=campaign.channel,
            spend=campaign.spend,
            currency=campaign.currency,
            leads_touched=lead_count,
            contracts_last_touch=contract_counts.get(campaign.id, 0),
            revenue_last_touch=campaign_revenue,
            cost_per_lead=cost_per_lead,
            roas_last_touch=roas,
        ))
    return output


@router.post("/growth/audiences", response_model=AudienceRead, status_code=201)
def create_audience(
    payload: AudienceCreate,
    ctx: RequestContext = Depends(growth_manage),
    db: Session = Depends(get_db),
) -> AudienceRead:
    if payload.rules.min_budget is not None and payload.rules.max_budget is not None and payload.rules.min_budget > payload.rules.max_budget:
        raise HTTPException(status_code=422, detail="Minimum budget cannot exceed maximum budget")
    row = AudienceSegment(
        tenant_id=ctx.tenant_id,
        name=payload.name.strip(),
        description=payload.description,
        rules_json=json.dumps(payload.rules.model_dump(mode="json"), ensure_ascii=False),
        is_active=1 if payload.is_active else 0,
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Audience segment name already exists") from exc
    db.refresh(row)
    return audience_read(row)


@router.get("/growth/audiences", response_model=list[AudienceRead])
def list_audiences(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[AudienceRead]:
    return [audience_read(row) for row in db.scalars(
        select(AudienceSegment)
        .where(AudienceSegment.tenant_id == ctx.tenant_id)
        .order_by(AudienceSegment.created_at.desc())
    ).all()]


@router.get("/growth/audiences/{segment_id}/preview", response_model=AudiencePreview)
def preview_audience(
    segment_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> AudiencePreview:
    segment = tenant_record(db, AudienceSegment, segment_id, ctx.tenant_id)
    rules = AudienceRules.model_validate(json.loads(segment.rules_json or "{}"))
    query = select(Lead).where(Lead.tenant_id == ctx.tenant_id)
    if rules.sources:
        query = query.where(Lead.source.in_(rules.sources))
    if rules.statuses:
        query = query.where(Lead.status.in_(rules.statuses))
    if rules.min_score is not None:
        query = query.where(Lead.score >= rules.min_score)
    if rules.preferred_city:
        query = query.where(func.lower(Lead.preferred_city) == rules.preferred_city.lower())
    if rules.min_budget is not None:
        query = query.where(Lead.budget >= rules.min_budget)
    if rules.max_budget is not None:
        query = query.where(Lead.budget <= rules.max_budget)
    rows = list(db.scalars(query.order_by(Lead.score.desc(), Lead.created_at.desc()).limit(limit)).all())
    return AudiencePreview(
        segment_id=segment.id,
        count=len(rows),
        leads=[
            {
                "id": lead.id,
                "name": lead.full_name,
                "source": lead.source,
                "status": lead.status.value,
                "score": lead.score,
                "preferred_city": lead.preferred_city,
                "budget": str(lead.budget) if lead.budget is not None else None,
            }
            for lead in rows
        ],
    )


@router.post("/growth/media", response_model=MediaRead, status_code=201)
def create_media(
    payload: MediaCreate,
    ctx: RequestContext = Depends(growth_manage),
    db: Session = Depends(get_db),
) -> MediaRead:
    if not payload.project_id and not payload.unit_id:
        raise HTTPException(status_code=422, detail="Media must be attached to a project or unit")
    project_id = payload.project_id
    if payload.unit_id:
        unit = tenant_record(db, Unit, payload.unit_id, ctx.tenant_id)
        if project_id and unit.project_id != project_id:
            raise HTTPException(status_code=409, detail="Unit belongs to a different project")
        project_id = project_id or unit.project_id
    if project_id:
        tenant_record(db, Project, project_id, ctx.tenant_id)
    row = PropertyMediaAsset(
        tenant_id=ctx.tenant_id,
        project_id=project_id,
        unit_id=payload.unit_id,
        title=payload.title,
        media_type=payload.media_type,
        url=payload.url,
        tags_json=json.dumps([item.strip() for item in payload.tags if item.strip()], ensure_ascii=False),
        source_kind=payload.source_kind,
        is_verified=1 if payload.is_verified else 0,
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return media_read(row)


@router.get("/growth/media", response_model=list[MediaRead])
def list_media(
    project_id: str | None = None,
    unit_id: str | None = None,
    media_type: MediaType | None = None,
    verified_only: bool = False,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[MediaRead]:
    query = select(PropertyMediaAsset).where(PropertyMediaAsset.tenant_id == ctx.tenant_id)
    if project_id:
        query = query.where(PropertyMediaAsset.project_id == project_id)
    if unit_id:
        query = query.where(PropertyMediaAsset.unit_id == unit_id)
    if media_type:
        query = query.where(PropertyMediaAsset.media_type == media_type)
    if verified_only:
        query = query.where(PropertyMediaAsset.is_verified == 1)
    rows = db.scalars(query.order_by(PropertyMediaAsset.created_at.desc()).limit(300)).all()
    return [media_read(row) for row in rows]


@router.post("/growth/playbooks", response_model=PlaybookRead, status_code=201)
def create_playbook(
    payload: PlaybookCreate,
    ctx: RequestContext = Depends(growth_manage),
    db: Session = Depends(get_db),
) -> PlaybookRead:
    row = SalesPlaybook(
        tenant_id=ctx.tenant_id,
        name=payload.name.strip(),
        description=payload.description,
        trigger_stage=payload.trigger_stage,
        steps_json=json.dumps([step.strip() for step in payload.steps if step.strip()], ensure_ascii=False),
        is_active=1 if payload.is_active else 0,
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Playbook name already exists") from exc
    db.refresh(row)
    return playbook_read(row)


@router.get("/growth/playbooks", response_model=list[PlaybookRead])
def list_playbooks(
    stage: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[PlaybookRead]:
    query = select(SalesPlaybook).where(SalesPlaybook.tenant_id == ctx.tenant_id, SalesPlaybook.is_active == 1)
    if stage:
        query = query.where((SalesPlaybook.trigger_stage == stage) | (SalesPlaybook.trigger_stage.is_(None)))
    return [playbook_read(row) for row in db.scalars(query.order_by(SalesPlaybook.created_at.desc())).all()]


@router.post("/growth/feedback", response_model=FeedbackRead, status_code=201)
def create_feedback(
    payload: FeedbackCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> CustomerFeedback:
    if payload.lead_id:
        tenant_record(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.conversation_id:
        tenant_record(db, InboxConversation, payload.conversation_id, ctx.tenant_id)
    row = CustomerFeedback(
        tenant_id=ctx.tenant_id,
        lead_id=payload.lead_id,
        conversation_id=payload.conversation_id,
        channel=payload.channel,
        category=payload.category,
        rating=payload.rating,
        comment=payload.comment,
        created_by_user_id=ctx.user_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/growth/feedback", response_model=list[FeedbackRead])
def list_feedback(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[CustomerFeedback]:
    return list(db.scalars(
        select(CustomerFeedback)
        .where(CustomerFeedback.tenant_id == ctx.tenant_id)
        .order_by(CustomerFeedback.created_at.desc())
        .limit(300)
    ).all())


@router.get("/growth/feedback/summary")
def feedback_summary(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    total = int(db.scalar(
        select(func.count()).select_from(CustomerFeedback).where(CustomerFeedback.tenant_id == ctx.tenant_id)
    ) or 0)
    rated = db.execute(
        select(func.avg(CustomerFeedback.rating), func.count(CustomerFeedback.rating))
        .where(CustomerFeedback.tenant_id == ctx.tenant_id, CustomerFeedback.rating.is_not(None))
    ).one()
    categories = db.execute(
        select(CustomerFeedback.category, func.count(CustomerFeedback.id))
        .where(CustomerFeedback.tenant_id == ctx.tenant_id)
        .group_by(CustomerFeedback.category)
        .order_by(func.count(CustomerFeedback.id).desc())
    ).all()
    return {
        "total": total,
        "average_rating": round(float(rated[0]), 2) if rated[0] is not None else None,
        "rated_count": int(rated[1] or 0),
        "categories": [{"category": category, "count": int(count)} for category, count in categories],
    }
