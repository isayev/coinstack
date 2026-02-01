"""variety_rarity_tracking

Revision ID: df5adc3d9e33
Revises: aa36a4e43fdb
Create Date: 2026-02-01 01:33:35.689574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df5adc3d9e33'
down_revision: Union[str, Sequence[str], None] = 'aa36a4e43fdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add variety rarity tracking columns to rarity_assessments table.

    Adds:
    - variety_code: Link to die variety classification
    - die_id: FK to dies catalog (enables die-level rarity assessment)
    - die_rarity_notes: Die-specific rarity observations
    - condition_rarity_threshold: Grade level where coin becomes rare
    - rarity_context: Clarifies if rarity is type-level, variety-level, or standalone
    """
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('rarity_assessments', schema=None) as batch_op:
        # Add variety_code column
        batch_op.add_column(sa.Column('variety_code', sa.String(50), nullable=True))

        # Add die_id foreign key (SET NULL on delete - die catalog is optional)
        batch_op.add_column(sa.Column('die_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_rarity_assessments_die_id',
            'dies',
            ['die_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add die rarity notes
        batch_op.add_column(sa.Column('die_rarity_notes', sa.Text(), nullable=True))

        # Add condition rarity threshold (e.g., "VF", "EF", "AU")
        batch_op.add_column(sa.Column('condition_rarity_threshold', sa.String(20), nullable=True))

        # Add rarity context enum
        batch_op.add_column(sa.Column('rarity_context', sa.String(30), nullable=True))

        # Create indexes for common queries
        batch_op.create_index('ix_rarity_assessments_variety_code', ['variety_code'])
        batch_op.create_index('ix_rarity_assessments_die_id', ['die_id'])


def downgrade() -> None:
    """Remove variety rarity tracking columns from rarity_assessments table."""
    with op.batch_alter_table('rarity_assessments', schema=None) as batch_op:
        # Drop indexes first
        batch_op.drop_index('ix_rarity_assessments_die_id')
        batch_op.drop_index('ix_rarity_assessments_variety_code')

        # Drop foreign key
        batch_op.drop_constraint('fk_rarity_assessments_die_id', type_='foreignkey')

        # Drop columns
        batch_op.drop_column('rarity_context')
        batch_op.drop_column('condition_rarity_threshold')
        batch_op.drop_column('die_rarity_notes')
        batch_op.drop_column('die_id')
        batch_op.drop_column('variety_code')
