from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.integration_crypto import encrypt_secret_map
from app.main import app
from app.saas_models import TenantIntegration
from seo_autopilot_core.models import (
    AuditCheck,
    AuditResult,
    CrawlPage,
    CrawlReport,
    PageSnapshot,
    SearchMetricRow,
    Severity,
)

client = TestClient(app)


def create_seo_project(headers, name="Company Website", site_url="https://example.com"):
    response = client.post(
        "/api/v1/seo/projects",
        headers=headers,
        json={"name": name, "site_url": site_url},
    )
    assert response.status_code == 201
    return response.json()


def test_seo_capabilities_pin_original_source(admin_headers):
    response = client.get("/api/v1/seo/capabilities", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["white_label"] is True
    assert body["live_writes_exposed"] is False
    assert body["source_repository"] == "nexvary/NEXVARY-SEO-Autopilot."
    assert body["source_commit"] == "3838cd8030be069db6a3503150bcaccf3210abe3"


def test_seo_projects_are_tenant_isolated(admin_headers, other_tenant_headers):
    project = create_seo_project(admin_headers)
    own = client.get("/api/v1/seo/projects", headers=admin_headers)
    assert own.status_code == 200
    assert [item["id"] for item in own.json()] == [project["id"]]

    other = client.get("/api/v1/seo/projects", headers=other_tenant_headers)
    assert other.status_code == 200
    assert other.json() == []


def test_audit_uses_copied_engine_and_persists_snapshot(admin_headers, monkeypatch):
    project = create_seo_project(admin_headers)

    async def fake_audit(url: str):
        return AuditResult(
            url=url,
            score=88,
            grade="B",
            snapshot=PageSnapshot(
                url=url,
                status_code=200,
                final_url=url,
                title="Example",
                h1_count=1,
                word_count=500,
            ),
            checks=[
                AuditCheck(
                    key="title",
                    title="Title",
                    passed=True,
                    score=100,
                    severity=Severity.info,
                    detail="Title exists.",
                )
            ],
            safe_auto_fix_candidates=[],
        )

    monkeypatch.setattr("app.seo_api.audit_url", fake_audit)

    response = client.post(
        f"/api/v1/seo/projects/{project['id']}/audit",
        headers=admin_headers,
        json={},
    )
    assert response.status_code == 200
    assert response.json()["score"] == 88
    assert response.json()["grade"] == "B"

    snapshots = client.get(
        f"/api/v1/seo/projects/{project['id']}/snapshots?kind=audit",
        headers=admin_headers,
    )
    assert snapshots.status_code == 200
    assert len(snapshots.json()) == 1
    assert snapshots.json()[0]["score"] == 88


def test_crawler_snapshot_and_dashboard(admin_headers, monkeypatch):
    project = create_seo_project(admin_headers)

    async def fake_crawl(url: str, max_pages: int, concurrency: int):
        now = datetime.now(timezone.utc)
        return CrawlReport(
            root_url=url,
            started_at=now,
            finished_at=now,
            pages=[
                CrawlPage(
                    url=url,
                    status_code=200,
                    title="Home",
                    h1_count=1,
                    word_count=600,
                    indexable=True,
                )
            ],
            issues=[],
            totals={"pages_crawled": 1, "issues": 0, "indexable_pages": 1},
        )

    monkeypatch.setattr("app.seo_api.crawl_site", fake_crawl)

    response = client.post(
        f"/api/v1/seo/projects/{project['id']}/crawl",
        headers=admin_headers,
        json={"max_pages": 20, "concurrency": 2},
    )
    assert response.status_code == 200
    assert response.json()["totals"]["pages_crawled"] == 1

    dashboard = client.get(
        f"/api/v1/seo/projects/{project['id']}/dashboard",
        headers=admin_headers,
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["latest_crawl_at"] is not None


def test_schema_performance_and_dry_run_autopilot(admin_headers):
    project = create_seo_project(admin_headers)

    schema = client.post(
        "/api/v1/seo/schema/build",
        headers=admin_headers,
        json={
            "schema_type": "Organization",
            "visible_data": {"name": "Example Realty", "url": "https://example.com"},
        },
    )
    assert schema.status_code == 200
    assert schema.json()["@type"] == "Organization"

    performance = client.post(
        "/api/v1/seo/performance/web-vitals",
        headers=admin_headers,
        json={"lcp_ms": 2100, "inp_ms": 160, "cls": 0.05},
    )
    assert performance.status_code == 200
    assert performance.json()["score"] == 100

    plan = client.post(
        f"/api/v1/seo/projects/{project['id']}/autopilot/plan",
        headers=admin_headers,
        json={
            "target_url": "https://example.com/listing",
            "action": "title_change",
            "before": {"title": "Old"},
            "after": {"title": "New"},
            "reason": "Align the title with visible listing intent.",
        },
    )
    assert plan.status_code == 201
    body = plan.json()
    assert body["risk"] == "review_required"
    assert body["payload"]["dry_run"] is True

    plans = client.get(
        f"/api/v1/seo/projects/{project['id']}/autopilot/plans",
        headers=admin_headers,
    )
    assert plans.status_code == 200
    assert len(plans.json()) == 1


def test_search_console_uses_encrypted_tenant_integration(admin_headers, monkeypatch):
    project = create_seo_project(admin_headers)

    db = SessionLocal()
    db.add(
        TenantIntegration(
            tenant_id="tenant-a",
            provider="google-search-console",
            display_name="Google Search Console",
            is_enabled=1,
            public_config_json='{"site_url":"https://example.com"}',
            encrypted_secret_json=encrypt_secret_map({"access_token": "runtime-token"}),
        )
    )
    db.commit()
    db.close()

    async def fake_search_analytics(self, site_url, start_date, end_date, **kwargs):
        assert self.access_token == "runtime-token"
        assert site_url == "https://example.com"
        return [
            SearchMetricRow(
                query="apartments in cairo",
                page="https://example.com/listings",
                clicks=20,
                impressions=1000,
                ctr=0.01,
                position=7,
            )
        ]

    monkeypatch.setattr(
        "seo_autopilot_core.search_console.SearchConsoleClient.search_analytics",
        fake_search_analytics,
    )

    sync = client.post(
        f"/api/v1/seo/projects/{project['id']}/search-console/sync",
        headers=admin_headers,
        json={
            "start_date": date(2026, 9, 1).isoformat(),
            "end_date": date(2026, 9, 25).isoformat(),
            "dimensions": ["query", "page"],
            "row_limit": 100,
        },
    )
    assert sync.status_code == 200
    assert sync.json()["rows"] == 1

    opportunities = client.get(
        f"/api/v1/seo/projects/{project['id']}/opportunities",
        headers=admin_headers,
    )
    assert opportunities.status_code == 200
    assert opportunities.json()
    assert opportunities.json()[0]["query"] == "apartments in cairo"


def test_cross_site_target_is_rejected(admin_headers):
    project = create_seo_project(admin_headers)
    response = client.post(
        f"/api/v1/seo/projects/{project['id']}/autopilot/plan",
        headers=admin_headers,
        json={
            "target_url": "https://other.example/listing",
            "action": "title_change",
            "before": {"title": "Old"},
            "after": {"title": "New"},
            "reason": "Should not cross project host.",
        },
    )
    assert response.status_code == 422
