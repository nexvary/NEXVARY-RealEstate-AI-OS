from __future__ import annotations

from datetime import date
from urllib.parse import quote

import httpx

from .models import SearchMetricRow

WEBMASTERS_BASE = "https://www.googleapis.com/webmasters/v3"
INSPECTION_URL = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
READONLY_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
WRITE_SCOPE = "https://www.googleapis.com/auth/webmasters"


class SearchConsoleError(RuntimeError):
    pass


class SearchConsoleClient:
    """REST adapter. Tokens are supplied at runtime and never persisted by this class."""

    def __init__(
        self,
        access_token: str,
        *,
        allow_write: bool = False,
        timeout_seconds: float = 20.0,
    ) -> None:
        if not access_token.strip():
            raise ValueError("An OAuth access token is required")
        self.access_token = access_token
        self.allow_write = allow_write
        self.timeout = httpx.Timeout(timeout_seconds)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            response = await client.request(method, url, **kwargs)
        if response.status_code >= 400:
            detail = response.text[:1000]
            raise SearchConsoleError(f"Search Console API returned {response.status_code}: {detail}")
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise SearchConsoleError("Search Console API returned invalid JSON") from exc

    async def search_analytics(
        self,
        site_url: str,
        start_date: date,
        end_date: date,
        *,
        dimensions: list[str] | None = None,
        search_type: str = "web",
        row_limit: int = 25000,
        start_row: int = 0,
        data_state: str = "final",
    ) -> list[SearchMetricRow]:
        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        dimensions = dimensions or ["query", "page"]
        allowed = {"query", "page", "country", "device", "searchAppearance", "date", "hour"}
        invalid = set(dimensions) - allowed
        if invalid:
            raise ValueError(f"Unsupported Search Console dimensions: {sorted(invalid)}")
        row_limit = max(1, min(int(row_limit), 25000))
        encoded_site = quote(site_url, safe="")
        url = f"{WEBMASTERS_BASE}/sites/{encoded_site}/searchAnalytics/query"
        payload = {
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": dimensions,
            "type": search_type,
            "rowLimit": row_limit,
            "startRow": max(0, int(start_row)),
            "dataState": data_state,
        }
        data = await self._request("POST", url, json=payload)
        output: list[SearchMetricRow] = []
        for raw in data.get("rows", []):
            keys = raw.get("keys", [])
            values = {name: keys[index] for index, name in enumerate(dimensions) if index < len(keys)}
            output.append(
                SearchMetricRow(
                    query=values.get("query"),
                    page=values.get("page"),
                    country=values.get("country"),
                    device=values.get("device"),
                    search_appearance=values.get("searchAppearance"),
                    clicks=float(raw.get("clicks", 0)),
                    impressions=float(raw.get("impressions", 0)),
                    ctr=float(raw.get("ctr", 0)),
                    position=float(raw.get("position", 0)),
                )
            )
        return output

    async def inspect_url(
        self,
        site_url: str,
        inspection_url: str,
        language_code: str = "en-US",
    ) -> dict:
        payload = {
            "inspectionUrl": inspection_url,
            "siteUrl": site_url,
            "languageCode": language_code,
        }
        return await self._request("POST", INSPECTION_URL, json=payload)

    async def list_sitemaps(self, site_url: str) -> list[dict]:
        encoded_site = quote(site_url, safe="")
        url = f"{WEBMASTERS_BASE}/sites/{encoded_site}/sitemaps"
        data = await self._request("GET", url)
        return list(data.get("sitemap", []))

    async def submit_sitemap(self, site_url: str, sitemap_url: str) -> None:
        if not self.allow_write:
            raise PermissionError(
                "Sitemap submission is disabled. Recreate the client with allow_write=True only "
                "after explicit approval and a webmasters write-scope token."
            )
        encoded_site = quote(site_url, safe="")
        encoded_feed = quote(sitemap_url, safe="")
        url = f"{WEBMASTERS_BASE}/sites/{encoded_site}/sitemaps/{encoded_feed}"
        await self._request("PUT", url)
