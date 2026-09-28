from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_white_label_settings_and_safe_export(admin_headers):
    settings = client.get("/api/v1/tenant/settings", headers=admin_headers)
    assert settings.status_code == 200
    assert settings.json()["slug"] == "company-a"

    updated = client.patch(
        "/api/v1/tenant/settings",
        headers=admin_headers,
        json={
            "brand_name": "Company A Properties",
            "primary_color": "#123456",
            "logo_data_url": "data:image/png;base64,aGVsbG8=",
            "cover_data_url": "data:image/webp;base64,Y292ZXI=",
            "contact_email": "hello@companya.test",
            "website_url": "https://company-a.test",
            "facebook_url": "https://facebook.com/company-a",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["brand_name"] == "Company A Properties"
    assert updated.json()["primary_color"] == "#123456"
    assert updated.json()["logo_data_url"].startswith("data:image/png;base64,")
    assert updated.json()["cover_data_url"].startswith("data:image/webp;base64,")
    assert updated.json()["contact_email"] == "hello@companya.test"
    assert updated.json()["website_url"] == "https://company-a.test"
    assert updated.json()["plan"] == "professional"

    exported = client.get("/api/v1/backup/export", headers=admin_headers)
    assert exported.status_code == 200
    data = exported.json()
    assert data["format"] == "Real-Estate-Business-OS-backup"
    assert data["tenant"]["slug"] == "company-a"
    assert data["tables"]["users"]
    assert all("password_hash" not in user for user in data["tables"]["users"])
    assert data["tables"]["tenant_saas_profiles"]
    assert all("encrypted_secret_json" not in row for row in data["tables"]["tenant_integrations"])


def test_audit_log_records_brand_update(admin_headers):
    response = client.patch(
        "/api/v1/tenant/settings",
        headers=admin_headers,
        json={"brand_name": "Audited Brand"},
    )
    assert response.status_code == 200

    audit = client.get("/api/v1/audit", headers=admin_headers)
    assert audit.status_code == 200
    assert any(item["action"] == "tenant.settings.update" for item in audit.json())
