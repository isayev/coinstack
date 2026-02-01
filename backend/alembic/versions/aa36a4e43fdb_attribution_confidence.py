"""attribution_confidence

Add attribution confidence tracking with field-level confidence:
- Modify coins_v2: Add attribution_certainty column
- Create attribution_hypotheses table: Multi-hypothesis attributions with field-level confidence

Revision ID: aa36a4e43fdb
Revises: 5620e2f02d8d
Create Date: 2026-02-01 01:16:56.364892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'aa36a4e43fdb'
down_revision: Union[str, Sequence[str], None] = '5620e2f02d8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        f"SELECT COUNT(*) FROM pragma_table_info('{table_name}') WHERE name='{column_name}'"
    ))
    return result.scalar() > 0


def table_exists(table_name: str) -> bool:
    """Check if table exists."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    ))
    return result.scalar() > 0


def upgrade() -> None:
    """Add attribution confidence tracking."""

    # 1. Add attribution_certainty column to coins_v2 (if not exists)
    if not column_exists('coins_v2', 'attribution_certainty'):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            batch_op.add_column(
                sa.Column('attribution_certainty', sa.String(20), nullable=True)
            )

    # 2. Create attribution_hypotheses table (if not exists)
    if not table_exists('attribution_hypotheses'):
        op.create_table(
            'attribution_hypotheses',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),
            sa.Column('hypothesis_rank', sa.Integer(), nullable=False),

            # Field-level attribution with confidence
            sa.Column('issuer', sa.String(200), nullable=True),
            sa.Column('issuer_confidence', sa.String(20), nullable=True),

            sa.Column('mint', sa.String(200), nullable=True),
            sa.Column('mint_confidence', sa.String(20), nullable=True),

            sa.Column('year_start', sa.Integer(), nullable=True),
            sa.Column('year_end', sa.Integer(), nullable=True),
            sa.Column('date_confidence', sa.String(20), nullable=True),

            sa.Column('denomination', sa.String(100), nullable=True),
            sa.Column('denomination_confidence', sa.String(20), nullable=True),

            # Overall confidence
            sa.Column('overall_certainty', sa.String(20), nullable=True),
            sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),  # 0.00-1.00

            # Evidence
            sa.Column('attribution_notes', sa.Text(), nullable=True),
            sa.Column('reference_support', sa.String(500), nullable=True),
            sa.Column('source', sa.String(50), nullable=True),  # 'llm' | 'expert' | 'user' | 'catalog'

            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow),

            # CRITICAL: Unique constraint to prevent duplicate ranks
            sa.UniqueConstraint('coin_id', 'hypothesis_rank', name='uq_attribution_hypothesis_rank'),
        )

        # Create indexes for common queries
        op.create_index('ix_attribution_hypotheses_coin_id', 'attribution_hypotheses', ['coin_id'])
        op.create_index('ix_attribution_hypotheses_coin_rank', 'attribution_hypotheses', ['coin_id', 'hypothesis_rank'])


def downgrade() -> None:
    """Remove attribution confidence tracking."""
    # Drop attribution_hypotheses table
    if table_exists('attribution_hypotheses'):
        op.drop_table('attribution_hypotheses')

    # Remove attribution_certainty column from coins_v2
    if column_exists('coins_v2', 'attribution_certainty'):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            batch_op.drop_column('attribution_certainty')
