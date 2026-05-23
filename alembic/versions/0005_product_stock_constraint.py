"""add product stock non-negative constraint

Revision ID: 0005_product_stock_constraint
Revises: 0004_order_entity_tables
Create Date: 2026-05-23 00:00:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_product_stock_constraint"
down_revision = "0004_order_entity_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add a check constraint to ensure stock_quantity is non-negative.
    # Note: on SQLite this may require table rebuild; alembic/autogenerate handles this normally.
    op.create_check_constraint(
        "ck_product_stock_non_negative", "products", "stock_quantity >= 0"
    )


def downgrade() -> None:
    op.drop_constraint("ck_product_stock_non_negative", "products", type_="check")
