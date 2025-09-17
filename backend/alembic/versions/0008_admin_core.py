from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_admin_core"
down_revision = "0007_driver_tables"  # adjust if different
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "contractors",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("org_name", sa.String(), nullable=False),
        sa.Column("contact_name", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("billing_address", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("reg", sa.String(), nullable=False, unique=True),
        sa.Column("make_model", sa.String(), nullable=True),
        sa.Column("capacity_kg", sa.Float(), nullable=True),
        sa.Column("contractor_id", sa.String(), sa.ForeignKey("contractors.id", ondelete="SET NULL")),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.create_table(
        "skip_assignments",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("skip_id", sa.String(), sa.ForeignKey("skips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contractor_id", sa.String(), sa.ForeignKey("contractors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(), nullable=True),
    )
    op.create_unique_constraint("uq_skip_active_assignment", "skip_assignments", ["skip_id", "unassigned_at"])

def downgrade() -> None:
    op.drop_constraint("uq_skip_active_assignment", "skip_assignments", type_="unique")
    op.drop_table("skip_assignments")
    op.drop_table("vehicles")
    op.drop_table("contractors")

