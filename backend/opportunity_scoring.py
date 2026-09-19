"""Explainable, tender-only opportunity prioritization for Phase 2.

This ranks notices for review; it deliberately does not predict a bidder's win
probability because contractor capability data has not yet been supplied.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


def _parse_closing_date(value: str):
    if not value:
        return None
    value = str(value).strip()
    for pattern in ("%d-%b-%Y %H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def score_tender(tender: Any, corrigendum_count: int = 0, now: datetime | None = None) -> Dict[str, Any]:
    """Return a 0-100 review-priority score and its complete factor breakdown."""
    now = now or datetime.now(timezone.utc)
    cost = float(getattr(tender, "estimated_cost", 0) or 0)
    security = float(getattr(tender, "tender_security", 0) or 0)
    liquidity = float(getattr(tender, "liquid_assets_req", 0) or 0)
    close_at = _parse_closing_date(getattr(tender, "closing_date", ""))

    if close_at:
        days_remaining = (close_at - now).total_seconds() / 86400
        readiness = 30 if days_remaining >= 14 else 20 if days_remaining >= 7 else 10 if days_remaining >= 3 else 2 if days_remaining >= 0 else 0
        readiness_reason = f"{max(0, int(days_remaining))} days until closing" if days_remaining >= 0 else "closing date has passed"
    else:
        days_remaining, readiness, readiness_reason = None, 12, "closing date unavailable"

    cost_crore = cost / 10_000_000
    if 10 <= cost_crore <= 250:
        scale = 25
        scale_reason = "mid-market contract scale"
    elif 1 <= cost_crore < 10 or 250 < cost_crore <= 500:
        scale = 18
        scale_reason = "reviewable contract scale"
    elif cost_crore > 0:
        scale = 10
        scale_reason = "very small or very large contract scale"
    else:
        scale = 5
        scale_reason = "estimated cost unavailable"

    terms = 20
    terms_reasons: List[str] = []
    if cost > 0 and liquidity / cost > 0.30:
        terms -= 8
        terms_reasons.append("liquidity requirement exceeds 30% of estimated cost")
    if cost > 0 and security / cost > 0.05:
        terms -= 6
        terms_reasons.append("tender security exceeds 5% of estimated cost")
    if not terms_reasons:
        terms_reasons.append("financial terms appear proportionate to published cost")

    completeness_fields: Iterable[Any] = (
        getattr(tender, "title", None), getattr(tender, "agency", None), getattr(tender, "district", None),
        getattr(tender, "closing_date", None), cost if cost > 0 else None,
    )
    populated = sum(1 for field in completeness_fields if field)
    completeness = round((populated / 5) * 15)
    amendment_penalty = min(corrigendum_count * 3, 10)

    total = max(0, min(100, readiness + scale + terms + completeness - amendment_penalty))
    tier = "PRIORITY" if total >= 70 else "REVIEW" if total >= 45 else "DEPRIORITIZE"
    return {
        "tender_id": getattr(tender, "tender_id", None),
        "title": getattr(tender, "title", "Untitled tender"),
        "agency": getattr(tender, "agency", ""),
        "closing_date": getattr(tender, "closing_date", ""),
        "days_remaining": max(0, int(days_remaining)) if days_remaining is not None else None,
        "priority_score": total,
        "priority_tier": tier,
        "corrigendum_count": corrigendum_count,
        "factors": [
            {"name": "Deadline readiness", "score": readiness, "max": 30, "reason": readiness_reason},
            {"name": "Contract scale", "score": scale, "max": 25, "reason": scale_reason},
            {"name": "Published financial terms", "score": terms, "max": 20, "reason": "; ".join(terms_reasons)},
            {"name": "Notice completeness", "score": completeness, "max": 15, "reason": f"{populated}/5 decision fields available"},
            {"name": "Amendment volatility", "score": -amendment_penalty, "max": 0, "reason": f"{corrigendum_count} recorded amendment(s)"},
        ],
        "disclaimer": "Review-priority score based only on published tender data; it is not a bid eligibility or win-probability assessment.",
    }


def rank_tenders(tenders: Iterable[Any], corrigenda_by_tender: Dict[str, int]) -> List[Dict[str, Any]]:
    ranked = [score_tender(tender, corrigenda_by_tender.get(tender.tender_id, 0)) for tender in tenders]
    return sorted(ranked, key=lambda item: (item["priority_score"], item["days_remaining"] is not None, item["days_remaining"] or -1), reverse=True)
