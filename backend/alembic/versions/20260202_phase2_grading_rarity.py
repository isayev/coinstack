"""Phase 2: Grading & Rarity System

Comprehensive TPG tracking with history and multi-source rarity assessments:
- grading_history: Track complete grading lifecycle (raw → slabbed → regraded)
- rarity_assessments: Multi-source rarity with grade-conditional support
- census_snapshots: NGC/PCGS population tracking over time

Revision ID: 20260202_phase2
Revises: 20260201_phase1
Create Date: 2026-02-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260202_phase2'
down_revision: Union[str, Sequence[str], None] = '20260201_phase1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create grading history, rarity assessments, and census snapshot tables."""

    # ==========================================================================
    # GRADING HISTORY TABLE
    # ==========================================================================
    # Track complete grading lifecycle (raw → slabbed → crossover → regrade)

    op.create_table(
        'grading_history',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Grading state at this point in time
        sa.Column('grading_state', sa.String(20), nullable=False),
        # grading_state values: 'raw', 'slabbed', 'details_grade'
        sa.Column('grade', sa.String(20), nullable=True),
        sa.Column('grade_service', sa.String(20), nullable=True),
        # grade_service values: 'NGC', 'PCGS', 'ANACS', 'ICG', 'other'
        sa.Column('certification_number', sa.String(50), nullable=True),
        sa.Column('strike_quality', sa.String(10), nullable=True),
        # strike_quality values: 1-5 scale
        sa.Column('surface_quality', sa.String(10), nullable=True),
        # surface_quality values: 1-5 scale
        sa.Column('grade_numeric', sa.Integer(), nullable=True),
        # NGC/PCGS numeric: 50, 53, 55, 58, 60, 62, 63, 64, 65, 66, 67, 68, 69, 70
        sa.Column('designation', sa.String(50), nullable=True),
        # designation values: 'Fine Style', 'Choice', 'Gem', 'Superb Gem'
        sa.Column('has_star', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('photo_cert', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('verification_url', sa.String(500), nullable=True),

        # Event tracking
        sa.Column('event_type', sa.String(30), nullable=False),
        # event_type values: 'initial', 'crossover', 'regrade', 'crack_out', 'upgrade_attempt'
        sa.Column('graded_date', sa.Date(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('submitter', sa.String(100), nullable=True),
        sa.Column('turnaround_days', sa.Integer(), nullable=True),
        sa.Column('grading_fee', sa.Numeric(8, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Ordering and current state
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_current', sa.Boolean(), nullable=False, server_default='0'),
    )

    op.create_index('ix_grading_history_coin_id', 'grading_history', ['coin_id'])
    op.create_index('ix_grading_history_is_current', 'grading_history', ['coin_id', 'is_current'])
    op.create_index('ix_grading_history_certification', 'grading_history', ['grade_service', 'certification_number'])

    # ==========================================================================
    # RARITY ASSESSMENTS TABLE
    # ==========================================================================
    # Multi-source rarity tracking with grade-conditional support

    op.create_table(
        'rarity_assessments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Classification
        sa.Column('rarity_code', sa.String(20), nullable=False),
        # rarity_code values: C, S, R1, R2, R3, R4, R5, RR, RRR, UNIQUE
        sa.Column('rarity_system', sa.String(30), nullable=False),
        # rarity_system values: 'RIC', 'catalog', 'census', 'market_frequency', 'custom'

        # Source attribution
        sa.Column('source_type', sa.String(30), nullable=False),
        # source_type values: 'catalog', 'census_data', 'auction_analysis', 'expert_opinion', 'database'
        sa.Column('source_name', sa.String(200), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('source_date', sa.Date(), nullable=True),

        # Grade-conditional rarity
        sa.Column('grade_range_low', sa.String(20), nullable=True),
        # e.g., 'VF' or numeric '30'
        sa.Column('grade_range_high', sa.String(20), nullable=True),
        # e.g., 'EF' or numeric '45'
        sa.Column('grade_conditional_notes', sa.Text(), nullable=True),
        # e.g., "R4 in Fine or better; RR in VF+"

        # Census data (if source_type = 'census_data')
        sa.Column('census_total', sa.Integer(), nullable=True),
        sa.Column('census_this_grade', sa.Integer(), nullable=True),
        sa.Column('census_finer', sa.Integer(), nullable=True),
        sa.Column('census_date', sa.Date(), nullable=True),

        # Metadata
        sa.Column('confidence', sa.String(20), server_default='medium', nullable=True),
        # confidence values: 'low', 'medium', 'high', 'authoritative'
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )

    op.create_index('ix_rarity_assessments_coin_id', 'rarity_assessments', ['coin_id'])
    op.create_index('ix_rarity_assessments_is_primary', 'rarity_assessments', ['coin_id', 'is_primary'])
    op.create_index('ix_rarity_assessments_rarity_code', 'rarity_assessments', ['rarity_code'])

    # ==========================================================================
    # CENSUS SNAPSHOTS TABLE
    # ==========================================================================
    # Track NGC/PCGS population over time for trend analysis

    op.create_table(
        'census_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Service and timing
        sa.Column('service', sa.String(20), nullable=False),
        # service values: 'NGC', 'PCGS'
        sa.Column('snapshot_date', sa.Date(), nullable=False),

        # Population data
        sa.Column('total_graded', sa.Integer(), nullable=False),
        sa.Column('grade_breakdown', sa.Text(), nullable=True),
        # JSON: {"VF": 10, "EF": 5, "AU": 2, "MS": 1}
        sa.Column('coins_at_grade', sa.Integer(), nullable=True),
        sa.Column('coins_finer', sa.Integer(), nullable=True),
        sa.Column('percentile', sa.Numeric(5, 2), nullable=True),
        # e.g., 95.00 means top 5%

        # Reference for lookup
        sa.Column('catalog_reference', sa.String(100), nullable=True),
        # e.g., "RIC III 42" used for census lookup
        sa.Column('notes', sa.Text(), nullable=True),
    )

    op.create_index('ix_census_snapshots_coin_id', 'census_snapshots', ['coin_id'])
    op.create_index('ix_census_snapshots_service_date', 'census_snapshots', ['service', 'snapshot_date'])

    # ==========================================================================
    # DATA MIGRATION: Populate grading_history from current coin data
    # ==========================================================================

    # This creates initial grading history entries from existing grading data
    op.execute("""
        INSERT INTO grading_history (
            coin_id, grading_state, grade, grade_service, certification_number,
            event_type, is_current, sequence_order
        )
        SELECT
            id,
            COALESCE(grading_state, 'raw'),
            grade,
            grade_service,
            certification_number,
            'initial',
            1,
            0
        FROM coins_v2
        WHERE grading_state IS NOT NULL OR grade IS NOT NULL
    """)

    # ==========================================================================
    # DATA MIGRATION: Populate rarity_assessments from current coin data
    # ==========================================================================

    op.execute("""
        INSERT INTO rarity_assessments (
            coin_id, rarity_code, rarity_system, source_type, is_primary
        )
        SELECT
            id,
            rarity,
            'catalog',
            'catalog',
            1
        FROM coins_v2
        WHERE rarity IS NOT NULL AND rarity != ''
    """)


def downgrade() -> None:
    """Remove grading history, rarity assessments, and census snapshot tables."""

    # Drop tables in reverse order
    op.drop_table('census_snapshots')
    op.drop_table('rarity_assessments')
    op.drop_table('grading_history')
