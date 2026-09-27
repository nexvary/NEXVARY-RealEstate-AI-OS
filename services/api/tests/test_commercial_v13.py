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


def test_subscription_invoice_and_payment_flow():
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
    assert subscription.json()["plan"] == "professional"
    assert subscription.json()["amount"] == "149.00"

    invoice = client.post(
        "/api/v1/platform/tenants/tenant-a/invoices",
        headers=headers,
        json={
            "subtotal": 149,
            "tax_amount": 20,
            "currency": "USD",
            "description": "Professional monthly subscription",
        },
    )
    assert invoice.status_code == 201
    assert invoice.json()["total"] == "169.00"
    assert invoice.json()["status"] == "open"

    paid = client.post(
        f"/api/v1/platform/invoices/{invoice.json()['id']}/pay",
        headers=headers,
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert paid.json()["paid_at"] is not None


def test_template_provisions_complete_tenant_with_subscription_and_integrations():
    headers = platform_headers()

    template = client.post(
        "/api/v1/platform/templates",
        headers=headers,
        json={
            "name": "Real Estate Pro",
            "description": "Commercial tenant template",
            "plan": "professional",
            "primary_color": "#123456",
            "powered_by_nexvary": True,
            "feature_flags": {"seo": True, "whatsapp": True, "ai_sales": True},
            "integration_providers": ["whatsapp", "google-search-console", "openai"],
            "subscription_amount": 199,
            "subscription_currency": "USD",
            "billing_cycle": "monthly",
        },
    )
    assert template.status_code == 201
    template_id = template.json()["id"]

    provisioned = client.post(
        f"/api/v1/platform/templates/{template_id}/provision",
        headers=headers,
        json={
            "company_name": "Atlas Commercial Realty",
            "company_slug": "atlas-commercial",
            "brand_name": "ATLAS",
            "owner_name": "Atlas Owner",
            "owner_email": "owner@atlas-commercial.test",
            "owner_password": "AtlasCommercial123!",
            "custom_domain": "crm.atlas-commercial.test",
            "contact_email": "sales@atlas-commercial.test",
            "website_url": "https://atlas-commercial.test",
        },
    )
    assert provisioned.status_code == 201
    body = provisioned.json()
    assert body["company_slug"] == "atlas-commercial"
    assert body["integrations_created"] == ["whatsapp", "google-search-console", "openai"]

    tenants = client.get("/api/v1/platform/tenants", headers=headers)
    assert tenants.status_code == 200
    atlas = next(item for item in tenants.json() if item["slug"] == "atlas-commercial")
    assert atlas["brand_name"] == "ATLAS"
    assert atlas["custom_domain"] == "crm.atlas-commercial.test"
    assert atlas["max_units"] == 5000

    subscription = client.get(
        f"/api/v1/platform/tenants/{atlas['id']}/subscription",
        headers=headers,
    )
    assert subscription.status_code == 200
    assert subscription.json()["amount"] == "199.00"


def test_whatsapp_channel_is_tenant_scoped_and_secrets_are_not_returned(admin_headers, other_tenant_headers):
    created = client.post(
        "/api/v1/whatsapp/channels",
        headers=admin_headers,
        json={
            "display_name": "Sales WhatsApp",
            "phone_number_id": "phone-123",
            "waba_id": "waba-456",
            "business_phone": "+201000000000",
            "graph_api_version": "v23.0",
            "access_token": "secret-access-token",
            "app_secret": "secret-app-value",
            "is_default": True,
            "enabled": True,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["status"] == "ready"
    assert body["is_default"] is True
    assert sorted(body["configured_secret_keys"]) == ["access_token", "app_secret"]
    assert "secret-access-token" not in created.text

    readiness = client.get(
        f"/api/v1/whatsapp/channels/{body['id']}/readiness",
        headers=admin_headers,
    )
    assert readiness.status_code == 200
    assert readiness.json()["ready"] is True
    assert readiness.json()["secret_values_exposed"] is False

    isolated = client.get("/api/v1/whatsapp/channels", headers=other_tenant_headers)
    assert isolated.status_code == 200
    assert isolated.json() == []


def prepare_real_estate_data(headers):
    project = client.post(
        "/api/v1/projects",
        headers=headers,
        json={
            "name": "Cairo Gardens",
            "city": "New Cairo",
            "developer": "Example Developer",
            "description": "Residential project with documented project information.",
        },
    )
    assert project.status_code == 201

    unit = client.post(
        "/api/v1/units",
        headers=headers,
        json={
            "project_id": project.json()["id"],
            "code": "A-101",
            "unit_type": "apartment",
            "bedrooms": 3,
            "area_sqm": 150,
            "price": 5000000,
            "currency": "EGP",
        },
    )
    assert unit.status_code == 201

    seo = client.post(
        "/api/v1/seo/projects",
        headers=headers,
        json={"name": "Company Website", "site_url": "https://example.com"},
    )
    assert seo.status_code == 201
    return project.json(), unit.json(), seo.json()


def test_real_estate_seo_pages_are_generated_from_transactional_data(admin_headers):
    project, unit, seo = prepare_real_estate_data(admin_headers)

    sync = client.post(
        f"/api/v1/seo/real-estate/projects/{project['id']}/sync-all?seo_project_id={seo['id']}",
        headers=admin_headers,
    )
    assert sync.status_code == 200
    assert sync.json()["unit_pages"] == 1
    assert sync.json()["hallucinated_fields"] == 0
    assert sync.json()["source"] == "transactional_database"

    pages = client.get(
        f"/api/v1/seo/real-estate/pages?seo_project_id={seo['id']}",
        headers=admin_headers,
    )
    assert pages.status_code == 200
    data = pages.json()
    assert len(data) == 2

    project_page = next(item for item in data if item["entity_type"] == "project")
    unit_page = next(item for item in data if item["entity_type"] == "unit")

    assert "Cairo Gardens" in project_page["title"]
    assert project_page["body"]["developer"] == "Example Developer"
    assert unit_page["body"]["unit_code"] == "A-101"
    assert unit_page["body"]["price"] == "5000000.00"
    assert unit_page["body"]["availability"] == "available"
    assert unit_page["structured_data"]["mainEntity"]["price"] == "5000000.00"

    # Change transactional inventory, regenerate, and verify the SEO output follows the DB.
    reservation_lead = client.post(
        "/api/v1/leads",
        headers=admin_headers,
        json={"full_name": "Buyer", "phone": "01000000001"},
    )
    assert reservation_lead.status_code == 201
    reservation = client.post(
        "/api/v1/reservations",
        headers=admin_headers,
        json={
            "lead_id": reservation_lead.json()["id"],
            "unit_id": unit["id"],
            "reservation_amount": 100000,
        },
    )
    assert reservation.status_code == 201

    refreshed = client.post(
        f"/api/v1/seo/real-estate/units/{unit['id']}/generate?seo_project_id={seo['id']}",
        headers=admin_headers,
    )
    assert refreshed.status_code == 200
    assert refreshed.json()["body"]["availability"] == "reserved"
    assert refreshed.json()["structured_data"]["mainEntity"]["availability"] == "https://schema.org/SoldOut"
