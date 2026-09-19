"""Add per-operator alert preferences.

Revision ID: 20260920_05
Revises: 20260920_04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260920_05"
down_revision = "20260920_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alert_preferences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_email", sa.String(length=256), nullable=False, unique=True),
        sa.Column("agencies_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("alert_types_json", sa.Text(), nullable=False, server_default='["closing_date", "tender_security"]'),
        sa.Column("deadline_window_hours", sa.Integer(), nullable=False, server_default="72"),
        sa.Column("requested_external_channel", sa.String(length=32), nullable=False, server_default="in_app"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_alert_preferences_user_email", "alert_preferences", ["user_email"])


def downgrade() -> None:
    op.drop_index("ix_alert_preferences_user_email", table_name="alert_preferences")
    op.drop_table("alert_preferences")
