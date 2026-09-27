from __future__ import annotations

import asyncio
import re
from collections import defaultdict, deque
from datetime import UTC, datetime
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from defusedxml.common import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

from .audit import USER_AGENT, _extract_snapshot, _validate_public_url
from .models import CrawlIssue, CrawlPage, CrawlReport, Severity

MAX_DISCOVERED_SITEMAPS = 25
MAX_SITEMAP_URLS = 5000
MAX_TEXT_BYTES = 2_000_000
ROBOT_USER_AGENT = "NEXVARY-SEO-Autopilot"


def _normalize_url(url: str) -> str:
    clean, _ = urldefrag(url)
    parsed = urlparse(clean)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    port = parsed.port
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"
    path = parsed.path or "/"
    return parsed._replace(scheme=scheme, netloc=netloc, path=path, fragment="").geturl()


def _same_site(candidate: str, root: str) -> bool:
    return (urlparse(candidate).hostname or "").lower() == (urlparse(root).hostname or "").lower()


async def _fetch_text(url: str, accept: str = "*/*") -> tuple[int, str, str]:
    current = url
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15.0),
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        follow_redirects=False,
    ) as client:
        for _ in range(6):
            await _validate_public_url(current)
            async with client.stream("GET", current) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        return response.status_code, current, ""
                    current = urljoin(current, location)
                    continue

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_TEXT_BYTES:
                        raise ValueError("Response exceeds crawler size limit")
                encoding = response.encoding or "utf-8"
                return response.status_code, str(response.url), bytes(body).decode(
                    encoding, errors="replace"
                )
    raise httpx.TooManyRedirects("Too many redirects")


def _parse_robots(text: str, robots_url: str) -> tuple[RobotFileParser, list[str]]:
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(text.splitlines())
    sitemaps: list[str] = []
    for line in text.splitlines():
        match = re.match(r"\s*sitemap\s*:\s*(\S+)", line, flags=re.IGNORECASE)
        if match:
            sitemaps.append(match.group(1).strip())
    return parser, list(dict.fromkeys(sitemaps))[:MAX_DISCOVERED_SITEMAPS]


def _parse_sitemap_xml(text: str) -> tuple[list[str], list[str]]:
    try:
        root = fromstring(text)
    except (ParseError, DefusedXmlException):
        return [], []

    tag = root.tag.rsplit("}", 1)[-1].lower()
    locations = [
        (node.text or "").strip()
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1].lower() == "loc" and (node.text or "").strip()
    ]
    if tag == "sitemapindex":
        return [], locations[:MAX_DISCOVERED_SITEMAPS]
    if tag == "urlset":
        return locations[:MAX_SITEMAP_URLS], []
    return [], []


def _extract_links(base_url: str, html: str) -> tuple[list[str], int]:
    soup = BeautifulSoup(html, "html.parser")
    internal: list[str] = []
    external = 0
    host = (urlparse(base_url).hostname or "").lower()
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:")):
            continue
        absolute = _normalize_url(urljoin(base_url, href))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if parsed.hostname.lower() == host:
            internal.append(absolute)
        else:
            external += 1
    return list(dict.fromkeys(internal)), external


async def _discover_sitemaps(root_url: str, robots_sitemaps: list[str]) -> tuple[list[str], list[str]]:
    queue = deque(robots_sitemaps or [urljoin(root_url, "/sitemap.xml")])
    seen_sitemaps: set[str] = set()
    readable_sitemaps: list[str] = []
    page_urls: list[str] = []

    while queue and len(seen_sitemaps) < MAX_DISCOVERED_SITEMAPS:
        sitemap_url = _normalize_url(queue.popleft())
        if sitemap_url in seen_sitemaps or not _same_site(sitemap_url, root_url):
            continue
        seen_sitemaps.add(sitemap_url)
        try:
            status, _, text = await _fetch_text(sitemap_url, "application/xml,text/xml,*/*")
        except (httpx.HTTPError, ValueError):
            continue
        if not 200 <= status < 300:
            continue
        urls, nested = _parse_sitemap_xml(text)
        if not urls and not nested:
            continue
        readable_sitemaps.append(sitemap_url)
        for candidate in urls:
            normalized = _normalize_url(candidate)
            if _same_site(normalized, root_url) and normalized not in page_urls:
                page_urls.append(normalized)
                if len(page_urls) >= MAX_SITEMAP_URLS:
                    break
        for child in nested:
            if len(seen_sitemaps) + len(queue) < MAX_DISCOVERED_SITEMAPS:
                queue.append(child)
    return readable_sitemaps, page_urls


async def crawl_site(root_url: str, max_pages: int = 100, concurrency: int = 5) -> CrawlReport:
    root_url = _normalize_url(root_url)
    await _validate_public_url(root_url)
    started_at = datetime.now(UTC)
    robots_url = urljoin(root_url, "/robots.txt")
    robots_found = False
    robots_parser = RobotFileParser()
    robots_parser.parse([])
    robots_sitemaps: list[str] = []
    issues: list[CrawlIssue] = []

    try:
        status, _, robots_text = await _fetch_text(robots_url, "text/plain,*/*")
        if 200 <= status < 300:
            robots_found = True
            robots_parser, robots_sitemaps = _parse_robots(robots_text, robots_url)
    except (httpx.HTTPError, ValueError):
        issues.append(
            CrawlIssue(
                key="robots_fetch_error",
                severity=Severity.low,
                url=robots_url,
                detail="robots.txt could not be fetched; crawling continues conservatively.",
            )
        )

    crawl_delay = 0.0
    if robots_found:
        crawl_delay = float(
            robots_parser.crawl_delay(ROBOT_USER_AGENT)
            or robots_parser.crawl_delay("*")
            or 0
        )
        crawl_delay = min(crawl_delay, 10.0)

    discovered_sitemaps, sitemap_urls = await _discover_sitemaps(root_url, robots_sitemaps)
    if not discovered_sitemaps:
        issues.append(
            CrawlIssue(
                key="sitemap_missing",
                severity=Severity.medium,
                url=root_url,
                detail="No readable XML sitemap was discovered.",
            )
        )

    seed_urls = [root_url, *sitemap_urls]
    queue: deque[tuple[str, int]] = deque()
    queued: set[str] = set()
    for seed in seed_urls:
        normalized = _normalize_url(seed)
        if normalized not in queued:
            queued.add(normalized)
            queue.append((normalized, 0 if normalized == root_url else 1))
        if len(queue) >= max_pages:
            break

    pages: list[CrawlPage] = []
    fetched: set[str] = set()
    discovered_edges: dict[str, list[str]] = {}
    effective_concurrency = 1 if crawl_delay > 0 else concurrency
    semaphore = asyncio.Semaphore(effective_concurrency)

    async def fetch_page(
        url: str,
        depth: int,
    ) -> tuple[CrawlPage | None, list[str], CrawlIssue | None]:
        if robots_found and not robots_parser.can_fetch(ROBOT_USER_AGENT, url):
            return None, [], CrawlIssue(
                key="blocked_by_robots",
                severity=Severity.info,
                url=url,
                detail="URL is blocked for this crawler by robots.txt.",
            )
        async with semaphore:
            if crawl_delay > 0:
                await asyncio.sleep(crawl_delay)
            try:
                status, final_url, html = await _fetch_text(url, "text/html,application/xhtml+xml")
            except (httpx.HTTPError, ValueError) as exc:
                return None, [], CrawlIssue(
                    key="fetch_error",
                    severity=Severity.high,
                    url=url,
                    detail=f"Fetch failed: {exc}",
                )

        content_prefix = html[:2000].lower()
        content_type_like_html = "<html" in content_prefix or "<!doctype html" in content_prefix
        if not content_type_like_html:
            return CrawlPage(url=url, status_code=status, depth=depth, indexable=False), [], None

        response = httpx.Response(status, request=httpx.Request("GET", final_url))
        snapshot = _extract_snapshot(url, response, html)
        links, external_count = _extract_links(final_url, html)
        robots_meta = (snapshot.robots_meta or "").lower()
        indexable = status == 200 and "noindex" not in robots_meta
        page = CrawlPage(
            url=url,
            status_code=status,
            depth=depth,
            title=snapshot.title,
            meta_description=snapshot.meta_description,
            canonical=snapshot.canonical,
            language=snapshot.language,
            h1_count=snapshot.h1_count,
            word_count=snapshot.word_count,
            internal_links=len(links),
            external_links=external_count,
            images=snapshot.images,
            images_missing_alt=snapshot.images_missing_alt,
            structured_data_types=snapshot.structured_data_types,
            hreflang_targets=snapshot.hreflang_targets,
            indexable=indexable,
        )
        return page, links, None

    while queue and len(fetched) < max_pages:
        batch: list[tuple[str, int]] = []
        while queue and len(batch) < effective_concurrency and len(fetched) + len(batch) < max_pages:
            url, depth = queue.popleft()
            if url not in fetched:
                batch.append((url, depth))
        if not batch:
            continue

        results = await asyncio.gather(*(fetch_page(url, depth) for url, depth in batch))
        for (url, depth), (page, links, issue) in zip(batch, results, strict=True):
            fetched.add(url)
            if issue:
                issues.append(issue)
            if page:
                pages.append(page)
            discovered_edges[url] = links
            for link in links:
                if link not in queued and link not in fetched and len(queued) < max_pages * 10:
                    queued.add(link)
                    queue.append((link, depth + 1))

    titles: dict[str, list[str]] = defaultdict(list)
    descriptions: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        if page.title:
            titles[page.title.strip().casefold()].append(page.url)
        if page.meta_description:
            descriptions[page.meta_description.strip().casefold()].append(page.url)
        if page.status_code >= 400:
            issues.append(
                CrawlIssue(
                    key="broken_internal_url",
                    severity=Severity.high,
                    url=page.url,
                    detail=f"Internal URL returned HTTP {page.status_code}.",
                )
            )
        if page.h1_count != 1 and page.indexable:
            issues.append(
                CrawlIssue(
                    key="h1_count",
                    severity=Severity.medium,
                    url=page.url,
                    detail=f"Indexable page has {page.h1_count} H1 elements.",
                )
            )
        if page.canonical and not _same_site(page.canonical, root_url):
            issues.append(
                CrawlIssue(
                    key="external_canonical",
                    severity=Severity.high,
                    url=page.url,
                    detail="Canonical points outside the crawled site.",
                    related_urls=[page.canonical],
                )
            )

    for group in titles.values():
        if len(group) > 1:
            issues.append(
                CrawlIssue(
                    key="duplicate_title",
                    severity=Severity.medium,
                    detail="Multiple pages share the same title.",
                    related_urls=group,
                )
            )
    for group in descriptions.values():
        if len(group) > 1:
            issues.append(
                CrawlIssue(
                    key="duplicate_description",
                    severity=Severity.low,
                    detail="Multiple pages share the same meta description.",
                    related_urls=group,
                )
            )

    linked_urls = {link for links in discovered_edges.values() for link in links}
    orphan_candidates = [
        page.url for page in pages if page.url != root_url and page.url not in linked_urls
    ]
    for orphan in orphan_candidates:
        if orphan in sitemap_urls:
            issues.append(
                CrawlIssue(
                    key="sitemap_orphan_candidate",
                    severity=Severity.low,
                    url=orphan,
                    detail="URL is in sitemap but no crawled internal link points to it.",
                )
            )

    finished_at = datetime.now(UTC)
    successful = sum(1 for page in pages if 200 <= page.status_code < 300)
    indexable = sum(1 for page in pages if page.indexable)
    schema_pages = sum(1 for page in pages if page.structured_data_types)
    totals: dict[str, int | float] = {
        "pages_crawled": len(pages),
        "successful_pages": successful,
        "indexable_pages": indexable,
        "issues": len(issues),
        "schema_pages": schema_pages,
        "avg_word_count": (
            round(sum(page.word_count for page in pages) / len(pages), 1) if pages else 0
        ),
        "crawl_delay_seconds": crawl_delay,
    }
    return CrawlReport(
        root_url=root_url,
        started_at=started_at,
        finished_at=finished_at,
        pages=pages,
        issues=issues,
        discovered_sitemaps=discovered_sitemaps,
        robots_txt_url=robots_url,
        robots_txt_found=robots_found,
        truncated=bool(queue),
        totals=totals,
    )
