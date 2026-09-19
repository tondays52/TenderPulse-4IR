"""Add individual due dates to shared preparation tasks."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_11"
down_revision = "20260920_10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bid_preparation_tasks", sa.Column("due_date", sa.String(64), nullable=True))


def downgrade():
    op.drop_column("bid_preparation_tasks", "due_date")
