"""Add administrator-managed team alert defaults.

Revision ID: 20260920_06
Revises: 20260920_05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260920_06"
down_revision = "20260920_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alert_preferences",
        sa.Column("is_customized", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "team_alert_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("agencies_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("alert_types_json", sa.Text(), nullable=False, server_default='["closing_date", "tender_security"]'),
        sa.Column("deadline_window_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("requested_external_channel", sa.String(length=32), nullable=False, server_default="in_app"),
        sa.Column("updated_by", sa.String(length=256), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("team_alert_policy")
    op.drop_column("alert_preferences", "is_customized")
