"""Performance: Add composite indexes for common query patterns

Add composite indexes for frequently-used filter combinations:
- (category, metal) - common filter combination
- (category, grading_state) - common filter combination
- (issuer_id, year_start) - attribution searches

Revision ID: 20260211_perf_indexes
Revises: 20260210_phase1_5c_numismatic
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260211_perf_indexes'
down_revision = '20260210_phase1_5c_numismatic'
branch_labels = None
depends_on = None


def index_exists(index_name: str) -> bool:
    """Check if index exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name=:name"),
        {"name": index_name}
    )
    return result.scalar() > 0


def upgrade() -> None:
    # Add composite indexes for common filter patterns
    if not index_exists('ix_coins_v2_category_metal'):
        op.create_index('ix_coins_v2_category_metal', 'coins_v2', ['category', 'metal'])

    if not index_exists('ix_coins_v2_category_grading_state'):
        op.create_index('ix_coins_v2_category_grading_state', 'coins_v2', ['category', 'grading_state'])

    if not index_exists('ix_coins_v2_issuer_year'):
        op.create_index('ix_coins_v2_issuer_year', 'coins_v2', ['issuer_id', 'year_start'])


def downgrade() -> None:
    # Drop indexes if they exist
    if index_exists('ix_coins_v2_issuer_year'):
        op.drop_index('ix_coins_v2_issuer_year', 'coins_v2')

    if index_exists('ix_coins_v2_category_grading_state'):
        op.drop_index('ix_coins_v2_category_grading_state', 'coins_v2')

    if index_exists('ix_coins_v2_category_metal'):
        op.drop_index('ix_coins_v2_category_metal', 'coins_v2')
