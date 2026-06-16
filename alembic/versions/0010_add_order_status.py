"""add order status column

Revision ID: 0010_add_order_status
Revises: 0009_revision_entity_tables
Create Date: 2026-06-15 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_add_order_status"
down_revision = "0009_revision_entity_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("orders", "status")
