"""Phase 1: Core Numismatic Enhancements

Add fields for world-class ancient coin cataloging:
- Secondary authority (Greek magistrates, provincial governors)
- Co-rulers (Byzantine, Imperial)
- Physical enhancements (weight standards, flan characteristics)
- Secondary treatments (overstrikes, test cuts, banker's marks)
- Grading TPG enhancements (star grades, photo certificates)
- Die study enhancements (separate die states per side)

Revision ID: 20260201_phase1
Revises: 20260131_provenance_v3_unified
Create Date: 2026-02-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260201_phase1'
down_revision: Union[str, Sequence[str], None] = '20260131_prov_v3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add numismatic enhancement columns to coins_v2."""

    with op.batch_alter_table('coins_v2', schema=None) as batch_op:
        # =======================================================================
        # ATTRIBUTION ENHANCEMENTS
        # =======================================================================

        # Secondary authority (Greek magistrates, provincial governors)
        batch_op.add_column(sa.Column('secondary_authority', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('secondary_authority_term_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('authority_type', sa.String(30), nullable=True))
        # authority_type values: 'magistrate', 'satrap', 'dynast', 'strategos', 'archon', 'epistates'

        # Co-rulers (Byzantine, Imperial joint reigns)
        batch_op.add_column(sa.Column('co_ruler', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('co_ruler_term_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('portrait_relationship', sa.String(30), nullable=True))
        # portrait_relationship values: 'self', 'consort', 'heir', 'parent', 'predecessor', 'commemorative', 'divus', 'diva'

        # Republican moneyer family
        batch_op.add_column(sa.Column('moneyer_gens', sa.String(50), nullable=True))

        # =======================================================================
        # PHYSICAL ENHANCEMENTS
        # =======================================================================

        # Weight standards
        batch_op.add_column(sa.Column('weight_standard', sa.String(50), nullable=True))
        # weight_standard values: 'attic', 'aeginetan', 'corinthian', 'phoenician', 'denarius_early', 'denarius_reformed', 'antoninianus'
        batch_op.add_column(sa.Column('expected_weight_g', sa.Numeric(10, 3), nullable=True))

        # Flan characteristics
        batch_op.add_column(sa.Column('flan_shape', sa.String(30), nullable=True))
        # flan_shape values: 'round', 'irregular', 'oval', 'square', 'scyphate'
        batch_op.add_column(sa.Column('flan_type', sa.String(30), nullable=True))
        # flan_type values: 'cast', 'struck', 'cut_from_bar', 'hammered'
        batch_op.add_column(sa.Column('flan_notes', sa.Text(), nullable=True))

        # =======================================================================
        # SECONDARY TREATMENTS (Structured)
        # =======================================================================

        # Overstrikes
        batch_op.add_column(sa.Column('is_overstrike', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('undertype_visible', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('undertype_attribution', sa.String(200), nullable=True))

        # Test cuts (Prüfhieb)
        batch_op.add_column(sa.Column('has_test_cut', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('test_cut_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('test_cut_positions', sa.Text(), nullable=True))

        # Banker's marks
        batch_op.add_column(sa.Column('has_bankers_marks', sa.Boolean(), server_default='0', nullable=True))

        # Graffiti
        batch_op.add_column(sa.Column('has_graffiti', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('graffiti_description', sa.Text(), nullable=True))

        # Jewelry mounting
        batch_op.add_column(sa.Column('was_mounted', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('mount_evidence', sa.Text(), nullable=True))

        # =======================================================================
        # TOOLING / REPAIRS
        # =======================================================================

        batch_op.add_column(sa.Column('tooling_extent', sa.String(30), nullable=True))
        # tooling_extent values: 'none', 'minor', 'moderate', 'significant', 'extensive'
        batch_op.add_column(sa.Column('tooling_details', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('has_ancient_repair', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('ancient_repairs', sa.Text(), nullable=True))

        # =======================================================================
        # CENTERING
        # =======================================================================

        batch_op.add_column(sa.Column('centering', sa.String(20), nullable=True))
        # centering values: 'well-centered', 'slightly_off', 'off_center', 'significantly_off'
        batch_op.add_column(sa.Column('centering_notes', sa.Text(), nullable=True))

        # =======================================================================
        # DIE STUDY ENHANCEMENTS
        # =======================================================================

        # Separate die states per side
        batch_op.add_column(sa.Column('obverse_die_state', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('reverse_die_state', sa.String(20), nullable=True))
        # die state values: 'fresh', 'early', 'middle', 'late', 'worn', 'broken', 'repaired'
        batch_op.add_column(sa.Column('die_break_description', sa.Text(), nullable=True))

        # =======================================================================
        # GRADING TPG ENHANCEMENTS
        # =======================================================================

        batch_op.add_column(sa.Column('grade_numeric', sa.Integer(), nullable=True))
        # NGC/PCGS numeric grades: 50, 53, 55, 58, 60, 62, 63, 64, 65, 66, 67, 68, 69, 70
        batch_op.add_column(sa.Column('grade_designation', sa.String(50), nullable=True))
        # grade_designation values: 'Fine Style', 'Choice', 'Gem', 'Superb Gem'
        batch_op.add_column(sa.Column('has_star_designation', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('photo_certificate', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('verification_url', sa.String(500), nullable=True))

        # =======================================================================
        # CHRONOLOGY ENHANCEMENTS
        # =======================================================================

        batch_op.add_column(sa.Column('date_period_notation', sa.String(100), nullable=True))
        # Human-readable: "c. 150-100 BC", "late 3rd century AD"
        batch_op.add_column(sa.Column('emission_phase', sa.String(50), nullable=True))
        # emission_phase values: 'First Issue', 'Second Issue', 'Reform Coinage', 'Heavy Series', 'Light Series'

        # =======================================================================
        # FOREIGN KEY CONSTRAINTS (for vocab term IDs)
        # =======================================================================

        batch_op.create_foreign_key(
            'fk_coins_secondary_authority_term',
            'vocab_terms',
            ['secondary_authority_term_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_coins_co_ruler_term',
            'vocab_terms',
            ['co_ruler_term_id'],
            ['id']
        )

        # =======================================================================
        # INDEXES
        # =======================================================================

        batch_op.create_index('ix_coins_v2_secondary_authority', ['secondary_authority'])
        batch_op.create_index('ix_coins_v2_co_ruler', ['co_ruler'])
        batch_op.create_index('ix_coins_v2_is_overstrike', ['is_overstrike'])
        batch_op.create_index('ix_coins_v2_has_star_designation', ['has_star_designation'])


def downgrade() -> None:
    """Remove numismatic enhancement columns from coins_v2."""

    with op.batch_alter_table('coins_v2', schema=None) as batch_op:
        # Drop indexes
        batch_op.drop_index('ix_coins_v2_has_star_designation')
        batch_op.drop_index('ix_coins_v2_is_overstrike')
        batch_op.drop_index('ix_coins_v2_co_ruler')
        batch_op.drop_index('ix_coins_v2_secondary_authority')

        # Drop foreign keys
        batch_op.drop_constraint('fk_coins_co_ruler_term', type_='foreignkey')
        batch_op.drop_constraint('fk_coins_secondary_authority_term', type_='foreignkey')

        # Drop columns (reverse order of creation)
        batch_op.drop_column('emission_phase')
        batch_op.drop_column('date_period_notation')
        batch_op.drop_column('verification_url')
        batch_op.drop_column('photo_certificate')
        batch_op.drop_column('has_star_designation')
        batch_op.drop_column('grade_designation')
        batch_op.drop_column('grade_numeric')
        batch_op.drop_column('die_break_description')
        batch_op.drop_column('reverse_die_state')
        batch_op.drop_column('obverse_die_state')
        batch_op.drop_column('centering_notes')
        batch_op.drop_column('centering')
        batch_op.drop_column('ancient_repairs')
        batch_op.drop_column('has_ancient_repair')
        batch_op.drop_column('tooling_details')
        batch_op.drop_column('tooling_extent')
        batch_op.drop_column('mount_evidence')
        batch_op.drop_column('was_mounted')
        batch_op.drop_column('graffiti_description')
        batch_op.drop_column('has_graffiti')
        batch_op.drop_column('has_bankers_marks')
        batch_op.drop_column('test_cut_positions')
        batch_op.drop_column('test_cut_count')
        batch_op.drop_column('has_test_cut')
        batch_op.drop_column('undertype_attribution')
        batch_op.drop_column('undertype_visible')
        batch_op.drop_column('is_overstrike')
        batch_op.drop_column('flan_notes')
        batch_op.drop_column('flan_type')
        batch_op.drop_column('flan_shape')
        batch_op.drop_column('expected_weight_g')
        batch_op.drop_column('weight_standard')
        batch_op.drop_column('moneyer_gens')
        batch_op.drop_column('portrait_relationship')
        batch_op.drop_column('co_ruler_term_id')
        batch_op.drop_column('co_ruler')
        batch_op.drop_column('authority_type')
        batch_op.drop_column('secondary_authority_term_id')
        batch_op.drop_column('secondary_authority')
