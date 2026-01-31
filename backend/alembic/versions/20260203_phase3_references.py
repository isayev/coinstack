"""Phase 3: Reference System Enhancements

Flexible catalog reference system with concordance and external links:
- Extend reference_types with additional metadata
- reference_concordance: Cross-reference linking (RIC 207 = RSC 112 = BMC 298)
- external_catalog_links: Links to OCRE, Nomisma, CRRO, RPC Online
- Extend coin_references with confidence and disagreement tracking

Revision ID: 20260203_phase3
Revises: 20260202_phase2
Create Date: 2026-02-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260203_phase3'
down_revision: Union[str, Sequence[str], None] = '20260202_phase2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enhance reference system with concordance and external links."""

    # ==========================================================================
    # EXTEND REFERENCE_TYPES TABLE
    # ==========================================================================

    with op.batch_alter_table('reference_types', schema=None) as batch_op:
        # SNG volume support (e.g., "SNG Copenhagen" vs "SNG von Aulock")
        batch_op.add_column(sa.Column('sng_volume', sa.String(100), nullable=True))

        # Parsed numeric for range queries (RIC 42 -> 42)
        batch_op.add_column(sa.Column('number_numeric', sa.Integer(), nullable=True))

        # Publication year for citation
        batch_op.add_column(sa.Column('publication_year', sa.Integer(), nullable=True))

        # Rarity code from catalog (if provided)
        batch_op.add_column(sa.Column('rarity_code', sa.String(20), nullable=True))

        # Full bibliographic citation
        batch_op.add_column(sa.Column('full_citation', sa.Text(), nullable=True))

        # Plate number reference
        batch_op.add_column(sa.Column('plate_number', sa.String(50), nullable=True))

        # Index for numeric range queries
        batch_op.create_index('ix_reference_types_number_numeric', ['system', 'number_numeric'])

    # ==========================================================================
    # REFERENCE CONCORDANCE TABLE
    # ==========================================================================
    # Cross-reference linking: RIC 207 = RSC 112 = BMC 298 = Cohen 169

    op.create_table(
        'reference_concordance',
        sa.Column('id', sa.Integer(), primary_key=True),

        # UUID grouping equivalent references
        sa.Column('concordance_group_id', sa.String(36), nullable=False),
        # e.g., "550e8400-e29b-41d4-a716-446655440000" for all equivalents

        # Link to reference type
        sa.Column('reference_type_id', sa.Integer(), sa.ForeignKey('reference_types.id', ondelete='CASCADE'), nullable=False),

        # Confidence in equivalence
        sa.Column('confidence', sa.Numeric(3, 2), server_default='1.0', nullable=True),
        # 1.0 = exact match, 0.8 = high confidence, 0.5 = possible match

        # Source of concordance data
        sa.Column('source', sa.String(50), nullable=True),
        # source values: 'ocre', 'crro', 'user', 'literature', 'coinproject'

        # Notes on concordance
        sa.Column('notes', sa.Text(), nullable=True),
        # e.g., "Var. with different reverse legend"

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),

        # Unique constraint: each reference can only be in one concordance group
        sa.UniqueConstraint('concordance_group_id', 'reference_type_id', name='uq_concordance_group_ref'),
    )

    op.create_index('ix_concordance_group_id', 'reference_concordance', ['concordance_group_id'])
    op.create_index('ix_concordance_reference_type_id', 'reference_concordance', ['reference_type_id'])

    # ==========================================================================
    # EXTERNAL CATALOG LINKS TABLE
    # ==========================================================================
    # Links to online databases: OCRE, Nomisma, CRRO, RPC Online

    op.create_table(
        'external_catalog_links',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Link to reference type
        sa.Column('reference_type_id', sa.Integer(), sa.ForeignKey('reference_types.id', ondelete='CASCADE'), nullable=False),

        # External catalog source
        sa.Column('catalog_source', sa.String(30), nullable=False),
        # catalog_source values: 'ocre', 'nomisma', 'crro', 'rpc_online', 'acsearch', 'coinproject'

        # External identifier
        sa.Column('external_id', sa.String(100), nullable=False),
        # e.g., "ric.3.ant.42" for OCRE

        # Direct URL to external record
        sa.Column('external_url', sa.String(500), nullable=True),
        # e.g., "http://numismatics.org/ocre/id/ric.3.ant.42"

        # Cached external data (JSON)
        sa.Column('external_data', sa.Text(), nullable=True),
        # JSON with metadata from external source

        # Sync tracking
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('sync_status', sa.String(20), server_default='pending', nullable=True),
        # sync_status values: 'pending', 'synced', 'error', 'not_found'

        # Unique constraint: one link per source per reference
        sa.UniqueConstraint('reference_type_id', 'catalog_source', name='uq_external_link_source'),
    )

    op.create_index('ix_external_catalog_links_reference_type_id', 'external_catalog_links', ['reference_type_id'])
    op.create_index('ix_external_catalog_links_source', 'external_catalog_links', ['catalog_source', 'external_id'])

    # ==========================================================================
    # EXTEND COIN_REFERENCES TABLE
    # ==========================================================================

    with op.batch_alter_table('coin_references', schema=None) as batch_op:
        # Attribution confidence for uncertain attributions
        batch_op.add_column(sa.Column('attribution_confidence', sa.String(20), nullable=True))
        # attribution_confidence values: 'certain', 'probable', 'possible', 'tentative'

        # Rarity note specific to this coin from catalog
        batch_op.add_column(sa.Column('catalog_rarity_note', sa.String(100), nullable=True))
        # e.g., "R2" from RIC, "Very Rare" from BMC

        # Note when reference attribution is disputed
        batch_op.add_column(sa.Column('disagreement_note', sa.Text(), nullable=True))
        # e.g., "RIC attributes to Nero, but legend style suggests Vespasian"

        # Page/plate reference in catalog
        batch_op.add_column(sa.Column('page_reference', sa.String(50), nullable=True))
        # e.g., "p. 234, pl. XV.7"

        # Variant within type
        batch_op.add_column(sa.Column('variant_note', sa.String(100), nullable=True))
        # e.g., "var. b with AVGVSTI"


def downgrade() -> None:
    """Remove reference system enhancements."""

    # Drop coin_references extensions
    with op.batch_alter_table('coin_references', schema=None) as batch_op:
        batch_op.drop_column('variant_note')
        batch_op.drop_column('page_reference')
        batch_op.drop_column('disagreement_note')
        batch_op.drop_column('catalog_rarity_note')
        batch_op.drop_column('attribution_confidence')

    # Drop new tables
    op.drop_table('external_catalog_links')
    op.drop_table('reference_concordance')

    # Drop reference_types extensions
    with op.batch_alter_table('reference_types', schema=None) as batch_op:
        batch_op.drop_index('ix_reference_types_number_numeric')
        batch_op.drop_column('plate_number')
        batch_op.drop_column('full_citation')
        batch_op.drop_column('rarity_code')
        batch_op.drop_column('publication_year')
        batch_op.drop_column('number_numeric')
        batch_op.drop_column('sng_volume')
