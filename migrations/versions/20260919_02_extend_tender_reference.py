"""allow long e-GP tender reference numbers

Revision ID: 20260919_02
Revises: 20260919_01
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260919_02"
down_revision = "20260919_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode keeps the migration compatible with the disposable SQLite
    # migration test while PostgreSQL uses an in-place type conversion.
    with op.batch_alter_table("tenders") as batch_op:
        batch_op.alter_column("ref_no", existing_type=sa.String(length=128), type_=sa.Text())


def downgrade() -> None:
    with op.batch_alter_table("tenders") as batch_op:
        batch_op.alter_column("ref_no", existing_type=sa.Text(), type_=sa.String(length=128))
