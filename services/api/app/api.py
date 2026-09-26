from decimal import Decimal
import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import get_settings
from .db import get_db
from .models import (
    Appointment,
    AuditEvent,
    Building,
    Lead,
    LeadStatus,
    PaymentPlan,
    Project,
    Reservation,
    ReservationStatus,
    Tenant,
    Unit,
    UnitStatus,
    User,
    UserRole,
)
from .policy import RequestContext, get_request_context, manage_inventory, manage_users, write_sales
from .quota import enforce_entity_limit
from .schemas import (
    AppointmentCreate,
    AppointmentRead,
    BuildingCreate,
    BuildingRead,
    LeadCreate,
    LeadRead,
    LeadUpdate,
    LoginRequest,
    Overview,
    PaymentPlanCreate,
    PaymentPlanRead,
    ProjectCreate,
    ProjectRead,
    ProvisionRequest,
    ProvisionResponse,
    ReservationCreate,
    ReservationRead,
    UnitCreate,
    TokenResponse,
    UnitRead,
    UserCreate,
    UserRead,
)
from .security import create_access_token, hash_password, verify_password
from .services.lead_scoring import score_lead

router = APIRouter(prefix="/api/v1")


def tenant_entity(db: Session, model, entity_id: str, tenant_id: str):
    entity = db.scalar(select(model).where(model.id == entity_id, model.tenant_id == tenant_id))
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return entity


def add_audit(
    db: Session,
    ctx: RequestContext,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: str | None = None,
) -> None:
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )


def commit_or_conflict(db: Session, detail: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc


@router.post("/auth/provision", response_model=ProvisionResponse, status_code=201)
def provision_company(
    payload: ProvisionRequest,
    x_platform_key: Annotated[str, Header(alias="X-Platform-Key")],
    db: Session = Depends(get_db),
) -> ProvisionResponse:
    settings = get_settings()
    if not hmac.compare_digest(x_platform_key, settings.platform_admin_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid platform provisioning key")

    tenant = Tenant(
        name=payload.company_name,
        slug=payload.company_slug.lower(),
        brand_name=payload.brand_name or payload.company_name,
        primary_color=payload.primary_color,
    )
    db.add(tenant)
    try:
        db.flush()
        owner = User(
            tenant_id=tenant.id,
            email=payload.owner_email.lower(),
            display_name=payload.owner_name,
            role=UserRole.owner,
            password_hash=hash_password(payload.owner_password),
        )
        db.add(owner)
        db.flush()
        db.add(
            AuditEvent(
                tenant_id=tenant.id,
                actor=owner.email,
                action="tenant.provision",
                entity_type="tenant",
                entity_id=tenant.id,
                details=tenant.slug,
            )
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Company slug or owner account already exists") from exc

    db.refresh(tenant)
    db.refresh(owner)
    token = create_access_token(user_id=owner.id, tenant_id=tenant.id, role=owner.role.value)
    return ProvisionResponse(
        tenant=tenant,
        user=owner,
        access_token=token,
        expires_in_minutes=settings.jwt_ttl_minutes,
    )


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == payload.tenant_slug.lower()))
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = db.scalar(
        select(User).where(
            User.tenant_id == tenant.id,
            func.lower(User.email) == payload.email.lower(),
            User.is_active == 1,
        )
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    settings = get_settings()
    token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role.value)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_ttl_minutes,
        user=user,
    )


@router.get("/me/context")
def request_context(ctx: RequestContext = Depends(get_request_context)) -> dict[str, str]:
    return {
        "tenant_id": ctx.tenant_id,
        "user_id": ctx.user_id,
        "actor": ctx.actor,
        "role": ctx.role.value,
    }


@router.post("/users", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    ctx: RequestContext = Depends(manage_users),
    db: Session = Depends(get_db),
) -> User:
    enforce_entity_limit(db, ctx.tenant_id, "users")
    user = User(
        tenant_id=ctx.tenant_id,
        email=payload.email.lower(),
        display_name=payload.display_name,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    add_audit(db, ctx, action="user.create", entity_type="user", entity_id=user.id, details=payload.email)
    commit_or_conflict(db, "A user with this email already exists in this company")
    db.refresh(user)
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[User]:
    return list(db.scalars(select(User).where(User.tenant_id == ctx.tenant_id).order_by(User.display_name)).all())


@router.post("/projects", response_model=ProjectRead, status_code=201)
def create_project(
    payload: ProjectCreate,
    ctx: RequestContext = Depends(manage_inventory),
    db: Session = Depends(get_db),
) -> Project:
    enforce_entity_limit(db, ctx.tenant_id, "projects")
    project = Project(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(project)
    add_audit(db, ctx, action="project.create", entity_type="project", entity_id=project.id, details=payload.name)
    commit_or_conflict(db, "A project with this name already exists in this company")
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectRead])
def list_projects(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Project]:
    return list(db.scalars(select(Project).where(Project.tenant_id == ctx.tenant_id).order_by(Project.name)).all())


@router.post("/buildings", response_model=BuildingRead, status_code=201)
def create_building(
    payload: BuildingCreate,
    ctx: RequestContext = Depends(manage_inventory),
    db: Session = Depends(get_db),
) -> Building:
    tenant_entity(db, Project, payload.project_id, ctx.tenant_id)
    building = Building(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(building)
    add_audit(db, ctx, action="building.create", entity_type="building", entity_id=building.id, details=payload.code)
    commit_or_conflict(db, "Building code already exists in this project")
    db.refresh(building)
    return building


@router.get("/buildings", response_model=list[BuildingRead])
def list_buildings(
    project_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Building]:
    query = select(Building).where(Building.tenant_id == ctx.tenant_id)
    if project_id:
        query = query.where(Building.project_id == project_id)
    return list(db.scalars(query.order_by(Building.code)).all())


@router.post("/payment-plans", response_model=PaymentPlanRead, status_code=201)
def create_payment_plan(
    payload: PaymentPlanCreate,
    ctx: RequestContext = Depends(manage_inventory),
    db: Session = Depends(get_db),
) -> PaymentPlan:
    tenant_entity(db, Project, payload.project_id, ctx.tenant_id)
    plan = PaymentPlan(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(plan)
    add_audit(db, ctx, action="payment_plan.create", entity_type="payment_plan", entity_id=plan.id, details=payload.name)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/payment-plans", response_model=list[PaymentPlanRead])
def list_payment_plans(
    project_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[PaymentPlan]:
    query = select(PaymentPlan).where(PaymentPlan.tenant_id == ctx.tenant_id)
    if project_id:
        query = query.where(PaymentPlan.project_id == project_id)
    return list(db.scalars(query.order_by(PaymentPlan.name)).all())


@router.post("/units", response_model=UnitRead, status_code=201)
def create_unit(
    payload: UnitCreate,
    ctx: RequestContext = Depends(manage_inventory),
    db: Session = Depends(get_db),
) -> Unit:
    enforce_entity_limit(db, ctx.tenant_id, "units")
    tenant_entity(db, Project, payload.project_id, ctx.tenant_id)
    if payload.building_id:
        building = tenant_entity(db, Building, payload.building_id, ctx.tenant_id)
        if building.project_id != payload.project_id:
            raise HTTPException(status_code=409, detail="Building belongs to a different project")
    if payload.payment_plan_id:
        plan = tenant_entity(db, PaymentPlan, payload.payment_plan_id, ctx.tenant_id)
        if plan.project_id != payload.project_id:
            raise HTTPException(status_code=409, detail="Payment plan belongs to a different project")

    unit = Unit(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(unit)
    add_audit(db, ctx, action="unit.create", entity_type="unit", entity_id=unit.id, details=payload.code)
    commit_or_conflict(db, "Unit code already exists in this project")
    db.refresh(unit)
    return unit


@router.get("/units", response_model=list[UnitRead])
def list_units(
    project_id: str | None = None,
    status_filter: UnitStatus | None = Query(default=None, alias="status"),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Unit]:
    query = select(Unit).where(Unit.tenant_id == ctx.tenant_id)
    if project_id:
        query = query.where(Unit.project_id == project_id)
    if status_filter:
        query = query.where(Unit.status == status_filter)
    return list(db.scalars(query.order_by(Unit.code).limit(250)).all())


@router.get("/units/search", response_model=list[UnitRead])
def search_units(
    city: str | None = None,
    max_price: Decimal | None = Query(default=None, ge=0),
    min_price: Decimal | None = Query(default=None, ge=0),
    bedrooms: int | None = Query(default=None, ge=0),
    unit_type: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Unit]:
    query = (
        select(Unit)
        .join(Project, Unit.project_id == Project.id)
        .where(Unit.tenant_id == ctx.tenant_id, Unit.status == UnitStatus.available)
    )
    if city:
        query = query.where(func.lower(Project.city) == city.lower())
    if max_price is not None:
        query = query.where(Unit.price <= max_price)
    if min_price is not None:
        query = query.where(Unit.price >= min_price)
    if bedrooms is not None:
        query = query.where(Unit.bedrooms == bedrooms)
    if unit_type:
        query = query.where(func.lower(Unit.unit_type) == unit_type.lower())
    return list(db.scalars(query.order_by(Unit.price.asc()).limit(100)).all())


@router.post("/leads", response_model=LeadRead, status_code=201)
def create_lead(
    payload: LeadCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Lead:
    if payload.assigned_user_id:
        tenant_entity(db, User, payload.assigned_user_id, ctx.tenant_id)
    lead = Lead(
        tenant_id=ctx.tenant_id,
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
    add_audit(db, ctx, action="lead.create", entity_type="lead", entity_id=lead.id, details=payload.phone)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/leads", response_model=list[LeadRead])
def list_leads(
    status_filter: LeadStatus | None = Query(default=None, alias="status"),
    min_score: int | None = Query(default=None, ge=0, le=100),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Lead]:
    query = select(Lead).where(Lead.tenant_id == ctx.tenant_id)
    if status_filter:
        query = query.where(Lead.status == status_filter)
    if min_score is not None:
        query = query.where(Lead.score >= min_score)
    return list(db.scalars(query.order_by(Lead.created_at.desc()).limit(250)).all())


@router.patch("/leads/{lead_id}", response_model=LeadRead)
def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Lead:
    lead = tenant_entity(db, Lead, lead_id, ctx.tenant_id)
    changes = payload.model_dump(exclude_unset=True)
    if "assigned_user_id" in changes and changes["assigned_user_id"]:
        tenant_entity(db, User, changes["assigned_user_id"], ctx.tenant_id)
    for key, value in changes.items():
        setattr(lead, key, value)

    if any(key in changes for key in {"budget", "preferred_city", "bedrooms", "notes"}):
        lead.score = score_lead(
            budget=lead.budget,
            preferred_city=lead.preferred_city,
            bedrooms=lead.bedrooms,
            source=lead.source,
            notes=lead.notes,
        )
    add_audit(db, ctx, action="lead.update", entity_type="lead", entity_id=lead.id, details=",".join(changes))
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/pipeline")
def sales_pipeline(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    rows = db.execute(
        select(Lead.status, func.count(Lead.id))
        .where(Lead.tenant_id == ctx.tenant_id)
        .group_by(Lead.status)
    ).all()
    result = {status.value: 0 for status in LeadStatus}
    for lead_status, count in rows:
        result[lead_status.value] = count
    return result


@router.post("/appointments", response_model=AppointmentRead, status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Appointment:
    tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.project_id:
        tenant_entity(db, Project, payload.project_id, ctx.tenant_id)
    if payload.assigned_user_id:
        tenant_entity(db, User, payload.assigned_user_id, ctx.tenant_id)

    appointment = Appointment(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(appointment)
    add_audit(db, ctx, action="appointment.create", entity_type="appointment", entity_id=appointment.id)
    db.commit()
    db.refresh(appointment)
    return appointment


@router.get("/appointments", response_model=list[AppointmentRead])
def list_appointments(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Appointment]:
    return list(
        db.scalars(
            select(Appointment)
            .where(Appointment.tenant_id == ctx.tenant_id)
            .order_by(Appointment.starts_at.asc())
            .limit(250)
        ).all()
    )


@router.post("/reservations", response_model=ReservationRead, status_code=201)
def create_reservation(
    payload: ReservationCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Reservation:
    tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    unit = db.scalar(
        select(Unit)
        .where(Unit.id == payload.unit_id, Unit.tenant_id == ctx.tenant_id)
        .with_for_update()
    )
    if unit is None:
        raise HTTPException(status_code=404, detail="Unit not found")
    if unit.status != UnitStatus.available:
        raise HTTPException(status_code=409, detail="Unit is not available")

    if payload.payment_plan_id:
        plan = tenant_entity(db, PaymentPlan, payload.payment_plan_id, ctx.tenant_id)
        if plan.project_id != unit.project_id:
            raise HTTPException(status_code=409, detail="Payment plan belongs to a different project")
    if payload.reserved_by_user_id:
        tenant_entity(db, User, payload.reserved_by_user_id, ctx.tenant_id)

    unit.status = UnitStatus.reserved
    reservation = Reservation(tenant_id=ctx.tenant_id, **payload.model_dump())
    db.add(reservation)
    add_audit(
        db,
        ctx,
        action="reservation.create",
        entity_type="reservation",
        entity_id=reservation.id,
        details=f"unit={unit.id}",
    )
    db.commit()
    db.refresh(reservation)
    return reservation


@router.post("/reservations/{reservation_id}/cancel", response_model=ReservationRead)
def cancel_reservation(
    reservation_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Reservation:
    reservation = tenant_entity(db, Reservation, reservation_id, ctx.tenant_id)
    if reservation.status != ReservationStatus.active:
        raise HTTPException(status_code=409, detail="Reservation is not active")

    unit = tenant_entity(db, Unit, reservation.unit_id, ctx.tenant_id)
    reservation.status = ReservationStatus.cancelled
    if unit.status == UnitStatus.reserved:
        unit.status = UnitStatus.available
    add_audit(
        db,
        ctx,
        action="reservation.cancel",
        entity_type="reservation",
        entity_id=reservation.id,
        details=f"unit={unit.id}",
    )
    db.commit()
    db.refresh(reservation)
    return reservation


@router.get("/reservations", response_model=list[ReservationRead])
def list_reservations(
    active_only: bool = False,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Reservation]:
    query = select(Reservation).where(Reservation.tenant_id == ctx.tenant_id)
    if active_only:
        query = query.where(Reservation.status == ReservationStatus.active)
    return list(db.scalars(query.order_by(Reservation.created_at.desc()).limit(250)).all())


@router.get("/overview", response_model=Overview)
def overview(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> Overview:
    tenant_id = ctx.tenant_id
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
    active_reservations = db.scalar(
        select(func.count())
        .select_from(Reservation)
        .where(Reservation.tenant_id == tenant_id, Reservation.status == ReservationStatus.active)
    ) or 0
    return Overview(
        leads_total=leads_total,
        leads_hot=leads_hot,
        units_available=units_available,
        appointments_total=appointments_total,
        active_reservations=active_reservations,
    )
