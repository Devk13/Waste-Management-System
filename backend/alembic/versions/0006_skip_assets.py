# path: backend/alembic/versions/0006_skip_assets.py
"""add table skip_assets for QR label PNGs and 3-up PDF"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "0006_skip_assets"
down_revision = "0005_create_skips"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skip_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "skip_id",
            UUID(as_uuid=True),
            sa.ForeignKey("skips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("bytes", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_skip_assets_skip_kind", "skip_assets", ["skip_id", "kind", "idx"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_skip_assets_skip_kind", table_name="skip_assets")
    op.drop_table("skip_assets")
