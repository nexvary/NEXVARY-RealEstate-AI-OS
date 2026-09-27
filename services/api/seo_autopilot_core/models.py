from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Severity(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskLevel(str, Enum):
    safe_auto = "safe_auto"
    review_required = "review_required"
    protected = "protected"


class AuditCheck(BaseModel):
    key: str
    title: str
    passed: bool
    score: int = Field(ge=0, le=100)
    severity: Severity
    detail: str
    recommendation: str | None = None


class PageSnapshot(BaseModel):
    url: str
    status_code: int
    final_url: str
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    language: str | None = None
    robots_meta: str | None = None
    h1_count: int = 0
    h2_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images: int = 0
    images_missing_alt: int = 0
    word_count: int = 0
    structured_data_types: list[str] = Field(default_factory=list)
    hreflang_targets: dict[str, str] = Field(default_factory=dict)


class AuditResult(BaseModel):
    url: str
    score: int = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "F"]
    snapshot: PageSnapshot
    checks: list[AuditCheck]
    safe_auto_fix_candidates: list[str] = Field(default_factory=list)


class AuditRequest(BaseModel):
    url: HttpUrl


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=100, ge=1, le=1000)
    concurrency: int = Field(default=5, ge=1, le=20)


class CrawlPage(BaseModel):
    url: str
    status_code: int
    depth: int = 0
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    language: str | None = None
    h1_count: int = 0
    word_count: int = 0
    internal_links: int = 0
    external_links: int = 0
    images: int = 0
    images_missing_alt: int = 0
    structured_data_types: list[str] = Field(default_factory=list)
    hreflang_targets: dict[str, str] = Field(default_factory=dict)
    indexable: bool = True


class CrawlIssue(BaseModel):
    key: str
    severity: Severity
    url: str | None = None
    detail: str
    related_urls: list[str] = Field(default_factory=list)


class CrawlReport(BaseModel):
    root_url: str
    started_at: datetime
    finished_at: datetime
    pages: list[CrawlPage] = Field(default_factory=list)
    issues: list[CrawlIssue] = Field(default_factory=list)
    discovered_sitemaps: list[str] = Field(default_factory=list)
    robots_txt_url: str | None = None
    robots_txt_found: bool = False
    truncated: bool = False
    totals: dict[str, int | float] = Field(default_factory=dict)


class SearchMetricRow(BaseModel):
    query: str | None = None
    page: str | None = None
    country: str | None = None
    device: str | None = None
    search_appearance: str | None = None
    clicks: float = 0
    impressions: float = 0
    ctr: float = 0
    position: float = 0


class Opportunity(BaseModel):
    key: str
    page: str | None = None
    query: str | None = None
    impact: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    effort: int = Field(ge=1, le=100)
    priority: float = Field(ge=0)
    reason: str
    recommended_action: str


class ContentBrief(BaseModel):
    page: str
    intent: Literal["informational", "commercial", "transactional", "navigational", "mixed"]
    primary_query: str | None = None
    supporting_queries: list[str] = Field(default_factory=list)
    recommended_sections: list[str] = Field(default_factory=list)
    schema_candidates: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)


class ChangePlan(BaseModel):
    id: str
    url: str
    action: str
    risk: RiskLevel
    reason: str
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    rollback: dict = Field(default_factory=dict)
    dry_run: bool = True


class RegressionSignal(BaseModel):
    key: str
    severity: Severity
    metric: str
    previous: float
    current: float
    change_percent: float
    detail: str


class OpportunityRequest(BaseModel):
    rows: list[SearchMetricRow]
    limit: int = Field(default=100, ge=1, le=500)


class ContentBriefRequest(BaseModel):
    page: HttpUrl
    rows: list[SearchMetricRow]


class RegressionRequest(BaseModel):
    previous: list[SearchMetricRow]
    current: list[SearchMetricRow]
    minimum_impressions: float = Field(default=50, ge=0)


class ChangePlanRequest(BaseModel):
    url: HttpUrl
    action: str = Field(min_length=1, max_length=100)
    before: dict = Field(default_factory=dict)
    after: dict = Field(default_factory=dict)
    reason: str = Field(min_length=3, max_length=1000)
    dry_run: bool = True


class SchemaBuildRequest(BaseModel):
    schema_type: str
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


class SitePolicy(BaseModel):
    site_url: str
    allowed_hosts: list[str] = Field(default_factory=list)
    live_writes_enabled: bool = False
    safe_auto_enabled: bool = False
    protected_writes_enabled: bool = False
    auto_rollback_enabled: bool = True
    max_daily_changes: int = Field(default=5, ge=1, le=100)


class ChangePreview(BaseModel):
    change_id: str
    url: str
    action: str
    risk: RiskLevel
    state_hash: str
    before: dict
    after: dict
    live_write_eligible: bool
    approval_required: bool


class ApplyChangeRequest(BaseModel):
    change_id: str = Field(min_length=8, max_length=100)
    expected_state_hash: str = Field(min_length=32, max_length=128)
    approved: bool = False
    protected_override: bool = False


class RollbackChangeRequest(BaseModel):
    change_id: str = Field(min_length=8, max_length=100)
    approved: bool = False


class SearchConsoleSyncRequest(BaseModel):
    site_url: HttpUrl
    start_date: date
    end_date: date
    dimensions: list[
        Literal["query", "page", "country", "device", "searchAppearance", "date", "hour"]
    ] = Field(default_factory=lambda: ["query", "page"])
    row_limit: int = Field(default=25000, ge=1, le=25000)


class SearchConsoleSyncResult(BaseModel):
    site_url: str
    start_date: date
    end_date: date
    rows_saved: int
    metric_set_id: int
    dimensions: list[str]


class PostChangeEvaluationRequest(BaseModel):
    previous: list[SearchMetricRow]
    current: list[SearchMetricRow]
    minimum_impressions: float = Field(default=50, ge=0)


class PostChangeEvaluation(BaseModel):
    regressions: list[RegressionSignal] = Field(default_factory=list)
    rollback_recommended: bool = False
    auto_rollback_eligible: bool = False
    reason: str
