"""Add persistent document requirement reviews."""
from alembic import op
import sqlalchemy as sa
revision = "20260920_19"
down_revision = "20260920_18"
branch_labels = None
depends_on = None
def upgrade():
    op.create_table("document_requirement_reviews", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tender_id", sa.String(64), nullable=False), sa.Column("requirement_key", sa.String(64), nullable=False), sa.Column("source_excerpt", sa.Text(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="unreviewed"), sa.Column("reviewed_by", sa.String(256)), sa.Column("reviewed_at", sa.DateTime()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_index("ix_document_requirement_reviews_tender_id", "document_requirement_reviews", ["tender_id"])
def downgrade():
    op.drop_index("ix_document_requirement_reviews_tender_id", table_name="document_requirement_reviews")
    op.drop_table("document_requirement_reviews")
