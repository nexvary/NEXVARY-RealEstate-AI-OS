from __future__ import annotations

import json
from datetime import date, datetime
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from seo_autopilot_core.audit import UnsafeTargetError, audit_url, summarize_severities
from seo_autopilot_core.autopilot import create_change_plan
from seo_autopilot_core.crawler import crawl_site
from seo_autopilot_core.growth import VisibilityEvidenceRequest, score_ai_visibility_evidence
from seo_autopilot_core.intelligence import build_content_brief, build_opportunities
from seo_autopilot_core.models import SearchMetricRow
from seo_autopilot_core.performance import WebVitals, answer_readiness_score, evaluate_web_vitals
from seo_autopilot_core.schema_engine import build_schema
from seo_autopilot_core.search_console import SearchConsoleClient, SearchConsoleError
from seo_autopilot_core.stage1000 import build_index_coverage

from .db import get_db
from .integration_crypto import decrypt_secret_map
from .models import AuditEvent, UserRole
from .policy import RequestContext, get_request_context, require_roles
from .saas_models import TenantIntegration
from .seo_models import SEOChangeDraft, SEOChangeStatus, SEOProject, SEOSnapshot, SEOSnapshotKind

router = APIRouter(prefix="/api/v1/seo")

SEO_SOURCE_REPOSITORY = "nexvary/NEXVARY-SEO-Autopilot."
SEO_SOURCE_COMMIT = "3838cd8030be069db6a3503150bcaccf3210abe3"

seo_operator = require_roles(UserRole.owner, UserRole.admin, UserRole.sales_manager)


class SEOProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    site_url: HttpUrl


class SEOProjectRead(BaseModel):
    id: str
    name: str
    site_url: str
    is_active: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditRunRequest(BaseModel):
    target_url: HttpUrl | None = None


class CrawlRunRequest(BaseModel):
    max_pages: int = Field(default=60, ge=1, le=300)
    concurrency: int = Field(default=4, ge=1, le=10)


class SearchConsoleRunRequest(BaseModel):
    start_date: date
    end_date: date
    dimensions: list[str] = Field(default_factory=lambda: ["query", "page"])
    row_limit: int = Field(default=5000, ge=1, le=25000)


class SchemaRequest(BaseModel):
    schema_type: str = Field(min_length=2, max_length=80)
    visible_data: dict


class WebVitalsRequest(BaseModel):
    lcp_ms: float | None = Field(default=None, ge=0)
    inp_ms: float | None = Field(default=None, ge=0)
    cls: float | None = Field(default=None, ge=0)


class AnswerReadinessRequest(BaseModel):
    has_clear_heading: bool
    has_direct_answer: bool
    has_supporting_details: bool
    has_sources_for_factual_claims: bool
    has_descriptive_links: bool
    hidden_critical_content: bool = False


class VisibilityRequest(BaseModel):
    clear_entity_identity: bool = False
    direct_answer_blocks: bool = False
    cited_primary_sources: bool = False
    unique_first_party_evidence: bool = False
    descriptive_internal_links: bool = False
    structured_data_matches_visible_content: bool = False
    important_content_is_indexable: bool = False
    author_or_organization_context: bool = False


class ChangePlanRequest(BaseModel):
    target_url: HttpUrl
    action: str = Field(min_length=1, max_length=100)
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    reason: str = Field(min_length=3, max_length=1000)


class ChangeDraftRead(BaseModel):
    id: str
    project_id: str
    upstream_change_id: str
    target_url: str
    action: str
    risk: str
    status: SEOChangeStatus
    created_at: datetime
    payload: dict


class SnapshotSummary(BaseModel):
    id: str
    project_id: str
    kind: SEOSnapshotKind
    score: int | None
    grade: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def _project(db: Session, project_id: str, tenant_id: str) -> SEOProject:
    record = db.scalar(
        select(SEOProject).where(
            SEOProject.id == project_id,
            SEOProject.tenant_id == tenant_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="SEO project not found")
    return record


def _host(value: str) -> str:
    return (urlparse(value).hostname or "").casefold().rstrip(".")


def _same_site(project: SEOProject, target_url: str) -> None:
    if _host(project.site_url) != _host(target_url):
        raise HTTPException(status_code=422, detail="Target URL must belong to the SEO project's website")


def _save_snapshot(
    db: Session,
    ctx: RequestContext,
    project: SEOProject,
    kind: SEOSnapshotKind,
    payload: dict | list,
    *,
    score: int | None = None,
    grade: str | None = None,
) -> SEOSnapshot:
    record = SEOSnapshot(
        tenant_id=ctx.tenant_id,
        project_id=project.id,
        kind=kind,
        score=score,
        grade=grade,
        payload_json=json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        created_by_user_id=ctx.user_id,
    )
    db.add(record)
    db.flush()
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action=f"seo.{kind.value}",
            entity_type="seo_project",
            entity_id=project.id,
            details=project.site_url,
        )
    )
    db.commit()
    db.refresh(record)
    return record


def _latest_snapshot(
    db: Session,
    tenant_id: str,
    project_id: str,
    kind: SEOSnapshotKind,
) -> SEOSnapshot | None:
    return db.scalar(
        select(SEOSnapshot)
        .where(
            SEOSnapshot.tenant_id == tenant_id,
            SEOSnapshot.project_id == project_id,
            SEOSnapshot.kind == kind,
        )
        .order_by(SEOSnapshot.created_at.desc())
        .limit(1)
    )


def _metric_rows(db: Session, ctx: RequestContext, project_id: str) -> list[SearchMetricRow]:
    snapshot = _latest_snapshot(db, ctx.tenant_id, project_id, SEOSnapshotKind.search_console)
    if snapshot is None:
        raise HTTPException(status_code=409, detail="Search Console data has not been synchronized yet")
    raw = json.loads(snapshot.payload_json)
    return [SearchMetricRow.model_validate(item) for item in raw]


def _search_console_integration(db: Session, tenant_id: str) -> tuple[SearchConsoleClient, dict]:
    integration = db.scalar(
        select(TenantIntegration).where(
            TenantIntegration.tenant_id == tenant_id,
            TenantIntegration.provider == "google-search-console",
            TenantIntegration.is_enabled == 1,
        )
    )
    if integration is None:
        raise HTTPException(status_code=409, detail="Google Search Console integration is not configured")
    secrets = decrypt_secret_map(integration.encrypted_secret_json)
    token = str(secrets.get("access_token") or "").strip()
    if not token:
        raise HTTPException(status_code=409, detail="Google Search Console access token is missing")
    public_config = json.loads(integration.public_config_json or "{}")
    return SearchConsoleClient(token, allow_write=False), public_config


@router.get("/capabilities")
def capabilities(ctx: RequestContext = Depends(get_request_context)) -> dict:
    return {
        "tenant_id": ctx.tenant_id,
        "source_repository": SEO_SOURCE_REPOSITORY,
        "source_commit": SEO_SOURCE_COMMIT,
        "white_label": True,
        "live_writes_exposed": False,
        "modules": [
            "technical_audit",
            "bounded_crawler",
            "search_console_readonly",
            "opportunity_engine",
            "content_brief",
            "schema_builder",
            "core_web_vitals",
            "answer_readiness",
            "ai_visibility_evidence",
            "index_coverage",
            "competitor_radar",
            "guarded_change_planning",
        ],
    }


@router.post("/projects", response_model=SEOProjectRead, status_code=201)
def create_project(
    payload: SEOProjectCreate,
    ctx: RequestContext = Depends(seo_operator),
    db: Session = Depends(get_db),
) -> SEOProject:
    record = SEOProject(
        tenant_id=ctx.tenant_id,
        name=payload.name.strip(),
        site_url=str(payload.site_url).rstrip("/"),
        created_by_user_id=ctx.user_id,
    )
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="This website already exists in the SEO workspace") from exc
    db.refresh(record)
    return record


@router.get("/projects", response_model=list[SEOProjectRead])
def list_projects(
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[SEOProject]:
    return list(
        db.scalars(
            select(SEOProject)
            .where(SEOProject.tenant_id == ctx.tenant_id)
            .order_by(SEOProject.created_at.desc())
        ).all()
    )


@router.get("/projects/{project_id}/dashboard")
def project_dashboard(
    project_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict:
    project = _project(db, project_id, ctx.tenant_id)
    latest_audit = _latest_snapshot(db, ctx.tenant_id, project.id, SEOSnapshotKind.audit)
    latest_crawl = _latest_snapshot(db, ctx.tenant_id, project.id, SEOSnapshotKind.crawl)
    latest_search = _latest_snapshot(db, ctx.tenant_id, project.id, SEOSnapshotKind.search_console)
    drafts = int(
        db.scalar(
            select(func.count()).select_from(SEOChangeDraft).where(
                SEOChangeDraft.tenant_id == ctx.tenant_id,
                SEOChangeDraft.project_id == project.id,
                SEOChangeDraft.status == SEOChangeStatus.planned,
            )
        )
        or 0
    )
    crawl_coverage = None
    if latest_crawl is not None:
        crawl_coverage = build_index_coverage(json.loads(latest_crawl.payload_json))
    return {
        "project": SEOProjectRead.model_validate(project).model_dump(mode="json"),
        "latest_audit": {
            "score": latest_audit.score,
            "grade": latest_audit.grade,
            "created_at": latest_audit.created_at,
        } if latest_audit else None,
        "latest_crawl_at": latest_crawl.created_at if latest_crawl else None,
        "search_console_synced_at": latest_search.created_at if latest_search else None,
        "index_coverage": crawl_coverage,
        "planned_changes": drafts,
    }


@router.post("/projects/{project_id}/audit")
async def run_audit(
    project_id: str,
    payload: AuditRunRequest,
    ctx: RequestContext = Depends(seo_operator),
    db: Session = Depends(get_db),
) -> dict:
    project = _project(db, project_id, ctx.tenant_id)
    target = str(payload.target_url or project.site_url)
    _same_site(project, target)
    try:
        result = await audit_url(target)
    except UnsafeTargetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"SEO audit failed: {exc}") from exc

    data = result.model_dump(mode="json")
    data["failed_by_severity"] = summarize_severities(result.checks)
    snapshot = _save_snapshot(
        db,
        ctx,
        project,
        SEOSnapshotKind.audit,
        data,
        score=result.score,
        grade=result.grade,
    )
    return {"snapshot_id": snapshot.id, **data}


@router.post("/projects/{project_id}/crawl")
async def run_crawl(
    project_id: str,
    payload: CrawlRunRequest,
    ctx: RequestContext = Depends(seo_operator),
    db: Session = Depends(get_db),
) -> dict:
    project = _project(db, project_id, ctx.tenant_id)
    try:
        report = await crawl_site(
            project.site_url,
            max_pages=payload.max_pages,
            concurrency=payload.concurrency,
        )
    except UnsafeTargetError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"SEO crawl failed: {exc}") from exc

    data = report.model_dump(mode="json")
    snapshot = _save_snapshot(db, ctx, project, SEOSnapshotKind.crawl, data)
    return {"snapshot_id": snapshot.id, **data}


@router.post("/projects/{project_id}/search-console/sync")
async def sync_search_console(
    project_id: str,
    payload: SearchConsoleRunRequest,
    ctx: RequestContext = Depends(seo_operator),
    db: Session = Depends(get_db),
) -> dict:
    project = _project(db, project_id, ctx.tenant_id)
    client, public_config = _search_console_integration(db, ctx.tenant_id)
    configured_site = str(public_config.get("site_url") or project.site_url)
    if _host(configured_site) and _host(project.site_url) and _host(configured_site) != _host(project.site_url):
        raise HTTPException(status_code=409, detail="Search Console integration site does not match this SEO project")
    try:
        rows = await client.search_analytics(
            configured_site,
            payload.start_date,
            payload.end_date,
            dimensions=payload.dimensions,
            row_limit=payload.row_limit,
        )
    except (SearchConsoleError, ValueError, httpx.HTTPError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    data = [row.model_dump(mode="json") for row in rows]
    snapshot = _save_snapshot(db, ctx, project, SEOSnapshotKind.search_console, data)
    return {
        "snapshot_id": snapshot.id,
        "site_url": configured_site,
        "rows": len(data),
        "start_date": payload.start_date,
        "end_date": payload.end_date,
    }


@router.get("/projects/{project_id}/opportunities")
def opportunities(
    project_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[dict]:
    _project(db, project_id, ctx.tenant_id)
    rows = _metric_rows(db, ctx, project_id)
    return [item.model_dump(mode="json") for item in build_opportunities(rows, limit=limit)]


class ContentBriefRequest(BaseModel):
    page: HttpUrl


@router.post("/projects/{project_id}/content-brief")
def content_brief(
    project_id: str,
    payload: ContentBriefRequest,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> dict:
    project = _project(db, project_id, ctx.tenant_id)
    _same_site(project, str(payload.page))
    rows = _metric_rows(db, ctx, project_id)
    return build_content_brief(str(payload.page), rows).model_dump(mode="json")


@router.post("/schema/build")
def schema_build(
    payload: SchemaRequest,
    _: RequestContext = Depends(get_request_context),
) -> dict:
    try:
        return build_schema(payload.schema_type, payload.visible_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/performance/web-vitals")
def web_vitals(
    payload: WebVitalsRequest,
    _: RequestContext = Depends(get_request_context),
) -> dict:
    return evaluate_web_vitals(WebVitals(**payload.model_dump()))


@router.post("/answer-readiness")
def answer_readiness(
    payload: AnswerReadinessRequest,
    _: RequestContext = Depends(get_request_context),
) -> dict:
    return answer_readiness_score(**payload.model_dump())


@router.post("/visibility-evidence")
def visibility_evidence(
    payload: VisibilityRequest,
    _: RequestContext = Depends(get_request_context),
) -> dict:
    return score_ai_visibility_evidence(VisibilityEvidenceRequest(**payload.model_dump()))


class CompetitorRadarRequest(BaseModel):
    targets: list[HttpUrl] = Field(min_length=1, max_length=5)


@router.post("/competitor-radar")
async def competitor_radar(
    payload: CompetitorRadarRequest,
    _: RequestContext = Depends(get_request_context),
) -> dict:
    output = []
    for target in payload.targets:
        url = str(target)
        try:
            result = await audit_url(url)
            output.append(
                {
                    "url": url,
                    "status": "ok",
                    "seo_score": result.score,
                    "grade": result.grade,
                    "title": result.snapshot.title,
                    "word_count": result.snapshot.word_count,
                    "h1_count": result.snapshot.h1_count,
                    "images_missing_alt": result.snapshot.images_missing_alt,
                    "schema_types": result.snapshot.structured_data_types,
                }
            )
        except UnsafeTargetError as exc:
            output.append({"url": url, "status": "blocked", "detail": str(exc)})
        except (httpx.HTTPError, ValueError) as exc:
            output.append({"url": url, "status": "error", "detail": str(exc)})
    return {
        "targets": output,
        "note": "Read-only page comparison; no ranking claim and no write operation.",
    }


@router.post("/projects/{project_id}/autopilot/plan", response_model=ChangeDraftRead, status_code=201)
def plan_change(
    project_id: str,
    payload: ChangePlanRequest,
    ctx: RequestContext = Depends(seo_operator),
    db: Session = Depends(get_db),
) -> ChangeDraftRead:
    project = _project(db, project_id, ctx.tenant_id)
    _same_site(project, str(payload.target_url))
    try:
        plan = create_change_plan(
            str(payload.target_url),
            payload.action,
            payload.before,
            payload.after,
            payload.reason,
            dry_run=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw = plan.model_dump(mode="json")
    record = SEOChangeDraft(
        tenant_id=ctx.tenant_id,
        project_id=project.id,
        upstream_change_id=plan.id,
        target_url=plan.url,
        action=plan.action,
        risk=plan.risk.value,
        status=SEOChangeStatus.planned,
        payload_json=json.dumps(raw, ensure_ascii=False, separators=(",", ":")),
        created_by_user_id=ctx.user_id,
    )
    db.add(record)
    db.add(
        AuditEvent(
            tenant_id=ctx.tenant_id,
            actor=ctx.actor,
            action="seo.autopilot.plan",
            entity_type="seo_project",
            entity_id=project.id,
            details=f"{plan.risk.value}:{plan.action}",
        )
    )
    db.commit()
    db.refresh(record)
    return ChangeDraftRead(
        id=record.id,
        project_id=record.project_id,
        upstream_change_id=record.upstream_change_id,
        target_url=record.target_url,
        action=record.action,
        risk=record.risk,
        status=record.status,
        created_at=record.created_at,
        payload=raw,
    )


@router.get("/projects/{project_id}/autopilot/plans", response_model=list[ChangeDraftRead])
def change_plans(
    project_id: str,
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[ChangeDraftRead]:
    _project(db, project_id, ctx.tenant_id)
    rows = db.scalars(
        select(SEOChangeDraft)
        .where(
            SEOChangeDraft.tenant_id == ctx.tenant_id,
            SEOChangeDraft.project_id == project_id,
        )
        .order_by(SEOChangeDraft.created_at.desc())
        .limit(200)
    ).all()
    return [
        ChangeDraftRead(
            id=row.id,
            project_id=row.project_id,
            upstream_change_id=row.upstream_change_id,
            target_url=row.target_url,
            action=row.action,
            risk=row.risk,
            status=row.status,
            created_at=row.created_at,
            payload=json.loads(row.payload_json),
        )
        for row in rows
    ]


@router.get("/projects/{project_id}/snapshots", response_model=list[SnapshotSummary])
def snapshots(
    project_id: str,
    kind: SEOSnapshotKind | None = Query(default=None),
    ctx: RequestContext = Depends(get_request_context),
    db: Session = Depends(get_db),
) -> list[SEOSnapshot]:
    _project(db, project_id, ctx.tenant_id)
    query = select(SEOSnapshot).where(
        SEOSnapshot.tenant_id == ctx.tenant_id,
        SEOSnapshot.project_id == project_id,
    )
    if kind is not None:
        query = query.where(SEOSnapshot.kind == kind)
    return list(db.scalars(query.order_by(SEOSnapshot.created_at.desc()).limit(200)).all())
