"""
init users and guild_settings

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("discord_id", sa.String(length=32), nullable=False),
        sa.Column("tz", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("google_sub", sa.String(length=64), nullable=True),
        sa.Column("token_ciphertext", sa.Text(), nullable=True),
    )
    op.create_index("ix_users_discord_id", "users", ["discord_id"], unique=True)

    op.create_table(
        "guild_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("guild_id", sa.String(length=32), nullable=False),
        sa.Column("default_channel_id", sa.String(length=32), nullable=True),
        sa.Column("default_tz", sa.String(length=64), nullable=True),
        sa.UniqueConstraint("guild_id", name="uq_guild_settings_guild"),
    )
    op.create_index("ix_guild_settings_guild_id", "guild_settings", ["guild_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_guild_settings_guild_id", table_name="guild_settings")
    op.drop_table("guild_settings")
    op.drop_index("ix_users_discord_id", table_name="users")
    op.drop_table("users")


