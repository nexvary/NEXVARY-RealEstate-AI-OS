from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WebVitals:
    lcp_ms: float | None = None
    inp_ms: float | None = None
    cls: float | None = None


def evaluate_web_vitals(vitals: WebVitals) -> dict:
    checks = {
        "lcp": {
            "value": vitals.lcp_ms,
            "threshold": 2500,
            "passed": vitals.lcp_ms is not None and vitals.lcp_ms <= 2500,
        },
        "inp": {
            "value": vitals.inp_ms,
            "threshold": 200,
            "passed": vitals.inp_ms is not None and vitals.inp_ms <= 200,
        },
        "cls": {
            "value": vitals.cls,
            "threshold": 0.1,
            "passed": vitals.cls is not None and vitals.cls <= 0.1,
        },
    }
    measured = [item for item in checks.values() if item["value"] is not None]
    passed = [item for item in measured if item["passed"]]
    score = round((len(passed) / len(measured)) * 100) if measured else 0
    return {"score": score, "checks": checks, "complete": len(measured) == 3}


def answer_readiness_score(
    *,
    has_clear_heading: bool,
    has_direct_answer: bool,
    has_supporting_details: bool,
    has_sources_for_factual_claims: bool,
    has_descriptive_links: bool,
    hidden_critical_content: bool = False,
) -> dict:
    weighted = {
        "clear_heading": (has_clear_heading, 15),
        "direct_answer": (has_direct_answer, 25),
        "supporting_details": (has_supporting_details, 20),
        "factual_sources": (has_sources_for_factual_claims, 20),
        "descriptive_links": (has_descriptive_links, 10),
        "critical_content_visible": (not hidden_critical_content, 10),
    }
    score = sum(weight for passed, weight in weighted.values() if passed)
    return {
        "score": score,
        "checks": {key: passed for key, (passed, _) in weighted.items()},
        "note": (
            "This is an internal content-quality heuristic, not a guarantee of inclusion in any "
            "Google AI feature."
        ),
    }
