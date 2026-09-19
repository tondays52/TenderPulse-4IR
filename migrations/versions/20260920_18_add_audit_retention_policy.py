"""Add configurable audit retention policy."""
from alembic import op
import sqlalchemy as sa

revision = "20260920_18"
down_revision = "20260920_17"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_retention_policy",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="2555"),
        sa.Column("updated_by", sa.String(length=256), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("audit_retention_policy")
