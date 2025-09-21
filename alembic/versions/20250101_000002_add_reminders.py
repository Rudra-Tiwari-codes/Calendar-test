"""
add reminders table

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-01 00:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=128), nullable=True),
        sa.Column("channel_id", sa.String(length=32), nullable=True),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("retries", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.UniqueConstraint("event_id", "remind_at", name="uq_reminder_event_at"),
    )


def downgrade() -> None:
    op.drop_table("reminders")


