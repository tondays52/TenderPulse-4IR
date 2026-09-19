"""initial TenderPulse relational schema

Revision ID: 20260919_01
Revises:
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa

revision = "20260919_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("tenders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tender_id", sa.String(64), nullable=False, unique=True),
        sa.Column("app_id", sa.String(64)), sa.Column("ref_no", sa.Text()),
        sa.Column("title", sa.Text(), nullable=False), sa.Column("agency", sa.String(128), nullable=False),
        sa.Column("ministry", sa.String(256)), sa.Column("division", sa.String(64)), sa.Column("district", sa.String(64)),
        sa.Column("work_type", sa.String(64)), sa.Column("procurement_method", sa.String(64)), sa.Column("std_document", sa.String(32)),
        sa.Column("estimated_cost", sa.Float(), server_default="0"), sa.Column("tender_security", sa.Float(), server_default="0"),
        sa.Column("liquid_assets_req", sa.Float(), server_default="0"), sa.Column("turnover_req", sa.Float(), server_default="0"),
        sa.Column("latitude", sa.Float()), sa.Column("longitude", sa.Float()),
        sa.Column("bbox_min_lat", sa.Float()), sa.Column("bbox_min_lon", sa.Float()), sa.Column("bbox_max_lat", sa.Float()), sa.Column("bbox_max_lon", sa.Float()),
        sa.Column("publish_date", sa.String(64)), sa.Column("closing_date", sa.String(64)), sa.Column("is_live", sa.Boolean(), server_default=sa.true()),
        sa.Column("raw_json", sa.Text()), sa.Column("created_at", sa.DateTime()), sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_tenders_tender_id", "tenders", ["tender_id"])
    op.create_index("ix_tenders_app_id", "tenders", ["app_id"])
    op.create_index("ix_tenders_agency", "tenders", ["agency"])
    op.create_index("ix_tenders_district", "tenders", ["district"])
    op.create_index("ix_tenders_agency_district", "tenders", ["agency", "district"])
    op.create_index("ix_tenders_spatial", "tenders", ["latitude", "longitude"])
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("email", sa.String(256), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False), sa.Column("password_hash", sa.String(256), nullable=False), sa.Column("salt", sa.String(128), nullable=False),
        sa.Column("role", sa.String(64)), sa.Column("agency", sa.String(128)), sa.Column("is_active", sa.Boolean(), server_default=sa.true()), sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("jti", sa.String(64), nullable=False, unique=True),
        sa.Column("email", sa.String(256), nullable=False), sa.Column("expires_at", sa.DateTime(), nullable=False), sa.Column("revoked_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"])
    op.create_index("ix_refresh_tokens_email_active", "refresh_tokens", ["email", "revoked_at"])
    op.create_table("bidding_syndicates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("tender_id", sa.String(64)), sa.Column("lead_contractor", sa.String(256), nullable=False),
        sa.Column("syndicate_name", sa.String(256)), sa.Column("co_bidders_json", sa.Text()), sa.Column("shared_guarantee_no", sa.String(128)), sa.Column("risk_score", sa.Float(), server_default="0"), sa.Column("risk_category", sa.String(64)), sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_bidding_syndicates_tender_id", "bidding_syndicates", ["tender_id"])
    op.create_table("sar_audits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("contract_id", sa.String(128), nullable=False), sa.Column("tender_id", sa.String(64)),
        sa.Column("claimed_progress", sa.Float(), server_default="0"), sa.Column("radar_ground_truth", sa.Float(), server_default="0"), sa.Column("discrepancy", sa.Float(), server_default="0"), sa.Column("coherence_decay", sa.Float(), server_default="0"), sa.Column("vv_db", sa.Float(), server_default="0"), sa.Column("vh_db", sa.Float(), server_default="0"), sa.Column("audit_verdict", sa.String(64)), sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_sar_audits_contract_id", "sar_audits", ["contract_id"])
    op.create_table("corrigenda",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("tender_id", sa.String(64), nullable=False), sa.Column("corrigendum_no", sa.Integer(), server_default="1"), sa.Column("field_changed", sa.String(64), nullable=False), sa.Column("old_value", sa.String(256)), sa.Column("new_value", sa.String(256)), sa.Column("reason", sa.String(512)), sa.Column("detected_at", sa.DateTime()),
    )
    op.create_index("ix_corrigenda_tender_id", "corrigenda", ["tender_id"])
    op.create_table("historical_awards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True), sa.Column("tender_id", sa.String(64), nullable=False, unique=True), sa.Column("agency", sa.String(128), nullable=False), sa.Column("division", sa.String(64)), sa.Column("district", sa.String(64)), sa.Column("year", sa.Integer(), nullable=False), sa.Column("procurement_type", sa.String(64)), sa.Column("title", sa.String(512)), sa.Column("estimated_cost", sa.Float(), server_default="0"), sa.Column("winning_contractor", sa.String(256), nullable=False), sa.Column("winning_price", sa.Float(), server_default="0"), sa.Column("bidders_count", sa.Integer(), server_default="3"), sa.Column("bidders_json", sa.Text(), nullable=False), sa.Column("has_collusion_flag", sa.Boolean(), server_default=sa.false()), sa.Column("collusion_vector", sa.String(128)), sa.Column("syndicate_name", sa.String(256)), sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_historical_awards_tender_id", "historical_awards", ["tender_id"])
    op.create_index("ix_historical_awards_agency", "historical_awards", ["agency"])
    op.create_index("ix_historical_awards_division", "historical_awards", ["division"])
    op.create_index("ix_historical_awards_district", "historical_awards", ["district"])
    op.create_index("ix_historical_awards_year", "historical_awards", ["year"])
    op.create_index("ix_historical_awards_winning_contractor", "historical_awards", ["winning_contractor"])
    op.create_index("ix_historical_awards_has_collusion_flag", "historical_awards", ["has_collusion_flag"])
    op.create_index("ix_historical_awards_syndicate_name", "historical_awards", ["syndicate_name"])
    op.create_index("ix_hist_agency_year", "historical_awards", ["agency", "year"])
    op.create_index("ix_hist_collusion_agency", "historical_awards", ["has_collusion_flag", "agency"])


def downgrade() -> None:
    op.drop_table("historical_awards")
    op.drop_table("corrigenda")
    op.drop_table("sar_audits")
    op.drop_table("bidding_syndicates")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenders")
