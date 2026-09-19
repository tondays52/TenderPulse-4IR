"""Add shared bid pipeline lifecycle records."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_07"
down_revision = "20260920_06"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("bid_pipeline_items",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tender_id", sa.String(64), nullable=False, unique=True),
        sa.Column("tender_title", sa.Text(), nullable=False), sa.Column("agency", sa.String(256)),
        sa.Column("owner_email", sa.String(256)), sa.Column("stage", sa.String(32), nullable=False, server_default="review"),
        sa.Column("internal_due_date", sa.String(64)), sa.Column("decision", sa.String(32)), sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.String(256), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bid_pipeline_items_tender_id", "bid_pipeline_items", ["tender_id"])
    op.create_index("ix_bid_pipeline_items_owner_email", "bid_pipeline_items", ["owner_email"])

def downgrade() -> None:
    op.drop_index("ix_bid_pipeline_items_owner_email", table_name="bid_pipeline_items")
    op.drop_index("ix_bid_pipeline_items_tender_id", table_name="bid_pipeline_items")
    op.drop_table("bid_pipeline_items")
