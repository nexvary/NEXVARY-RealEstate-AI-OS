from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urlparse

from .models import ChangePlan, RiskLevel

SAFE_ACTIONS = {
    "meta_description_add",
    "lang_attribute_add",
    "image_alt_attribute_add",
    "sitemap_refresh_local",
    "schema_deterministic_add",
}
REVIEW_ACTIONS = {
    "title_change",
    "meta_description_rewrite",
    "internal_link_insert",
    "content_update",
    "schema_content_change",
    "canonical_single_page_change",
}
PROTECTED_ACTIONS = {
    "url_change",
    "delete_page",
    "redirect_create",
    "redirect_bulk_change",
    "robots_change",
    "noindex_change",
    "canonical_bulk_change",
}


class WriteAdapter(Protocol):
    async def read_state(self, url: str, action: str) -> dict: ...

    async def apply(self, url: str, action: str, after: dict) -> dict: ...

    async def rollback(self, url: str, action: str, before: dict) -> dict: ...


def classify_risk(action: str) -> RiskLevel:
    if action in SAFE_ACTIONS:
        return RiskLevel.safe_auto
    if action in REVIEW_ACTIONS:
        return RiskLevel.review_required
    return RiskLevel.protected


def create_change_plan(
    url: str,
    action: str,
    before: dict,
    after: dict,
    reason: str,
    *,
    dry_run: bool = True,
) -> ChangePlan:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Change plans require an absolute http/https URL")
    if before == after:
        raise ValueError("Change plan has no effective difference")
    risk = classify_risk(action)
    return ChangePlan(
        id=str(uuid.uuid4()),
        url=url,
        action=action,
        risk=risk,
        reason=reason,
        before=before,
        after=after,
        rollback=before.copy(),
        dry_run=dry_run,
    )


async def execute_change(
    plan: ChangePlan,
    adapter: WriteAdapter,
    *,
    approved: bool = False,
    allow_protected: bool = False,
) -> dict:
    current = await adapter.read_state(plan.url, plan.action)
    if current != plan.before:
        raise RuntimeError("Target state changed after planning; refusing stale write")

    if plan.dry_run:
        return {
            "status": "dry_run",
            "change_id": plan.id,
            "risk": plan.risk.value,
            "would_apply": plan.after,
        }

    if plan.risk == RiskLevel.review_required and not approved:
        raise PermissionError("This change requires explicit approval")
    if plan.risk == RiskLevel.protected and not (approved and allow_protected):
        raise PermissionError("Protected change requires explicit approval and protected override")

    result = await adapter.apply(plan.url, plan.action, plan.after)
    return {
        "status": "applied",
        "change_id": plan.id,
        "risk": plan.risk.value,
        "result": result,
    }


async def rollback_change(
    plan: ChangePlan,
    adapter: WriteAdapter,
    *,
    approved: bool = False,
) -> dict:
    if not approved:
        raise PermissionError("Rollback requires explicit approval")
    result = await adapter.rollback(plan.url, plan.action, plan.rollback)
    return {
        "status": "rolled_back",
        "change_id": plan.id,
        "result": result,
    }


@dataclass
class MemoryWriteAdapter:
    """Deterministic adapter for tests and demonstrations; never writes to a live website."""

    state: dict[tuple[str, str], dict] = field(default_factory=dict)

    async def read_state(self, url: str, action: str) -> dict:
        return self.state.get((url, action), {}).copy()

    async def apply(self, url: str, action: str, after: dict) -> dict:
        self.state[(url, action)] = after.copy()
        return after.copy()

    async def rollback(self, url: str, action: str, before: dict) -> dict:
        self.state[(url, action)] = before.copy()
        return before.copy()
