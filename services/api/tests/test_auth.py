from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_login_returns_signed_access_token(admin_headers):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "company-a",
            "email": "owner@example.com",
            "password": "TestPassword123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["role"] == "owner"

    context = client.get(
        "/api/v1/me/context",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert context.status_code == 200
    assert context.json()["tenant_id"] == "tenant-a"
    assert context.json()["role"] == "owner"


def test_invalid_password_is_rejected():
    response = client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "company-a",
            "email": "owner@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401


def test_platform_provisioning_creates_owner_and_token():
    response = client.post(
        "/api/v1/auth/provision",
        headers={"X-Platform-Key": get_settings().platform_admin_key},
        json={
            "company_name": "New Estate Company",
            "company_slug": "new-estate-company",
            "brand_name": "NEC",
            "owner_name": "First Owner",
            "owner_email": "first.owner@example.com",
            "owner_password": "StrongPassword123!",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["tenant"]["slug"] == "new-estate-company"
    assert data["user"]["role"] == "owner"
    assert data["access_token"]


def test_invalid_platform_key_is_rejected():
    response = client.post(
        "/api/v1/auth/provision",
        headers={"X-Platform-Key": "not-the-key"},
        json={
            "company_name": "Blocked Company",
            "company_slug": "blocked-company",
            "owner_name": "Blocked Owner",
            "owner_email": "blocked@example.com",
            "owner_password": "StrongPassword123!",
        },
    )
    assert response.status_code == 403


def test_role_cannot_be_forged_with_headers(viewer_headers):
    forged = dict(viewer_headers)
    forged["X-Role"] = "owner"
    response = client.post(
        "/api/v1/projects",
        headers=forged,
        json={"name": "Forged Project", "city": "Cairo"},
    )
    assert response.status_code == 403
