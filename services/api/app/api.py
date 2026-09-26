from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import get_db
from .models import Appointment, Lead, Project, Unit, UnitStatus
from .schemas import LeadCreate, LeadRead, Overview, UnitRead
from .services.lead_scoring import score_lead

router = APIRouter(prefix="/api/v1")


@router.post("/leads", response_model=LeadRead, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> Lead:
    lead = Lead(
        **payload.model_dump(),
        score=score_lead(
            budget=payload.budget,
            preferred_city=payload.preferred_city,
            bedrooms=payload.bedrooms,
            source=payload.source,
            notes=payload.notes,
        ),
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/units/search", response_model=list[UnitRead])
def search_units(
    tenant_id: str,
    city: str | None = None,
    max_price: Decimal | None = Query(default=None, ge=0),
    bedrooms: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
) -> list[Unit]:
    query = (
        select(Unit)
        .join(Project, Unit.project_id == Project.id)
        .where(Unit.tenant_id == tenant_id, Unit.status == UnitStatus.available)
    )
    if city:
        query = query.where(func.lower(Project.city) == city.lower())
    if max_price is not None:
        query = query.where(Unit.price <= max_price)
    if bedrooms is not None:
        query = query.where(Unit.bedrooms == bedrooms)

    return list(db.scalars(query.order_by(Unit.price.asc()).limit(50)).all())


@router.get("/overview", response_model=Overview)
def overview(tenant_id: str, db: Session = Depends(get_db)) -> Overview:
    leads_total = db.scalar(select(func.count()).select_from(Lead).where(Lead.tenant_id == tenant_id)) or 0
    leads_hot = db.scalar(
        select(func.count()).select_from(Lead).where(Lead.tenant_id == tenant_id, Lead.score >= 70)
    ) or 0
    units_available = db.scalar(
        select(func.count()).select_from(Unit).where(Unit.tenant_id == tenant_id, Unit.status == UnitStatus.available)
    ) or 0
    appointments_total = db.scalar(
        select(func.count()).select_from(Appointment).where(Appointment.tenant_id == tenant_id)
    ) or 0
    return Overview(
        leads_total=leads_total,
        leads_hot=leads_hot,
        units_available=units_available,
        appointments_total=appointments_total,
    )
