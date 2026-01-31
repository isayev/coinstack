"""Provenance V3: Unified source_name field and acquisition integration

Revision ID: 20260131_prov_v3
Revises: 892810d42bbe
Create Date: 2026-01-31

Changes:
- Add source_name column (unified field replacing auction_house/dealer_name/collection_name)
- Add sale_name column (replaces sale_series)
- Add source_origin column (track data origin: manual, scraper, import, etc.)
- Add created_at, updated_at timestamps
- Migrate existing data: consolidate legacy fields into source_name
- Create ACQUISITION provenance entries from existing coin acquisition data
- Keep legacy columns for backward compatibility (to be removed in future migration)
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = '20260131_prov_v3'
down_revision = '892810d42bbe'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade to V3 provenance schema.

    1. Add new columns with defaults
    2. Migrate data from legacy fields
    3. Create acquisition entries from coin acquisition data
    """

    # Step 1: Add new columns to provenance_events
    # Using batch mode for SQLite compatibility
    with op.batch_alter_table('provenance_events') as batch_op:
        # V3 unified field
        batch_op.add_column(
            sa.Column('source_name', sa.String(200), nullable=True, default='')
        )
        # Renamed from sale_series
        batch_op.add_column(
            sa.Column('sale_name', sa.String(255), nullable=True)
        )
        # Data origin tracking
        batch_op.add_column(
            sa.Column('source_origin', sa.String(30), nullable=True, default='migration')
        )
        # Timestamps
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('updated_at', sa.DateTime(), nullable=True)
        )

    # Step 2: Migrate data - populate source_name from legacy fields
    connection = op.get_bind()

    # Consolidate auction_house, dealer_name, collection_name into source_name
    connection.execute(sa.text("""
        UPDATE provenance_events
        SET source_name = COALESCE(auction_house, dealer_name, collection_name, ''),
            sale_name = sale_series,
            source_origin = 'migration',
            created_at = CURRENT_TIMESTAMP
        WHERE source_name IS NULL OR source_name = ''
    """))

    # Step 3: Create ACQUISITION entries from coin acquisition data
    # For each coin with acquisition data, create a provenance entry if not exists
    connection.execute(sa.text("""
        INSERT INTO provenance_events (
            coin_id, event_type, source_name, event_date,
            total_price, currency, url, notes,
            source_origin, sort_order, created_at,
            receipt_available
        )
        SELECT
            c.id as coin_id,
            'acquisition' as event_type,
            COALESCE(c.acquisition_source, 'Unknown') as source_name,
            c.acquisition_date as event_date,
            c.acquisition_price as total_price,
            c.acquisition_currency as currency,
            c.acquisition_url as url,
            'Auto-created from acquisition data' as notes,
            'auto_acquisition' as source_origin,
            999 as sort_order,  -- Highest sort_order = most recent
            CURRENT_TIMESTAMP as created_at,
            0 as receipt_available
        FROM coins_v2 c
        WHERE c.acquisition_price IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM provenance_events p
              WHERE p.coin_id = c.id AND p.event_type = 'acquisition'
          )
    """))

    # Step 4: Set NOT NULL defaults and add indexes
    with op.batch_alter_table('provenance_events') as batch_op:
        # Create indexes for common queries
        batch_op.create_index('ix_provenance_events_source_name', ['source_name'])
        batch_op.create_index('ix_provenance_events_source_origin', ['source_origin'])
        batch_op.create_index('ix_provenance_events_event_date', ['event_date'])
        batch_op.create_index('ix_provenance_events_sort_order', ['sort_order'])


def downgrade():
    """
    Rollback V3 changes.

    NOTE: This will NOT remove acquisition entries created from coin data.
    Those should be manually reviewed if rollback is needed.
    """

    with op.batch_alter_table('provenance_events') as batch_op:
        # Drop indexes
        batch_op.drop_index('ix_provenance_events_source_name')
        batch_op.drop_index('ix_provenance_events_source_origin')
        batch_op.drop_index('ix_provenance_events_event_date')
        batch_op.drop_index('ix_provenance_events_sort_order')

        # Drop new columns
        batch_op.drop_column('source_name')
        batch_op.drop_column('sale_name')
        batch_op.drop_column('source_origin')
        batch_op.drop_column('created_at')
        batch_op.drop_column('updated_at')
