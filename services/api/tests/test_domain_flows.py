from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_inventory(admin_headers):
    project = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={
            "name": "NEXVARY Heights",
            "city": "New Cairo",
            "developer": "NEXVARY Development",
        },
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    building = client.post(
        "/api/v1/buildings",
        headers=admin_headers,
        json={"project_id": project_id, "code": "A", "name": "Tower A", "floors": 20},
    )
    assert building.status_code == 201

    plan = client.post(
        "/api/v1/payment-plans",
        headers=admin_headers,
        json={
            "project_id": project_id,
            "name": "10% over 8 years",
            "down_payment_percent": 10,
            "years": 8,
            "installment_frequency_months": 3,
        },
    )
    assert plan.status_code == 201

    unit = client.post(
        "/api/v1/units",
        headers=admin_headers,
        json={
            "project_id": project_id,
            "building_id": building.json()["id"],
            "payment_plan_id": plan.json()["id"],
            "code": "A-1204",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 165,
            "price": 4900000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201
    return project.json(), plan.json(), unit.json()


def test_role_policy_rejects_viewer_for_inventory(viewer_headers):
    response = client.post(
        "/api/v1/projects",
        headers=viewer_headers,
        json={"name": "Forbidden Project", "city": "Cairo"},
    )
    assert response.status_code == 403


def test_inventory_search_is_tenant_scoped(admin_headers, other_tenant_headers):
    _, _, unit = create_inventory(admin_headers)

    own = client.get(
        "/api/v1/units/search?city=New%20Cairo&max_price=5000000&bedrooms=3",
        headers=admin_headers,
    )
    assert own.status_code == 200
    assert [item["id"] for item in own.json()] == [unit["id"]]

    other = client.get("/api/v1/units/search?city=New%20Cairo", headers=other_tenant_headers)
    assert other.status_code == 200
    assert other.json() == []


def test_sales_pipeline_and_appointment(admin_headers, sales_headers):
    project, _, _ = create_inventory(admin_headers)

    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={
            "full_name": "Ahmed Mahmoud",
            "phone": "01000000001",
            "source": "whatsapp",
            "preferred_city": "New Cairo",
            "budget": 5000000,
            "bedrooms": 3,
            "notes": "Ready for a viewing this weekend and has a confirmed down payment.",
        },
    )
    assert lead.status_code == 201
    assert lead.json()["score"] >= 70

    updated = client.patch(
        f"/api/v1/leads/{lead.json()['id']}",
        headers=sales_headers,
        json={"status": "qualified"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "qualified"

    pipeline = client.get("/api/v1/pipeline", headers=sales_headers)
    assert pipeline.status_code == 200
    assert pipeline.json()["qualified"] == 1

    starts_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    appointment = client.post(
        "/api/v1/appointments",
        headers=sales_headers,
        json={
            "lead_id": lead.json()["id"],
            "project_id": project["id"],
            "starts_at": starts_at,
            "notes": "Site viewing",
        },
    )
    assert appointment.status_code == 201


def test_reservation_locks_unit_and_cancel_releases_it(admin_headers, sales_headers):
    _, plan, unit = create_inventory(admin_headers)
    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={"full_name": "Sara Ali", "phone": "01111111111", "source": "website"},
    )
    assert lead.status_code == 201

    reservation = client.post(
        "/api/v1/reservations",
        headers=sales_headers,
        json={
            "lead_id": lead.json()["id"],
            "unit_id": unit["id"],
            "payment_plan_id": plan["id"],
            "reservation_amount": 50000,
        },
    )
    assert reservation.status_code == 201
    assert reservation.json()["status"] == "active"

    duplicate = client.post(
        "/api/v1/reservations",
        headers=sales_headers,
        json={
            "lead_id": lead.json()["id"],
            "unit_id": unit["id"],
            "reservation_amount": 50000,
        },
    )
    assert duplicate.status_code == 409

    available_after_reserve = client.get("/api/v1/units/search", headers=sales_headers)
    assert all(item["id"] != unit["id"] for item in available_after_reserve.json())

    cancelled = client.post(
        f"/api/v1/reservations/{reservation.json()['id']}/cancel",
        headers=sales_headers,
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    available_after_cancel = client.get("/api/v1/units/search", headers=sales_headers)
    assert any(item["id"] == unit["id"] for item in available_after_cancel.json())


def test_cross_tenant_references_are_rejected(admin_headers, other_tenant_headers):
    _, _, unit = create_inventory(admin_headers)

    other_lead = client.post(
        "/api/v1/leads",
        headers=other_tenant_headers,
        json={"full_name": "Other Tenant", "phone": "01222222222"},
    )
    assert other_lead.status_code == 201

    response = client.post(
        "/api/v1/reservations",
        headers=other_tenant_headers,
        json={
            "lead_id": other_lead.json()["id"],
            "unit_id": unit["id"],
            "reservation_amount": 1000,
        },
    )
    assert response.status_code == 404


def test_overview_tracks_active_reservations(admin_headers, sales_headers):
    _, _, unit = create_inventory(admin_headers)
    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={"full_name": "Lead One", "phone": "01033333333"},
    )
    assert lead.status_code == 201

    reservation = client.post(
        "/api/v1/reservations",
        headers=sales_headers,
        json={"lead_id": lead.json()["id"], "unit_id": unit["id"], "reservation_amount": 10000},
    )
    assert reservation.status_code == 201

    overview = client.get("/api/v1/overview", headers=admin_headers)
    assert overview.status_code == 200
    data = overview.json()
    assert data["leads_total"] == 1
    assert data["active_reservations"] == 1
    assert data["units_available"] == 0
