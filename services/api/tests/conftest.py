import pytest

from app.db import Base, SessionLocal, engine
from app.models import Tenant


@pytest.fixture(autouse=True)
def clean_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all(
        [
            Tenant(id="tenant-a", name="Company A", slug="company-a"),
            Tenant(id="tenant-b", name="Company B", slug="company-b"),
        ]
    )
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def admin_headers():
    return {
        "X-Tenant-ID": "tenant-a",
        "X-Actor": "owner@example.com",
        "X-Role": "owner",
    }


@pytest.fixture
def sales_headers():
    return {
        "X-Tenant-ID": "tenant-a",
        "X-Actor": "sales@example.com",
        "X-Role": "sales_agent",
    }


@pytest.fixture
def other_tenant_headers():
    return {
        "X-Tenant-ID": "tenant-b",
        "X-Actor": "other@example.com",
        "X-Role": "owner",
    }
