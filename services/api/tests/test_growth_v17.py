from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def prepare_sale(headers):
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Growth Towers",
            "city": "New Cairo",
            "developer": "Growth Developer",
            "description": "Verified development information.",
        },
    )
    assert project.status_code == 201

    unit = client.post(
        "/api/v1/units",
        headers=headers,
        json={
            "project_id": project.json()["id"],
            "code": "G-101",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 160,
            "price": 6000000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201

    lead = client.post(
        "/api/v1/leads",
        headers=headers,
        json={
            "full_name": "Campaign Buyer",
            "phone": "01010101010",
            "source": "facebook",
            "preferred_city": "New Cairo",
            "budget": 7000000,
            "bedrooms": 3,
        },
    )
    assert lead.status_code == 201
    return project.json(), unit.json(), lead.json()


def test_campaign_journey_and_last_touch_revenue_attribution(admin_headers):
    project, unit, lead = prepare_sale(admin_headers)

    campaign = client.post(
        "/api/v1/growth/campaigns",
        headers=admin_headers,
        json={
            "name": "New Cairo Leads",
            "channel": "facebook",
            "objective": "Qualified leads",
            "status": "active",
            "budget": 2000,
            "spend": 1000,
            "currency": "EGP",
            "utm_source": "facebook",
            "utm_medium": "paid-social",
            "utm_campaign": "new-cairo-leads",
        },
    )
    assert campaign.status_code == 201

    touch = client.post(
        "/api/v1/growth/journeys/events",
        headers=admin_headers,
        json={
            "lead_id": lead["id"],
            "campaign_id": campaign.json()["id"],
            "event_type": "campaign_touch",
            "channel": "facebook",
            "metadata": {"creative": "video-01"},
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert touch.status_code == 201

    reservation = client.post(
        "/api/v1/reservations",
        headers=admin_headers,
        json={
            "lead_id": lead["id"],
            "unit_id": unit["id"],
            "reservation_amount": 100000,
        },
    )
    assert reservation.status_code == 201

    contract = client.post(
        f"/api/v1/contracts/from-reservation/{reservation.json()['id']}",
        headers=admin_headers,
        json={"contract_number": "GR-0001"},
    )
    assert contract.status_code == 201

    journey = client.get(f"/api/v1/growth/journeys/{lead['id']}", headers=admin_headers)
    assert journey.status_code == 200
    types = [item["event_type"] for item in journey.json()]
    assert "lead_created" in types
    assert "campaign_touch" in types
    assert "reservation_created" in types
    assert "deal_won" in types

    attribution = client.get("/api/v1/growth/attribution/campaigns", headers=admin_headers)
    assert attribution.status_code == 200
    row = next(item for item in attribution.json() if item["campaign_id"] == campaign.json()["id"])
    assert row["leads_touched"] == 1
    assert row["contracts_last_touch"] == 1
    assert row["revenue_last_touch"] == "6000000.00"
    assert row["cost_per_lead"] == "1000.00"
    assert row["roas_last_touch"] == "6000.00"


def test_audience_360_preview_filters_real_leads(admin_headers):
    _, _, lead = prepare_sale(admin_headers)

    segment = client.post(
        "/api/v1/growth/audiences",
        headers=admin_headers,
        json={
            "name": "New Cairo Facebook",
            "description": "High-intent Facebook leads",
            "rules": {
                "sources": ["facebook"],
                "statuses": ["new"],
                "min_score": 0,
                "preferred_city": "New Cairo",
                "min_budget": 5000000,
                "max_budget": 8000000,
            },
        },
    )
    assert segment.status_code == 201

    preview = client.get(
        f"/api/v1/growth/audiences/{segment.json()['id']}/preview",
        headers=admin_headers,
    )
    assert preview.status_code == 200
    assert preview.json()["count"] == 1
    assert preview.json()["leads"][0]["id"] == lead["id"]


def test_verified_property_media_flows_into_grounded_sales_copilot(admin_headers):
    project, unit, _ = prepare_sale(admin_headers)

    media = client.post(
        "/api/v1/growth/media",
        headers=admin_headers,
        json={
            "project_id": project["id"],
            "unit_id": unit["id"],
            "title": "Actual living room video",
            "media_type": "video",
            "url": "https://media.example.test/g-101-living-room.mp4",
            "tags": ["living-room", "actual-footage"],
            "source_kind": "verified",
            "is_verified": True,
        },
    )
    assert media.status_code == 201

    result = client.post(
        "/api/v1/ai/sales/assist",
        headers=admin_headers,
        json={
            "question": "أريد شقة 3 غرف في القاهرة الجديدة",
            "city": "New Cairo",
            "bedrooms": 3,
            "max_price": 7000000,
        },
    )
    assert result.status_code == 200
    body = result.json()
    assert body["units"][0]["id"] == unit["id"]
    assert body["media"][0]["id"] == media.json()["id"]
    assert body["media"][0]["verified"] is True
    assert "tenant_scoped_media" in body["grounding"]


def test_playbooks_feedback_and_tenant_isolation(admin_headers, other_tenant_headers):
    playbook = client.post(
        "/api/v1/growth/playbooks",
        headers=admin_headers,
        json={
            "name": "Viewing Follow-up",
            "description": "Standardized sales follow-up after a viewing.",
            "trigger_stage": "viewing",
            "steps": [
                "Confirm the viewed unit.",
                "Ask for objections.",
                "Send verified media if requested.",
                "Create the next follow-up task.",
            ],
        },
    )
    assert playbook.status_code == 201

    feedback = client.post(
        "/api/v1/growth/feedback",
        headers=admin_headers,
        json={
            "channel": "whatsapp",
            "category": "sales_experience",
            "rating": 5,
            "comment": "The viewing explanation was clear.",
        },
    )
    assert feedback.status_code == 201

    summary = client.get("/api/v1/growth/feedback/summary", headers=admin_headers)
    assert summary.status_code == 200
    assert summary.json()["total"] == 1
    assert summary.json()["average_rating"] == 5.0

    other_campaigns = client.get("/api/v1/growth/campaigns", headers=other_tenant_headers)
    other_media = client.get("/api/v1/growth/media", headers=other_tenant_headers)
    other_playbooks = client.get("/api/v1/growth/playbooks", headers=other_tenant_headers)
    other_feedback = client.get("/api/v1/growth/feedback", headers=other_tenant_headers)
    assert other_campaigns.json() == []
    assert other_media.json() == []
    assert other_playbooks.json() == []
    assert other_feedback.json() == []
