from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def prepare_sale(admin_headers, sales_headers):
    project = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"name": "Finance Test Project", "city": "Cairo"},
    )
    assert project.status_code == 201

    unit = client.post(
        "/api/v1/units",
        headers=admin_headers,
        json={
            "project_id": project.json()["id"],
            "code": "FIN-01",
            "unit_type": "apartment",
            "bedrooms": 2,
            "area_sqm": 120,
            "price": 2000000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201

    lead = client.post(
        "/api/v1/leads",
        headers=sales_headers,
        json={"full_name": "Contract Client", "phone": "01099999999"},
    )
    assert lead.status_code == 201

    reservation = client.post(
        "/api/v1/reservations",
        headers=sales_headers,
        json={
            "lead_id": lead.json()["id"],
            "unit_id": unit.json()["id"],
            "reservation_amount": 200000,
        },
    )
    assert reservation.status_code == 201
    return unit.json(), reservation.json()


def test_contract_schedule_payment_and_commission(admin_headers, sales_headers):
    unit, reservation = prepare_sale(admin_headers, sales_headers)

    contract = client.post(
        f"/api/v1/contracts/from-reservation/{reservation['id']}",
        headers=sales_headers,
        json={"contract_number": "CNT-2026-001"},
    )
    assert contract.status_code == 201
    contract_data = contract.json()
    assert contract_data["total_price"] == "2000000.00"

    available = client.get("/api/v1/units/search", headers=admin_headers)
    assert all(item["id"] != unit["id"] for item in available.json())

    first_due = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    schedule = client.post(
        f"/api/v1/contracts/{contract_data['id']}/schedule",
        headers=sales_headers,
        json={"first_due_at": first_due, "installment_count": 6, "frequency_months": 1},
    )
    assert schedule.status_code == 201
    items = schedule.json()
    assert len(items) == 6
    total = sum(float(item["amount"]) for item in items)
    assert round(total, 2) == 1800000.00

    paid = client.post(
        f"/api/v1/installments/{items[0]['id']}/pay",
        headers=sales_headers,
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    commission = client.post(
        f"/api/v1/contracts/{contract_data['id']}/commissions",
        headers=sales_headers,
        json={"broker_name": "Broker One", "rate_percent": 2.5},
    )
    assert commission.status_code == 201
    assert commission.json()["amount"] == "50000.00"

    paid_commission = client.post(
        f"/api/v1/commissions/{commission.json()['id']}/pay",
        headers=sales_headers,
    )
    assert paid_commission.status_code == 200
    assert paid_commission.json()["status"] == "paid"
