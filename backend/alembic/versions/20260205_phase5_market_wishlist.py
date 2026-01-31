"""Phase 5: Market Tracking & Wishlists

Price monitoring, valuations, alerts, and acquisition wishlists:
- market_prices: Aggregate pricing by attribution
- market_data_points: Individual price observations
- coin_valuations: Valuation snapshots per coin
- price_alerts: User alert configurations
- wishlist_items: Acquisition targets
- wishlist_matches: Matched auction lots

Revision ID: 20260205_phase5
Revises: 20260204_phase4
Create Date: 2026-02-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260205_phase5'
down_revision: Union[str, Sequence[str], None] = '20260204_phase4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create market tracking and wishlist tables."""

    # ==========================================================================
    # MARKET PRICES TABLE
    # ==========================================================================
    # Aggregate pricing by attribution (type-level pricing)

    op.create_table(
        'market_prices',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Attribution key (composite identifier for coin type)
        sa.Column('attribution_key', sa.String(200), nullable=False, unique=True),
        # Format: "{issuer}|{denomination}|{mint}|{catalog_ref}" or similar composite

        # Attribution components
        sa.Column('issuer', sa.String(100), nullable=True),
        sa.Column('denomination', sa.String(50), nullable=True),
        sa.Column('mint', sa.String(100), nullable=True),
        sa.Column('metal', sa.String(20), nullable=True),
        sa.Column('catalog_ref', sa.String(100), nullable=True),
        # Primary catalog reference: "RIC III 42"

        # Aggregate statistics
        sa.Column('avg_price_vf', sa.Numeric(12, 2), nullable=True),
        sa.Column('avg_price_ef', sa.Numeric(12, 2), nullable=True),
        sa.Column('avg_price_au', sa.Numeric(12, 2), nullable=True),
        sa.Column('min_price_seen', sa.Numeric(12, 2), nullable=True),
        sa.Column('max_price_seen', sa.Numeric(12, 2), nullable=True),
        sa.Column('median_price', sa.Numeric(12, 2), nullable=True),

        # Data quality
        sa.Column('data_point_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_sale_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )

    op.create_index('ix_market_prices_attribution_key', 'market_prices', ['attribution_key'])
    op.create_index('ix_market_prices_issuer', 'market_prices', ['issuer'])
    op.create_index('ix_market_prices_catalog_ref', 'market_prices', ['catalog_ref'])

    # ==========================================================================
    # MARKET DATA POINTS TABLE
    # ==========================================================================
    # Individual price observations (auction realized, dealer asking)

    op.create_table(
        'market_data_points',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('market_price_id', sa.Integer(), sa.ForeignKey('market_prices.id', ondelete='CASCADE'), nullable=False),

        # Price data
        sa.Column('price', sa.Numeric(12, 2), nullable=False),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=True),
        sa.Column('price_usd', sa.Numeric(12, 2), nullable=True),
        # Normalized to USD for comparison

        # Source classification
        sa.Column('source_type', sa.String(30), nullable=False),
        # source_type values: 'auction_realized', 'auction_unsold', 'dealer_asking', 'private_sale', 'estimate'
        sa.Column('date', sa.Date(), nullable=False),

        # Condition
        sa.Column('grade', sa.String(30), nullable=True),
        sa.Column('grade_numeric', sa.Integer(), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),

        # Source details
        sa.Column('auction_house', sa.String(100), nullable=True),
        sa.Column('sale_name', sa.String(200), nullable=True),
        sa.Column('lot_number', sa.String(20), nullable=True),
        sa.Column('lot_url', sa.String(500), nullable=True),
        sa.Column('dealer_name', sa.String(100), nullable=True),

        # Quality/reliability
        sa.Column('confidence', sa.String(20), server_default='medium', nullable=True),
        # confidence values: 'low', 'medium', 'high', 'verified'
        sa.Column('notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )

    op.create_index('ix_market_data_points_market_price_id', 'market_data_points', ['market_price_id'])
    op.create_index('ix_market_data_points_date', 'market_data_points', ['date'])
    op.create_index('ix_market_data_points_source_type', 'market_data_points', ['source_type'])

    # ==========================================================================
    # COIN VALUATIONS TABLE
    # ==========================================================================
    # Valuation snapshots per coin (for portfolio tracking)

    op.create_table(
        'coin_valuations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Valuation date
        sa.Column('valuation_date', sa.Date(), nullable=False),

        # Purchase info (denormalized for historical tracking)
        sa.Column('purchase_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('purchase_currency', sa.String(3), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=True),

        # Current market estimate
        sa.Column('current_market_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('value_currency', sa.String(3), server_default='USD', nullable=True),
        sa.Column('market_confidence', sa.String(20), nullable=True),
        # market_confidence values: 'low', 'medium', 'high', 'strong'

        # Comparables used
        sa.Column('comparable_count', sa.Integer(), nullable=True),
        sa.Column('comparable_avg_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('comparable_date_range', sa.String(50), nullable=True),
        # e.g., "2024-2026"

        # Trend analysis
        sa.Column('price_trend_6mo', sa.Numeric(5, 2), nullable=True),
        # Percentage change: -10.50 = down 10.5%
        sa.Column('price_trend_12mo', sa.Numeric(5, 2), nullable=True),
        sa.Column('price_trend_36mo', sa.Numeric(5, 2), nullable=True),

        # Gain/loss calculation
        sa.Column('gain_loss_usd', sa.Numeric(12, 2), nullable=True),
        sa.Column('gain_loss_pct', sa.Numeric(8, 2), nullable=True),

        # Methodology
        sa.Column('valuation_method', sa.String(30), nullable=True),
        # valuation_method values: 'comparable_sales', 'dealer_estimate', 'insurance', 'user_estimate', 'llm_estimate'
        sa.Column('notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )

    op.create_index('ix_coin_valuations_coin_id', 'coin_valuations', ['coin_id'])
    op.create_index('ix_coin_valuations_date', 'coin_valuations', ['valuation_date'])
    op.create_index('ix_coin_valuations_coin_date', 'coin_valuations', ['coin_id', 'valuation_date'])

    # ==========================================================================
    # WISHLIST ITEMS TABLE
    # ==========================================================================
    # Acquisition targets (coins you want to buy)

    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Basic info
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Targeting criteria (any can be null for broad matching)
        sa.Column('issuer', sa.String(100), nullable=True),
        sa.Column('issuer_id', sa.Integer(), sa.ForeignKey('vocab_terms.id'), nullable=True),
        sa.Column('mint', sa.String(100), nullable=True),
        sa.Column('mint_id', sa.Integer(), sa.ForeignKey('vocab_terms.id'), nullable=True),
        sa.Column('year_start', sa.Integer(), nullable=True),
        sa.Column('year_end', sa.Integer(), nullable=True),
        sa.Column('denomination', sa.String(50), nullable=True),
        sa.Column('metal', sa.String(20), nullable=True),
        sa.Column('category', sa.String(30), nullable=True),

        # Catalog reference targeting
        sa.Column('catalog_ref', sa.String(100), nullable=True),
        # e.g., "RIC III 42" - exact match
        sa.Column('catalog_ref_pattern', sa.String(100), nullable=True),
        # e.g., "RIC III 40-50" - range match

        # Quality/condition preferences
        sa.Column('min_grade', sa.String(20), nullable=True),
        sa.Column('min_grade_numeric', sa.Integer(), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),

        # Budget
        sa.Column('max_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('target_price', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=True),

        # Priority and organization
        sa.Column('priority', sa.Integer(), server_default='2', nullable=True),
        # priority values: 1 (highest), 2 (medium), 3 (low), 4 (someday)
        sa.Column('tags', sa.Text(), nullable=True),
        # JSON array of tags

        # Series slot linking (for completion tracking)
        sa.Column('series_slot_id', sa.Integer(), sa.ForeignKey('series_slots.id'), nullable=True),

        # Status tracking
        sa.Column('status', sa.String(20), server_default='wanted', nullable=True),
        # status values: 'wanted', 'watching', 'bidding', 'acquired', 'cancelled'
        sa.Column('acquired_coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id'), nullable=True),
        sa.Column('acquired_at', sa.DateTime(), nullable=True),
        sa.Column('acquired_price', sa.Numeric(12, 2), nullable=True),

        # Notifications
        sa.Column('notify_on_match', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('notify_email', sa.Boolean(), server_default='0', nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
    )

    op.create_index('ix_wishlist_items_status', 'wishlist_items', ['status'])
    op.create_index('ix_wishlist_items_priority', 'wishlist_items', ['priority'])
    op.create_index('ix_wishlist_items_issuer', 'wishlist_items', ['issuer'])
    op.create_index('ix_wishlist_items_catalog_ref', 'wishlist_items', ['catalog_ref'])

    # ==========================================================================
    # PRICE ALERTS TABLE
    # ==========================================================================
    # User alert configurations

    op.create_table(
        'price_alerts',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Target specification (one of these should be set)
        sa.Column('attribution_key', sa.String(200), nullable=True),
        # Monitor a coin type by attribution
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='SET NULL'), nullable=True),
        # Monitor a specific owned coin's value
        sa.Column('wishlist_item_id', sa.Integer(), sa.ForeignKey('wishlist_items.id', ondelete='CASCADE'), nullable=True),
        # Monitor for wishlist item availability

        # Trigger configuration
        sa.Column('trigger_type', sa.String(30), nullable=False),
        # trigger_type values: 'price_below', 'price_above', 'price_change_pct', 'new_listing', 'auction_soon'
        sa.Column('threshold_value', sa.Numeric(12, 2), nullable=True),
        # Absolute price threshold
        sa.Column('threshold_pct', sa.Numeric(5, 2), nullable=True),
        # Percentage threshold
        sa.Column('threshold_grade', sa.String(20), nullable=True),
        # Minimum grade for listings

        # Alert state
        sa.Column('status', sa.String(20), server_default='active', nullable=True),
        # status values: 'active', 'triggered', 'paused', 'expired', 'deleted'
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),

        # Notification tracking
        sa.Column('notification_sent', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('notification_sent_at', sa.DateTime(), nullable=True),
        sa.Column('notification_channel', sa.String(20), nullable=True),
        # notification_channel values: 'in_app', 'email', 'push'

        # Cooldown (prevent spam)
        sa.Column('cooldown_hours', sa.Integer(), server_default='24', nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),

        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_index('ix_price_alerts_status', 'price_alerts', ['status'])
    op.create_index('ix_price_alerts_coin_id', 'price_alerts', ['coin_id'])
    op.create_index('ix_price_alerts_wishlist_item_id', 'price_alerts', ['wishlist_item_id'])

    # ==========================================================================
    # WISHLIST MATCHES TABLE
    # ==========================================================================
    # Matched auction lots for wishlists

    op.create_table(
        'wishlist_matches',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('wishlist_item_id', sa.Integer(), sa.ForeignKey('wishlist_items.id', ondelete='CASCADE'), nullable=False),

        # Match source
        sa.Column('match_type', sa.String(30), nullable=False),
        # match_type values: 'auction_lot', 'dealer_listing', 'ebay_listing', 'vcoins'
        sa.Column('match_source', sa.String(50), nullable=True),
        # e.g., 'heritage', 'cng', 'biddr', 'ebay', 'vcoins'
        sa.Column('match_id', sa.String(100), nullable=False),
        # External ID from source
        sa.Column('match_url', sa.String(500), nullable=True),

        # Listing details
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_url', sa.String(500), nullable=True),

        # Condition/grade
        sa.Column('grade', sa.String(30), nullable=True),
        sa.Column('grade_numeric', sa.Integer(), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),

        # Price info
        sa.Column('price', sa.Numeric(12, 2), nullable=True),
        sa.Column('estimate_low', sa.Numeric(12, 2), nullable=True),
        sa.Column('estimate_high', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(3), server_default='USD', nullable=True),
        sa.Column('current_bid', sa.Numeric(12, 2), nullable=True),

        # Timing
        sa.Column('auction_date', sa.Date(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),

        # Match quality
        sa.Column('match_score', sa.Numeric(3, 2), nullable=True),
        # 0.00 to 1.00 - how well it matches criteria
        sa.Column('match_confidence', sa.String(20), nullable=True),
        # match_confidence values: 'exact', 'high', 'medium', 'possible'
        sa.Column('match_reasons', sa.Text(), nullable=True),
        # JSON array of reasons: ["issuer_match", "catalog_match", "grade_meets_min"]

        # Value analysis
        sa.Column('is_below_budget', sa.Boolean(), nullable=True),
        sa.Column('is_below_market', sa.Boolean(), nullable=True),
        sa.Column('value_score', sa.Numeric(3, 2), nullable=True),
        # 0.00 to 1.00 - value for money

        # User interaction
        sa.Column('notified', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.Column('saved', sa.Boolean(), server_default='0', nullable=True),
        # Saved for later review

        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),

        # Unique constraint: one match per wishlist item + external ID
        sa.UniqueConstraint('wishlist_item_id', 'match_type', 'match_id', name='uq_wishlist_match'),
    )

    op.create_index('ix_wishlist_matches_wishlist_item_id', 'wishlist_matches', ['wishlist_item_id'])
    op.create_index('ix_wishlist_matches_match_source', 'wishlist_matches', ['match_source'])
    op.create_index('ix_wishlist_matches_auction_date', 'wishlist_matches', ['auction_date'])
    op.create_index('ix_wishlist_matches_dismissed', 'wishlist_matches', ['dismissed'])


def downgrade() -> None:
    """Remove market tracking and wishlist tables."""

    op.drop_table('wishlist_matches')
    op.drop_table('price_alerts')
    op.drop_table('wishlist_items')
    op.drop_table('coin_valuations')
    op.drop_table('market_data_points')
    op.drop_table('market_prices')
