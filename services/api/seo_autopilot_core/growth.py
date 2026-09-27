from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from .intelligence import build_opportunities, detect_regressions
from .models import SearchMetricRow

TOKEN_RE = re.compile(r"[A-Za-z0-9_\u0600-\u06FF]{3,}")
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "على",
    "من",
    "في",
    "الى",
    "إلى",
    "عن",
    "مع",
    "هذا",
    "هذه",
}


class InternalLinkPage(BaseModel):
    url: HttpUrl
    title: str = Field(min_length=2, max_length=300)
    keywords: list[str] = Field(default_factory=list, max_length=30)
    outbound_links: list[str] = Field(default_factory=list, max_length=500)


class InternalLinkRequest(BaseModel):
    pages: list[InternalLinkPage] = Field(min_length=2, max_length=200)
    limit: int = Field(default=30, ge=1, le=200)


class VisibilityEvidenceRequest(BaseModel):
    clear_entity_identity: bool = False
    direct_answer_blocks: bool = False
    cited_primary_sources: bool = False
    unique_first_party_evidence: bool = False
    descriptive_internal_links: bool = False
    structured_data_matches_visible_content: bool = False
    important_content_is_indexable: bool = False
    author_or_organization_context: bool = False


class CompetitorRadarRequest(BaseModel):
    targets: list[HttpUrl] = Field(min_length=1, max_length=5)


def _tokens(*parts: str) -> set[str]:
    values: set[str] = set()
    for part in parts:
        for token in TOKEN_RE.findall(part.casefold()):
            if token not in STOPWORDS:
                values.add(token)
    return values


def build_internal_link_suggestions(payload: InternalLinkRequest) -> list[dict[str, Any]]:
    pages = payload.pages
    suggestions: list[dict[str, Any]] = []

    normalized = []
    for page in pages:
        topic = _tokens(page.title, " ".join(page.keywords))
        normalized.append((page, topic))

    for source, source_tokens in normalized:
        existing = {link.rstrip("/") for link in source.outbound_links}
        for target, target_tokens in normalized:
            if source.url == target.url:
                continue
            target_url = str(target.url)
            if target_url.rstrip("/") in existing:
                continue
            overlap = source_tokens & target_tokens
            if not overlap:
                continue
            union = source_tokens | target_tokens
            score = round((len(overlap) / max(len(union), 1)) * 100, 2)
            if score < 8:
                continue
            anchor = target.keywords[0] if target.keywords else target.title
            suggestions.append(
                {
                    "source_url": str(source.url),
                    "target_url": target_url,
                    "anchor_candidate": anchor,
                    "shared_topics": sorted(overlap)[:8],
                    "relevance_score": score,
                    "risk": "review_required",
                    "reason": "Topical overlap detected; review placement and anchor wording manually.",
                }
            )

    suggestions.sort(key=lambda item: item["relevance_score"], reverse=True)
    return suggestions[: payload.limit]


def compare_crawl_payloads(previous: dict, current: dict) -> dict[str, Any]:
    previous_pages = {page.get("url"): page for page in previous.get("pages", []) if page.get("url")}
    current_pages = {page.get("url"): page for page in current.get("pages", []) if page.get("url")}

    newly_broken: list[dict[str, Any]] = []
    recovered: list[dict[str, Any]] = []
    for url, page in current_pages.items():
        old = previous_pages.get(url)
        if not old:
            continue
        old_status = int(old.get("status_code", 0) or 0)
        new_status = int(page.get("status_code", 0) or 0)
        if old_status < 400 <= new_status:
            newly_broken.append({"url": url, "previous": old_status, "current": new_status})
        elif old_status >= 400 > new_status:
            recovered.append({"url": url, "previous": old_status, "current": new_status})

    def issue_counts(payload: dict) -> Counter[str]:
        return Counter(str(issue.get("key", "unknown")) for issue in payload.get("issues", []))

    before_issues = issue_counts(previous)
    after_issues = issue_counts(current)
    new_issue_keys = {
        key: after_issues[key] - before_issues.get(key, 0)
        for key in after_issues
        if after_issues[key] > before_issues.get(key, 0)
    }
    resolved_issue_keys = {
        key: before_issues[key] - after_issues.get(key, 0)
        for key in before_issues
        if before_issues[key] > after_issues.get(key, 0)
    }

    before_totals = previous.get("totals", {})
    after_totals = current.get("totals", {})
    keys = sorted(set(before_totals) | set(after_totals))
    totals_delta = {
        key: {
            "previous": before_totals.get(key, 0),
            "current": after_totals.get(key, 0),
            "delta": (after_totals.get(key, 0) or 0) - (before_totals.get(key, 0) or 0),
        }
        for key in keys
        if isinstance(before_totals.get(key, 0), (int, float))
        and isinstance(after_totals.get(key, 0), (int, float))
    }

    return {
        "newly_broken": newly_broken,
        "recovered": recovered,
        "new_issue_keys": new_issue_keys,
        "resolved_issue_keys": resolved_issue_keys,
        "totals_delta": totals_delta,
        "regression_detected": bool(newly_broken or new_issue_keys),
    }


def _aggregate_metric_rows(rows: list[dict]) -> dict[str, Any]:
    clicks = sum(float(row.get("clicks", 0) or 0) for row in rows)
    impressions = sum(float(row.get("impressions", 0) or 0) for row in rows)
    weighted_position_total = 0.0
    weighted_position_weight = 0.0
    for row in rows:
        impressions_row = float(row.get("impressions", 0) or 0)
        position = float(row.get("position", 0) or 0)
        if impressions_row > 0 and position > 0:
            weighted_position_total += position * impressions_row
            weighted_position_weight += impressions_row
    avg_position = (
        weighted_position_total / weighted_position_weight if weighted_position_weight else 0.0
    )
    return {
        "clicks": round(clicks, 2),
        "impressions": round(impressions, 2),
        "ctr": round(clicks / impressions, 6) if impressions else 0.0,
        "position": round(avg_position, 2),
    }


def build_rank_tracking(metric_sets: list[dict[str, Any]]) -> dict[str, Any]:
    if not metric_sets:
        return {"series": [], "query_trends": []}

    chronological = list(reversed(metric_sets))
    series = [
        {
            "metric_set_id": item["id"],
            "measured_at": item["measured_at"],
            **_aggregate_metric_rows(item.get("rows", [])),
        }
        for item in chronological
    ]

    first_rows = chronological[0].get("rows", [])
    latest_rows = chronological[-1].get("rows", [])

    def by_query(rows: list[dict]) -> dict[str, dict[str, float]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            query = row.get("query")
            if query:
                grouped[str(query)].append(row)
        return {query: _aggregate_metric_rows(items) for query, items in grouped.items()}

    old = by_query(first_rows)
    current = by_query(latest_rows)
    query_trends = []
    for query, now in current.items():
        prior = old.get(query, {"clicks": 0.0, "impressions": 0.0, "ctr": 0.0, "position": 0.0})
        query_trends.append(
            {
                "query": query,
                "clicks": now["clicks"],
                "impressions": now["impressions"],
                "position": now["position"],
                "click_delta": round(now["clicks"] - prior["clicks"], 2),
                "position_delta": round(now["position"] - prior["position"], 2),
            }
        )
    query_trends.sort(key=lambda item: item["impressions"], reverse=True)
    return {"series": series, "query_trends": query_trends[:50]}


def build_alerts(
    metric_sets: list[dict[str, Any]],
    crawl_snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if len(metric_sets) >= 2:
        current = [SearchMetricRow.model_validate(row) for row in metric_sets[0].get("rows", [])]
        previous = [SearchMetricRow.model_validate(row) for row in metric_sets[1].get("rows", [])]
        for signal in detect_regressions(previous, current):
            alerts.append(
                {
                    "source": "search_console",
                    "severity": signal.severity.value,
                    "key": signal.key,
                    "detail": signal.detail,
                    "metric": signal.metric,
                    "change_percent": signal.change_percent,
                }
            )

    if len(crawl_snapshots) >= 2:
        comparison = compare_crawl_payloads(
            crawl_snapshots[1]["payload"], crawl_snapshots[0]["payload"]
        )
        for item in comparison["newly_broken"]:
            alerts.append(
                {
                    "source": "crawl",
                    "severity": "high",
                    "key": "newly_broken_url",
                    "detail": (
                        f"{item['url']} changed from HTTP {item['previous']} "
                        f"to {item['current']}."
                    ),
                }
            )
        for key, count in comparison["new_issue_keys"].items():
            alerts.append(
                {
                    "source": "crawl",
                    "severity": "medium",
                    "key": key,
                    "detail": f"{count} new {key} issue(s) appeared in the latest crawl.",
                }
            )
    return alerts[:100]


def build_executive_report(
    site: str,
    metric_sets: list[dict[str, Any]],
    crawl_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_rows = metric_sets[0].get("rows", []) if metric_sets else []
    latest_metrics = _aggregate_metric_rows(latest_rows)
    opportunities = build_opportunities(
        [SearchMetricRow.model_validate(row) for row in latest_rows], limit=8
    )
    alerts = build_alerts(metric_sets, crawl_snapshots)
    latest_crawl = crawl_snapshots[0]["payload"] if crawl_snapshots else {}
    totals = latest_crawl.get("totals", {})
    return {
        "site": site,
        "search": latest_metrics,
        "crawl": {
            "pages_crawled": totals.get("pages_crawled", len(latest_crawl.get("pages", []))),
            "issues": totals.get("issues", len(latest_crawl.get("issues", []))),
            "indexable_pages": totals.get("indexable_pages", 0),
        },
        "top_opportunities": [item.model_dump(mode="json") for item in opportunities],
        "alerts": alerts[:12],
        "data_status": {
            "metric_sets": len(metric_sets),
            "crawl_snapshots": len(crawl_snapshots),
        },
        "note": "Executive summary uses only locally stored crawl and Search Console evidence.",
    }


def score_ai_visibility_evidence(payload: VisibilityEvidenceRequest) -> dict[str, Any]:
    checks = payload.model_dump()
    passed = sum(1 for value in checks.values() if value)
    score = round((passed / len(checks)) * 100)
    recommendations = [
        label.replace("_", " ") for label, value in checks.items() if not value
    ]
    return {
        "score": score,
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "missing_evidence": recommendations,
        "note": (
            "This is an evidence-readiness score, not a claim that an AI system will cite or rank the page."
        ),
    }
