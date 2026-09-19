"""Add shared bid preparation checklist tasks."""
from alembic import op
import sqlalchemy as sa
revision="20260920_10"
down_revision="20260920_09"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("bid_preparation_tasks",sa.Column("id",sa.Integer(),primary_key=True,autoincrement=True),sa.Column("tender_id",sa.String(64),nullable=False),sa.Column("title",sa.String(512),nullable=False),sa.Column("owner_email",sa.String(256)),sa.Column("status",sa.String(32),nullable=False,server_default="open"),sa.Column("blocker",sa.Text()),sa.Column("created_by",sa.String(256),nullable=False),sa.Column("created_at",sa.DateTime(),nullable=False),sa.Column("updated_at",sa.DateTime(),nullable=False));op.create_index("ix_bid_preparation_tasks_tender_id","bid_preparation_tasks",["tender_id"]);op.create_index("ix_bid_preparation_tasks_owner_email","bid_preparation_tasks",["owner_email"])
def downgrade():
 op.drop_index("ix_bid_preparation_tasks_owner_email",table_name="bid_preparation_tasks");op.drop_index("ix_bid_preparation_tasks_tender_id",table_name="bid_preparation_tasks");op.drop_table("bid_preparation_tasks")
