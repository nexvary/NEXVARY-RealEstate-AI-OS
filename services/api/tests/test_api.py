from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["version"] == "2.2.0"


def test_business_routes_require_bearer_token() -> None:
    response = client.get("/api/v1/projects")
    assert response.status_code == 401
