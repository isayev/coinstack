"""Phase 5 numismatic enhancements

Adds additional fields to market_prices and market_data_points tables based on
numismatic domain expert review:

market_prices:
- category (coin category: imperial, republic, provincial, etc.)
- avg_price_ms (Mint State grade pricing)

market_data_points:
- is_hammer_price (whether price is hammer or includes buyer's premium)
- buyers_premium_pct (buyer's premium percentage)
- is_slabbed (whether coin is slabbed/graded)
- grading_service (NGC, PCGS, etc.)
- certification_number (slab certification number)

Revision ID: 20260207_phase5_enhancements
Revises: 20260206_phase6_collections
Create Date: 2026-02-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260207_phase5_enhancements'
down_revision: Union[str, None] = '20260206_phase6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to market_prices table
    op.add_column('market_prices', sa.Column('category', sa.String(30), nullable=True))
    op.add_column('market_prices', sa.Column('avg_price_ms', sa.Numeric(12, 2), nullable=True))

    # Create index on category
    op.create_index('ix_market_prices_category', 'market_prices', ['category'])

    # Add columns to market_data_points table
    op.add_column('market_data_points', sa.Column('is_hammer_price', sa.Boolean(), nullable=True, server_default='1'))
    op.add_column('market_data_points', sa.Column('buyers_premium_pct', sa.Numeric(5, 2), nullable=True))
    op.add_column('market_data_points', sa.Column('is_slabbed', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('market_data_points', sa.Column('grading_service', sa.String(20), nullable=True))
    op.add_column('market_data_points', sa.Column('certification_number', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove columns from market_data_points
    op.drop_column('market_data_points', 'certification_number')
    op.drop_column('market_data_points', 'grading_service')
    op.drop_column('market_data_points', 'is_slabbed')
    op.drop_column('market_data_points', 'buyers_premium_pct')
    op.drop_column('market_data_points', 'is_hammer_price')

    # Remove columns from market_prices
    op.drop_index('ix_market_prices_category', table_name='market_prices')
    op.drop_column('market_prices', 'avg_price_ms')
    op.drop_column('market_prices', 'category')
