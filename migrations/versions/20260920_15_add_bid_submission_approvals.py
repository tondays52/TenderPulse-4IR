"""Add authorized submission sign-off records."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_15"
down_revision = "20260920_14"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("bid_submission_approvals",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tender_id", sa.String(64), nullable=False, unique=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("signed_by", sa.String(256), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("readiness_fingerprint", sa.String(64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bid_submission_approvals_tender_id", "bid_submission_approvals", ["tender_id"])
    op.create_index("ix_bid_submission_approvals_signed_by", "bid_submission_approvals", ["signed_by"])


def downgrade():
    op.drop_index("ix_bid_submission_approvals_signed_by", table_name="bid_submission_approvals")
    op.drop_index("ix_bid_submission_approvals_tender_id", table_name="bid_submission_approvals")
    op.drop_table("bid_submission_approvals")
