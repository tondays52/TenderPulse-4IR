"""Add post-submission bid outcome records."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_16"
down_revision = "20260920_15"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("bid_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tender_id", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="submitted"),
        sa.Column("submission_reference", sa.String(256), nullable=True),
        sa.Column("submitted_at", sa.String(64), nullable=True),
        sa.Column("outcome_date", sa.String(64), nullable=True),
        sa.Column("awarded_contract_value", sa.Float(), nullable=True),
        sa.Column("lessons_learned", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(256), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bid_outcomes_tender_id", "bid_outcomes", ["tender_id"])


def downgrade():
    op.drop_index("ix_bid_outcomes_tender_id", table_name="bid_outcomes")
    op.drop_table("bid_outcomes")
