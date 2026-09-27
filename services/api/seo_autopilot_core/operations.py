from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import httpx

from .cms import CMSAdapter
from .models import ChangePlan, ChangePreview, RiskLevel, SitePolicy
from .policy import evaluate_change_policy, site_root
from .storage import RepositoryStore


def state_hash(state: dict) -> str:
    raw = json.dumps(state, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def preview_change(
    plan: ChangePlan,
    adapter: CMSAdapter,
    policy: SitePolicy,
) -> ChangePreview:
    current = await adapter.read_state(plan.url, plan.action)
    if current != plan.before:
        raise RuntimeError("Target state changed after planning; preview is stale")

    approval_required = plan.risk != RiskLevel.safe_auto or not policy.safe_auto_enabled
    decision = evaluate_change_policy(
        plan,
        policy,
        approved=False,
        protected_override=False,
        daily_change_count=0,
    )
    return ChangePreview(
        change_id=plan.id,
        url=plan.url,
        action=plan.action,
        risk=plan.risk,
        state_hash=state_hash(current),
        before=current,
        after=plan.after,
        live_write_eligible=decision.allowed,
        approval_required=approval_required,
    )


async def apply_change(
    plan: ChangePlan,
    adapter: CMSAdapter,
    store: RepositoryStore,
    policy: SitePolicy,
    *,
    expected_state_hash: str,
    approved: bool,
    protected_override: bool,
) -> dict:
    site = site_root(plan.url)
    since = datetime.now(UTC) - timedelta(hours=24)
    daily_count = store.count_applied_changes_since(site, since)
    decision = evaluate_change_policy(
        plan,
        policy,
        approved=approved,
        protected_override=protected_override,
        daily_change_count=daily_count,
    )
    if not decision.allowed:
        raise PermissionError(decision.reason)

    current = await adapter.read_state(plan.url, plan.action)
    if current != plan.before:
        raise RuntimeError("Target state changed after planning; refusing stale write")
    if state_hash(current) != expected_state_hash:
        raise RuntimeError("Preview hash no longer matches current state")
    if not store.claim_change_for_apply(plan.id):
        raise RuntimeError("Change is no longer in planned state; refusing duplicate apply")

    backup_id = store.save_backup(plan.id, site, plan.url, plan.action, current)
    try:
        result = await adapter.apply(plan.url, plan.action, plan.after)
        verified = await adapter.read_state(plan.url, plan.action)
    except Exception:
        store.update_change_status(plan.id, "apply_failed")
        raise

    if verified != plan.after:
        try:
            await adapter.rollback(plan.url, plan.action, current)
        except (RuntimeError, PermissionError, ValueError, httpx.HTTPError):
            store.update_change_status(plan.id, "verification_failed_rollback_failed")
            raise RuntimeError(
                "Post-write verification failed and emergency rollback also failed"
            ) from None
        store.update_change_status(plan.id, "verification_failed_rolled_back")
        raise RuntimeError("Post-write verification failed; change was rolled back")

    store.update_change_status(plan.id, "applied")
    return {
        "status": "applied",
        "change_id": plan.id,
        "backup_id": backup_id,
        "risk": plan.risk.value,
        "result": result,
        "verified_state_hash": state_hash(verified),
        "daily_change_count": daily_count + 1,
    }


async def rollback_change(
    plan: ChangePlan,
    adapter: CMSAdapter,
    store: RepositoryStore,
    *,
    approved: bool,
) -> dict:
    if not approved:
        raise PermissionError("Rollback requires explicit approval")
    backup = store.latest_backup(plan.id)
    if backup is None:
        raise RuntimeError("No rollback backup exists for this change")
    if not store.claim_change_for_rollback(plan.id):
        raise RuntimeError("Only an applied change can be rolled back")

    before = backup["payload"]
    try:
        result = await adapter.rollback(plan.url, plan.action, before)
        verified = await adapter.read_state(plan.url, plan.action)
    except Exception:
        store.update_change_status(plan.id, "rollback_failed")
        raise

    if verified != before:
        store.update_change_status(plan.id, "rollback_verification_failed")
        raise RuntimeError("Rollback verification failed")

    store.update_change_status(plan.id, "rolled_back")
    return {
        "status": "rolled_back",
        "change_id": plan.id,
        "backup_id": backup["id"],
        "result": result,
        "verified_state_hash": state_hash(verified),
    }
