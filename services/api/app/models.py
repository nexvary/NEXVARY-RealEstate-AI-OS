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


class UnitStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    sold = "sold"
    blocked = "blocked"


class LeadStatus(str, enum.Enum):
    new = "new"
    qualified = "qualified"
    viewing = "viewing"
    negotiation = "negotiation"
    won = "won"
    lost = "lost"


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    sales_manager = "sales_manager"
    sales_agent = "sales_agent"
    finance = "finance"
    viewer = "viewer"


class ReservationStatus(str, enum.Enum):
    active = "active"
    cancelled = "cancelled"
    converted = "converted"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    brand_name: Mapped[str | None] = mapped_column(String(160))
    primary_color: Mapped[str] = mapped_column(String(20), default="#0B1F33")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.sales_agent, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_projects_tenant_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    developer: Mapped[str | None] = mapped_column(String(180))
    description: Mapped[str | None] = mapped_column(Text)


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (UniqueConstraint("tenant_id", "project_id", "code", name="uq_buildings_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str | None] = mapped_column(String(180))
    floors: Mapped[int | None] = mapped_column(Integer)


class PaymentPlan(Base):
    __tablename__ = "payment_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    down_payment_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    years: Mapped[int] = mapped_column(Integer, nullable=False)
    installment_frequency_months: Mapped[int] = mapped_column(Integer, default=3, nullable=False)


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("tenant_id", "project_id", "code", name="uq_units_project_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    building_id: Mapped[str | None] = mapped_column(ForeignKey("buildings.id"), index=True)
    payment_plan_id: Mapped[str | None] = mapped_column(ForeignKey("payment_plans.id"))
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    unit_type: Mapped[str] = mapped_column(String(80), nullable=False)
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(16, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(8), default="EGP", nullable=False)
    status: Mapped[UnitStatus] = mapped_column(Enum(UnitStatus), default=UnitStatus.available, nullable=False, index=True)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    full_name: Mapped[str] = mapped_column(String(180), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(80), default="manual")
    preferred_city: Mapped[str | None] = mapped_column(String(120))
    budget: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.new, nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    assigned_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="scheduled", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    lead_id: Mapped[str] = mapped_column(ForeignKey("leads.id"), nullable=False, index=True)
    unit_id: Mapped[str] = mapped_column(ForeignKey("units.id"), nullable=False, index=True)
    payment_plan_id: Mapped[str | None] = mapped_column(ForeignKey("payment_plans.id"))
    reserved_by_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    reservation_amount: Mapped[Decimal] = mapped_column(Numeric(16, 2), default=0, nullable=False)
    status: Mapped[ReservationStatus] = mapped_column(Enum(ReservationStatus), default=ReservationStatus.active, nullable=False, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(180), nullable=False)
    action: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36))
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
