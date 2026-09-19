"""Add append-only shared bid workflow activity events."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_12"
down_revision = "20260920_11"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("bid_activity_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tender_id", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(32), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("summary", sa.String(1000), nullable=False),
        sa.Column("actor_email", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bid_activity_events_tender_id", "bid_activity_events", ["tender_id"])
    op.create_index("ix_bid_activity_events_actor_email", "bid_activity_events", ["actor_email"])


def downgrade():
    op.drop_index("ix_bid_activity_events_actor_email", table_name="bid_activity_events")
    op.drop_index("ix_bid_activity_events_tender_id", table_name="bid_activity_events")
    op.drop_table("bid_activity_events")
