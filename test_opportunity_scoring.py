from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from backend.opportunity_scoring import score_tender


def test_priority_score_is_explainable_and_bounded():
    tender = SimpleNamespace(
        tender_id="egp-42", title="Bridge rehabilitation", agency="LGED", district="Dhaka",
        closing_date=(datetime.now(timezone.utc) + timedelta(days=20)).strftime("%Y-%m-%d %H:%M"),
        estimated_cost=120_000_000, tender_security=2_000_000, liquid_assets_req=20_000_000,
    )
    result = score_tender(tender, corrigendum_count=1)
    assert 0 <= result["priority_score"] <= 100
    assert result["priority_tier"] == "PRIORITY"
    assert len(result["factors"]) == 5
    assert "not a bid eligibility" in result["disclaimer"]


if __name__ == "__main__":
    test_priority_score_is_explainable_and_bounded()
    print("Opportunity scoring passed")
