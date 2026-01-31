"""Phase 1.5c: Numismatic Expert Recommendations

Add fields from numismatic domain expert review:
- punch_shape for countermarks (rectangular, circular, etc.)
- off_center_pct for coins_v2 (percentage off-center strike)

Revision ID: 20260210_phase1_5c_numismatic
Revises: 20260209_phase1_5b_countermark
Create Date: 2026-02-10
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260210_phase1_5c_numismatic'
down_revision = '20260209_phase1_5b_countermark'
branch_labels = None
depends_on = None


def column_exists(table_name: str, column_name: str) -> bool:
    """Check if column exists (idempotent migration)."""
    conn = op.get_bind()
    result = conn.execute(sa.text(
        f"SELECT COUNT(*) FROM pragma_table_info('{table_name}') WHERE name='{column_name}'"
    ))
    return result.scalar() > 0


def upgrade() -> None:
    # 1. Add punch_shape to countermarks table
    if not column_exists('countermarks', 'punch_shape'):
        with op.batch_alter_table('countermarks', schema=None) as batch_op:
            batch_op.add_column(sa.Column('punch_shape', sa.String(20), nullable=True))

    # 2. Add off_center_pct to coins_v2 table
    if not column_exists('coins_v2', 'off_center_pct'):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            batch_op.add_column(sa.Column('off_center_pct', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Drop off_center_pct from coins_v2
    if column_exists('coins_v2', 'off_center_pct'):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            batch_op.drop_column('off_center_pct')

    # Drop punch_shape from countermarks
    if column_exists('countermarks', 'punch_shape'):
        with op.batch_alter_table('countermarks', schema=None) as batch_op:
            batch_op.drop_column('punch_shape')
