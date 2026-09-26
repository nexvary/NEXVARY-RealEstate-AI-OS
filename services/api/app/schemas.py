from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .models import LeadStatus, UnitStatus


class LeadCreate(BaseModel):
    tenant_id: str
    full_name: str = Field(min_length=2, max_length=180)
    phone: str = Field(min_length=5, max_length=40)
    source: str = "manual"
    preferred_city: str | None = None
    budget: Decimal | None = Field(default=None, ge=0)
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    notes: str | None = None


class LeadRead(BaseModel):
    id: str
    tenant_id: str
    full_name: str
    phone: str
    source: str
    preferred_city: str | None
    budget: Decimal | None
    bedrooms: int | None
    status: LeadStatus
    score: int

    model_config = ConfigDict(from_attributes=True)


class UnitRead(BaseModel):
    id: str
    project_id: str
    code: str
    unit_type: str
    bedrooms: int | None
    area_sqm: Decimal
    price: Decimal
    status: UnitStatus

    model_config = ConfigDict(from_attributes=True)


class Overview(BaseModel):
    leads_total: int
    leads_hot: int
    units_available: int
    appointments_total: int
