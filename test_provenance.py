"""Regression tests for explicit real/cached/synthetic data labeling."""

from backend.egp_live_scraper import EgpLiveScraper
from backend.live_ingestion import _synthesize_tender
from backend.provenance import annotate_tender, provenance_summary


def test_synthetic_scraper_fallback_is_explicitly_labeled():
    record = EgpLiveScraper()._generate_synthetic_live_tenders("LGED", count=1)[0]
    assert record["provenance"]["kind"] == "synthetic"
    assert "not an official" in record["description"].lower()


def test_live_radar_events_are_labeled_as_simulated():
    event = _synthesize_tender()
    assert event["provenance"]["kind"] == "synthetic"
    assert "not an e-gp award" in event["provenance"]["notes"][0].lower()


def test_legacy_records_are_not_silently_presented_as_live():
    record = annotate_tender({"tenderId": "legacy-1", "source": "old import"})
    assert record["provenance"]["kind"] == "legacy_unknown"
    assert provenance_summary([record])["counts"] == {"legacy_unknown": 1}


if __name__ == "__main__":
    test_synthetic_scraper_fallback_is_explicitly_labeled()
    test_live_radar_events_are_labeled_as_simulated()
    test_legacy_records_are_not_silently_presented_as_live()
    print("provenance tests passed")
