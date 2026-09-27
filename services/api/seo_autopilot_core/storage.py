from __future__ import annotations

import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import ChangePlan, CrawlReport, SearchMetricRow


class RepositoryStore:
    """SQLite persistence for history, metrics, change plans and rollback backups."""

    def __init__(self, path: str | Path | None = None) -> None:
        configured = path or os.getenv("SEO_DATA_PATH", "data/seo-autopilot.db")
        self.path = Path(configured)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kind TEXT NOT NULL,
                    site TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_snapshots_site_kind_created
                ON snapshots(site, kind, created_at DESC);

                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site TEXT NOT NULL,
                    measured_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_metrics_site_created
                ON metrics(site, measured_at DESC);

                CREATE TABLE IF NOT EXISTS changes (
                    id TEXT PRIMARY KEY,
                    site TEXT NOT NULL,
                    url TEXT NOT NULL,
                    action TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    applied_at TEXT,
                    rolled_back_at TEXT,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_changes_site_created
                ON changes(site, created_at DESC);

                CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    change_id TEXT NOT NULL,
                    site TEXT NOT NULL,
                    url TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_backups_change_created
                ON backups(change_id, created_at DESC);
                """
            )

    @staticmethod
    def _dump(value: BaseModel | dict | list) -> str:
        if isinstance(value, BaseModel):
            payload = value.model_dump(mode="json")
        else:
            payload = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    def save_crawl(self, report: CrawlReport) -> int:
        return self.save_snapshot("crawl", report.root_url, report)

    def save_snapshot(self, kind: str, site: str, payload: BaseModel | dict | list) -> int:
        created_at = datetime.now(UTC).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO snapshots(kind, site, created_at, payload) VALUES (?, ?, ?, ?)",
                (kind, site, created_at, self._dump(payload)),
            )
            return int(cursor.lastrowid)

    def recent_snapshots(self, site: str, kind: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, kind, site, created_at, payload
                FROM snapshots
                WHERE site = ? AND kind = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (site, kind, max(1, min(limit, 100))),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "kind": row["kind"],
                "site": row["site"],
                "created_at": row["created_at"],
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def save_metrics(self, site: str, rows: list[SearchMetricRow]) -> int:
        measured_at = datetime.now(UTC).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO metrics(site, measured_at, payload) VALUES (?, ?, ?)",
                (site, measured_at, self._dump([row.model_dump(mode="json") for row in rows])),
            )
            return int(cursor.lastrowid)

    def recent_metric_sets(self, site: str, limit: int = 2) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, measured_at, payload
                FROM metrics
                WHERE site = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (site, max(1, min(limit, 50))),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "measured_at": row["measured_at"],
                "rows": json.loads(row["payload"]),
            }
            for row in rows
        ]

    def record_change(self, site: str, plan: ChangePlan, status: str = "planned") -> None:
        with self._connect() as db:
            db.execute(
                """
                INSERT OR REPLACE INTO changes(
                    id, site, url, action, risk, status, created_at, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.id,
                    site,
                    plan.url,
                    plan.action,
                    plan.risk.value,
                    status,
                    datetime.now(UTC).isoformat(),
                    self._dump(plan),
                ),
            )

    def get_change(self, change_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT id, site, url, action, risk, status, created_at,
                       applied_at, rolled_back_at, payload
                FROM changes
                WHERE id = ?
                """,
                (change_id,),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["payload"] = json.loads(row["payload"])
        return result

    def update_change_status(self, change_id: str, status: str) -> bool:
        now = datetime.now(UTC).isoformat()
        with self._connect() as db:
            if status == "applied":
                cursor = db.execute(
                    "UPDATE changes SET status = ?, applied_at = ? WHERE id = ?",
                    (status, now, change_id),
                )
            elif status == "rolled_back":
                cursor = db.execute(
                    "UPDATE changes SET status = ?, rolled_back_at = ? WHERE id = ?",
                    (status, now, change_id),
                )
            else:
                cursor = db.execute(
                    "UPDATE changes SET status = ? WHERE id = ?",
                    (status, change_id),
                )
            return cursor.rowcount > 0

    def claim_change_for_apply(self, change_id: str) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE changes SET status = 'applying' WHERE id = ? AND status = 'planned'",
                (change_id,),
            )
            return cursor.rowcount == 1

    def claim_change_for_rollback(self, change_id: str) -> bool:
        with self._connect() as db:
            cursor = db.execute(
                "UPDATE changes SET status = 'rolling_back' WHERE id = ? AND status = 'applied'",
                (change_id,),
            )
            return cursor.rowcount == 1

    def count_applied_changes_since(self, site: str, since: datetime) -> int:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT COUNT(*) AS count
                FROM changes
                WHERE site = ? AND status = 'applied' AND applied_at >= ?
                """,
                (site, since.isoformat()),
            ).fetchone()
        return int(row["count"] if row else 0)

    def save_backup(
        self,
        change_id: str,
        site: str,
        url: str,
        action: str,
        state: dict,
    ) -> int:
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO backups(change_id, site, url, action, created_at, payload)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    change_id,
                    site,
                    url,
                    action,
                    datetime.now(UTC).isoformat(),
                    self._dump(state),
                ),
            )
            return int(cursor.lastrowid)

    def latest_backup(self, change_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT id, change_id, site, url, action, created_at, payload
                FROM backups
                WHERE change_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (change_id,),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["payload"] = json.loads(row["payload"])
        return result

    def change_history(self, site: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT id, url, action, risk, status, created_at, applied_at, rolled_back_at, payload
                FROM changes
                WHERE site = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (site, max(1, min(limit, 200))),
            ).fetchall()
        return [
            {
                **dict(row),
                "payload": json.loads(row["payload"]),
            }
            for row in rows
        ]
