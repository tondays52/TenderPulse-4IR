"""Add daily executive operating summaries."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_17"
down_revision = "20260920_16"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "executive_kpi_summaries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("summary_date", sa.String(length=10), nullable=False, unique=True),
        sa.Column("pipeline_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_pipeline", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overdue_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("submitted_pending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("decisioned_bids", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("won_bids", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lost_bids", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_rate_pct", sa.Float(), nullable=True),
        sa.Column("awarded_contract_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("needs_attention_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("generated_by", sa.String(length=256), nullable=False, server_default="scheduler"),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_executive_kpi_summaries_summary_date", "executive_kpi_summaries", ["summary_date"])


def downgrade():
    op.drop_index("ix_executive_kpi_summaries_summary_date", table_name="executive_kpi_summaries")
    op.drop_table("executive_kpi_summaries")
