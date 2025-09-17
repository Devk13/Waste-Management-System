from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "0009_wtn_table"
down_revision = "0008_admin_core"  # adjust if different in your repo
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "waste_transfer_notes",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("number", sa.String(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
    )
    op.create_index("ix_wtn_number", "waste_transfer_notes", ["number"])

def downgrade() -> None:
    op.drop_index("ix_wtn_number", table_name="waste_transfer_notes")
    op.drop_table("waste_transfer_notes")

