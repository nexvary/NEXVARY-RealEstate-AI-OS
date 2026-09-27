import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PASSWORD = "TestPassword123!"


def claim_platform_admin():
    response = client.post(
        "/api/v1/platform/auth/claim",
        json={
            "tenant_slug": "company-a",
            "email": "owner@example.com",
            "password": PASSWORD,
        },
    )
    assert response.status_code == 201
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_owner_can_claim_and_login_to_platform_admin():
    status = client.get("/api/v1/platform/status")
    assert status.status_code == 200
    assert status.json()["configured"] is False

    headers = claim_platform_admin()
    overview = client.get("/api/v1/platform/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["tenants_total"] == 2

    login = client.post(
        "/api/v1/platform/auth/login",
        json={"email": "owner@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    assert login.json()["admin"]["email"] == "owner@example.com"


def test_platform_admin_can_create_and_configure_tenant():
    headers = claim_platform_admin()

    created = client.post(
        "/api/v1/platform/tenants",
        headers=headers,
        json={
            "company_name": "Atlas Realty",
            "company_slug": "atlas-realty",
            "brand_name": "ATLAS",
            "primary_color": "#123456",
            "owner_name": "Atlas Owner",
            "owner_email": "owner@atlas.test",
            "owner_password": "AtlasOwner123!",
            "plan": "starter",
            "lifecycle": "trial",
            "custom_domain": "crm.atlas.test",
            "powered_by_nexvary": False,
        },
    )
    assert created.status_code == 201
    data = created.json()
    assert data["slug"] == "atlas-realty"
    assert data["plan"] == "starter"
    assert data["lifecycle"] == "trial"
    assert data["powered_by_nexvary"] is False
    assert data["max_users"] == 8

    updated = client.patch(
        f"/api/v1/platform/tenants/{data['id']}",
        headers=headers,
        json={
            "plan": "enterprise",
            "apply_plan_defaults": True,
            "lifecycle": "active",
            "brand_name": "Atlas Enterprise",
            "powered_by_nexvary": True,
        },
    )
    assert updated.status_code == 200
    changed = updated.json()
    assert changed["plan"] == "enterprise"
    assert changed["max_users"] == 250
    assert changed["lifecycle"] == "active"
    assert changed["brand_name"] == "Atlas Enterprise"


def test_suspended_workspace_is_blocked():
    headers = claim_platform_admin()
    tenants = client.get("/api/v1/platform/tenants", headers=headers).json()
    tenant_a = next(item for item in tenants if item["slug"] == "company-a")

    suspended = client.patch(
        f"/api/v1/platform/tenants/{tenant_a['id']}",
        headers=headers,
        json={"lifecycle": "suspended"},
    )
    assert suspended.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "company-a",
            "email": "owner@example.com",
            "password": PASSWORD,
        },
    )
    assert login.status_code == 200
    user_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    blocked = client.get("/api/v1/projects", headers=user_headers)
    assert blocked.status_code == 403
    assert "suspended" in blocked.json()["detail"].lower()


def test_plan_project_limit_is_enforced(admin_headers):
    platform_headers = claim_platform_admin()
    tenants = client.get("/api/v1/platform/tenants", headers=platform_headers).json()
    tenant_a = next(item for item in tenants if item["slug"] == "company-a")

    changed = client.patch(
        f"/api/v1/platform/tenants/{tenant_a['id']}",
        headers=platform_headers,
        json={"max_projects": 1},
    )
    assert changed.status_code == 200

    first = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"name": "Only Project", "city": "Cairo"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/projects",
        headers=admin_headers,
        json={"name": "Blocked Project", "city": "Cairo"},
    )
    assert second.status_code == 409
    assert "limit" in second.json()["detail"].lower()


def test_integration_secrets_are_encrypted_and_never_returned():
    headers = claim_platform_admin()
    tenants = client.get("/api/v1/platform/tenants", headers=headers).json()
    tenant_a = next(item for item in tenants if item["slug"] == "company-a")

    configured = client.put(
        f"/api/v1/platform/tenants/{tenant_a['id']}/integrations/whatsapp",
        headers=headers,
        json={
            "display_name": "WhatsApp Business",
            "is_enabled": True,
            "public_config": {"phone_number_id": "123456"},
            "secrets": {"access_token": "super-secret-token", "app_secret": "another-secret"},
        },
    )
    assert configured.status_code == 200
    body = configured.json()
    assert body["is_enabled"] is True
    assert body["public_config"]["phone_number_id"] == "123456"
    assert sorted(body["secret_keys"]) == ["access_token", "app_secret"]
    assert "super-secret-token" not in json.dumps(body)

    listed = client.get(
        f"/api/v1/platform/tenants/{tenant_a['id']}/integrations",
        headers=headers,
    )
    assert listed.status_code == 200
    assert "super-secret-token" not in listed.text



def test_custom_domain_resolves_public_white_label_branding():
    headers = claim_platform_admin()
    tenants = client.get("/api/v1/platform/tenants", headers=headers).json()
    tenant_a = next(item for item in tenants if item["slug"] == "company-a")

    updated = client.patch(
        f"/api/v1/platform/tenants/{tenant_a['id']}",
        headers=headers,
        json={
            "custom_domain": "CRM.COMPANY-A.TEST.",
            "brand_name": "Company A White Label",
            "primary_color": "#224466",
            "logo_data_url": "data:image/png;base64,aGVsbG8=",
            "powered_by_nexvary": False,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["custom_domain"] == "crm.company-a.test"

    resolved = client.get("/api/v1/branding/resolve?host=crm.company-a.test:443")
    assert resolved.status_code == 200
    body = resolved.json()
    assert body["tenant_slug"] == "company-a"
    assert body["brand_name"] == "Company A White Label"
    assert body["primary_color"] == "#224466"
    assert body["powered_by_nexvary"] is False
    assert body["logo_data_url"].startswith("data:image/png;base64,")
