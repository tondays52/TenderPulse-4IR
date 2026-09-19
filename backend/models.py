"""
TenderPulse 4IR AI - Relational Database Schema Models
SQLAlchemy 2.0 ORM definitions for Tenders, Cartel Syndicates, SAR Audits, and Users.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Index, ForeignKey, UniqueConstraint
)
from backend.database import Base


class TenderModel(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, index=True, nullable=False)
    app_id = Column(String(64), index=True, nullable=True)
    # e-GP composite package references can exceed typical VARCHAR limits.
    ref_no = Column(Text, nullable=True)
    # Official notices can contain lengthy multi-asset procurement descriptions.
    title = Column(Text, nullable=False)
    agency = Column(String(128), index=True, nullable=False)
    ministry = Column(String(256), nullable=True)
    division = Column(String(64), nullable=True)
    district = Column(String(64), index=True, nullable=True)
    work_type = Column(String(64), nullable=True)             # Works / Goods / Services
    procurement_method = Column(String(64), nullable=True)    # OTM / LTM / NCT / OSTETM
    std_document = Column(String(32), nullable=True)          # e-PW3 / e-PW2A / e-PG3
    estimated_cost = Column(Float, default=0.0)
    tender_security = Column(Float, default=0.0)
    liquid_assets_req = Column(Float, default=0.0)
    turnover_req = Column(Float, default=0.0)
    
    # Geospatial Coordinates & Bounding Box
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    bbox_min_lat = Column(Float, nullable=True)
    bbox_min_lon = Column(Float, nullable=True)
    bbox_max_lat = Column(Float, nullable=True)
    bbox_max_lon = Column(Float, nullable=True)
    
    publish_date = Column(String(64), nullable=True)
    closing_date = Column(String(64), nullable=True)
    is_live = Column(Boolean, default=True)
    raw_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_tenders_agency_district", "agency", "district"),
        Index("ix_tenders_spatial", "latitude", "longitude"),
    )


class BiddingSyndicateModel(Base):
    __tablename__ = "bidding_syndicates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tender_id = Column(String(64), index=True, nullable=True)
    lead_contractor = Column(String(256), nullable=False)
    syndicate_name = Column(String(256), nullable=True)
    co_bidders_json = Column(Text, nullable=True)
    shared_guarantee_no = Column(String(128), nullable=True)
    risk_score = Column(Float, default=0.0)
    risk_category = Column(String(64), default="CLEAN")  # CLEAN / WATCHLIST / SUSPECTED_COLLUSION / CARTEL_RING
    created_at = Column(DateTime, default=datetime.utcnow)


class SarAuditModel(Base):
    __tablename__ = "sar_audits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    contract_id = Column(String(128), index=True, nullable=False)
    tender_id = Column(String(64), nullable=True)
    claimed_progress = Column(Float, default=0.0)
    radar_ground_truth = Column(Float, default=0.0)
    discrepancy = Column(Float, default=0.0)
    coherence_decay = Column(Float, default=0.0)
    vv_db = Column(Float, default=0.0)
    vh_db = Column(Float, default=0.0)
    audit_verdict = Column(String(64), default="VERIFIED")
    created_at = Column(DateTime, default=datetime.utcnow)


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(128), nullable=False)
    role = Column(String(64), default="Tender Analyst")
    agency = Column(String(128), default="Di-Tender Ltd.")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RefreshTokenModel(Base):
    """Durable refresh-token registry used for rotation and replay prevention."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(256), index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_refresh_tokens_email_active", "email", "revoked_at"),
    )


class CorrigendumModel(Base):
    __tablename__ = "corrigenda"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tender_id = Column(String(64), index=True, nullable=False)
    corrigendum_no = Column(Integer, default=1)
    field_changed = Column(String(64), nullable=False)      # closing_date / tender_security / estimated_cost
    old_value = Column(String(256), nullable=True)
    new_value = Column(String(256), nullable=True)
    reason = Column(String(512), nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)


class CorrigendumReviewModel(Base):
    """An operator's durable acknowledgement or completed review of an alert."""

    __tablename__ = "corrigendum_reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    corrigendum_id = Column(Integer, ForeignKey("corrigenda.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_email = Column(String(256), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="acknowledged")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("corrigendum_id", "reviewer_email", name="uq_corrigendum_review_reviewer"),
        Index("ix_corrigendum_reviews_reviewer_status", "reviewer_email", "status"),
    )


class AlertPreferenceModel(Base):
    """Per-operator delivery and filtering preferences for corrigendum alerts."""

    __tablename__ = "alert_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(256), unique=True, nullable=False, index=True)
    agencies_json = Column(Text, nullable=False, default="[]")
    alert_types_json = Column(Text, nullable=False, default='["closing_date", "tender_security"]')
    deadline_window_hours = Column(Integer, nullable=False, default=72)
    requested_external_channel = Column(String(32), nullable=False, default="in_app")
    is_customized = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TeamAlertPolicyModel(Base):
    """Singleton team defaults administered by an Administrator."""

    __tablename__ = "team_alert_policy"

    id = Column(Integer, primary_key=True)
    agencies_json = Column(Text, nullable=False, default="[]")
    alert_types_json = Column(Text, nullable=False, default='["closing_date", "tender_security"]')
    deadline_window_hours = Column(Integer, nullable=False, default=72)
    requested_external_channel = Column(String(32), nullable=False, default="in_app")
    updated_by = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BidPipelineItemModel(Base):
    """Shared, server-side lifecycle record for a tender under bid consideration."""
    __tablename__ = "bid_pipeline_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, nullable=False, index=True)
    tender_title = Column(Text, nullable=False)
    agency = Column(String(256), nullable=True)
    owner_email = Column(String(256), nullable=True, index=True)
    stage = Column(String(32), nullable=False, default="review")
    internal_due_date = Column(String(64), nullable=True)
    decision = Column(String(32), nullable=True)
    next_action = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BidReadinessProfileModel(Base):
    """Singleton company capability profile used for tender-specific readiness checks."""
    __tablename__ = "bid_readiness_profile"
    id = Column(Integer, primary_key=True)
    contractor_name = Column(String(256), nullable=False, default="Tender Trading Inc.")
    peak_turnover_bdt = Column(Float, nullable=False, default=0.0)
    active_commitments_bdt = Column(Float, nullable=False, default=0.0)
    available_credit_bdt = Column(Float, nullable=False, default=0.0)
    past_similar_max_bdt = Column(Float, nullable=False, default=0.0)
    engineers_count = Column(Integer, nullable=False, default=0)
    updated_by = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BidPreparationTaskModel(Base):
    __tablename__ = "bid_preparation_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    owner_email = Column(String(256), nullable=True, index=True)
    due_date = Column(String(64), nullable=True)
    is_required = Column(Boolean, nullable=False, default=True)
    status = Column(String(32), nullable=False, default="open")
    blocker = Column(Text, nullable=True)
    created_by = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BidActivityEventModel(Base):
    """Append-only audit timeline for shared pipeline and preparation work."""
    __tablename__ = "bid_activity_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(Integer, nullable=True)
    action = Column(String(64), nullable=False)
    summary = Column(String(1000), nullable=False)
    actor_email = Column(String(256), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BidTaskAttachmentModel(Base):
    """Private evidence file metadata; binary content remains outside the web root."""
    __tablename__ = "bid_task_attachments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("bid_preparation_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    storage_key = Column(String(128), unique=True, nullable=False)
    content_type = Column(String(128), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    uploaded_by = Column(String(256), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BidSubmissionApprovalModel(Base):
    """Executive/Admin sign-off tied to a point-in-time readiness fingerprint."""
    __tablename__ = "bid_submission_approvals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending")
    note = Column(Text, nullable=True)
    signed_by = Column(String(256), nullable=True, index=True)
    signed_at = Column(DateTime, nullable=True)
    readiness_fingerprint = Column(String(64), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BidOutcomeModel(Base):
    """Post-submission tender outcome and reusable lessons learned."""
    __tablename__ = "bid_outcomes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), nullable=False, default="submitted")
    submission_reference = Column(String(256), nullable=True)
    submitted_at = Column(String(64), nullable=True)
    outcome_date = Column(String(64), nullable=True)
    awarded_contract_value = Column(Float, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    recorded_by = Column(String(256), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ExecutiveKpiSummaryModel(Base):
    """One durable operational snapshot per UTC day for executive review."""
    __tablename__ = "executive_kpi_summaries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    summary_date = Column(String(10), unique=True, nullable=False, index=True)
    pipeline_total = Column(Integer, nullable=False, default=0)
    active_pipeline = Column(Integer, nullable=False, default=0)
    overdue_tasks = Column(Integer, nullable=False, default=0)
    blocked_tasks = Column(Integer, nullable=False, default=0)
    submitted_pending = Column(Integer, nullable=False, default=0)
    decisioned_bids = Column(Integer, nullable=False, default=0)
    won_bids = Column(Integer, nullable=False, default=0)
    lost_bids = Column(Integer, nullable=False, default=0)
    win_rate_pct = Column(Float, nullable=True)
    awarded_contract_value = Column(Float, nullable=False, default=0.0)
    needs_attention_json = Column(Text, nullable=False, default="[]")
    generated_by = Column(String(256), nullable=False, default="scheduler")
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditRetentionPolicyModel(Base):
    """Singleton policy describing retention expectations; it never purges records itself."""
    __tablename__ = "audit_retention_policy"
    id = Column(Integer, primary_key=True)
    retention_days = Column(Integer, nullable=False, default=2555)
    updated_by = Column(String(256), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class DocumentRequirementReviewModel(Base):
    __tablename__ = "document_requirement_reviews"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tender_id = Column(String(64), nullable=False, index=True)
    requirement_key = Column(String(64), nullable=False)
    source_excerpt = Column(Text, nullable=False)
    source_page = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="unreviewed")
    reviewed_by = Column(String(256), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class HistoricalAwardModel(Base):
    __tablename__ = "historical_awards"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, index=True, nullable=False)
    agency = Column(String(128), index=True, nullable=False)
    division = Column(String(64), index=True, nullable=True)
    district = Column(String(64), index=True, nullable=True)
    year = Column(Integer, index=True, nullable=False)
    procurement_type = Column(String(64), default="Works")
    title = Column(String(512), nullable=True)
    estimated_cost = Column(Float, default=0.0)
    winning_contractor = Column(String(256), index=True, nullable=False)
    winning_price = Column(Float, default=0.0)
    bidders_count = Column(Integer, default=3)
    bidders_json = Column(Text, nullable=False)
    has_collusion_flag = Column(Boolean, default=False, index=True)
    collusion_vector = Column(String(128), nullable=True)  # GUARANTEE / ADDRESS / COVER_BID / ROTATIONAL / CLEAN
    syndicate_name = Column(String(256), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_hist_agency_year", "agency", "year"),
        Index("ix_hist_collusion_agency", "has_collusion_flag", "agency"),
    )
