from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .crm_models import (
    Expense,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    Proposal,
    ProposalStatus,
    Reminder,
    ReminderStatus,
    SupportTicket,
    TicketPriority,
    TicketStatus,
)
from .db import get_db
from .finance_models import Contract
from .growth_models import CustomerJourneyEvent
from .models import Appointment, AuditEvent, Lead, Project, Reservation, Unit
from .policy import RequestContext, get_request_context, write_sales


router = APIRouter(prefix="/api/v1/enterprise-crm", tags=["enterprise-crm"])


def tenant_entity(db: Session, model, entity_id: str, tenant_id: str):
    entity = db.scalar(select(model).where(model.id == entity_id, model.tenant_id == tenant_id))
    if entity is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return entity


def audit(db: Session, ctx: RequestContext, action: str, entity_type: str, entity_id: str, details: str = "") -> None:
    db.add(AuditEvent(
        tenant_id=ctx.tenant_id,
        actor=ctx.actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or None,
    ))


def journey(
    db: Session,
    ctx: RequestContext,
    lead_id: str | None,
    event_type: str,
    *,
    channel: str = "crm",
    metadata: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> None:
    if not lead_id:
        return
    db.add(CustomerJourneyEvent(
        tenant_id=ctx.tenant_id,
        lead_id=lead_id,
        event_type=event_type,
        channel=channel,
        metadata_json=json.dumps(metadata or {}, ensure_ascii=False, default=str),
        occurred_at=occurred_at or datetime.now(timezone.utc),
        created_by_user_id=ctx.user_id,
    ))


class ProposalCreate(BaseModel):
    lead_id: str
    unit_id: str | None = None
    proposal_number: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)
    expires_at: datetime | None = None
    notes: str | None = None


class ProposalRead(ProposalCreate):
    id: str
    status: ProposalStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProposalStatusUpdate(BaseModel):
    status: ProposalStatus


class InvoiceCreate(BaseModel):
    lead_id: str
    contract_id: str | None = None
    invoice_number: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=2, max_length=220)
    total_amount: Decimal = Field(gt=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)
    due_at: datetime | None = None
    notes: str | None = None


class InvoiceRead(InvoiceCreate):
    id: str
    paid_amount: Decimal
    status: InvoiceStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    method: PaymentMethod = PaymentMethod.bank_transfer
    reference: str | None = Field(default=None, max_length=180)
    notes: str | None = None
    paid_at: datetime | None = None


class PaymentRead(BaseModel):
    id: str
    invoice_id: str
    lead_id: str
    amount: Decimal
    currency: str
    method: PaymentMethod
    reference: str | None
    notes: str | None
    paid_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(BaseModel):
    project_id: str | None = None
    category: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=2, max_length=240)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="EGP", min_length=3, max_length=8)
    incurred_at: datetime | None = None
    receipt_reference: str | None = Field(default=None, max_length=180)


class ExpenseRead(BaseModel):
    id: str
    project_id: str | None
    category: str
    description: str
    amount: Decimal
    currency: str
    incurred_at: datetime
    receipt_reference: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TicketCreate(BaseModel):
    lead_id: str | None = None
    contract_id: str | None = None
    subject: str = Field(min_length=2, max_length=220)
    description: str = Field(min_length=2)
    priority: TicketPriority = TicketPriority.normal
    assigned_user_id: str | None = None


class TicketRead(TicketCreate):
    id: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class ReminderCreate(BaseModel):
    lead_id: str | None = None
    entity_type: str | None = Field(default=None, max_length=80)
    entity_id: str | None = None
    title: str = Field(min_length=2, max_length=220)
    due_at: datetime
    assigned_user_id: str | None = None


class ReminderRead(ReminderCreate):
    id: str
    status: ReminderStatus
    completed_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EnterpriseSummary(BaseModel):
    proposals_open: int
    proposals_accepted: int
    invoices_open: int
    receivables: Decimal
    payments_total: Decimal
    expenses_total: Decimal
    tickets_open: int
    reminders_pending: int


class TimelineItem(BaseModel):
    id: str
    kind: str
    title: str
    channel: str | None = None
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/summary", response_model=EnterpriseSummary)
def enterprise_summary(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> EnterpriseSummary:
    proposals_open = db.scalar(select(func.count()).select_from(Proposal).where(
        Proposal.tenant_id == ctx.tenant_id,
        Proposal.status.in_([ProposalStatus.draft, ProposalStatus.sent]),
    )) or 0
    proposals_accepted = db.scalar(select(func.count()).select_from(Proposal).where(
        Proposal.tenant_id == ctx.tenant_id,
        Proposal.status == ProposalStatus.accepted,
    )) or 0
    invoices_open = db.scalar(select(func.count()).select_from(Invoice).where(
        Invoice.tenant_id == ctx.tenant_id,
        Invoice.status.in_([InvoiceStatus.issued, InvoiceStatus.partial]),
    )) or 0
    invoice_rows = db.scalars(select(Invoice).where(
        Invoice.tenant_id == ctx.tenant_id,
        Invoice.status.in_([InvoiceStatus.issued, InvoiceStatus.partial]),
    )).all()
    receivables = sum((Decimal(row.total_amount) - Decimal(row.paid_amount) for row in invoice_rows), Decimal("0"))
    payments_total = db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.tenant_id == ctx.tenant_id)) or Decimal("0")
    expenses_total = db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.tenant_id == ctx.tenant_id)) or Decimal("0")
    tickets_open = db.scalar(select(func.count()).select_from(SupportTicket).where(
        SupportTicket.tenant_id == ctx.tenant_id,
        SupportTicket.status.in_([TicketStatus.open, TicketStatus.in_progress, TicketStatus.pending_customer]),
    )) or 0
    reminders_pending = db.scalar(select(func.count()).select_from(Reminder).where(
        Reminder.tenant_id == ctx.tenant_id,
        Reminder.status == ReminderStatus.pending,
    )) or 0
    return EnterpriseSummary(
        proposals_open=int(proposals_open),
        proposals_accepted=int(proposals_accepted),
        invoices_open=int(invoices_open),
        receivables=receivables,
        payments_total=Decimal(payments_total),
        expenses_total=Decimal(expenses_total),
        tickets_open=int(tickets_open),
        reminders_pending=int(reminders_pending),
    )


@router.post("/proposals", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def create_proposal(
    payload: ProposalCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Proposal:
    tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.unit_id:
        tenant_entity(db, Unit, payload.unit_id, ctx.tenant_id)
    proposal = Proposal(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        **payload.model_dump(),
    )
    db.add(proposal)
    db.flush()
    audit(db, ctx, "proposal.create", "proposal", proposal.id, payload.proposal_number)
    journey(db, ctx, proposal.lead_id, "proposal_created", metadata={
        "proposal_id": proposal.id,
        "proposal_number": proposal.proposal_number,
        "amount": proposal.amount,
        "currency": proposal.currency,
        "unit_id": proposal.unit_id,
    })
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Proposal number already exists") from exc
    db.refresh(proposal)
    return proposal


@router.get("/proposals", response_model=list[ProposalRead])
def list_proposals(
    lead_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Proposal]:
    query = select(Proposal).where(Proposal.tenant_id == ctx.tenant_id)
    if lead_id:
        tenant_entity(db, Lead, lead_id, ctx.tenant_id)
        query = query.where(Proposal.lead_id == lead_id)
    return list(db.scalars(query.order_by(Proposal.created_at.desc()).limit(300)).all())


@router.patch("/proposals/{proposal_id}/status", response_model=ProposalRead)
def update_proposal_status(
    proposal_id: str,
    payload: ProposalStatusUpdate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Proposal:
    proposal = tenant_entity(db, Proposal, proposal_id, ctx.tenant_id)
    proposal.status = payload.status
    audit(db, ctx, "proposal.status", "proposal", proposal.id, payload.status.value)
    journey(db, ctx, proposal.lead_id, f"proposal_{payload.status.value}", metadata={
        "proposal_id": proposal.id,
        "proposal_number": proposal.proposal_number,
    })
    db.commit()
    db.refresh(proposal)
    return proposal


@router.post("/invoices", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Invoice:
    tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.contract_id:
        contract = tenant_entity(db, Contract, payload.contract_id, ctx.tenant_id)
        if contract.lead_id != payload.lead_id:
            raise HTTPException(status_code=409, detail="Contract belongs to a different lead")
    invoice = Invoice(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        paid_amount=Decimal("0"),
        status=InvoiceStatus.issued,
        **payload.model_dump(),
    )
    db.add(invoice)
    db.flush()
    audit(db, ctx, "invoice.create", "invoice", invoice.id, payload.invoice_number)
    journey(db, ctx, invoice.lead_id, "invoice_issued", channel="finance", metadata={
        "invoice_id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "total_amount": invoice.total_amount,
        "currency": invoice.currency,
    })
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Invoice number already exists") from exc
    db.refresh(invoice)
    return invoice


@router.get("/invoices", response_model=list[InvoiceRead])
def list_invoices(
    lead_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Invoice]:
    query = select(Invoice).where(Invoice.tenant_id == ctx.tenant_id)
    if lead_id:
        tenant_entity(db, Lead, lead_id, ctx.tenant_id)
        query = query.where(Invoice.lead_id == lead_id)
    return list(db.scalars(query.order_by(Invoice.created_at.desc()).limit(300)).all())


@router.post("/invoices/{invoice_id}/payments", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def record_payment(
    invoice_id: str,
    payload: PaymentCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Payment:
    invoice = tenant_entity(db, Invoice, invoice_id, ctx.tenant_id)
    if invoice.status in {InvoiceStatus.paid, InvoiceStatus.void}:
        raise HTTPException(status_code=409, detail="Invoice cannot accept payments")
    remaining = Decimal(invoice.total_amount) - Decimal(invoice.paid_amount)
    if payload.amount > remaining:
        raise HTTPException(status_code=409, detail="Payment exceeds invoice balance")

    payment = Payment(
        tenant_id=ctx.tenant_id,
        invoice_id=invoice.id,
        lead_id=invoice.lead_id,
        amount=payload.amount,
        currency=invoice.currency,
        method=payload.method,
        reference=payload.reference,
        notes=payload.notes,
        paid_at=payload.paid_at or datetime.now(timezone.utc),
        recorded_by_user_id=ctx.user_id,
    )
    invoice.paid_amount = Decimal(invoice.paid_amount) + payload.amount
    invoice.status = InvoiceStatus.paid if Decimal(invoice.paid_amount) >= Decimal(invoice.total_amount) else InvoiceStatus.partial
    db.add(payment)
    db.flush()
    audit(db, ctx, "payment.record", "payment", payment.id, f"invoice={invoice.invoice_number}")
    journey(db, ctx, invoice.lead_id, "payment_received", channel="finance", metadata={
        "payment_id": payment.id,
        "invoice_id": invoice.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "method": payment.method.value,
    }, occurred_at=payment.paid_at)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/payments", response_model=list[PaymentRead])
def list_payments(
    lead_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Payment]:
    query = select(Payment).where(Payment.tenant_id == ctx.tenant_id)
    if lead_id:
        tenant_entity(db, Lead, lead_id, ctx.tenant_id)
        query = query.where(Payment.lead_id == lead_id)
    return list(db.scalars(query.order_by(Payment.paid_at.desc()).limit(500)).all())


@router.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Expense:
    if payload.project_id:
        tenant_entity(db, Project, payload.project_id, ctx.tenant_id)
    data = payload.model_dump()
    data["incurred_at"] = payload.incurred_at or datetime.now(timezone.utc)
    expense = Expense(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        **data,
    )
    db.add(expense)
    db.flush()
    audit(db, ctx, "expense.create", "expense", expense.id, expense.category)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses", response_model=list[ExpenseRead])
def list_expenses(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Expense]:
    return list(db.scalars(
        select(Expense)
        .where(Expense.tenant_id == ctx.tenant_id)
        .order_by(Expense.incurred_at.desc())
        .limit(500)
    ).all())


@router.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> SupportTicket:
    if payload.lead_id:
        tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    if payload.contract_id:
        contract = tenant_entity(db, Contract, payload.contract_id, ctx.tenant_id)
        if payload.lead_id and contract.lead_id != payload.lead_id:
            raise HTTPException(status_code=409, detail="Contract belongs to a different lead")
    ticket = SupportTicket(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        **payload.model_dump(),
    )
    db.add(ticket)
    db.flush()
    audit(db, ctx, "ticket.create", "support_ticket", ticket.id, ticket.subject)
    journey(db, ctx, ticket.lead_id, "support_ticket_opened", channel="support", metadata={
        "ticket_id": ticket.id,
        "subject": ticket.subject,
        "priority": ticket.priority.value,
    })
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(
    lead_id: str | None = None,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[SupportTicket]:
    query = select(SupportTicket).where(SupportTicket.tenant_id == ctx.tenant_id)
    if lead_id:
        tenant_entity(db, Lead, lead_id, ctx.tenant_id)
        query = query.where(SupportTicket.lead_id == lead_id)
    return list(db.scalars(query.order_by(SupportTicket.updated_at.desc()).limit(500)).all())


@router.patch("/tickets/{ticket_id}/status", response_model=TicketRead)
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> SupportTicket:
    ticket = tenant_entity(db, SupportTicket, ticket_id, ctx.tenant_id)
    ticket.status = payload.status
    audit(db, ctx, "ticket.status", "support_ticket", ticket.id, payload.status.value)
    journey(db, ctx, ticket.lead_id, f"support_ticket_{payload.status.value}", channel="support", metadata={
        "ticket_id": ticket.id,
        "subject": ticket.subject,
    })
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/reminders", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Reminder:
    if payload.lead_id:
        tenant_entity(db, Lead, payload.lead_id, ctx.tenant_id)
    reminder = Reminder(
        tenant_id=ctx.tenant_id,
        created_by_user_id=ctx.user_id,
        **payload.model_dump(),
    )
    db.add(reminder)
    db.flush()
    audit(db, ctx, "reminder.create", "reminder", reminder.id, reminder.title)
    journey(db, ctx, reminder.lead_id, "reminder_created", metadata={
        "reminder_id": reminder.id,
        "title": reminder.title,
        "due_at": reminder.due_at.isoformat(),
    })
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/reminders", response_model=list[ReminderRead])
def list_reminders(
    pending_only: bool = False,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[Reminder]:
    query = select(Reminder).where(Reminder.tenant_id == ctx.tenant_id)
    if pending_only:
        query = query.where(Reminder.status == ReminderStatus.pending)
    return list(db.scalars(query.order_by(Reminder.due_at.asc()).limit(500)).all())


@router.post("/reminders/{reminder_id}/complete", response_model=ReminderRead)
def complete_reminder(
    reminder_id: str,
    ctx: RequestContext = Depends(write_sales),
    db: Session = Depends(get_db),
) -> Reminder:
    reminder = tenant_entity(db, Reminder, reminder_id, ctx.tenant_id)
    if reminder.status != ReminderStatus.pending:
        raise HTTPException(status_code=409, detail="Reminder is not pending")
    reminder.status = ReminderStatus.completed
    reminder.completed_at = datetime.now(timezone.utc)
    audit(db, ctx, "reminder.complete", "reminder", reminder.id, reminder.title)
    journey(db, ctx, reminder.lead_id, "reminder_completed", metadata={"reminder_id": reminder.id})
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/leads/{lead_id}/timeline", response_model=list[TimelineItem])
def customer_timeline(
    lead_id: str,
    limit: int = Query(default=250, ge=1, le=1000),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[TimelineItem]:
    lead = tenant_entity(db, Lead, lead_id, ctx.tenant_id)
    items: list[TimelineItem] = []

    items.append(TimelineItem(
        id=f"lead:{lead.id}",
        kind="lead",
        title=f"Lead created · {lead.full_name}",
        channel=lead.source,
        occurred_at=lead.created_at,
        metadata={"status": lead.status.value, "phone": lead.phone, "source": lead.source},
    ))

    for event in db.scalars(select(CustomerJourneyEvent).where(
        CustomerJourneyEvent.tenant_id == ctx.tenant_id,
        CustomerJourneyEvent.lead_id == lead.id,
    )).all():
        try:
            metadata = json.loads(event.metadata_json or "{}")
        except (TypeError, ValueError, json.JSONDecodeError):
            metadata = {}
        items.append(TimelineItem(
            id=f"journey:{event.id}",
            kind=event.event_type,
            title=event.event_type.replace("_", " ").title(),
            channel=event.channel,
            occurred_at=event.occurred_at,
            metadata=metadata if isinstance(metadata, dict) else {},
        ))

    for appointment in db.scalars(select(Appointment).where(
        Appointment.tenant_id == ctx.tenant_id,
        Appointment.lead_id == lead.id,
    )).all():
        items.append(TimelineItem(
            id=f"appointment:{appointment.id}",
            kind="appointment",
            title="Viewing / appointment",
            channel="calendar",
            occurred_at=appointment.starts_at,
            metadata={"status": appointment.status, "project_id": appointment.project_id},
        ))

    for reservation in db.scalars(select(Reservation).where(
        Reservation.tenant_id == ctx.tenant_id,
        Reservation.lead_id == lead.id,
    )).all():
        items.append(TimelineItem(
            id=f"reservation:{reservation.id}",
            kind="reservation",
            title="Reservation",
            channel="sales",
            occurred_at=reservation.created_at,
            metadata={
                "status": reservation.status.value,
                "unit_id": reservation.unit_id,
                "amount": str(reservation.reservation_amount),
            },
        ))

    for contract in db.scalars(select(Contract).where(
        Contract.tenant_id == ctx.tenant_id,
        Contract.lead_id == lead.id,
    )).all():
        items.append(TimelineItem(
            id=f"contract:{contract.id}",
            kind="contract",
            title=f"Contract · {contract.contract_number}",
            channel="finance",
            occurred_at=contract.signed_at,
            metadata={
                "status": contract.status.value,
                "unit_id": contract.unit_id,
                "total_price": str(contract.total_price),
                "currency": contract.currency,
            },
        ))

    items.sort(key=lambda item: item.occurred_at, reverse=True)
    return items[:limit]
