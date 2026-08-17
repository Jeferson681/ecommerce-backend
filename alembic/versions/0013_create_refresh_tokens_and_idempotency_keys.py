"""create refresh_tokens and idempotency_keys tables

Revision ID: 0013_create_refresh_tokens_and_idempotency_keys
Revises: 0012_add_image_url_to_products
Create Date: 2026-08-14 00:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0013_create_refresh_tokens_and_idempotency_keys"
down_revision = "0012_add_image_url_to_products"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "jti_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "last_used_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_refresh_tokens_jti_hash",
        "refresh_tokens",
        ["jti_hash"],
        unique=True,
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_hash", sa.String(), nullable=False),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_body", sa.Text(), nullable=True),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id",
            "key",
            name="uq_idempotency_user_key",
        ),
    )
    op.create_index(
        "ix_idempotency_keys_key",
        "idempotency_keys",
        ["key"],
        unique=False,
    )
    op.create_index(
        "ix_idempotency_keys_user_id",
        "idempotency_keys",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_idempotency_keys_request_hash",
        "idempotency_keys",
        ["request_hash"],
        unique=False,
    )
    op.create_index(
        "ix_idempotency_keys_expires_at",
        "idempotency_keys",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("refresh_tokens")
