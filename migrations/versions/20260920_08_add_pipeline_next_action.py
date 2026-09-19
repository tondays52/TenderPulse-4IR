"""Add explicit next action to shared bid pipeline items."""
from alembic import op
import sqlalchemy as sa
revision = "20260920_08"
down_revision = "20260920_07"
branch_labels = None
depends_on = None
def upgrade() -> None:
    op.add_column("bid_pipeline_items", sa.Column("next_action", sa.Text(), nullable=True))
def downgrade() -> None:
    op.drop_column("bid_pipeline_items", "next_action")
