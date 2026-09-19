"""Add shared bidder readiness profile."""
from alembic import op
import sqlalchemy as sa
revision = "20260920_09"
down_revision = "20260920_08"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.create_table("bid_readiness_profile", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("contractor_name", sa.String(256), nullable=False, server_default="Tender Trading Inc."), sa.Column("peak_turnover_bdt", sa.Float(), nullable=False, server_default="0"), sa.Column("active_commitments_bdt", sa.Float(), nullable=False, server_default="0"), sa.Column("available_credit_bdt", sa.Float(), nullable=False, server_default="0"), sa.Column("past_similar_max_bdt", sa.Float(), nullable=False, server_default="0"), sa.Column("engineers_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("updated_by", sa.String(256)), sa.Column("updated_at", sa.DateTime(), nullable=False))
def downgrade() -> None: op.drop_table("bid_readiness_profile")
