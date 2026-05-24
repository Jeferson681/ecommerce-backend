"""add role to users

Revision ID: 0006_add_role_to_users
Revises: 0005_product_stock_constraint
Create Date: 2026-05-24 13:20:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0006_add_role_to_users"
down_revision = "0005_product_stock_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add `role` column to users with default 'user'. SQLite supports adding simple columns.
    user_role_enum = sa.Enum("user", "admin", name="userrole")
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
    )
    # Ensure existing rows have the default value
    op.execute("UPDATE users SET role='user' WHERE role IS NULL")


def downgrade() -> None:
    op.drop_column("users", "role")
    try:
        sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
    except Exception:
        pass
