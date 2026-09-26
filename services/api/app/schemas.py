from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .models import LeadStatus, ReservationStatus, UnitStatus, UserRole


class TenantCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,98}[a-z0-9]$")
    brand_name: str | None = None
    primary_color: str = "#0B1F33"


class TenantRead(TenantCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    display_name: str = Field(min_length=2, max_length=160)
    role: UserRole = UserRole.sales_agent


class UserRead(UserCreate):
    id: str
    tenant_id: str
    is_active: int
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    city: str = Field(min_length=2, max_length=120)
    developer: str | None = None
    description: str | None = None


class ProjectRead(ProjectCreate):
    id: str
    tenant_id: str
    model_config = ConfigDict(from_attributes=True)


class BuildingCreate(BaseModel):
    project_id: str
    code: str = Field(min_length=1, max_length=80)
    name: str | None = None
    floors: int | None = Field(default=None, ge=1, le=300)


class BuildingRead(BuildingCreate):
    id: str
    tenant_id: str
    model_config = ConfigDict(from_attributes=True)


class PaymentPlanCreate(BaseModel):
    project_id: str
    name: str = Field(min_length=2, max_length=160)
    down_payment_percent: Decimal = Field(default=0, ge=0, le=100)
    years: int = Field(ge=1, le=30)
    installment_frequency_months: int = Field(default=3, ge=1, le=12)


class PaymentPlanRead(PaymentPlanCreate):
    id: str
    tenant_id: str
    model_config = ConfigDict(from_attributes=True)


class UnitCreate(BaseModel):
    project_id: str
    building_id: str | None = None
    payment_plan_id: str | None = None
    code: str = Field(min_length=1, max_length=80)
    unit_type: str = Field(min_length=2, max_length=80)
    bedrooms: int | None = Field(default=None, ge=0, le=30)
    area_sqm: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)


class UnitRead(UnitCreate):
    id: str
    tenant_id: str
    status: UnitStatus
    model_config = ConfigDict(from_attributes=True)


class LeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=180)
    phone: str = Field(min_length=5, max_length=40)
    email: str | None = None
    source: str = "manual"
    preferred_city: str | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    assigned_user_id: str | None = None
    notes: str | None = None


class LeadUpdate(BaseModel):
    status: LeadStatus | None = None
    assigned_user_id: str | None = None
    preferred_city: str | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    notes: str | None = None


class LeadRead(BaseModel):
    id: str
    tenant_id: str
    assigned_user_id: str | None
    full_name: str
    phone: str
    email: str | None
    source: str
    preferred_city: str | None
    budget: Decimal | None
    bedrooms: int | None
    status: LeadStatus
    score: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AppointmentCreate(BaseModel):
    lead_id: str
    project_id: str | None = None
    assigned_user_id: str | None = None
    starts_at: datetime
    notes: str | None = None


class AppointmentRead(AppointmentCreate):
    id: str
    tenant_id: str
    status: str
    model_config = ConfigDict(from_attributes=True)


class ReservationCreate(BaseModel):
    lead_id: str
    unit_id: str
    payment_plan_id: str | None = None
    reserved_by_user_id: str | None = None
    reservation_amount: Decimal = Field(default=0, ge=0)
    expires_at: datetime | None = None


class ReservationRead(ReservationCreate):
    id: str
    tenant_id: str
    status: ReservationStatus
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Overview(BaseModel):
    leads_total: int
    leads_hot: int
    units_available: int
    appointments_total: int
    active_reservations: int
