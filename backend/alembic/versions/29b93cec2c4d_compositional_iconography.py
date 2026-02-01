"""compositional_iconography

Revision ID: 29b93cec2c4d
Revises: df5adc3d9e33
Create Date: 2026-02-01 01:49:51.667304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29b93cec2c4d'
down_revision: Union[str, Sequence[str], None] = 'df5adc3d9e33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create compositional iconography schema (6 tables).

    Enables scholarly iconographic research with compositional model:
    - Elements: Catalog of iconographic elements (Victory, Mars, Eagle, etc.)
    - Attributes: Vocabulary for describing elements (pose, direction, clothing)
    - Compositions: Full scene descriptions with structured JSON
    - Coin Iconography: Links coins to compositions
    - Composition Elements: Many-to-many between compositions and elements
    - Element Attributes: Attributes applied to elements in specific compositions

    This replaces simple tagging with compositional descriptions like:
    "Victory standing left, holding wreath and palm, draped"
    """

    # Table 1: iconography_elements - Element catalog
    op.create_table(
        'iconography_elements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('canonical_name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('category', sa.String(30), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('aliases', sa.Text(), nullable=True),  # JSON array
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_name', name='uq_iconography_element_name')
    )
    op.create_index('ix_iconography_elements_canonical_name', 'iconography_elements', ['canonical_name'])
    op.create_index('ix_iconography_elements_category', 'iconography_elements', ['category'])

    # Table 2: iconography_attributes - Attribute vocabulary
    op.create_table(
        'iconography_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('attribute_type', sa.String(50), nullable=False),
        sa.Column('attribute_value', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('attribute_type', 'attribute_value', name='uq_iconography_attribute')
    )
    op.create_index('ix_iconography_attributes_type', 'iconography_attributes', ['attribute_type'])

    # Table 3: iconography_compositions - Full scene descriptions
    op.create_table(
        'iconography_compositions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composition_name', sa.String(200), nullable=False),
        sa.Column('canonical_description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('composition_json', sa.Text(), nullable=True),  # Structured JSON
        sa.Column('reference_system', sa.String(50), nullable=True),
        sa.Column('reference_numbers', sa.Text(), nullable=True),  # JSON array
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_iconography_compositions_name', 'iconography_compositions', ['composition_name'])
    op.create_index('ix_iconography_compositions_category', 'iconography_compositions', ['category'])

    # Table 4: coin_iconography - Link coins to compositions
    op.create_table(
        'coin_iconography',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('coin_id', sa.Integer(), nullable=False),
        sa.Column('composition_id', sa.Integer(), nullable=False),
        sa.Column('coin_side', sa.String(10), nullable=True),
        sa.Column('position', sa.String(50), nullable=True),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['coin_id'], ['coins_v2.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['composition_id'], ['iconography_compositions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('coin_id', 'composition_id', 'coin_side', name='uq_coin_iconography')
    )
    op.create_index('ix_coin_iconography_coin_id', 'coin_iconography', ['coin_id'])
    op.create_index('ix_coin_iconography_composition_id', 'coin_iconography', ['composition_id'])
    op.create_index('ix_coin_iconography_coin_side', 'coin_iconography', ['coin_side'])
    # Composite index for common query pattern (Architecture review fix from plan)
    op.create_index('ix_coin_iconography_side_composition', 'coin_iconography', ['coin_side', 'composition_id'])

    # Table 5: composition_elements - Elements in compositions (many-to-many)
    op.create_table(
        'composition_elements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composition_id', sa.Integer(), nullable=False),
        sa.Column('element_id', sa.Integer(), nullable=False),
        sa.Column('element_position', sa.Integer(), nullable=True),
        sa.Column('prominence', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['composition_id'], ['iconography_compositions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['element_id'], ['iconography_elements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('composition_id', 'element_id', name='uq_composition_element')
    )
    op.create_index('ix_composition_elements_composition_id', 'composition_elements', ['composition_id'])
    op.create_index('ix_composition_elements_element_id', 'composition_elements', ['element_id'])

    # Table 6: element_attributes - Attributes for elements in compositions
    op.create_table(
        'element_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('composition_element_id', sa.Integer(), nullable=False),
        sa.Column('attribute_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['composition_element_id'], ['composition_elements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['iconography_attributes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_element_attributes_composition_element_id', 'element_attributes', ['composition_element_id'])
    op.create_index('ix_element_attributes_attribute_id', 'element_attributes', ['attribute_id'])


def downgrade() -> None:
    """Drop compositional iconography schema (6 tables in reverse order)."""
    # Drop in reverse order of creation (dependencies first)
    op.drop_table('element_attributes')
    op.drop_table('composition_elements')
    op.drop_table('coin_iconography')
    op.drop_table('iconography_compositions')
    op.drop_table('iconography_attributes')
    op.drop_table('iconography_elements')
