import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.commercial_models import SaaSSubscription
from app.db import SessionLocal
from app.main import app
import app.production_api as production_api

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


def test_billing_reconcile_marks_overdue_invoice_and_past_due_subscription():
    headers = platform_headers()
    subscription = client.put(
        "/api/v1/platform/tenants/tenant-a/subscription",
        headers=headers,
        json={
            "plan": "professional",
            "status": "active",
            "billing_cycle": "monthly",
            "amount": 149,
            "currency": "USD",
            "apply_plan_limits": True,
        },
    )
    assert subscription.status_code == 200

    due_at = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    invoice = client.post(
        "/api/v1/platform/tenants/tenant-a/invoices",
        headers=headers,
        json={
            "subtotal": 149,
            "tax_amount": 0,
            "currency": "USD",
            "due_at": due_at,
            "description": "Past due subscription invoice",
        },
    )
    assert invoice.status_code == 201

    db = SessionLocal()
    try:
        row = db.get(SaaSSubscription, subscription.json()["id"])
        assert row is not None
        row.current_period_end = datetime.now(timezone.utc) - timedelta(days=1)
        db.commit()
    finally:
        db.close()

    reconciled = client.post("/api/v1/platform/billing/reconcile", headers=headers)
    assert reconciled.status_code == 200
    body = reconciled.json()
    assert body["invoices_marked_overdue"] == 1
    assert body["subscriptions_marked_past_due"] == 1

    summary = client.get("/api/v1/platform/billing/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["invoices"]["overdue"] == 1
    assert summary.json()["subscriptions"]["past_due"] == 1


class FakeMetaResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"messaging_product": "whatsapp", "messages": [{"id": "wamid.outbound-1"}]}


def test_live_whatsapp_send_verify_webhook_and_receive(admin_headers, monkeypatch):
    created = client.post(
        "/api/v1/whatsapp/channels",
        headers=admin_headers,
        json={
            "display_name": "Live Sales WhatsApp",
            "phone_number_id": "phone-live-123",
            "waba_id": "waba-live-456",
            "business_phone": "+201000000001",
            "graph_api_version": "v23.0",
            "access_token": "live-access-token",
            "app_secret": "meta-app-secret",
            "is_default": True,
            "enabled": True,
        },
    )
    assert created.status_code == 201
    channel_id = created.json()["id"]

    webhook_config = client.put(
        f"/api/v1/whatsapp/channels/{channel_id}/webhook-config",
        headers=admin_headers,
        json={"verify_token": "verify-token-123456"},
    )
    assert webhook_config.status_code == 200
    assert webhook_config.json()["secret_values_exposed"] is False

    verified = client.get(
        f"/api/v1/whatsapp/webhook/{channel_id}",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-token-123456",
            "hub.challenge": "challenge-ok",
        },
    )
    assert verified.status_code == 200
    assert verified.text == "challenge-ok"

    monkeypatch.setattr(production_api.httpx, "post", lambda *args, **kwargs: FakeMetaResponse())
    sent = client.post(
        f"/api/v1/whatsapp/channels/{channel_id}/messages",
        headers=admin_headers,
        json={
            "to": "201111111111",
            "message_type": "text",
            "text": "Hello from the live WhatsApp API",
        },
    )
    assert sent.status_code == 201
    assert sent.json()["status"] == "accepted"
    assert sent.json()["external_message_id"] == "wamid.outbound-1"

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "waba-live-456",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": "phone-live-123"},
                            "messages": [
                                {
                                    "from": "201222222222",
                                    "id": "wamid.inbound-1",
                                    "timestamp": "1790459000",
                                    "type": "text",
                                    "text": {"body": "How much is this unit?"},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(b"meta-app-secret", raw, hashlib.sha256).hexdigest()
    inbound = client.post(
        f"/api/v1/whatsapp/webhook/{channel_id}",
        content=raw,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": f"sha256={signature}",
        },
    )
    assert inbound.status_code == 200
    assert inbound.json()["messages_received"] == 1

    duplicate = client.post(
        f"/api/v1/whatsapp/webhook/{channel_id}",
        content=raw,
        headers={
            "content-type": "application/json",
            "x-hub-signature-256": f"sha256={signature}",
        },
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["status"] == "duplicate"

    messages = client.get(
        f"/api/v1/whatsapp/messages?channel_id={channel_id}",
        headers=admin_headers,
    )
    assert messages.status_code == 200
    data = messages.json()
    assert len(data) == 2
    assert {item["direction"] for item in data} == {"inbound", "outbound"}
    assert next(item for item in data if item["direction"] == "inbound")["status"] == "received"
