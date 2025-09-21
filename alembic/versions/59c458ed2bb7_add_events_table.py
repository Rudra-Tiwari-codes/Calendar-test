"""
Revision ID: 59c458ed2bb7
Revises: 4e28fbd68bba
Create Date: 2025-09-11 19:29:37.696794
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '59c458ed2bb7'
down_revision = '4e28fbd68bba'


def upgrade() -> None:
    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('discord_user_id', sa.String(length=32), nullable=False),
        sa.Column('google_event_id', sa.String(length=128), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('description', sa.String(length=1024), nullable=True),
        sa.Column('location', sa.String(length=256), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attendees', sa.String(length=512), nullable=True),
        sa.Column('google_calendar_link', sa.String(length=512), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_events_discord_user_id'), 'events', ['discord_user_id'], unique=False)
    op.create_index(op.f('ix_events_google_event_id'), 'events', ['google_event_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_events_google_event_id'), table_name='events')
    op.drop_index(op.f('ix_events_discord_user_id'), table_name='events')
    op.drop_table('events')


