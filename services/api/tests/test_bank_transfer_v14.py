from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
PASSWORD = "TestPassword123!"


def platform_headers():
    response = client.post(
        "/api/v1/platform/auth/claim",
        json={
            "tenant_slug": "company-a",
            "email": "owner@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_invoice_and_bank(platform):
    bank = client.post(
        "/api/v1/platform/bank-accounts",
        headers=platform,
        json={
            "label": "NEXVARY EGP",
            "bank_name": "Example Bank",
            "account_name": "NEXVARY",
            "account_number": "0011223344",
            "iban": "EG12000100112233445566778899",
            "swift_code": "EXAMPLE1",
            "currency": "EGP",
            "instructions": "Write the invoice number in the transfer description.",
            "is_active": True,
            "is_default": True,
        },
    )
    assert bank.status_code == 201

    subscription = client.put(
        "/api/v1/platform/tenants/tenant-a/subscription",
        headers=platform,
        json={
            "plan": "professional",
            "status": "past_due",
            "billing_cycle": "monthly",
            "amount": 5000,
            "currency": "EGP",
            "apply_plan_limits": True,
        },
    )
    assert subscription.status_code == 200

    invoice = client.post(
        "/api/v1/platform/tenants/tenant-a/invoices",
        headers=platform,
        json={
            "subtotal": 5000,
            "tax_amount": 0,
            "currency": "EGP",
            "description": "Professional subscription renewal",
        },
    )
    assert invoice.status_code == 201
    return bank.json(), invoice.json()


def test_bank_transfer_requires_manual_verification_before_invoice_is_paid(admin_headers):
    platform = platform_headers()
    bank, invoice = create_invoice_and_bank(platform)

    accounts = client.get("/api/v1/billing/bank-accounts", headers=admin_headers)
    assert accounts.status_code == 200
    assert accounts.json()[0]["id"] == bank["id"]
    assert accounts.json()[0]["currency"] == "EGP"

    submitted = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/bank-transfer",
        headers=admin_headers,
        json={
            "bank_account_id": bank["id"],
            "amount": 5000,
            "currency": "EGP",
            "sender_name": "Company A",
            "sender_bank": "Sender Bank",
            "transfer_reference": "BANK-REF-10001",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
            "receipt_note": "Transfer completed from company account.",
        },
    )
    assert submitted.status_code == 201
    transfer = submitted.json()
    assert transfer["status"] == "pending"

    invoices = client.get("/api/v1/billing/invoices", headers=admin_headers)
    assert invoices.status_code == 200
    current = next(item for item in invoices.json() if item["id"] == invoice["id"])
    assert current["status"] == "pending_verification"
    assert current["paid_at"] is None

    approved = client.post(
        f"/api/v1/platform/bank-transfers/{transfer['id']}/approve",
        headers=platform,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["reviewed_by"]

    invoices = client.get("/api/v1/billing/invoices", headers=admin_headers)
    current = next(item for item in invoices.json() if item["id"] == invoice["id"])
    assert current["status"] == "paid"
    assert current["paid_at"] is not None

    subscription = client.get(
        "/api/v1/platform/tenants/tenant-a/subscription",
        headers=platform,
    )
    assert subscription.status_code == 200
    assert subscription.json()["status"] == "active"


def test_rejected_transfer_reopens_invoice_and_keeps_reason(admin_headers):
    platform = platform_headers()
    bank, invoice = create_invoice_and_bank(platform)

    submitted = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/bank-transfer",
        headers=admin_headers,
        json={
            "bank_account_id": bank["id"],
            "amount": 5000,
            "currency": "EGP",
            "sender_name": "Company A",
            "transfer_reference": "BANK-REF-REJECT",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert submitted.status_code == 201

    rejected = client.post(
        f"/api/v1/platform/bank-transfers/{submitted.json()['id']}/reject",
        headers=platform,
        json={"rejection_reason": "Reference not found on bank statement."},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["rejection_reason"] == "Reference not found on bank statement."

    invoices = client.get("/api/v1/billing/invoices", headers=admin_headers)
    current = next(item for item in invoices.json() if item["id"] == invoice["id"])
    assert current["status"] == "open"
    assert current["paid_at"] is None


def test_transfer_amount_and_currency_must_match_invoice(admin_headers):
    platform = platform_headers()
    bank, invoice = create_invoice_and_bank(platform)

    wrong_amount = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/bank-transfer",
        headers=admin_headers,
        json={
            "bank_account_id": bank["id"],
            "amount": 4900,
            "currency": "EGP",
            "sender_name": "Company A",
            "transfer_reference": "BANK-REF-WRONG-AMOUNT",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert wrong_amount.status_code == 422

    wrong_currency = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/bank-transfer",
        headers=admin_headers,
        json={
            "bank_account_id": bank["id"],
            "amount": 5000,
            "currency": "USD",
            "sender_name": "Company A",
            "transfer_reference": "BANK-REF-WRONG-CURRENCY",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert wrong_currency.status_code == 422


def test_bank_transfer_history_is_tenant_isolated(admin_headers, other_tenant_headers):
    platform = platform_headers()
    bank, invoice = create_invoice_and_bank(platform)

    submitted = client.post(
        f"/api/v1/billing/invoices/{invoice['id']}/bank-transfer",
        headers=admin_headers,
        json={
            "bank_account_id": bank["id"],
            "amount": 5000,
            "currency": "EGP",
            "sender_name": "Company A",
            "transfer_reference": "BANK-REF-ISOLATION",
            "transferred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert submitted.status_code == 201

    own = client.get("/api/v1/billing/bank-transfers", headers=admin_headers)
    assert own.status_code == 200
    assert any(item["id"] == submitted.json()["id"] for item in own.json())

    other = client.get("/api/v1/billing/bank-transfers", headers=other_tenant_headers)
    assert other.status_code == 200
    assert other.json() == []
