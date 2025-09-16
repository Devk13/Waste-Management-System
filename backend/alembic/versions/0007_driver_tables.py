# revision identifiers, used by Alembic.
revision = "0007_driver_tables"
down_revision = "0006_skip_assets"  # keep in step with your last migration filename
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade():
        # driver_profiles
    op.create_table(
        "driver_profiles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        # drop index=True here
        sa.Column("user_id", sa.String(length=36), unique=True, nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
    )

    # driver_assignments
    op.create_table(
        "driver_assignments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        # drop index=True here too; we create it explicitly below
        sa.Column("driver_user_id", sa.String(length=36), nullable=False),
        sa.Column("skip_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="assigned"),
        sa.Column("open", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("(datetime('now'))")),
    )

    # keep one explicit non-unique index for driver_assignments.driver_user_id
    op.create_index("ix_driver_assignments_driver_user_id", "driver_assignments", ["driver_user_id"])

    def downgrade():
        # drop the index we explicitly created
        op.drop_index("ix_driver_assignments_driver_user_id", table_name="driver_assignments")
        op.drop_table("driver_assignments")
        # remove this if you did not explicitly create a separate index for user_id
        # op.drop_index("ix_driver_profiles_user_id", table_name="driver_profiles")
        op.drop_table("driver_profiles")
