"""Add private evidence attachments for shared preparation tasks."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_13"
down_revision = "20260920_12"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("bid_task_attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("bid_preparation_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(128), nullable=False, unique=True),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by", sa.String(256), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_bid_task_attachments_task_id", "bid_task_attachments", ["task_id"])
    op.create_index("ix_bid_task_attachments_uploaded_by", "bid_task_attachments", ["uploaded_by"])


def downgrade():
    op.drop_index("ix_bid_task_attachments_uploaded_by", table_name="bid_task_attachments")
    op.drop_index("ix_bid_task_attachments_task_id", table_name="bid_task_attachments")
    op.drop_table("bid_task_attachments")
