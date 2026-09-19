"""Add PDF source-page references to document reviews."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_20"
down_revision = "20260920_19"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("document_requirement_reviews", sa.Column("source_page", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("document_requirement_reviews", "source_page")
