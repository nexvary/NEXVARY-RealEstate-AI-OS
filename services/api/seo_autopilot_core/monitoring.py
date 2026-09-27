from __future__ import annotations

from .intelligence import detect_regressions
from .models import PostChangeEvaluation, SearchMetricRow, Severity, SitePolicy


def evaluate_post_change(
    previous: list[SearchMetricRow],
    current: list[SearchMetricRow],
    policy: SitePolicy,
    *,
    minimum_impressions: float = 50,
) -> PostChangeEvaluation:
    regressions = detect_regressions(
        previous,
        current,
        minimum_impressions=minimum_impressions,
    )
    severe = [signal for signal in regressions if signal.severity in {Severity.high, Severity.critical}]
    rollback_recommended = bool(severe)
    auto_rollback_eligible = rollback_recommended and policy.auto_rollback_enabled

    if not regressions:
        reason = "No material regression detected in the compared Search Console metrics."
    elif severe:
        reason = (
            f"Detected {len(severe)} high-severity regression signal(s); "
            "rollback should be reviewed against the change timeline."
        )
    else:
        reason = "Only medium/low regression signals were detected; continue observation."

    return PostChangeEvaluation(
        regressions=regressions,
        rollback_recommended=rollback_recommended,
        auto_rollback_eligible=auto_rollback_eligible,
        reason=reason,
    )
