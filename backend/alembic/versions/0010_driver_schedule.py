# ======================================================================
# file: backend/alembic/versions/0010_driver_schedule.py
# adjust down_revision to your last revision id
# ======================================================================
from alembic import op
import sqlalchemy as sa

revision = "0010_driver_schedule"
down_revision = "0009_wtn_table"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "driver_tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("driver_name", sa.String(), nullable=False, index=True),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("skip_qr", sa.String(), nullable=True),
        sa.Column("to_zone_id", sa.String(), nullable=True),
        sa.Column("destination_name", sa.String(), nullable=True),
        sa.Column("destination_type", sa.String(), nullable=True),
        sa.Column("gross_kg", sa.Float(), nullable=True),
        sa.Column("tare_kg", sa.Float(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("done", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )

def downgrade() -> None:
    op.drop_table("driver_tasks")
