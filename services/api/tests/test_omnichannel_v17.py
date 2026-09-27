from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.commercial_models import WhatsAppChannel, WhatsAppChannelStatus
from app.db import SessionLocal
from app.integration_crypto import encrypt_secret_map
from app.main import app
from app.saas_models import TenantIntegration

client = TestClient(app)


def create_project_unit(headers):
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={"name": "Nile Residence", "city": "New Cairo", "developer": "NEX Developer"},
    )
    assert project.status_code == 201
    plan = client.post(
        "/api/v1/payment-plans",
        headers=headers,
        json={
            "project_id": project.json()["id"],
            "name": "20% over 8 years",
            "down_payment_percent": 20,
            "years": 8,
            "installment_frequency_months": 3,
        },
    )
    assert plan.status_code == 201
    unit = client.post(
        "/api/v1/units",
        headers=headers,
        json={
            "project_id": project.json()["id"],
            "payment_plan_id": plan.json()["id"],
            "code": "NR-A12",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 165,
            "price": 6500000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201
    media = client.post(
        "/api/v1/growth/media",
        headers=headers,
        json={
            "project_id": project.json()["id"],
            "unit_id": unit.json()["id"],
            "title": "NR-A12 Living Room",
            "media_type": "image",
            "url": "https://assets.example.test/nr-a12-living.jpg",
            "source_kind": "verified",
            "is_verified": True,
        },
    )
    assert media.status_code == 201
    return project.json(), unit.json()


def inbound(
    headers,
    external_id="wamid-001",
    campaign_id="cmp-001",
    *,
    ad_id="ad-001",
    project_id=None,
    unit_id=None,
):
    payload = {
        "channel": "whatsapp",
        "external_message_id": external_id,
        "external_contact": "201000000001",
        "display_name": "Customer One",
        "body": "عايز شقة 3 غرف في القاهرة الجديدة",
        "campaign_id": campaign_id,
        "ad_id": ad_id,
    }
    if project_id:
        payload["project_id"] = project_id
    if unit_id:
        payload["unit_id"] = unit_id
    response = client.post(
        "/api/v1/omnichannel/inbound",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201
    return response.json()


def test_inbound_dedupes_and_preserves_campaign_context(admin_headers):
    first = inbound(admin_headers)
    assert first["duplicate"] is False

    second = inbound(admin_headers)
    assert second["duplicate"] is True
    assert second["conversation_id"] == first["conversation_id"]
    assert second["message_id"] == first["message_id"]

    state = client.get(
        f"/api/v1/omnichannel/conversations/{first['conversation_id']}/sales-state",
        headers=admin_headers,
    )
    assert state.status_code == 200
    assert state.json()["campaign_id"] == "cmp-001"
    assert state.json()["ad_id"] == "ad-001"

    campaigns = client.get("/api/v1/omnichannel/attribution/campaigns", headers=admin_headers)
    assert campaigns.status_code == 200
    assert campaigns.json()[0]["campaign_id"] == "cmp-001"
    assert campaigns.json()[0]["events"]["conversation"] == 1



def test_whatsapp_ad_referral_creates_crm_lead_and_property_context(admin_headers):
    project, unit = create_project_unit(admin_headers)
    mapped = client.post(
        "/api/v1/property-sales/ad-referrals",
        headers=admin_headers,
        json={
            "channel": "whatsapp",
            "campaign_id": "meta-campaign-77",
            "ad_id": "meta-ad-77",
            "project_id": project["id"],
            "unit_id": unit["id"],
            "label": "NR A12 WhatsApp Ad",
            "source_url": "https://facebook.example.test/ad/77",
        },
    )
    assert mapped.status_code == 201

    received = inbound(
        admin_headers,
        external_id="wamid-referral-77",
        campaign_id=None,
        ad_id="meta-ad-77",
    )
    assert received["lead_id"]
    assert received["project_id"] == project["id"]
    assert received["unit_id"] == unit["id"]

    leads = client.get("/api/v1/leads", headers=admin_headers)
    assert leads.status_code == 200
    lead = next(item for item in leads.json() if item["id"] == received["lead_id"])
    assert lead["source"] == "whatsapp_ad"
    assert lead["preferred_city"] == "New Cairo"

    context = client.get(
        f"/api/v1/property-sales/conversations/{received['conversation_id']}/context",
        headers=admin_headers,
    )
    assert context.status_code == 200
    property_context = context.json()["context"]
    assert property_context["ad_id"] == "meta-ad-77"
    assert property_context["campaign_id"] == "meta-campaign-77"
    assert property_context["project_name"] == "Nile Residence"
    assert property_context["unit_code"] == "NR-A12"

def test_grounded_auto_reply_uses_live_inventory_and_voice_preference(admin_headers):
    project, unit = create_project_unit(admin_headers)
    received = inbound(
        admin_headers,
        external_id="wamid-grounded",
        project_id=project["id"],
        unit_id=unit["id"],
    )

    state = client.patch(
        f"/api/v1/omnichannel/conversations/{received['conversation_id']}/sales-state",
        headers=admin_headers,
        json={
            "reply_preference": "voice",
            "auto_reply_enabled": True,
            "journey_stage": "qualified",
            "lead_score": 88,
        },
    )
    assert state.status_code == 200
    assert state.json()["reply_preference"] == "voice"

    reply = client.post(
        f"/api/v1/omnichannel/conversations/{received['conversation_id']}/grounded-reply",
        headers=admin_headers,
        json={
            "question": "عايز شقة 3 غرف في القاهرة الجديدة",
            "city": "New Cairo",
            "bedrooms": 3,
            "source_confidence": 0.95,
        },
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["grounded"] is True
    assert body["requires_handoff"] is False
    assert body["approval_required"] is False
    assert body["outbox"]["status"] == "approved"
    assert body["units"][0]["code"] == "NR-A12"
    assert body["units"][0]["price"] == "6500000.00"
    assert body["units"][0]["payment_plan"]["years"] == 8
    assert body["units"][0]["payment_plan"]["down_payment_percent"] == "20.00"
    assert body["media"][0]["title"] == "NR-A12 Living Room"
    assert body["media"][0]["verified"] is True
    assert body["voice_plan"]["gender"] == "female"
    assert body["voice_plan"]["style"] == "professional"
    assert len(body["voice_plan"]["segments"]) <= 3

    queued = client.post(
        f"/api/v1/property-sales/conversations/{received['conversation_id']}/media-outbox",
        headers=admin_headers,
        json={"asset_ids": [body["media"][0]["id"]]},
    )
    assert queued.status_code == 201
    assert queued.json()[0]["kind"] == "image"
    assert queued.json()[0]["status"] == "approved"
    assert queued.json()[0]["grounded"] is True


def test_no_inventory_forces_handoff_and_human_approval(admin_headers):
    received = inbound(admin_headers, external_id="wamid-handoff")
    reply = client.post(
        f"/api/v1/omnichannel/conversations/{received['conversation_id']}/grounded-reply",
        headers=admin_headers,
        json={
            "question": "عايز فيلا 6 غرف في أسوان",
            "city": "Aswan",
            "bedrooms": 6,
            "unit_type": "villa",
            "source_confidence": 0.99,
        },
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["requires_handoff"] is True
    assert body["approval_required"] is True
    assert body["outbox"]["status"] == "pending_approval"

    tasks = client.get("/api/v1/tasks", headers=admin_headers)
    assert tasks.status_code == 200
    assert any(item["title"] == "Human handoff required" for item in tasks.json())


def test_outbox_approval_and_official_whatsapp_dispatch(admin_headers, monkeypatch):
    create_project_unit(admin_headers)
    received = inbound(admin_headers, external_id="wamid-dispatch")

    db = SessionLocal()
    integration = TenantIntegration(
        tenant_id="tenant-a",
        provider="whatsapp",
        display_name="WhatsApp Business",
        is_enabled=1,
        public_config_json="{}",
        encrypted_secret_json=encrypt_secret_map({"access_token": "secret-meta-token"}),
    )
    db.add(integration)
    db.flush()
    channel = WhatsAppChannel(
        tenant_id="tenant-a",
        integration_id=integration.id,
        display_name="Sales WhatsApp",
        phone_number_id="phone-number-123",
        waba_id="waba-123",
        business_phone="+201000000001",
        graph_api_version="v23.0",
        status=WhatsAppChannelStatus.ready,
        is_default=1,
    )
    db.add(channel)
    db.commit()
    channel_id = channel.id
    db.close()

    prepared = client.post(
        f"/api/v1/omnichannel/conversations/{received['conversation_id']}/grounded-reply",
        headers=admin_headers,
        json={
            "question": "شقة 3 غرف",
            "bedrooms": 3,
            "source_confidence": 0.95,
            "channel_id": channel_id,
        },
    )
    assert prepared.status_code == 200
    assert prepared.json()["outbox"]["status"] == "pending_approval"
    outbox_id = prepared.json()["outbox"]["id"]

    approved = client.post(
        f"/api/v1/omnichannel/outbox/{outbox_id}/approve",
        headers=admin_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    captured = {}

    class FakeResponse:
        status_code = 200
        content = b'{"messages":[{"id":"wamid.sent.001"}]}'

        def raise_for_status(self):
            return None

        def json(self):
            return {"messages": [{"id": "wamid.sent.001"}]}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("app.omnichannel_api.httpx.post", fake_post)

    sent = client.post(
        f"/api/v1/omnichannel/outbox/{outbox_id}/dispatch",
        headers=admin_headers,
    )
    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"
    assert sent.json()["external_message_id"] == "wamid.sent.001"
    assert captured["url"] == "https://graph.facebook.com/v23.0/phone-number-123/messages"
    assert captured["headers"]["Authorization"] == "Bearer secret-meta-token"
    assert captured["json"]["to"] == "201000000001"
    assert captured["json"]["type"] == "text"

    messages = client.get(
        f"/api/v1/inbox/conversations/{received['conversation_id']}/messages",
        headers=admin_headers,
    )
    assert messages.status_code == 200
    assert any(item["direction"] == "outbound" for item in messages.json())


def test_attribution_is_tenant_isolated(admin_headers, other_tenant_headers):
    received = inbound(admin_headers, external_id="wamid-attr", campaign_id="campaign-realestate")
    event = client.post(
        "/api/v1/omnichannel/attribution/events",
        headers=admin_headers,
        json={
            "campaign_id": "campaign-realestate",
            "ad_id": "ad-realestate",
            "event_type": "revenue",
            "value": 125000,
            "currency": "EGP",
            "conversation_id": received["conversation_id"],
        },
    )
    assert event.status_code == 201

    own = client.get("/api/v1/omnichannel/attribution/campaigns", headers=admin_headers)
    assert own.status_code == 200
    summary = next(item for item in own.json() if item["campaign_id"] == "campaign-realestate")
    assert summary["events"]["conversation"] == 1
    assert summary["events"]["revenue"] == 1
    assert Decimal(summary["revenue"]) == Decimal("125000.00")

    other = client.get("/api/v1/omnichannel/attribution/campaigns", headers=other_tenant_headers)
    assert other.status_code == 200
    assert other.json() == []
