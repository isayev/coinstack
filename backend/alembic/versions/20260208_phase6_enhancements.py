"""Phase 6 Collection Enhancements

Adds fields based on architecture and numismatic domain expert reviews:

collections:
- purpose (collection purpose classification)
- cover_coin_id (featured coin as thumbnail)
- is_type_set (type set tracking flag)
- type_set_definition (JSON defining required types)
- storage_location (physical storage mapping)
- completion_percentage (cached completion for type sets)

collection_coins:
- is_placeholder (temporary coin until upgrade)
- exclude_from_stats (don't count in totals)
- fulfills_type (which type requirement this satisfies)

Revision ID: 20260208_phase6_enhancements
Revises: 20260207_phase5_enhancements
Create Date: 2026-02-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '20260208_phase6_enhancements'
down_revision: Union[str, None] = '20260207_phase5_enhancements'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table (SQLite compatible)."""
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # =========================================================================
    # COLLECTIONS TABLE ENHANCEMENTS
    # =========================================================================
    # Note: Checking for existing columns to handle partial migration state

    # Purpose classification
    if not column_exists('collections', 'purpose'):
        op.add_column('collections', sa.Column('purpose', sa.String(30), nullable=True, server_default='general'))

    # Cover coin selection
    if not column_exists('collections', 'cover_coin_id'):
        op.add_column('collections', sa.Column('cover_coin_id', sa.Integer(), nullable=True))

    # Type set tracking
    if not column_exists('collections', 'is_type_set'):
        op.add_column('collections', sa.Column('is_type_set', sa.Boolean(), nullable=True, server_default='0'))

    if not column_exists('collections', 'type_set_definition'):
        op.add_column('collections', sa.Column('type_set_definition', sa.Text(), nullable=True))

    # Physical storage mapping
    if not column_exists('collections', 'storage_location'):
        op.add_column('collections', sa.Column('storage_location', sa.String(200), nullable=True))

    # Cached completion percentage
    if not column_exists('collections', 'completion_percentage'):
        op.add_column('collections', sa.Column('completion_percentage', sa.Numeric(5, 2), nullable=True))

    # Create index on purpose (if not exists - SQLite doesn't have IF NOT EXISTS for indexes)
    try:
        op.create_index('ix_collections_purpose', 'collections', ['purpose'])
    except Exception:
        pass  # Index may already exist

    # =========================================================================
    # COLLECTION_COINS TABLE ENHANCEMENTS
    # =========================================================================

    if not column_exists('collection_coins', 'is_placeholder'):
        op.add_column('collection_coins', sa.Column('is_placeholder', sa.Boolean(), nullable=True, server_default='0'))

    if not column_exists('collection_coins', 'exclude_from_stats'):
        op.add_column('collection_coins', sa.Column('exclude_from_stats', sa.Boolean(), nullable=True, server_default='0'))

    if not column_exists('collection_coins', 'fulfills_type'):
        op.add_column('collection_coins', sa.Column('fulfills_type', sa.String(100), nullable=True))


def downgrade() -> None:
    # Remove collection_coins enhancements
    if column_exists('collection_coins', 'fulfills_type'):
        op.drop_column('collection_coins', 'fulfills_type')
    if column_exists('collection_coins', 'exclude_from_stats'):
        op.drop_column('collection_coins', 'exclude_from_stats')
    if column_exists('collection_coins', 'is_placeholder'):
        op.drop_column('collection_coins', 'is_placeholder')

    # Remove collections enhancements
    try:
        op.drop_index('ix_collections_purpose', table_name='collections')
    except Exception:
        pass
    if column_exists('collections', 'completion_percentage'):
        op.drop_column('collections', 'completion_percentage')
    if column_exists('collections', 'storage_location'):
        op.drop_column('collections', 'storage_location')
    if column_exists('collections', 'type_set_definition'):
        op.drop_column('collections', 'type_set_definition')
    if column_exists('collections', 'is_type_set'):
        op.drop_column('collections', 'is_type_set')
    if column_exists('collections', 'cover_coin_id'):
        op.drop_column('collections', 'cover_coin_id')
    if column_exists('collections', 'purpose'):
        op.drop_column('collections', 'purpose')
