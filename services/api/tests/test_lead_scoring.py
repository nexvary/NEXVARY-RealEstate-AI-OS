from decimal import Decimal

from app.services.lead_scoring import score_lead


def test_complete_high_intent_lead_scores_hot() -> None:
    score = score_lead(
        budget=Decimal("5000000"),
        preferred_city="New Cairo",
        bedrooms=3,
        source="whatsapp",
        notes="Wants a viewing this weekend and has confirmed down payment.",
    )
    assert score >= 70


def test_sparse_lead_stays_low_priority() -> None:
    score = score_lead(
        budget=None,
        preferred_city=None,
        bedrooms=None,
        source="unknown",
        notes=None,
    )
    assert score == 20
