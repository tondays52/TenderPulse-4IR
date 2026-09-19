"""Database-level regression test for the per-operator corrigendum workflow."""

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import TenderModel, CorrigendumModel, CorrigendumReviewModel
from backend import crud


def test_review_upsert_is_per_operator():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        session.add(TenderModel(tender_id="egp-1", title="Deadline amendment", agency="LGED"))
        session.commit()
        alert = CorrigendumModel(
            tender_id="egp-1", field_changed="closing_date", old_value="2026-09-20", new_value="2026-09-27",
            detected_at=datetime.utcnow(),
        )
        session.add(alert)
        session.commit()

        first = crud.save_corrigendum_review(session, alert.id, "operator@example.com", "acknowledged", "Assigned")
        second = crud.save_corrigendum_review(session, alert.id, "operator@example.com", "reviewed", "Deadline assessed")

        assert first.id == second.id
        assert second.status == "reviewed"
        assert second.note == "Deadline assessed"
        assert session.query(CorrigendumReviewModel).count() == 1

        preferences = crud.save_alert_preferences(
            session, "operator@example.com", '["LGED"]', '["closing_date"]', 48, "email"
        )
        assert preferences.deadline_window_hours == 48
        assert preferences.requested_external_channel == "email"
        assert crud.get_alert_preferences(session, "operator@example.com").agencies_json == '["LGED"]'

        team_policy = crud.save_team_alert_policy(
            session, '["RHD", "LGED"]', '["closing_date"]', 24, "in_app", "admin@example.com"
        )
        assert team_policy.id == 1
        assert team_policy.deadline_window_hours == 24
        assert crud.get_team_alert_policy(session).updated_by == "admin@example.com"
    finally:
        session.close()


if __name__ == "__main__":
    test_review_upsert_is_per_operator()
    print("Corrigendum review workflow passed")
