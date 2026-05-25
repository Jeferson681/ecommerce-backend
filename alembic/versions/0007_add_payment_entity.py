"""add payments entity

Revision ID: 0007_add_payment_entity
Revises: 0006_add_role_to_users
Create Date: 2026-05-25 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_add_payment_entity"
down_revision = "0006_add_role_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="pending"
        ),
        sa.Column(
            "provider", sa.String(length=50), nullable=False, server_default="stripe"
        ),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("amount > 0", name="ck_payment_amount_positive"),
        sa.CheckConstraint(
            "status in ('pending', 'approved', 'failed', 'cancelled', 'refunded')",
            name="ck_payment_status_valid",
        ),
    )
    op.create_index(
        op.f("ix_payments_order_id"), "payments", ["order_id"], unique=False
    )
    op.create_index(op.f("ix_payments_user_id"), "payments", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_payments_provider_payment_id"),
        "payments",
        ["provider_payment_id"],
        unique=False,
    )
    # add unique constraint for provider_payment_id where supported
    try:
        op.create_unique_constraint(
            "uq_payments_provider_payment_id", "payments", ["provider_payment_id"]
        )
    except Exception:
        # Some dialects (SQLite older) may not support creating named unique constraints easily
        pass


def downgrade() -> None:
    try:
        op.drop_constraint(
            "uq_payments_provider_payment_id", "payments", type_="unique"
        )
    except Exception:
        pass
    op.drop_index(op.f("ix_payments_provider_payment_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_user_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_order_id"), table_name="payments")
    op.drop_table("payments")
