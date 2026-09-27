from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def prepare_entities(admin_headers, sales_headers):
    project = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"name": "Enterprise CRM Project", "city": "Cairo"},
    )
    assert project.status_code == 201

    unit = client.post(
        "/api/v1/units",
        headers=admin_headers,
        json={
            "project_id": project.json()["id"],
            "code": "CRM-01",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 155,
            "price": 3200000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201

    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={
            "full_name": "Enterprise Customer",
            "phone": "01022223333",
            "email": "enterprise@example.com",
            "source": "facebook",
            "budget": 4000000,
        },
    )
    assert lead.status_code == 201
    return project.json(), unit.json(), lead.json()


def test_enterprise_crm_flow_and_universal_timeline(admin_headers, sales_headers, other_tenant_headers):
    project, unit, lead = prepare_entities(admin_headers, sales_headers)

    proposal = client.post(
        "/api/v1/enterprise-crm/proposals",
        headers=sales_headers,
        json={
            "lead_id": lead["id"],
            "unit_id": unit["id"],
            "proposal_number": "PROP-2026-001",
            "title": "Apartment CRM-01 offer",
            "amount": 3200000,
            "currency": "EGP",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        },
    )
    assert proposal.status_code == 201
    assert proposal.json()["status"] == "draft"

    accepted = client.patch(
        f"/api/v1/enterprise-crm/proposals/{proposal.json()['id']}/status",
        headers=sales_headers,
        json={"status": "accepted"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    invoice = client.post(
        "/api/v1/enterprise-crm/invoices",
        headers=sales_headers,
        json={
            "lead_id": lead["id"],
            "invoice_number": "INV-2026-001",
            "title": "Reservation and first payment",
            "total_amount": 500000,
            "currency": "EGP",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat(),
        },
    )
    assert invoice.status_code == 201
    assert invoice.json()["status"] == "issued"

    first_payment = client.post(
        f"/api/v1/enterprise-crm/invoices/{invoice.json()['id']}/payments",
        headers=sales_headers,
        json={
            "amount": 200000,
            "method": "bank_transfer",
            "reference": "BANK-REF-1",
        },
    )
    assert first_payment.status_code == 201

    invoices = client.get("/api/v1/enterprise-crm/invoices", headers=sales_headers)
    assert invoices.status_code == 200
    current = next(row for row in invoices.json() if row["id"] == invoice.json()["id"])
    assert current["status"] == "partial"
    assert current["paid_amount"] == "200000.00"

    second_payment = client.post(
        f"/api/v1/enterprise-crm/invoices/{invoice.json()['id']}/payments",
        headers=sales_headers,
        json={
            "amount": 300000,
            "method": "cash",
            "reference": "CASH-001",
        },
    )
    assert second_payment.status_code == 201

    invoices = client.get("/api/v1/enterprise-crm/invoices", headers=sales_headers)
    current = next(row for row in invoices.json() if row["id"] == invoice.json()["id"])
    assert current["status"] == "paid"
    assert current["paid_amount"] == "500000.00"

    ticket = client.post(
        "/api/v1/enterprise-crm/tickets",
        headers=sales_headers,
        json={
            "lead_id": lead["id"],
            "subject": "Finishing clarification",
            "description": "Customer requested clarification about finishing package.",
            "priority": "high",
        },
    )
    assert ticket.status_code == 201
    assert ticket.json()["status"] == "open"

    ticket_done = client.patch(
        f"/api/v1/enterprise-crm/tickets/{ticket.json()['id']}/status",
        headers=sales_headers,
        json={"status": "resolved"},
    )
    assert ticket_done.status_code == 200
    assert ticket_done.json()["status"] == "resolved"

    reminder = client.post(
        "/api/v1/enterprise-crm/reminders",
        headers=sales_headers,
        json={
            "lead_id": lead["id"],
            "entity_type": "proposal",
            "entity_id": proposal.json()["id"],
            "title": "Follow up after proposal",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )
    assert reminder.status_code == 201

    complete = client.post(
        f"/api/v1/enterprise-crm/reminders/{reminder.json()['id']}/complete",
        headers=sales_headers,
    )
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"

    expense = client.post(
        "/api/v1/enterprise-crm/expenses",
        headers=sales_headers,
        json={
            "project_id": project["id"],
            "category": "marketing",
            "description": "Campaign landing page production",
            "amount": 12500,
            "currency": "EGP",
        },
    )
    assert expense.status_code == 201

    summary = client.get("/api/v1/enterprise-crm/summary", headers=admin_headers)
    assert summary.status_code == 200
    data = summary.json()
    assert data["proposals_accepted"] == 1
    assert data["invoices_open"] == 0
    assert data["receivables"] == "0"
    assert data["payments_total"] == "500000.00"
    assert data["expenses_total"] == "12500.00"
    assert data["tickets_open"] == 0
    assert data["reminders_pending"] == 0

    timeline = client.get(
        f"/api/v1/enterprise-crm/leads/{lead['id']}/timeline",
        headers=sales_headers,
    )
    assert timeline.status_code == 200
    kinds = {row["kind"] for row in timeline.json()}
    assert "lead" in kinds
    assert "proposal_created" in kinds
    assert "proposal_accepted" in kinds
    assert "invoice_issued" in kinds
    assert "payment_received" in kinds
    assert "support_ticket_opened" in kinds
    assert "support_ticket_resolved" in kinds
    assert "reminder_created" in kinds
    assert "reminder_completed" in kinds

    isolated = client.get(
        f"/api/v1/enterprise-crm/leads/{lead['id']}/timeline",
        headers=other_tenant_headers,
    )
    assert isolated.status_code == 404


def test_enterprise_crm_rejects_overpayment(admin_headers, sales_headers):
    _, _, lead = prepare_entities(admin_headers, sales_headers)
    invoice = client.post(
        "/api/v1/enterprise-crm/invoices",
        headers=sales_headers,
        json={
            "lead_id": lead["id"],
            "invoice_number": "INV-OVERPAY",
            "title": "Test invoice",
            "total_amount": 1000,
            "currency": "EGP",
        },
    )
    assert invoice.status_code == 201

    payment = client.post(
        f"/api/v1/enterprise-crm/invoices/{invoice.json()['id']}/payments",
        headers=sales_headers,
        json={"amount": 1001, "method": "cash"},
    )
    assert payment.status_code == 409
    assert "exceeds" in payment.json()["detail"].lower()
