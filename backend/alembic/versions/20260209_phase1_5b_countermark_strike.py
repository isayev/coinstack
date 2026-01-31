"""Phase 1.5b: Countermarks table, Strike Quality, NGC Grade Components

Add comprehensive numismatic support:
- Countermark System (separate table): Full multi-countermark support with placement tracking
- Strike Quality Detail (4 columns): Manufacturing characteristics and die errors
- NGC Grade Components (3 columns): NGC-specific detailed grading

Revision ID: 20260209_phase1_5b_countermark
Revises: 20260208_phase6_enhancements
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '20260209_phase1_5b_countermark'
down_revision = '20260208_phase6_enhancements'
branch_labels = None
depends_on = None


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
    # 1. Create countermarks table (if not exists), or add missing columns
    if not table_exists('countermarks'):
        op.create_table(
            'countermarks',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),
            sa.Column('countermark_type', sa.String(50), nullable=True),
            sa.Column('position', sa.String(20), nullable=True),
            sa.Column('condition', sa.String(20), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('authority', sa.String(), nullable=True),
            sa.Column('reference', sa.String(100), nullable=True),
            sa.Column('date_applied', sa.String(50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        )
        op.create_index('ix_countermarks_coin_id', 'countermarks', ['coin_id'])
        op.create_index('ix_countermarks_coin_type', 'countermarks', ['coin_id', 'countermark_type'])
    else:
        # Table exists - add missing columns from Phase 1.5b
        add_reference = not column_exists('countermarks', 'reference')
        add_created_at = not column_exists('countermarks', 'created_at')

        if add_reference or add_created_at:
            with op.batch_alter_table('countermarks', schema=None) as batch_op:
                if add_reference:
                    batch_op.add_column(sa.Column('reference', sa.String(100), nullable=True))
                if add_created_at:
                    batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # 2. Add columns to coins_v2 - check OUTSIDE batch context
    add_strike_detail = not column_exists('coins_v2', 'strike_quality_detail')
    add_double_struck = not column_exists('coins_v2', 'is_double_struck')
    add_brockage = not column_exists('coins_v2', 'is_brockage')
    add_off_center = not column_exists('coins_v2', 'is_off_center')
    add_ngc_strike = not column_exists('coins_v2', 'ngc_strike_grade')
    add_ngc_surface = not column_exists('coins_v2', 'ngc_surface_grade')
    add_fine_style = not column_exists('coins_v2', 'is_fine_style')

    # Only open batch context if we have columns to add
    if any([add_strike_detail, add_double_struck, add_brockage, add_off_center,
            add_ngc_strike, add_ngc_surface, add_fine_style]):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            # Strike quality detail (4 columns)
            if add_strike_detail:
                batch_op.add_column(sa.Column('strike_quality_detail', sa.String(), nullable=True))
            if add_double_struck:
                batch_op.add_column(sa.Column('is_double_struck', sa.Boolean(), server_default='0'))
            if add_brockage:
                batch_op.add_column(sa.Column('is_brockage', sa.Boolean(), server_default='0'))
            if add_off_center:
                batch_op.add_column(sa.Column('is_off_center', sa.Boolean(), server_default='0'))

            # NGC-specific grades (3 columns)
            if add_ngc_strike:
                batch_op.add_column(sa.Column('ngc_strike_grade', sa.Integer(), nullable=True))
            if add_ngc_surface:
                batch_op.add_column(sa.Column('ngc_surface_grade', sa.Integer(), nullable=True))
            if add_fine_style:
                batch_op.add_column(sa.Column('is_fine_style', sa.Boolean(), server_default='0'))


def downgrade() -> None:
    # Check existence before dropping (idempotent)
    drop_strike_detail = column_exists('coins_v2', 'strike_quality_detail')
    drop_double_struck = column_exists('coins_v2', 'is_double_struck')
    drop_brockage = column_exists('coins_v2', 'is_brockage')
    drop_off_center = column_exists('coins_v2', 'is_off_center')
    drop_ngc_strike = column_exists('coins_v2', 'ngc_strike_grade')
    drop_ngc_surface = column_exists('coins_v2', 'ngc_surface_grade')
    drop_fine_style = column_exists('coins_v2', 'is_fine_style')

    if any([drop_strike_detail, drop_double_struck, drop_brockage, drop_off_center,
            drop_ngc_strike, drop_ngc_surface, drop_fine_style]):
        with op.batch_alter_table('coins_v2', schema=None) as batch_op:
            if drop_fine_style:
                batch_op.drop_column('is_fine_style')
            if drop_ngc_surface:
                batch_op.drop_column('ngc_surface_grade')
            if drop_ngc_strike:
                batch_op.drop_column('ngc_strike_grade')
            if drop_off_center:
                batch_op.drop_column('is_off_center')
            if drop_brockage:
                batch_op.drop_column('is_brockage')
            if drop_double_struck:
                batch_op.drop_column('is_double_struck')
            if drop_strike_detail:
                batch_op.drop_column('strike_quality_detail')

    # Drop countermarks table
    if table_exists('countermarks'):
        op.drop_index('ix_countermarks_coin_type', 'countermarks')
        op.drop_index('ix_countermarks_coin_id', 'countermarks')
        op.drop_table('countermarks')
