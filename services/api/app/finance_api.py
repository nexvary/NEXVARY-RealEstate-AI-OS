from __future__ import annotations

import calendar
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_db
from .finance_models import (
    BrokerCommission,
    CommissionStatus,
    Contract,
    ContractStatus,
    Installment,
    InstallmentStatus,
)
from .models import AuditEvent, Reservation, ReservationStatus, Unit, UnitStatus
from .policy import RequestContext, get_request_context, write_sales

router = APIRouter(prefix="/api/v1")


def tenant_record(db: Session, model, record_id: str, tenant_id: str):
    record = db.scalar(select(model).where(model.id == record_id, model.tenant_id == tenant_id))
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record


def add_months(value: datetime, months: int) -> datetime:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


class ContractFromReservation(BaseModel):
    contract_number: str = Field(min_length=2, max_length=120)
    signed_at: datetime | None = None


class ContractRead(BaseModel):
    id: str
    reservation_id: str
    lead_id: str
    unit_id: str
    contract_number: str
    total_price: Decimal
    currency: str
    status: ContractStatus
    signed_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ScheduleCreate(BaseModel):
    first_due_at: datetime
    installment_count: int = Field(ge=1, le=240)
    frequency_months: int = Field(default=1, ge=1, le=12)


class InstallmentRead(BaseModel):
    id: str
    contract_id: str
    sequence: int
    due_at: datetime
    amount: Decimal
    status: InstallmentStatus
    paid_at: datetime | None
    model_config = ConfigDict(from_attributes=True)


class CommissionCreate(BaseModel):
    broker_name: str = Field(min_length=2, max_length=180)
    rate_percent: Decimal = Field(gt=0, le=100)


class CommissionRead(BaseModel):
    id: str
    contract_id: str
    broker_name: str
    rate_percent: Decimal
    amount: Decimal
    status: CommissionStatus
    paid_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.post("/contracts/from-reservation/{reservation_id}", response_model=ContractRead, status_code=201)
def convert_reservation_to_contract(
    reservation_id: str,
    payload: ContractFromReservation,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Contract:
    reservation = tenant_record(db, Reservation, reservation_id, ctx.tenant_id)
    if reservation.status != ReservationStatus.active:
        raise HTTPException(status_code=409, detail="Only active reservations can become contracts")
    unit = tenant_record(db, Unit, reservation.unit_id, ctx.tenant_id)
    if unit.status != UnitStatus.reserved:
        raise HTTPException(status_code=409, detail="Reserved unit state is required")

    contract = Contract(
        tenant_id=ctx.tenant_id,
        reservation_id=reservation.id,
        lead_id=reservation.lead_id,
        unit_id=unit.id,
        contract_number=payload.contract_number.strip(),
        total_price=unit.price,
        currency=unit.currency,
        signed_at=payload.signed_at or datetime.now(timezone.utc),
    )
    reservation.status = ReservationStatus.converted
    unit.status = UnitStatus.sold
    db.add(contract)
    db.flush()
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="contract.create",
            entity_type="contract",
            entity_id=contract.id,
            details=f"reservation={reservation.id};unit={unit.id}",
        )
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Contract number already exists or reservation already converted") from exc
    db.refresh(contract)
    return contract


@router.get("/contracts", response_model=list[ContractRead])
def list_contracts(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Contract]:
    return list(
        db.scalars(
            select(Contract)
            .where(Contract.tenant_id == ctx.tenant_id)
            .order_by(Contract.created_at.desc())
        ).all()
    )


@router.post("/contracts/{contract_id}/schedule", response_model=list[InstallmentRead], status_code=201)
def generate_installment_schedule(
    contract_id: str,
    payload: ScheduleCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> list[Installment]:
    contract = tenant_record(db, Contract, contract_id, ctx.tenant_id)
    existing = db.scalar(select(Installment.id).where(Installment.contract_id == contract.id).limit(1))
    if existing:
        raise HTTPException(status_code=409, detail="Installment schedule already exists")

    reservation = tenant_record(db, Reservation, contract.reservation_id, ctx.tenant_id)
    remaining = max(Decimal("0"), Decimal(contract.total_price) - Decimal(reservation.reservation_amount))
    count = payload.installment_count
    base_amount = (remaining / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    created: list[Installment] = []
    allocated = Decimal("0")
    for index in range(count):
        amount = base_amount if index < count - 1 else (remaining - allocated).quantize(Decimal("0.01"))
        allocated += amount
        installment = Installment(
            tenant_id=ctx.tenant_id,
            contract_id=contract.id,
            sequence=index + 1,
            due_at=add_months(payload.first_due_at, index * payload.frequency_months),
            amount=amount,
        )
        db.add(installment)
        created.append(installment)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


@router.get("/contracts/{contract_id}/installments", response_model=list[InstallmentRead])
def list_installments(
    contract_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Installment]:
    tenant_record(db, Contract, contract_id, ctx.tenant_id)
    return list(
        db.scalars(
            select(Installment)
            .where(Installment.tenant_id == ctx.tenant_id, Installment.contract_id == contract_id)
            .order_by(Installment.sequence.asc())
        ).all()
    )


@router.post("/installments/{installment_id}/pay", response_model=InstallmentRead)
def pay_installment(
    installment_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Installment:
    installment = tenant_record(db, Installment, installment_id, ctx.tenant_id)
    if installment.status != InstallmentStatus.due:
        raise HTTPException(status_code=409, detail="Installment is not due")
    installment.status = InstallmentStatus.paid
    installment.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(installment)
    return installment


@router.post("/contracts/{contract_id}/commissions", response_model=CommissionRead, status_code=201)
def create_commission(
    contract_id: str,
    payload: CommissionCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> BrokerCommission:
    contract = tenant_record(db, Contract, contract_id, ctx.tenant_id)
    amount = (Decimal(contract.total_price) * Decimal(payload.rate_percent) / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    commission = BrokerCommission(
        tenant_id=ctx.tenant_id,
        contract_id=contract.id,
        broker_name=payload.broker_name,
        rate_percent=payload.rate_percent,
        amount=amount,
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


@router.get("/commissions", response_model=list[CommissionRead])
def list_commissions(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[BrokerCommission]:
    return list(
        db.scalars(
            select(BrokerCommission)
            .where(BrokerCommission.tenant_id == ctx.tenant_id)
            .order_by(BrokerCommission.created_at.desc())
        ).all()
    )


@router.post("/commissions/{commission_id}/pay", response_model=CommissionRead)
def pay_commission(
    commission_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> BrokerCommission:
    commission = tenant_record(db, BrokerCommission, commission_id, ctx.tenant_id)
    if commission.status != CommissionStatus.pending:
        raise HTTPException(status_code=409, detail="Commission is not pending")
    commission.status = CommissionStatus.paid
    commission.paid_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(commission)
    return commission
