"""add image_url to products

Revision ID: 0012_add_image_url_to_products
Revises: 0011_add_payment_provider_fields
Create Date: 2026-08-10 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0012_add_image_url_to_products"
down_revision = "0011_add_payment_provider_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("products", "image_url")
