import pytest

from app.db import Base, SessionLocal, engine
from app.models import Tenant, User, UserRole
from app.security import create_access_token, hash_password


TEST_PASSWORD = "TestPassword123!"


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    tenant_a = Tenant(id="tenant-a", name="Company A", slug="company-a")
    tenant_b = Tenant(id="tenant-b", name="Company B", slug="company-b")
    db.add_all([tenant_a, tenant_b])
    db.flush()

    users = [
        User(
            id="user-owner-a",
            tenant_id="tenant-a",
            email="owner@example.com",
            display_name="Owner A",
            role=UserRole.owner,
            password_hash=hash_password(TEST_PASSWORD),
        ),
        User(
            id="user-sales-a",
            tenant_id="tenant-a",
            email="sales@example.com",
            display_name="Sales A",
            role=UserRole.sales_agent,
            password_hash=hash_password(TEST_PASSWORD),
        ),
        User(
            id="user-viewer-a",
            tenant_id="tenant-a",
            email="viewer@example.com",
            display_name="Viewer A",
            role=UserRole.viewer,
            password_hash=hash_password(TEST_PASSWORD),
        ),
        User(
            id="user-owner-b",
            tenant_id="tenant-b",
            email="other@example.com",
            display_name="Owner B",
            role=UserRole.owner,
            password_hash=hash_password(TEST_PASSWORD),
        ),
    ]
    db.add_all(users)
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def auth_header(user_id: str, tenant_id: str, role: UserRole):
    token = create_access_token(user_id=user_id, tenant_id=tenant_id, role=role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers():
    return auth_header("user-owner-a", "tenant-a", UserRole.owner)


@pytest.fixture
def sales_headers():
    return auth_header("user-sales-a", "tenant-a", UserRole.sales_agent)


@pytest.fixture
def viewer_headers():
    return auth_header("user-viewer-a", "tenant-a", UserRole.viewer)


@pytest.fixture
def other_tenant_headers():
    return auth_header("user-owner-b", "tenant-b", UserRole.owner)
