from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from .models import ChangePlan, RiskLevel, SitePolicy

TRUE_VALUES = {"1", "true", "yes", "on"}


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().casefold() in TRUE_VALUES


def _normalize_host(value: str) -> str:
    candidate = value.strip().casefold()
    if not candidate:
        return ""
    if "://" in candidate:
        candidate = urlparse(candidate).hostname or ""
    return candidate.rstrip(".")


def _host_from_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("A valid absolute http/https URL is required")
    return _normalize_host(parsed.hostname)


def site_root(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("A valid absolute http/https URL is required")
    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname}{port}/"


def load_site_policy(site_url: str) -> SitePolicy:
    host = _host_from_url(site_url)
    configured_hosts = [
        _normalize_host(item)
        for item in os.getenv("SEO_ALLOWED_HOSTS", "").split(",")
        if _normalize_host(item)
    ]
    max_daily_raw = os.getenv("SEO_MAX_DAILY_CHANGES", "5")
    try:
        max_daily_changes = max(1, min(int(max_daily_raw), 100))
    except ValueError:
        max_daily_changes = 5

    return SitePolicy(
        site_url=site_root(site_url),
        allowed_hosts=list(dict.fromkeys(configured_hosts or [host])),
        live_writes_enabled=_env_bool("SEO_ENABLE_LIVE_WRITES"),
        safe_auto_enabled=_env_bool("SEO_ENABLE_SAFE_AUTO"),
        protected_writes_enabled=_env_bool("SEO_ENABLE_PROTECTED_WRITES"),
        auto_rollback_enabled=_env_bool("SEO_ENABLE_AUTO_ROLLBACK", default=True),
        max_daily_changes=max_daily_changes,
    )


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


def evaluate_change_policy(
    plan: ChangePlan,
    policy: SitePolicy,
    *,
    approved: bool,
    protected_override: bool,
    daily_change_count: int = 0,
) -> PolicyDecision:
    host = _host_from_url(plan.url)
    allowed_hosts = {_normalize_host(item) for item in policy.allowed_hosts}

    if host not in allowed_hosts:
        return PolicyDecision(False, f"Host {host!r} is not in SEO_ALLOWED_HOSTS")
    if plan.dry_run:
        return PolicyDecision(False, "Dry-run plans cannot be applied; create a write-enabled plan")
    if not policy.live_writes_enabled:
        return PolicyDecision(False, "Live writes are disabled by SEO_ENABLE_LIVE_WRITES")
    if daily_change_count >= policy.max_daily_changes:
        return PolicyDecision(False, "Daily live-change limit reached")

    if plan.risk == RiskLevel.safe_auto:
        if policy.safe_auto_enabled or approved:
            return PolicyDecision(True, "Safe change is allowed")
        return PolicyDecision(False, "Safe auto is disabled and explicit approval was not supplied")

    if plan.risk == RiskLevel.review_required:
        if approved:
            return PolicyDecision(True, "Review-required change has explicit approval")
        return PolicyDecision(False, "This change requires explicit approval")

    if not policy.protected_writes_enabled:
        return PolicyDecision(False, "Protected writes are globally disabled")
    if not (approved and protected_override):
        return PolicyDecision(False, "Protected change requires approval and protected override")
    return PolicyDecision(True, "Protected write has both explicit gates")
