"""die_study_module

Add comprehensive die study support:
- Dies catalog table: Master die catalog with die state tracking
- Die links: Track coins sharing same die with confidence levels
- Die pairings: Obverse-reverse die combinations
- Die varieties: Die variety classifications

Revision ID: 5620e2f02d8d
Revises: 20260211_perf_indexes
Create Date: 2026-02-01 00:38:23.330756

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '5620e2f02d8d'
down_revision: Union[str, Sequence[str], None] = '20260211_perf_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(table_name: str) -> bool:
    """Check if table exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    ))
    return result.scalar() > 0


def upgrade() -> None:
    """Create die study tables."""

    # 1. Dies catalog table - master die catalog
    if not table_exists('dies'):
        op.create_table(
            'dies',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('die_identifier', sa.String(100), nullable=False, unique=True),
            sa.Column('die_side', sa.String(10), nullable=True),  # 'obverse' | 'reverse'
            sa.Column('die_state', sa.String(20), nullable=True),  # 'early' | 'middle' | 'late' | 'broken' | 'repaired'
            sa.Column('has_die_crack', sa.Boolean(), server_default='0'),
            sa.Column('has_die_clash', sa.Boolean(), server_default='0'),
            sa.Column('die_rotation_angle', sa.Integer(), nullable=True),  # 0-360 degrees
            sa.Column('reference_system', sa.String(50), nullable=True),
            sa.Column('reference_number', sa.String(100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        )
        op.create_index('ix_dies_identifier', 'dies', ['die_identifier'])
        op.create_index('ix_dies_side', 'dies', ['die_side'])
        op.create_index('ix_dies_reference', 'dies', ['reference_system', 'reference_number'])

    # 2. Die links - track coins sharing same die
    if not table_exists('die_links'):
        op.create_table(
            'die_links',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('die_id', sa.Integer(), sa.ForeignKey('dies.id', ondelete='CASCADE'), nullable=False),
            sa.Column('coin_a_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),
            sa.Column('coin_b_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),
            sa.Column('confidence', sa.String(20), nullable=False),  # 'certain' | 'probable' | 'possible'
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.CheckConstraint('coin_a_id < coin_b_id', name='check_coin_order'),
            sa.UniqueConstraint('die_id', 'coin_a_id', 'coin_b_id', name='uq_die_link'),
        )
        op.create_index('ix_die_links_die_id', 'die_links', ['die_id'])
        op.create_index('ix_die_links_coin_a', 'die_links', ['coin_a_id', 'die_id'])
        op.create_index('ix_die_links_coin_b', 'die_links', ['coin_b_id', 'die_id'])

    # 3. Die pairings - obverse-reverse die combinations
    if not table_exists('die_pairings'):
        op.create_table(
            'die_pairings',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('obverse_die_id', sa.Integer(), sa.ForeignKey('dies.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reverse_die_id', sa.Integer(), sa.ForeignKey('dies.id', ondelete='CASCADE'), nullable=False),
            sa.Column('reference_system', sa.String(50), nullable=True),
            sa.Column('reference_number', sa.String(100), nullable=True),
            sa.Column('rarity_notes', sa.Text(), nullable=True),
            sa.Column('specimen_count', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.UniqueConstraint('obverse_die_id', 'reverse_die_id', name='uq_die_pairing'),
        )
        op.create_index('ix_die_pairings_obverse', 'die_pairings', ['obverse_die_id'])
        op.create_index('ix_die_pairings_reverse', 'die_pairings', ['reverse_die_id'])

    # 4. Die varieties - die variety classifications
    if not table_exists('die_varieties'):
        op.create_table(
            'die_varieties',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),
            sa.Column('die_id', sa.Integer(), sa.ForeignKey('dies.id', ondelete='SET NULL'), nullable=True),
            sa.Column('variety_code', sa.String(50), nullable=False),
            sa.Column('variety_description', sa.String(500), nullable=True),
            sa.Column('distinguishing_features', sa.Text(), nullable=True),
            sa.Column('reference', sa.String(200), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        )
        op.create_index('ix_die_varieties_coin_id', 'die_varieties', ['coin_id'])
        op.create_index('ix_die_varieties_die_id', 'die_varieties', ['die_id'])
        op.create_index('ix_die_varieties_code', 'die_varieties', ['variety_code'])


def downgrade() -> None:
    """Drop die study tables."""
    if table_exists('die_varieties'):
        op.drop_table('die_varieties')
    if table_exists('die_pairings'):
        op.drop_table('die_pairings')
    if table_exists('die_links'):
        op.drop_table('die_links')
    if table_exists('dies'):
        op.drop_table('dies')
