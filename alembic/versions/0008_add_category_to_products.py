"""add category to products

Revision ID: 0008_add_category_to_products
Revises: 0007_add_payment_entity
Create Date: 2026-05-29 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0008_add_category_to_products"
down_revision = "0007_add_payment_entity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("category", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_products_category"), "products", ["category"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_column("products", "category")
