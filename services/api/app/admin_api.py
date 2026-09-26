from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db
from .finance_models import BrokerCommission, Contract, Installment
from .models import (
    Appointment,
    AuditEvent,
    Building,
    Lead,
    PaymentPlan,
    Project,
    Reservation,
    Tenant,
    Unit,
    User,
)
from .policy import RequestContext, get_request_context, manage_users
from .workspace_models import FollowUpTask, InboxConversation, InboxMessage, KnowledgeDocument

router = APIRouter(prefix="/api/v1")


class TenantSettingsRead(BaseModel):
    id: str
    name: str
    slug: str
    brand_name: str | None
    primary_color: str
    model_config = ConfigDict(from_attributes=True)


class TenantSettingsUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=2, max_length=160)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")


class AuditRead(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str | None
    details: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def serializable(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, "value"):
        return value.value
    return value


def row_dict(row: Any, excluded: set[str] | None = None) -> dict[str, Any]:
    excluded = excluded or set()
    return {
        column.name: serializable(getattr(row, column.name))
        for column in row.__table__.columns
        if column.name not in excluded
    }


@router.get("/tenant/settings", response_model=TenantSettingsRead)
def tenant_settings(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/tenant/settings", response_model=TenantSettingsRead)
def update_tenant_settings(
    payload: TenantSettingsUpdate,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if value is not None:
            setattr(tenant, key, value)

    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="tenant.settings.update",
            entity_type="tenant",
            entity_id=tenant.id,
            details=",".join(changes.keys()),
        )
    )
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("/audit", response_model=list[AuditRead])
def audit_log(
    limit: int = 200,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[AuditEvent]:
    safe_limit = max(1, min(limit, 1000))
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.tenant_id == ctx.tenant_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(safe_limit)
        ).all()
    )


@router.get("/backup/export")
def export_backup(
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    models = {
        "users": (User, {"password_hash"}),
        "projects": (Project, set()),
        "buildings": (Building, set()),
        "payment_plans": (PaymentPlan, set()),
        "units": (Unit, set()),
        "leads": (Lead, set()),
        "appointments": (Appointment, set()),
        "reservations": (Reservation, set()),
        "contracts": (Contract, set()),
        "installments": (Installment, set()),
        "broker_commissions": (BrokerCommission, set()),
        "knowledge_documents": (KnowledgeDocument, {"content"}),
        "inbox_conversations": (InboxConversation, set()),
        "inbox_messages": (InboxMessage, set()),
        "followup_tasks": (FollowUpTask, set()),
        "audit_events": (AuditEvent, set()),
    }

    tenant = db.scalar(select(Tenant).where(Tenant.id == ctx.tenant_id))
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    data: dict[str, Any] = {
        "format": "NEXVARY-RealEstate-AI-OS-backup",
        "version": "1.0.0-stage170",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tenant": row_dict(tenant),
        "tables": {},
    }
    for name, (model, excluded) in models.items():
        rows = db.scalars(select(model).where(model.tenant_id == ctx.tenant_id)).all()
        data["tables"][name] = [row_dict(row, excluded) for row in rows]
    return data
