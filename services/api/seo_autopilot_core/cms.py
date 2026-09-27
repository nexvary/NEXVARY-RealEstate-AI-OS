from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from urllib.parse import urljoin, urlparse

import httpx

from .audit import _validate_public_url


class CMSBridgeError(RuntimeError):
    pass


class CMSAdapter(Protocol):
    async def read_state(self, url: str, action: str) -> dict: ...

    async def apply(self, url: str, action: str, after: dict) -> dict: ...

    async def rollback(self, url: str, action: str, before: dict) -> dict: ...


@dataclass
class MemoryCMSAdapter:
    """In-memory CMS used for deterministic tests; it never touches a live website."""

    state: dict[tuple[str, str], dict] = field(default_factory=dict)

    async def read_state(self, url: str, action: str) -> dict:
        return self.state.get((url, action), {}).copy()

    async def apply(self, url: str, action: str, after: dict) -> dict:
        self.state[(url, action)] = after.copy()
        return after.copy()

    async def rollback(self, url: str, action: str, before: dict) -> dict:
        self.state[(url, action)] = before.copy()
        return before.copy()


class CompanionCMSAdapter:
    """Adapter for a dedicated site-side SEO bridge.

    The bridge is intentionally generic: the website owns the actual CMS-specific implementation.
    This client never stores its token and refuses writes unless live_writes_enabled is true.
    """

    def __init__(
        self,
        bridge_url: str,
        access_token: str,
        *,
        allowed_hosts: list[str],
        live_writes_enabled: bool = False,
        timeout_seconds: float = 20.0,
    ) -> None:
        parsed = urlparse(bridge_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("SEO_CMS_BRIDGE_URL must be an absolute HTTPS URL")
        if not access_token.strip():
            raise ValueError("SEO_CMS_BRIDGE_TOKEN is required")
        hosts = {item.strip().casefold().rstrip(".") for item in allowed_hosts if item.strip()}
        if not hosts:
            raise ValueError("At least one allowed website host is required")

        self.bridge_url = bridge_url.rstrip("/") + "/"
        self.access_token = access_token
        self.allowed_hosts = hosts
        self.live_writes_enabled = live_writes_enabled
        self.timeout = httpx.Timeout(timeout_seconds)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _validate_target_host(self, target_url: str) -> None:
        parsed = urlparse(target_url)
        host = (parsed.hostname or "").casefold().rstrip(".")
        if parsed.scheme not in {"http", "https"} or not host:
            raise ValueError("Target URL must be absolute http/https")
        if host not in self.allowed_hosts:
            raise PermissionError(f"Target host {host!r} is not allowed")

    async def _request(self, method: str, endpoint: str, payload: dict) -> dict:
        request_url = urljoin(self.bridge_url, endpoint.lstrip("/"))
        await _validate_public_url(request_url)
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.request(method, request_url, json=payload)
        if response.status_code >= 400:
            detail = response.text[:1000]
            raise CMSBridgeError(f"CMS bridge returned {response.status_code}: {detail}")
        if not response.content:
            return {}
        try:
            data = response.json()
        except ValueError as exc:
            raise CMSBridgeError("CMS bridge returned invalid JSON") from exc
        if not isinstance(data, dict):
            raise CMSBridgeError("CMS bridge response must be a JSON object")
        return data

    async def read_state(self, url: str, action: str) -> dict:
        self._validate_target_host(url)
        data = await self._request("POST", "state", {"url": url, "action": action})
        state = data.get("state", data)
        if not isinstance(state, dict):
            raise CMSBridgeError("CMS bridge state must be a JSON object")
        return state

    async def apply(self, url: str, action: str, after: dict) -> dict:
        self._validate_target_host(url)
        if not self.live_writes_enabled:
            raise PermissionError("CMS bridge live writes are disabled")
        return await self._request(
            "POST",
            "apply",
            {"url": url, "action": action, "after": after},
        )

    async def rollback(self, url: str, action: str, before: dict) -> dict:
        self._validate_target_host(url)
        if not self.live_writes_enabled:
            raise PermissionError("CMS bridge live writes are disabled")
        return await self._request(
            "POST",
            "rollback",
            {"url": url, "action": action, "before": before},
        )
