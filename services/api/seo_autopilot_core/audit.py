from __future__ import annotations

import asyncio
import ipaddress
import json
import socket
from collections import Counter
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .models import AuditCheck, AuditResult, PageSnapshot, Severity

USER_AGENT = "NEXVARY-SEO-Autopilot/0.2 (+https://nexvary.com/)"
MAX_BODY_BYTES = 2_000_000
MAX_REDIRECTS = 5


class UnsafeTargetError(ValueError):
    pass


async def _validate_public_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeTargetError("Only public http/https URLs are allowed")

    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith(".localhost"):
        raise UnsafeTargetError("Localhost targets are not allowed")

    def resolve() -> list[str]:
        return list({item[4][0] for item in socket.getaddrinfo(host, parsed.port)})

    try:
        addresses = await asyncio.to_thread(resolve)
    except socket.gaierror as exc:
        raise UnsafeTargetError("Hostname could not be resolved") from exc

    if not addresses:
        raise UnsafeTargetError("Hostname could not be resolved")

    for value in addresses:
        ip = ipaddress.ip_address(value)
        if not ip.is_global:
            raise UnsafeTargetError("Private, loopback, link-local, and reserved targets are blocked")


async def _fetch_public_html(url: str) -> tuple[httpx.Response, str]:
    current = url
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(15.0),
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        follow_redirects=False,
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            await _validate_public_url(current)
            async with client.stream("GET", current) as response:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location:
                        raise httpx.HTTPError("Redirect response has no Location header")
                    current = urljoin(current, location)
                    continue

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise ValueError("Target did not return an HTML document")

                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BODY_BYTES:
                        raise ValueError("HTML document exceeds the 2 MB audit limit")
                encoding = response.encoding or "utf-8"
                return response, bytes(body).decode(encoding, errors="replace")

    raise httpx.TooManyRedirects("Too many redirects")


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _check(
    key: str,
    title: str,
    passed: bool,
    severity: Severity,
    detail: str,
    recommendation: str | None = None,
) -> AuditCheck:
    return AuditCheck(
        key=key,
        title=title,
        passed=passed,
        score=100 if passed else 0,
        severity=severity,
        detail=detail,
        recommendation=None if passed else recommendation,
    )


def _collect_jsonld_types(value: object, output: set[str]) -> None:
    if isinstance(value, dict):
        item_type = value.get("@type")
        if isinstance(item_type, str):
            output.add(item_type)
        elif isinstance(item_type, list):
            output.update(str(item) for item in item_type if item)
        for child in value.values():
            _collect_jsonld_types(child, output)
    elif isinstance(value, list):
        for child in value:
            _collect_jsonld_types(child, output)


def _extract_snapshot(url: str, response: httpx.Response, html: str) -> PageSnapshot:
    soup = BeautifulSoup(html, "html.parser")
    base_url = str(response.url)
    base_host = (urlparse(base_url).hostname or "").lower()

    title = soup.title.get_text(" ", strip=True) if soup.title else None
    description_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    description = description_tag.get("content", "").strip() if description_tag else None
    canonical_tag = soup.find("link", attrs={"rel": lambda v: v and "canonical" in v})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else None
    language = soup.html.get("lang") if soup.html else None
    robots_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() in {"robots", "googlebot"}})
    robots_meta = robots_tag.get("content", "").strip() if robots_tag else None

    structured_types: set[str] = set()
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            _collect_jsonld_types(json.loads(raw), structured_types)
        except (json.JSONDecodeError, TypeError):
            continue

    hreflang_targets: dict[str, str] = {}
    for link in soup.find_all("link", href=True):
        rel = link.get("rel", [])
        rel_values = [rel] if isinstance(rel, str) else rel
        hreflang = link.get("hreflang")
        if hreflang and any(str(item).lower() == "alternate" for item in rel_values):
            hreflang_targets[str(hreflang).lower()] = urljoin(base_url, link["href"])

    internal_links = 0
    external_links = 0
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(base_url, anchor["href"])
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        if parsed.hostname.lower() == base_host:
            internal_links += 1
        else:
            external_links += 1

    images = soup.find_all("img")
    missing_alt = sum(1 for image in images if image.get("alt") is None)
    h1_count = len(soup.find_all("h1"))
    h2_count = len(soup.find_all("h2"))

    for node in soup(["script", "style", "noscript", "template"]):
        node.decompose()
    words = [word for word in soup.get_text(" ", strip=True).split() if word]

    return PageSnapshot(
        url=url,
        status_code=response.status_code,
        final_url=base_url,
        title=title,
        meta_description=description,
        canonical=urljoin(base_url, canonical) if canonical else None,
        language=language,
        robots_meta=robots_meta,
        h1_count=h1_count,
        h2_count=h2_count,
        internal_links=internal_links,
        external_links=external_links,
        images=len(images),
        images_missing_alt=missing_alt,
        word_count=len(words),
        structured_data_types=sorted(structured_types),
        hreflang_targets=hreflang_targets,
    )


def _build_checks(snapshot: PageSnapshot) -> tuple[list[AuditCheck], list[str], int]:
    title_len = len(snapshot.title or "")
    description_len = len(snapshot.meta_description or "")
    robots_meta = (snapshot.robots_meta or "").lower()

    checks = [
        _check(
            "http_status",
            "Successful HTTP response",
            200 <= snapshot.status_code < 300,
            Severity.critical,
            f"HTTP status: {snapshot.status_code}",
            "Resolve HTTP errors and redirect problems before content optimization.",
        ),
        _check(
            "indexable",
            "Page is not explicitly noindex",
            "noindex" not in robots_meta,
            Severity.critical,
            f"Robots meta: {snapshot.robots_meta or 'not declared'}",
            "Review noindex intent before changing it; protected pages must never be auto-enabled.",
        ),
        _check(
            "title",
            "Descriptive page title",
            15 <= title_len <= 65,
            Severity.high,
            f"Title length: {title_len}",
            "Use a unique, descriptive title of roughly 15-65 characters.",
        ),
        _check(
            "meta_description",
            "Meta description",
            50 <= description_len <= 170,
            Severity.medium,
            f"Description length: {description_len}",
            "Add a useful page-specific description, avoiding duplication and keyword stuffing.",
        ),
        _check(
            "h1",
            "Single primary H1",
            snapshot.h1_count == 1,
            Severity.medium,
            f"H1 count: {snapshot.h1_count}",
            "Use one clear primary H1 that describes the page.",
        ),
        _check(
            "canonical",
            "Canonical URL declared",
            bool(snapshot.canonical),
            Severity.medium,
            f"Canonical: {snapshot.canonical or 'missing'}",
            "Declare a canonical URL where appropriate; canonical changes require review.",
        ),
        _check(
            "lang",
            "Document language declared",
            bool((snapshot.language or "").strip()),
            Severity.low,
            f"HTML lang: {snapshot.language or 'missing'}",
            "Set the html lang attribute to the page language.",
        ),
        _check(
            "image_alt",
            "Images declare alt attributes",
            snapshot.images_missing_alt == 0,
            Severity.medium,
            f"Images missing alt attribute: {snapshot.images_missing_alt}/{snapshot.images}",
            "Add meaningful alt text to informative images and empty alt to decorative images.",
        ),
        _check(
            "internal_links",
            "Internal linking present",
            snapshot.internal_links > 0,
            Severity.medium,
            f"Internal links: {snapshot.internal_links}",
            "Add useful contextual links to related pages on the same site.",
        ),
        _check(
            "content",
            "Substantive crawlable text",
            snapshot.word_count >= 120,
            Severity.medium,
            f"Visible words: {snapshot.word_count}",
            "Ensure the page contains useful crawlable text that satisfies its search intent.",
        ),
    ]

    weights = {
        "http_status": 15,
        "indexable": 15,
        "title": 15,
        "meta_description": 10,
        "h1": 10,
        "canonical": 10,
        "lang": 5,
        "image_alt": 5,
        "internal_links": 5,
        "content": 10,
    }
    weighted_score = sum(weights[check.key] for check in checks if check.passed)

    auto_fixable = {"meta_description", "lang", "image_alt"}
    safe_candidates = [
        check.key for check in checks if not check.passed and check.key in auto_fixable
    ]
    return checks, safe_candidates, weighted_score


async def audit_url(url: str) -> AuditResult:
    response, html = await _fetch_public_html(url)
    snapshot = _extract_snapshot(url, response, html)
    checks, safe_candidates, score = _build_checks(snapshot)
    return AuditResult(
        url=url,
        score=score,
        grade=_grade(score),
        snapshot=snapshot,
        checks=checks,
        safe_auto_fix_candidates=safe_candidates,
    )


def summarize_severities(checks: list[AuditCheck]) -> dict[str, int]:
    failed = Counter(check.severity.value for check in checks if not check.passed)
    return dict(failed)
