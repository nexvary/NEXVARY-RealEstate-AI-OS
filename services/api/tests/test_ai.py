from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_grounded_sales_copilot_uses_inventory_and_knowledge(admin_headers):
    project = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"name": "Copilot Project", "city": "New Cairo"},
    )
    assert project.status_code == 201
    project_id = project.json()["id"]

    unit = client.post(
        "/api/v1/units",
        headers=admin_headers,
        json={
            "project_id": project_id,
            "code": "AI-301",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 155,
            "price": 4800000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201

    doc = client.post(
        "/api/v1/knowledge/documents",
        headers=admin_headers,
        json={
            "title": "Copilot Project brochure",
            "category": "brochure",
            "source_name": "copilot-project.pdf",
            "content": "Copilot Project in New Cairo includes a clubhouse, landscaped areas, and apartment buildings.",
        },
    )
    assert doc.status_code == 201

    response = client.post(
        "/api/v1/ai/sales/assist",
        headers=admin_headers,
        json={
            "question": "هل يوجد مشروع في القاهرة الجديدة به clubhouse؟",
            "city": "New Cairo",
            "max_price": 5000000,
            "bedrooms": 3,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "grounded-local-copilot"
    assert data["units"][0]["code"] == "AI-301"
    assert data["evidence"][0]["document_title"] == "Copilot Project brochure"
    assert "transactional_inventory" in data["grounding"]
