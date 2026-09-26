from decimal import Decimal


def score_lead(
    *,
    budget: Decimal | None,
    preferred_city: str | None,
    bedrooms: int | None,
    source: str,
    notes: str | None,
) -> int:
    """Transparent first-pass lead score.

    This intentionally uses deterministic business rules. AI can enrich lead data later,
    but it must not silently control the score or sales priority.
    """
    score = 20

    if budget is not None and budget > 0:
        score += 25
    if preferred_city:
        score += 20
    if bedrooms is not None:
        score += 15
    if source.lower() in {"whatsapp", "website", "referral"}:
        score += 10
    if notes and len(notes.strip()) >= 20:
        score += 10

    return min(score, 100)
