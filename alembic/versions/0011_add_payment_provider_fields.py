"""add provider_status and provider_reference to payments

Revision ID: 0011_add_payment_provider_fields
Revises: 0010_add_order_status
Create Date: 2026-06-16 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0011_add_payment_provider_fields"
down_revision = "0010_add_order_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("provider_status", sa.String(100), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("provider_reference", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("payments", "provider_reference")
    op.drop_column("payments", "provider_status")
