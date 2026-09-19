"""Mark preparation tasks required for submission readiness."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_14"
down_revision = "20260920_13"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("bid_preparation_tasks", sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    op.drop_column("bid_preparation_tasks", "is_required")
