from __future__ import annotations

import html
import re
import sqlite3
import uuid
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse, urlunparse

from pydantic import BaseModel, Field, HttpUrl

from .models import SearchMetricRow

TOKEN_RE = re.compile(r"[A-Za-z0-9_\u0600-\u06FF]{3,}")
STOPWORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "your",
    "على", "من", "في", "الى", "إلى", "عن", "مع", "هذا", "هذه", "التي", "الذي",
}


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    site_url: HttpUrl


class ProjectActivateRequest(BaseModel):
    project_id: str = Field(min_length=8, max_length=80)


class ChangeReviewRequest(BaseModel):
    change_id: str = Field(min_length=8, max_length=100)
    decision: Literal["approved", "rejected", "needs_changes"]
    note: str = Field(default="", max_length=1000)


class KeywordClusterRequest(BaseModel):
    rows: list[SearchMetricRow] = Field(min_length=1, max_length=1000)
    minimum_shared_terms: int = Field(default=1, ge=1, le=5)
    limit: int = Field(default=100, ge=1, le=300)


def normalize_site_url(value: str) -> str:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("site_url must be a valid HTTP(S) URL")
    host = parsed.hostname.casefold()
    port = f":{parsed.port}" if parsed.port else ""
    return urlunparse((parsed.scheme.casefold(), f"{host}{port}", "/", "", "", ""))


class ControlStore:
    """Stage 1000 control-plane persistence kept separate from evidence tables."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS site_projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    site_url TEXT NOT NULL UNIQUE,
                    active INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_site_projects_active
                ON site_projects(active DESC, updated_at DESC);

                CREATE TABLE IF NOT EXISTS change_reviews (
                    change_id TEXT PRIMARY KEY,
                    decision TEXT NOT NULL,
                    note TEXT NOT NULL,
                    reviewed_at TEXT NOT NULL
                );
                """
            )

    def create_project(self, name: str, site_url: str) -> dict[str, Any]:
        normalized = normalize_site_url(site_url)
        now = datetime.now(UTC).isoformat()
        project_id = uuid.uuid4().hex
        with self._connect() as db:
            existing = db.execute(
                "SELECT id FROM site_projects WHERE site_url = ?",
                (normalized,),
            ).fetchone()
            if existing:
                db.execute(
                    "UPDATE site_projects SET name = ?, updated_at = ? WHERE id = ?",
                    (name.strip(), now, existing["id"]),
                )
                project_id = str(existing["id"])
            else:
                count = db.execute("SELECT COUNT(*) AS count FROM site_projects").fetchone()["count"]
                db.execute(
                    """
                    INSERT INTO site_projects(id, name, site_url, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (project_id, name.strip(), normalized, 1 if count == 0 else 0, now, now),
                )
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute(
                "SELECT id, name, site_url, active, created_at, updated_at FROM site_projects WHERE id = ?",
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(project_id)
        item = dict(row)
        item["active"] = bool(item["active"])
        return item

    def list_projects(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, name, site_url, active, created_at, updated_at
                FROM site_projects
                ORDER BY active DESC, updated_at DESC
                """
            ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["active"] = bool(item["active"])
            output.append(item)
        return output

    def activate_project(self, project_id: str) -> dict[str, Any]:
        with self._connect() as db:
            exists = db.execute("SELECT id FROM site_projects WHERE id = ?", (project_id,)).fetchone()
            if exists is None:
                raise KeyError(project_id)
            db.execute("UPDATE site_projects SET active = 0")
            db.execute(
                "UPDATE site_projects SET active = 1, updated_at = ? WHERE id = ?",
                (datetime.now(UTC).isoformat(), project_id),
            )
        return self.get_project(project_id)

    def save_review(self, payload: ChangeReviewRequest) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self._connect() as db:
            db.execute(
                """
                INSERT INTO change_reviews(change_id, decision, note, reviewed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(change_id) DO UPDATE SET
                    decision = excluded.decision,
                    note = excluded.note,
                    reviewed_at = excluded.reviewed_at
                """,
                (payload.change_id, payload.decision, payload.note.strip(), now),
            )
        return {
            "change_id": payload.change_id,
            "decision": payload.decision,
            "note": payload.note.strip(),
            "reviewed_at": now,
        }

    def review_map(self, change_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not change_ids:
            return {}
        wanted = set(change_ids)
        with self._connect() as db:
            rows = db.execute(
                "SELECT change_id, decision, note, reviewed_at FROM change_reviews"
            ).fetchall()
        return {
            str(row["change_id"]): dict(row)
            for row in rows
            if str(row["change_id"]) in wanted
        }


def _query_tokens(query: str) -> set[str]:
    return {
        token
        for token in TOKEN_RE.findall(query.casefold())
        if token not in STOPWORDS and not token.isdigit()
    }


def build_keyword_clusters(payload: KeywordClusterRequest) -> list[dict[str, Any]]:
    rows = [row for row in payload.rows if row.query]
    if not rows:
        return []

    parents = list(range(len(rows)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        a, b = find(left), find(right)
        if a != b:
            parents[b] = a

    tokens = [_query_tokens(row.query or "") for row in rows]
    for left in range(len(rows)):
        for right in range(left + 1, len(rows)):
            same_page = bool(rows[left].page and rows[left].page == rows[right].page)
            shared = tokens[left] & tokens[right]
            if same_page or len(shared) >= payload.minimum_shared_terms:
                union(left, right)

    groups: dict[int, list[SearchMetricRow]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[find(index)].append(row)

    output: list[dict[str, Any]] = []
    for items in groups.values():
        query_terms = Counter()
        pages = Counter()
        clicks = 0.0
        impressions = 0.0
        weighted_position = 0.0
        weight = 0.0
        for row in items:
            query_terms.update(_query_tokens(row.query or ""))
            if row.page:
                pages[row.page] += 1
            clicks += row.clicks
            impressions += row.impressions
            if row.impressions > 0 and row.position > 0:
                weighted_position += row.position * row.impressions
                weight += row.impressions
        label = " / ".join(term for term, _ in query_terms.most_common(3)) or (items[0].query or "cluster")
        output.append(
            {
                "label": label,
                "queries": sorted({row.query for row in items if row.query}),
                "primary_page": pages.most_common(1)[0][0] if pages else None,
                "clicks": round(clicks, 2),
                "impressions": round(impressions, 2),
                "ctr": round(clicks / impressions, 6) if impressions else 0.0,
                "position": round(weighted_position / weight, 2) if weight else 0.0,
                "query_count": len({row.query for row in items if row.query}),
            }
        )
    output.sort(key=lambda item: (item["impressions"], item["query_count"]), reverse=True)
    return output[: payload.limit]


def build_index_coverage(crawl_payload: dict[str, Any]) -> dict[str, Any]:
    pages = crawl_payload.get("pages", [])
    issues = crawl_payload.get("issues", [])
    total = len(pages)
    indexable = [page for page in pages if bool(page.get("indexable", True))]
    non_indexable = [page for page in pages if not bool(page.get("indexable", True))]
    errors = [page for page in pages if int(page.get("status_code", 0) or 0) >= 400]
    issue_counts = Counter(str(issue.get("key", "unknown")) for issue in issues)
    orphan_urls = []
    for issue in issues:
        if str(issue.get("key", "")).casefold() in {"sitemap_orphan", "sitemap_orphan_candidate"}:
            if issue.get("url"):
                orphan_urls.append(issue["url"])
            orphan_urls.extend(issue.get("related_urls", []) or [])
    return {
        "total_pages": total,
        "indexable_pages": len(indexable),
        "non_indexable_pages": len(non_indexable),
        "http_error_pages": len(errors),
        "indexable_ratio": round(len(indexable) / total, 4) if total else 0.0,
        "sitemap_orphan_candidates": len(set(orphan_urls)),
        "issue_counts": dict(issue_counts.most_common(25)),
        "samples": {
            "non_indexable": [page.get("url") for page in non_indexable[:20]],
            "http_errors": [page.get("url") for page in errors[:20]],
            "sitemap_orphans": sorted(set(orphan_urls))[:20],
        },
        "note": "Coverage is derived from locally stored crawl evidence; it is not a substitute for Google index coverage data.",
    }


def merge_change_reviews(changes: list[dict[str, Any]], reviews: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for change in changes:
        item = dict(change)
        item["review"] = reviews.get(str(change.get("id")))
        output.append(item)
    return output


def render_executive_html(report: dict[str, Any]) -> str:
    search = report.get("search", {})
    crawl = report.get("crawl", {})
    opportunities = report.get("top_opportunities", [])
    alerts = report.get("alerts", [])

    def esc(value: Any) -> str:
        return html.escape(str(value if value is not None else "—"))

    opportunity_rows = "".join(
        f"<tr><td>{esc(item.get('query'))}</td><td>{esc(item.get('page'))}</td><td>{esc(item.get('priority'))}</td><td>{esc(item.get('recommended_action'))}</td></tr>"
        for item in opportunities
    ) or "<tr><td colspan='4'>No opportunity evidence available.</td></tr>"
    alert_rows = "".join(
        f"<li><strong>{esc(item.get('severity'))}</strong> — {esc(item.get('detail'))}</li>"
        for item in alerts
    ) or "<li>No current alert evidence.</li>"

    return f"""<!doctype html>
<html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>NEXVARY SEO Executive Report</title><style>
body{{font-family:Arial,Tahoma,sans-serif;background:#f5f7fb;color:#122033;margin:0;padding:32px}}main{{max-width:1100px;margin:auto;background:#fff;padding:32px;border-radius:18px}}h1,h2{{color:#0a2a4d}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.card{{border:1px solid #d9e2ee;padding:16px;border-radius:12px}}table{{width:100%;border-collapse:collapse}}th,td{{border:1px solid #d9e2ee;padding:9px;text-align:right}}@media(max-width:700px){{.grid{{grid-template-columns:1fr 1fr}}body{{padding:10px}}}}
</style></head><body><main>
<h1>NEXVARY SEO Autopilot — Executive Report</h1><p><strong>Site:</strong> {esc(report.get('site'))}</p>
<div class='grid'><div class='card'><b>Clicks</b><div>{esc(search.get('clicks', 0))}</div></div><div class='card'><b>Impressions</b><div>{esc(search.get('impressions', 0))}</div></div><div class='card'><b>CTR</b><div>{esc(search.get('ctr', 0))}</div></div><div class='card'><b>Avg Position</b><div>{esc(search.get('position', 0))}</div></div></div>
<h2>Crawl health</h2><div class='grid'><div class='card'><b>Pages</b><div>{esc(crawl.get('pages_crawled', 0))}</div></div><div class='card'><b>Issues</b><div>{esc(crawl.get('issues', 0))}</div></div><div class='card'><b>Indexable</b><div>{esc(crawl.get('indexable_pages', 0))}</div></div></div>
<h2>Top opportunities</h2><table><thead><tr><th>Query</th><th>Page</th><th>Priority</th><th>Action</th></tr></thead><tbody>{opportunity_rows}</tbody></table>
<h2>Alerts</h2><ul>{alert_rows}</ul><p>{esc(report.get('note', ''))}</p>
</main></body></html>"""
