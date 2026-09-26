from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class ContractStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    cancelled = "cancelled"


class InstallmentStatus(str, enum.Enum):
    due = "due"
    paid = "paid"
    cancelled = "cancelled"


class CommissionStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class Contract(Base):
    __tablename__ = "contracts"
    __table_args__ = (UniqueConstraint("tenant_id", "contract_number", name="uq_contract_tenant_number"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    reservation_id: Mapped[str] = mapped_column(ForeignKey("reservations.id"), nullable=False, unique=True, index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    contract_number: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="EGP", nullable=False)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.active, nullable=False, index=True)
    signed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Installment(Base):
    __tablename__ = "installments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[InstallmentStatus] = mapped_column(Enum(InstallmentStatus), default=InstallmentStatus.due, nullable=False, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BrokerCommission(Base):
    __tablename__ = "broker_commissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    contract_id: Mapped[str] = mapped_column(ForeignKey("contracts.id"), nullable=False, index=True)
    broker_name: Mapped[str] = mapped_column(String(180), nullable=False)
    rate_percent: Mapped[Decimal] = mapped_column(Numeric(6, 3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False)
    status: Mapped[CommissionStatus] = mapped_column(Enum(CommissionStatus), default=CommissionStatus.pending, nullable=False, index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
