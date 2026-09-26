from __future__ import annotations

import os

from .models import SearchConsoleSyncRequest, SearchConsoleSyncResult
from .search_console import SearchConsoleClient
from .storage import RepositoryStore


async def sync_search_console(
    request: SearchConsoleSyncRequest,
    store: RepositoryStore,
) -> SearchConsoleSyncResult:
    token = os.getenv("GOOGLE_SEARCH_CONSOLE_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "GOOGLE_SEARCH_CONSOLE_TOKEN is not configured; credentials are runtime-only and "
            "must not be committed to the repository"
        )

    client = SearchConsoleClient(token, allow_write=False)
    site_url = str(request.site_url)
    rows = await client.search_analytics(
        site_url,
        request.start_date,
        request.end_date,
        dimensions=list(request.dimensions),
        row_limit=request.row_limit,
    )
    metric_set_id = store.save_metrics(site_url, rows)
    return SearchConsoleSyncResult(
        site_url=site_url,
        start_date=request.start_date,
        end_date=request.end_date,
        rows_saved=len(rows),
        metric_set_id=metric_set_id,
        dimensions=list(request.dimensions),
    )
