"""Add per-operator corrigendum review state.

Revision ID: 20260920_04
Revises: 20260919_03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260920_04"
down_revision = "20260919_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "corrigendum_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("corrigendum_id", sa.Integer(), sa.ForeignKey("corrigenda.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_email", sa.String(length=256), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("corrigendum_id", "reviewer_email", name="uq_corrigendum_review_reviewer"),
    )
    op.create_index("ix_corrigendum_reviews_corrigendum_id", "corrigendum_reviews", ["corrigendum_id"])
    op.create_index("ix_corrigendum_reviews_reviewer_email", "corrigendum_reviews", ["reviewer_email"])
    op.create_index("ix_corrigendum_reviews_reviewer_status", "corrigendum_reviews", ["reviewer_email", "status"])


def downgrade() -> None:
    op.drop_index("ix_corrigendum_reviews_reviewer_status", table_name="corrigendum_reviews")
    op.drop_index("ix_corrigendum_reviews_reviewer_email", table_name="corrigendum_reviews")
    op.drop_index("ix_corrigendum_reviews_corrigendum_id", table_name="corrigendum_reviews")
    op.drop_table("corrigendum_reviews")
