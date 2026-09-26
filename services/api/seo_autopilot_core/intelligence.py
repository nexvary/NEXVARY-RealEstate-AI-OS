from __future__ import annotations

from collections import defaultdict
from math import log10

from .models import (
    ContentBrief,
    Opportunity,
    RegressionSignal,
    SearchMetricRow,
    Severity,
)

QUESTION_PREFIXES = (
    "how ",
    "what ",
    "why ",
    "when ",
    "where ",
    "who ",
    "هل ",
    "كيف ",
    "ما ",
    "ماذا ",
    "لماذا ",
    "متى ",
    "أين ",
)
TRANSACTIONAL_TERMS = (
    "buy",
    "price",
    "pricing",
    "order",
    "quote",
    "book",
    "purchase",
    "شراء",
    "سعر",
    "اسعار",
    "أسعار",
    "احجز",
    "اطلب",
)
COMMERCIAL_TERMS = (
    "best",
    "compare",
    "comparison",
    "review",
    "vs",
    "أفضل",
    "مقارنة",
    "تقييم",
)
NAVIGATIONAL_TERMS = ("login", "contact", "facebook", "youtube", "تسجيل الدخول", "اتصل")


def classify_intent(query: str) -> str:
    value = f" {query.strip().casefold()} "
    if any(term in value for term in TRANSACTIONAL_TERMS):
        return "transactional"
    if any(term in value for term in COMMERCIAL_TERMS):
        return "commercial"
    if any(term in value for term in NAVIGATIONAL_TERMS):
        return "navigational"
    if value.strip().startswith(QUESTION_PREFIXES):
        return "informational"
    return "mixed"


def _priority(impact: int, confidence: int, effort: int) -> float:
    return round((impact * (confidence / 100)) / max(effort, 1), 3)


def _visibility_impact(row: SearchMetricRow) -> int:
    impression_signal = min(45, int(log10(max(row.impressions, 1) + 1) * 14))
    position_signal = 0
    if 4 <= row.position <= 20:
        position_signal = max(5, int(40 - abs(row.position - 8) * 2.2))
    ctr_signal = 15 if row.impressions >= 100 and row.ctr < 0.02 else 0
    return min(100, impression_signal + position_signal + ctr_signal)


def build_opportunities(rows: list[SearchMetricRow], limit: int = 100) -> list[Opportunity]:
    opportunities: list[Opportunity] = []
    by_query_pages: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        if row.query and row.page:
            by_query_pages[row.query.casefold()].add(row.page)

        if row.impressions >= 100 and row.ctr < 0.02:
            impact = _visibility_impact(row)
            confidence = min(95, 55 + int(log10(row.impressions + 1) * 10))
            effort = 25
            opportunities.append(
                Opportunity(
                    key="high_impressions_low_ctr",
                    page=row.page,
                    query=row.query,
                    impact=impact,
                    confidence=confidence,
                    effort=effort,
                    priority=_priority(impact, confidence, effort),
                    reason=(
                        f"{row.impressions:.0f} impressions with CTR {row.ctr:.2%} "
                        f"at average position {row.position:.1f}."
                    ),
                    recommended_action=(
                        "Review title/snippet alignment with intent; preserve factual accuracy and "
                        "measure CTR after the change."
                    ),
                )
            )

        if row.impressions >= 50 and 4 <= row.position <= 20:
            impact = _visibility_impact(row)
            confidence = 80 if row.impressions >= 500 else 70
            effort = 40
            opportunities.append(
                Opportunity(
                    key="striking_distance",
                    page=row.page,
                    query=row.query,
                    impact=impact,
                    confidence=confidence,
                    effort=effort,
                    priority=_priority(impact, confidence, effort),
                    reason=(
                        f"Query is within striking distance at position {row.position:.1f} "
                        f"with {row.impressions:.0f} impressions."
                    ),
                    recommended_action=(
                        "Strengthen intent coverage, internal links and evidence on the existing page "
                        "instead of creating a duplicate page."
                    ),
                )
            )

    row_lookup: dict[tuple[str, str], SearchMetricRow] = {}
    for row in rows:
        if row.query and row.page:
            row_lookup[(row.query.casefold(), row.page)] = row

    for query, pages in by_query_pages.items():
        if len(pages) < 2:
            continue
        competing = [row_lookup[(query, page)] for page in pages if (query, page) in row_lookup]
        total_impressions = sum(row.impressions for row in competing)
        if total_impressions < 100:
            continue
        best = min(competing, key=lambda row: row.position or 999)
        impact = min(90, 45 + int(log10(total_impressions + 1) * 10))
        opportunities.append(
            Opportunity(
                key="query_cannibalization",
                page=best.page,
                query=best.query,
                impact=impact,
                confidence=75,
                effort=60,
                priority=_priority(impact, 75, 60),
                reason=f"The same query is associated with {len(pages)} pages.",
                recommended_action=(
                    "Inspect intent overlap and consolidate or differentiate pages only after manual review; "
                    "do not auto-redirect or delete URLs."
                ),
            )
        )

    deduped: dict[tuple[str, str | None, str | None], Opportunity] = {}
    for item in opportunities:
        key = (item.key, item.page, item.query)
        existing = deduped.get(key)
        if not existing or item.priority > existing.priority:
            deduped[key] = item
    return sorted(deduped.values(), key=lambda item: item.priority, reverse=True)[:limit]


def build_content_brief(page: str, rows: list[SearchMetricRow]) -> ContentBrief:
    page_rows = [row for row in rows if row.page == page and row.query]
    page_rows.sort(key=lambda row: (row.impressions, row.clicks), reverse=True)
    primary = page_rows[0].query if page_rows else None
    supporting = [row.query for row in page_rows[1:8] if row.query]
    intent = classify_intent(primary or "")

    sections = ["Direct answer / value proposition", "Core topic coverage"]
    if intent == "informational":
        sections.extend(["How it works", "Common questions", "Evidence and sources"])
    elif intent == "commercial":
        sections.extend(["Comparison criteria", "Use cases", "Decision guidance"])
    elif intent == "transactional":
        sections.extend(["Offer details", "Specifications or scope", "Trust and next step"])
    elif intent == "navigational":
        sections.extend(["Destination details", "Contact or access information"])
    else:
        sections.extend(["Key details", "Questions users may still have"])

    schema_candidates = ["BreadcrumbList"]
    if intent == "informational":
        schema_candidates.append("Article")
    if intent in {"commercial", "transactional"}:
        schema_candidates.extend(["Product", "Service"])

    question_queries = [
        row.query for row in page_rows if row.query and row.query.casefold().startswith(QUESTION_PREFIXES)
    ]
    if question_queries:
        sections.append("FAQ-style visible answers (schema only when Google eligibility rules fit)")

    return ContentBrief(
        page=page,
        intent=intent,
        primary_query=primary,
        supporting_queries=supporting,
        recommended_sections=list(dict.fromkeys(sections)),
        schema_candidates=list(dict.fromkeys(schema_candidates)),
        guardrails=[
            "Do not invent facts, reviews, prices, credentials or sources.",
            "Do not create a new page when an existing page already satisfies the same intent.",
            "Keep important answers visible to users, not only inside structured data.",
            "Measure results after publication before making another major change.",
        ],
    )


def detect_regressions(
    previous: list[SearchMetricRow],
    current: list[SearchMetricRow],
    minimum_impressions: float = 50,
) -> list[RegressionSignal]:
    def key(row: SearchMetricRow) -> tuple[str | None, str | None]:
        return row.query, row.page

    old = {key(row): row for row in previous}
    signals: list[RegressionSignal] = []
    for row in current:
        prior = old.get(key(row))
        if not prior or max(prior.impressions, row.impressions) < minimum_impressions:
            continue

        if prior.clicks > 0:
            click_change = ((row.clicks - prior.clicks) / prior.clicks) * 100
            if click_change <= -25:
                signals.append(
                    RegressionSignal(
                        key="click_drop",
                        severity=Severity.high if click_change <= -50 else Severity.medium,
                        metric="clicks",
                        previous=prior.clicks,
                        current=row.clicks,
                        change_percent=round(click_change, 2),
                        detail=f"Clicks fell for query={row.query!r}, page={row.page!r}.",
                    )
                )

        position_change = row.position - prior.position
        if position_change >= 3:
            base = max(abs(prior.position), 1)
            signals.append(
                RegressionSignal(
                    key="ranking_drop",
                    severity=Severity.high if position_change >= 7 else Severity.medium,
                    metric="position",
                    previous=prior.position,
                    current=row.position,
                    change_percent=round((position_change / base) * 100, 2),
                    detail=f"Average position worsened by {position_change:.1f} places.",
                )
            )

    return sorted(
        signals,
        key=lambda signal: (signal.severity.value, abs(signal.change_percent)),
        reverse=True,
    )
