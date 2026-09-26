from __future__ import annotations

from copy import deepcopy
from urllib.parse import urlparse

SUPPORTED_TYPES = {
    "Organization",
    "WebSite",
    "BreadcrumbList",
    "Article",
    "Product",
    "LocalBusiness",
}

REQUIRED_FIELDS: dict[str, set[str]] = {
    "Organization": {"name", "url"},
    "WebSite": {"name", "url"},
    "BreadcrumbList": {"itemListElement"},
    "Article": {"headline", "datePublished"},
    "Product": {"name"},
    "LocalBusiness": {"name", "address"},
}


def _valid_absolute_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def validate_schema(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload.get("@context") != "https://schema.org":
        errors.append("@context must be https://schema.org")
    schema_type = payload.get("@type")
    if schema_type not in SUPPORTED_TYPES:
        errors.append(f"Unsupported @type: {schema_type!r}")
        return errors

    for field in sorted(REQUIRED_FIELDS[schema_type]):
        value = payload.get(field)
        if value is None or value == "" or value == []:
            errors.append(f"Missing required field: {field}")

    for field in ("url", "mainEntityOfPage"):
        value = payload.get(field)
        if isinstance(value, str) and not _valid_absolute_url(value):
            errors.append(f"{field} must be an absolute http/https URL")

    if schema_type == "BreadcrumbList":
        items = payload.get("itemListElement", [])
        if not isinstance(items, list) or not items:
            errors.append("BreadcrumbList requires non-empty itemListElement")
        else:
            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    errors.append(f"Breadcrumb item {index} must be an object")
                    continue
                if item.get("@type") != "ListItem":
                    errors.append(f"Breadcrumb item {index} must use @type ListItem")
                if not item.get("name"):
                    errors.append(f"Breadcrumb item {index} is missing name")
                if item.get("position") != index:
                    errors.append(f"Breadcrumb item {index} has incorrect position")

    return errors


def build_schema(schema_type: str, visible_data: dict) -> dict:
    """Build JSON-LD only from supplied visible facts. No inferred reviews, ratings or claims."""

    if schema_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported schema type: {schema_type}")
    payload = {"@context": "https://schema.org", "@type": schema_type}
    payload.update(deepcopy(visible_data))
    errors = validate_schema(payload)
    if errors:
        raise ValueError("; ".join(errors))
    return payload


def build_breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    visible = {
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": name,
                "item": url,
            }
            for index, (name, url) in enumerate(items, start=1)
        ]
    }
    return build_schema("BreadcrumbList", visible)


def schema_gap_recommendations(
    page_url: str,
    present_types: list[str],
    *,
    is_article: bool = False,
    is_product: bool = False,
    is_local_business_page: bool = False,
) -> list[str]:
    recommendations: list[str] = []
    present = set(present_types)
    if "BreadcrumbList" not in present and urlparse(page_url).path.strip("/"):
        recommendations.append("BreadcrumbList")
    if is_article and "Article" not in present:
        recommendations.append("Article")
    if is_product and "Product" not in present:
        recommendations.append("Product")
    if is_local_business_page and "LocalBusiness" not in present:
        recommendations.append("LocalBusiness")
    return recommendations
