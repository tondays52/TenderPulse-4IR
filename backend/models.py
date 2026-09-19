"""
TenderPulse 4IR AI - Relational Database Schema Models
SQLAlchemy 2.0 ORM definitions for Tenders, Cartel Syndicates, SAR Audits, and Users.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Index
)
from backend.database import Base


class TenderModel(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tender_id = Column(String(64), unique=True, index=True, nullable=False)
    app_id = Column(String(64), index=True, nullable=True)
    ref_no = Column(String(128), nullable=True)
    title = Column(String(512), nullable=False)
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

