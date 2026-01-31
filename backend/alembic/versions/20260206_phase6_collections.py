"""Phase 6: Collections & Sub-collections

User-defined collection groupings with smart filters:
- collections: Collection definitions (custom and smart)
- collection_coins: Many-to-many linking with ordering

Revision ID: 20260206_phase6
Revises: 20260205_phase5
Create Date: 2026-02-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260206_phase6'
down_revision: Union[str, Sequence[str], None] = '20260205_phase5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create collections and collection_coins tables."""

    # ==========================================================================
    # COLLECTIONS TABLE
    # ==========================================================================
    # Collection definitions with support for custom and smart collections

    op.create_table(
        'collections',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Basic info
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(100), nullable=True),
        # URL-friendly name for potential sharing

        # Collection type
        sa.Column('collection_type', sa.String(20), server_default='custom', nullable=True),
        # collection_type values:
        # - 'custom': Manual membership
        # - 'smart': Auto-populated by filter criteria
        # - 'series': Linked to a coin series for completion tracking
        # - 'system': System-generated (e.g., "All Coins", "Recently Added")

        # Smart collection filter (JSON)
        sa.Column('smart_filter', sa.Text(), nullable=True),
        # JSON filter criteria for smart collections
        # Example: {"category": ["roman_imperial"], "metal": ["gold"], "year_start_gte": -100}

        # Series linking (for series-based collections)
        sa.Column('series_id', sa.Integer(), sa.ForeignKey('series.id', ondelete='SET NULL'), nullable=True),

        # Display settings
        sa.Column('cover_image_url', sa.String(500), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        # Hex color for UI: "#FFD700"
        sa.Column('icon', sa.String(50), nullable=True),
        # Icon name: "crown", "temple", "eagle"
        sa.Column('display_order', sa.Integer(), nullable=True),
        sa.Column('default_sort', sa.String(30), nullable=True),
        # default_sort values: 'added_date', 'year', 'denomination', 'value', 'custom'
        sa.Column('default_view', sa.String(20), nullable=True),
        # default_view values: 'grid', 'table', 'timeline'

        # Statistics (denormalized for performance)
        sa.Column('coin_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_value', sa.Numeric(14, 2), nullable=True),
        sa.Column('stats_updated_at', sa.DateTime(), nullable=True),

        # User preferences
        sa.Column('is_favorite', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('is_hidden', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('is_public', sa.Boolean(), server_default='0', nullable=True),
        # For future sharing features

        # Parent collection (for hierarchical organization)
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('collections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('level', sa.Integer(), server_default='0', nullable=True),
        # Nesting level: 0 = top-level, 1 = sub-collection, etc.

        # Metadata
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )

    op.create_index('ix_collections_name', 'collections', ['name'])
    op.create_index('ix_collections_collection_type', 'collections', ['collection_type'])
    op.create_index('ix_collections_is_favorite', 'collections', ['is_favorite'])
    op.create_index('ix_collections_parent_id', 'collections', ['parent_id'])
    op.create_index('ix_collections_series_id', 'collections', ['series_id'])
    op.create_index('ix_collections_display_order', 'collections', ['display_order'])

    # ==========================================================================
    # COLLECTION COINS TABLE
    # ==========================================================================
    # Many-to-many linking with ordering and metadata

    op.create_table(
        'collection_coins',
        sa.Column('collection_id', sa.Integer(), sa.ForeignKey('collections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Membership metadata
        sa.Column('added_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('added_by', sa.String(100), nullable=True),
        # For future multi-user support

        # Ordering within collection
        sa.Column('position', sa.Integer(), nullable=True),
        # Manual sort position (null = use default sort)
        sa.Column('custom_order', sa.Integer(), nullable=True),
        # User-defined order for drag-and-drop

        # Coin-specific notes within this collection
        sa.Column('notes', sa.Text(), nullable=True),
        # e.g., "Key coin for completing this series"

        # Highlight/feature flags
        sa.Column('is_featured', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('is_cover_coin', sa.Boolean(), server_default='0', nullable=True),
        # Use this coin's image as collection cover

        # Series slot tracking (for completion)
        sa.Column('series_slot_id', sa.Integer(), sa.ForeignKey('series_slots.id', ondelete='SET NULL'), nullable=True),
        # Links to which slot this coin fills

        # Primary key
        sa.PrimaryKeyConstraint('collection_id', 'coin_id'),
    )

    op.create_index('ix_collection_coins_collection_id', 'collection_coins', ['collection_id'])
    op.create_index('ix_collection_coins_coin_id', 'collection_coins', ['coin_id'])
    op.create_index('ix_collection_coins_position', 'collection_coins', ['collection_id', 'position'])
    op.create_index('ix_collection_coins_added_at', 'collection_coins', ['added_at'])

    # ==========================================================================
    # CREATE DEFAULT SYSTEM COLLECTIONS
    # ==========================================================================

    op.execute("""
        INSERT INTO collections (name, description, collection_type, display_order, icon)
        VALUES
            ('All Coins', 'Complete collection', 'system', 0, 'coins'),
            ('Recently Added', 'Coins added in the last 30 days', 'smart', 1, 'clock'),
            ('Favorites', 'Your favorite coins', 'smart', 2, 'star'),
            ('High Value', 'Coins valued over $1000', 'smart', 3, 'gem')
    """)

    # Set smart filters for system collections
    op.execute("""
        UPDATE collections
        SET smart_filter = '{"created_days_ago_lte": 30}'
        WHERE name = 'Recently Added'
    """)

    op.execute("""
        UPDATE collections
        SET smart_filter = '{"is_favorite": true}'
        WHERE name = 'Favorites'
    """)

    op.execute("""
        UPDATE collections
        SET smart_filter = '{"value_gte": 1000}'
        WHERE name = 'High Value'
    """)


def downgrade() -> None:
    """Remove collections and collection_coins tables."""

    op.drop_table('collection_coins')
    op.drop_table('collections')
