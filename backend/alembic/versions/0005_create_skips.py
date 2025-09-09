# path: backend/alembic/versions/0005_create_skips.py
"""create skips table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0005_create_skips"
down_revision = None  # <- if you already have migrations, set this to your current head
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skips",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("qr_code", sa.String(length=64), nullable=False),
        sa.Column("owner_org_id", UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_commodity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("zone_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="in_stock"),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_by_id", UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_skips_qr_code", "skips", ["qr_code"], unique=True)
    op.create_index("ix_skips_owner_org", "skips", ["owner_org_id"], unique=False)
    op.create_index("ix_skips_zone", "skips", ["zone_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_skips_zone", table_name="skips")
    op.drop_index("ix_skips_owner_org", table_name="skips")
    op.drop_index("ix_skips_qr_code", table_name="skips")
    op.drop_table("skips")
