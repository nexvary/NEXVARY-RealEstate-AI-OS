from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app

client = TestClient(app)


def test_development_skip_creates_workspace_and_quick_entry_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    status = client.get("/api/v1/setup/status")
    assert status.status_code == 200
    assert status.json()["needs_setup"] is True
    assert status.json()["development_workspace"] is False

    skipped = client.post("/api/v1/auth/bootstrap-development")
    assert skipped.status_code == 201
    body = skipped.json()
    assert body["tenant_slug"] == "workspace"
    assert body["user_email"] == "owner@workspace.local"
    assert body["role"] == "owner"
    assert body["access_token"]

    status = client.get("/api/v1/setup/status")
    assert status.status_code == 200
    assert status.json()["needs_setup"] is False
    assert status.json()["tenant_count"] == 1
    assert status.json()["development_workspace"] is True

    quick = client.post("/api/v1/auth/development-session")
    assert quick.status_code == 200
    quick_body = quick.json()
    assert quick_body["tenant_id"] == body["tenant_id"]
    assert quick_body["tenant_slug"] == "workspace"
    assert quick_body["user_id"] == body["user_id"]
    assert quick_body["access_token"]


def test_development_workspace_can_be_created_alongside_existing_companies():
    status = client.get("/api/v1/setup/status")
    assert status.status_code == 200
    assert status.json()["tenant_count"] == 2
    assert status.json()["development_workspace"] is False

    response = client.post("/api/v1/auth/bootstrap-development")
    assert response.status_code == 201
    assert response.json()["tenant_slug"] == "workspace"

    status = client.get("/api/v1/setup/status")
    assert status.status_code == 200
    assert status.json()["tenant_count"] == 3
    assert status.json()["development_workspace"] is True
