"""Phase 4: LLM Architecture Refactor

Centralized LLM enrichments with versioning, review workflow, and quality tracking:
- llm_enrichments: Replaces 11 inline columns with structured, versioned storage
- llm_prompt_templates: Database-managed prompts for versioning and A/B testing
- llm_feedback: Quality feedback loop for continuous improvement
- llm_usage_daily: Aggregated analytics for cost and quality tracking

Revision ID: 20260204_phase4
Revises: 20260203_phase3
Create Date: 2026-02-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260204_phase4'
down_revision: Union[str, Sequence[str], None] = '20260203_phase3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create LLM architecture tables."""

    # ==========================================================================
    # LLM ENRICHMENTS TABLE
    # ==========================================================================
    # Replaces 11 inline columns with structured, versioned storage

    op.create_table(
        'llm_enrichments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins_v2.id', ondelete='CASCADE'), nullable=False),

        # Capability identification
        sa.Column('capability', sa.String(50), nullable=False),
        # capability values: 'context_generate', 'attribution_suggest', 'catalog_lookup',
        #                    'provenance_parse', 'design_describe', 'value_estimate',
        #                    'rarity_assess', 'condition_assess', 'iconography_identify'
        sa.Column('capability_version', sa.Integer(), nullable=False, server_default='1'),

        # Model provenance
        sa.Column('model_id', sa.String(50), nullable=False),
        # model_id values: 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'gpt-4o', etc.
        sa.Column('model_version', sa.String(50), nullable=True),
        # Specific model version for reproducibility

        # Input tracking (for cache invalidation)
        sa.Column('input_hash', sa.String(64), nullable=False),
        # SHA-256 of input content for deduplication
        sa.Column('input_snapshot', sa.Text(), nullable=True),
        # JSON snapshot of input data used for generation

        # Output content
        sa.Column('output_content', sa.Text(), nullable=False),
        # Main LLM output (may be JSON or text depending on capability)
        sa.Column('raw_response', sa.Text(), nullable=True),
        # Full API response for debugging

        # Quality metrics
        sa.Column('confidence', sa.Numeric(3, 2), nullable=False),
        # 0.00 to 1.00 confidence score
        sa.Column('needs_review', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('quality_flags', sa.Text(), nullable=True),
        # JSON array of quality flags: ["low_confidence", "needs_verification", "incomplete"]

        # Cost tracking
        sa.Column('cost_usd', sa.Numeric(8, 6), server_default='0', nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cached', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),

        # Review workflow
        sa.Column('review_status', sa.String(20), server_default='pending', nullable=True),
        # review_status values: 'pending', 'approved', 'rejected', 'revised'
        sa.Column('reviewed_by', sa.String(100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),

        # Lifecycle management
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        # Auto-expire old enrichments
        sa.Column('superseded_by', sa.Integer(), sa.ForeignKey('llm_enrichments.id'), nullable=True),
        # Points to newer version if this was regenerated

        # Request tracking
        sa.Column('request_id', sa.String(100), nullable=True),
        # API request ID for debugging
        sa.Column('batch_job_id', sa.String(100), nullable=True),
        # For batch processing jobs

        # Unique constraint: one active enrichment per coin+capability+input
        sa.UniqueConstraint('coin_id', 'capability', 'input_hash', 'review_status', name='uq_enrichment_active'),
    )

    op.create_index('ix_llm_enrichments_coin_id', 'llm_enrichments', ['coin_id'])
    op.create_index('ix_llm_enrichments_capability', 'llm_enrichments', ['capability'])
    op.create_index('ix_llm_enrichments_review_status', 'llm_enrichments', ['review_status'])
    op.create_index('ix_llm_enrichments_needs_review', 'llm_enrichments', ['needs_review'])
    op.create_index('ix_llm_enrichments_created_at', 'llm_enrichments', ['created_at'])

    # ==========================================================================
    # LLM PROMPT TEMPLATES TABLE
    # ==========================================================================
    # Database-managed prompts for versioning and A/B testing

    op.create_table(
        'llm_prompt_templates',
        sa.Column('id', sa.Integer(), primary_key=True),

        # Template identification
        sa.Column('capability', sa.String(50), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),

        # Prompt content
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('user_template', sa.Text(), nullable=False),
        # Template with placeholders: "Analyze this {coin_type} from {mint}..."
        sa.Column('parameters', sa.Text(), nullable=True),
        # JSON schema for template parameters

        # Model requirements
        sa.Column('requires_vision', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('preferred_model', sa.String(50), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Numeric(3, 2), nullable=True),

        # Output specification
        sa.Column('output_schema', sa.Text(), nullable=True),
        # JSON schema for expected output structure

        # A/B testing support
        sa.Column('variant_name', sa.String(50), server_default='default', nullable=True),
        sa.Column('traffic_weight', sa.Numeric(3, 2), server_default='1.0', nullable=True),
        # 0.0 to 1.0 weight for traffic allocation

        # Lifecycle
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column('deprecated_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Unique constraint: one version per capability per variant
        sa.UniqueConstraint('capability', 'version', 'variant_name', name='uq_prompt_version'),
    )

    op.create_index('ix_llm_prompt_templates_capability', 'llm_prompt_templates', ['capability'])
    op.create_index('ix_llm_prompt_templates_is_active', 'llm_prompt_templates', ['is_active'])

    # ==========================================================================
    # LLM FEEDBACK TABLE
    # ==========================================================================
    # Quality feedback loop for continuous improvement

    op.create_table(
        'llm_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('enrichment_id', sa.Integer(), sa.ForeignKey('llm_enrichments.id', ondelete='CASCADE'), nullable=False),

        # Feedback type
        sa.Column('feedback_type', sa.String(30), nullable=False),
        # feedback_type values: 'correction', 'rating', 'flag', 'approval', 'rejection'

        # Field-level feedback
        sa.Column('field_path', sa.String(100), nullable=True),
        # JSON path to field: "attribution.issuer" or "provenance[0].date"
        sa.Column('original_value', sa.Text(), nullable=True),
        sa.Column('corrected_value', sa.Text(), nullable=True),

        # Rating feedback
        sa.Column('rating', sa.Integer(), nullable=True),
        # 1-5 star rating
        sa.Column('helpful', sa.Boolean(), nullable=True),
        # Was this output helpful?

        # User info
        sa.Column('user_id', sa.String(100), nullable=True),
        sa.Column('feedback_notes', sa.Text(), nullable=True),

        sa.Column('created_at', sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
    )

    op.create_index('ix_llm_feedback_enrichment_id', 'llm_feedback', ['enrichment_id'])
    op.create_index('ix_llm_feedback_type', 'llm_feedback', ['feedback_type'])

    # ==========================================================================
    # LLM USAGE DAILY TABLE
    # ==========================================================================
    # Aggregated analytics for cost and quality tracking

    op.create_table(
        'llm_usage_daily',
        sa.Column('date', sa.String(10), nullable=False),
        # Format: YYYY-MM-DD
        sa.Column('capability', sa.String(50), nullable=False),
        sa.Column('model_id', sa.String(50), nullable=False),

        # Volume metrics
        sa.Column('request_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('cache_hits', sa.Integer(), server_default='0', nullable=True),
        sa.Column('error_count', sa.Integer(), server_default='0', nullable=True),

        # Cost metrics
        sa.Column('total_cost_usd', sa.Numeric(10, 4), server_default='0', nullable=True),
        sa.Column('total_input_tokens', sa.Integer(), server_default='0', nullable=True),
        sa.Column('total_output_tokens', sa.Integer(), server_default='0', nullable=True),

        # Quality metrics
        sa.Column('avg_confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('review_approved', sa.Integer(), server_default='0', nullable=True),
        sa.Column('review_rejected', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_rating', sa.Numeric(2, 1), nullable=True),

        # Performance metrics
        sa.Column('avg_latency_ms', sa.Numeric(8, 2), nullable=True),
        sa.Column('p95_latency_ms', sa.Numeric(8, 2), nullable=True),

        sa.PrimaryKeyConstraint('date', 'capability', 'model_id'),
    )

    op.create_index('ix_llm_usage_daily_date', 'llm_usage_daily', ['date'])
    op.create_index('ix_llm_usage_daily_capability', 'llm_usage_daily', ['capability'])

    # ==========================================================================
    # DATA MIGRATION: Populate llm_enrichments from existing coin columns
    # ==========================================================================
    # Note: This migrates existing LLM data to the new table structure.
    # The old columns can be deprecated after dual-write period.
    #
    # Actual LLM columns in coins_v2:
    # - llm_enriched_at (timestamp)
    # - llm_analysis_sections (main content)
    # - llm_suggested_references
    # - llm_suggested_rarity
    # - llm_suggested_design
    # - llm_suggested_attribution

    # Migrate llm_analysis_sections (main context generation)
    op.execute("""
        INSERT INTO llm_enrichments (
            coin_id, capability, capability_version, model_id,
            input_hash, output_content, confidence, review_status, created_at
        )
        SELECT
            id,
            'context_generate',
            1,
            'unknown',
            'legacy_' || id,
            llm_analysis_sections,
            0.7,
            'approved',
            COALESCE(llm_enriched_at, CURRENT_TIMESTAMP)
        FROM coins_v2
        WHERE llm_analysis_sections IS NOT NULL AND llm_analysis_sections != ''
    """)

    # Migrate llm_suggested_attribution
    op.execute("""
        INSERT INTO llm_enrichments (
            coin_id, capability, capability_version, model_id,
            input_hash, output_content, confidence, review_status, created_at
        )
        SELECT
            id,
            'attribution_suggest',
            1,
            'unknown',
            'legacy_attr_' || id,
            llm_suggested_attribution,
            0.6,
            'pending',
            COALESCE(llm_enriched_at, CURRENT_TIMESTAMP)
        FROM coins_v2
        WHERE llm_suggested_attribution IS NOT NULL AND llm_suggested_attribution != ''
    """)

    # Migrate llm_suggested_design
    op.execute("""
        INSERT INTO llm_enrichments (
            coin_id, capability, capability_version, model_id,
            input_hash, output_content, confidence, review_status, created_at
        )
        SELECT
            id,
            'design_describe',
            1,
            'unknown',
            'legacy_design_' || id,
            llm_suggested_design,
            0.6,
            'pending',
            COALESCE(llm_enriched_at, CURRENT_TIMESTAMP)
        FROM coins_v2
        WHERE llm_suggested_design IS NOT NULL AND llm_suggested_design != ''
    """)

    # Migrate llm_suggested_rarity
    op.execute("""
        INSERT INTO llm_enrichments (
            coin_id, capability, capability_version, model_id,
            input_hash, output_content, confidence, review_status, created_at
        )
        SELECT
            id,
            'rarity_assess',
            1,
            'unknown',
            'legacy_rarity_' || id,
            llm_suggested_rarity,
            0.5,
            'pending',
            COALESCE(llm_enriched_at, CURRENT_TIMESTAMP)
        FROM coins_v2
        WHERE llm_suggested_rarity IS NOT NULL AND llm_suggested_rarity != ''
    """)

    # Migrate llm_suggested_references
    op.execute("""
        INSERT INTO llm_enrichments (
            coin_id, capability, capability_version, model_id,
            input_hash, output_content, confidence, review_status, created_at
        )
        SELECT
            id,
            'catalog_lookup',
            1,
            'unknown',
            'legacy_refs_' || id,
            llm_suggested_references,
            0.5,
            'pending',
            COALESCE(llm_enriched_at, CURRENT_TIMESTAMP)
        FROM coins_v2
        WHERE llm_suggested_references IS NOT NULL AND llm_suggested_references != ''
    """)


def downgrade() -> None:
    """Remove LLM architecture tables."""

    # Note: Data migration back to coins_v2 columns would need to be done manually
    # if old columns still exist. This just removes the new tables.

    op.drop_table('llm_usage_daily')
    op.drop_table('llm_feedback')
    op.drop_table('llm_prompt_templates')
    op.drop_table('llm_enrichments')
