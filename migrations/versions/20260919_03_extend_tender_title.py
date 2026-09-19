"""Allow full official tender titles without truncation.

Revision ID: 20260919_03
Revises: 20260919_02
"""

from alembic import op
import sqlalchemy as sa


revision = "20260919_03"
down_revision = "20260919_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("tenders") as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.String(length=512),
            type_=sa.Text(),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("tenders") as batch_op:
        batch_op.alter_column(
            "title",
            existing_type=sa.Text(),
            type_=sa.String(length=512),
            existing_nullable=False,
        )
