from __future__ import annotations

import os

from .cms import CompanionCMSAdapter
from .models import SitePolicy


def build_runtime_cms_adapter(policy: SitePolicy) -> CompanionCMSAdapter:
    bridge_url = os.getenv("SEO_CMS_BRIDGE_URL", "").strip()
    bridge_token = os.getenv("SEO_CMS_BRIDGE_TOKEN", "").strip()
    if not bridge_url or not bridge_token:
        raise RuntimeError(
            "CMS bridge is not configured. Set SEO_CMS_BRIDGE_URL and SEO_CMS_BRIDGE_TOKEN at runtime."
        )
    return CompanionCMSAdapter(
        bridge_url,
        bridge_token,
        allowed_hosts=policy.allowed_hosts,
        live_writes_enabled=policy.live_writes_enabled,
    )
