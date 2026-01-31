"""
LLM Enrichment Repository Implementation.

Handles persistence of LLM enrichments with versioning, review workflow,
and cost tracking. Implements ILLMEnrichmentRepository protocol.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import LLMEnrichment
from src.domain.repositories import ILLMEnrichmentRepository
from src.infrastructure.persistence.orm import LLMEnrichmentModel


class SqlAlchemyLLMEnrichmentRepository(ILLMEnrichmentRepository):
    """
    Repository for managing LLM enrichments.

    Provides centralized storage for all LLM-generated content with
    versioning, review workflow, and cost tracking capabilities.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, enrichment_id: int) -> Optional[LLMEnrichment]:
        """Get a specific enrichment by ID."""
        model = self.session.get(LLMEnrichmentModel, enrichment_id)
        return self._to_domain(model) if model else None

    def get_by_coin_id(
        self,
        coin_id: int,
        capability: Optional[str] = None,
        review_status: Optional[str] = None
    ) -> List[LLMEnrichment]:
        """
        Get enrichments for a coin, optionally filtered by capability and status.

        Returns enrichments ordered by created_at desc.
        """
        query = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.coin_id == coin_id
        )

        if capability:
            query = query.filter(LLMEnrichmentModel.capability == capability)

        if review_status:
            query = query.filter(LLMEnrichmentModel.review_status == review_status)

        query = query.order_by(desc(LLMEnrichmentModel.created_at))
        models = query.all()

        return [self._to_domain(m) for m in models]

    def get_current(self, coin_id: int, capability: str) -> Optional[LLMEnrichment]:
        """
        Get the current (active) enrichment for a coin/capability.

        Returns the most recent approved enrichment, or pending if none approved.
        """
        # First try approved
        model = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.coin_id == coin_id,
            LLMEnrichmentModel.capability == capability,
            LLMEnrichmentModel.review_status == "approved",
            LLMEnrichmentModel.superseded_by.is_(None)
        ).order_by(desc(LLMEnrichmentModel.created_at)).first()

        if model:
            return self._to_domain(model)

        # Fallback to most recent pending
        model = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.coin_id == coin_id,
            LLMEnrichmentModel.capability == capability,
            LLMEnrichmentModel.review_status == "pending",
            LLMEnrichmentModel.superseded_by.is_(None)
        ).order_by(desc(LLMEnrichmentModel.created_at)).first()

        return self._to_domain(model) if model else None

    def get_by_input_hash(
        self,
        capability: str,
        input_hash: str
    ) -> Optional[LLMEnrichment]:
        """
        Get enrichment by input hash for cache lookup.

        Used to check if we already have a result for this exact input.
        """
        model = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.capability == capability,
            LLMEnrichmentModel.input_hash == input_hash,
            LLMEnrichmentModel.review_status.in_(["pending", "approved"]),
            LLMEnrichmentModel.superseded_by.is_(None)
        ).order_by(desc(LLMEnrichmentModel.created_at)).first()

        return self._to_domain(model) if model else None

    def create(self, enrichment: LLMEnrichment) -> LLMEnrichment:
        """Create a new enrichment. Returns enrichment with ID assigned."""
        model = self._to_model(enrichment)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(
        self,
        enrichment_id: int,
        enrichment: LLMEnrichment
    ) -> Optional[LLMEnrichment]:
        """Update an existing enrichment."""
        model = self.session.get(LLMEnrichmentModel, enrichment_id)
        if not model:
            return None

        # Update fields
        model.output_content = enrichment.output_content
        model.confidence = Decimal(str(enrichment.confidence))
        model.needs_review = enrichment.needs_review
        model.quality_flags = enrichment.quality_flags
        model.review_status = enrichment.review_status
        model.reviewed_by = enrichment.reviewed_by
        model.reviewed_at = enrichment.reviewed_at
        model.review_notes = enrichment.review_notes

        self.session.flush()
        return self._to_domain(model)

    def update_review_status(
        self,
        enrichment_id: int,
        review_status: str,
        reviewed_by: Optional[str] = None,
        review_notes: Optional[str] = None
    ) -> bool:
        """Update the review status of an enrichment."""
        model = self.session.get(LLMEnrichmentModel, enrichment_id)
        if not model:
            return False

        model.review_status = review_status
        model.reviewed_by = reviewed_by
        model.reviewed_at = datetime.now(timezone.utc)
        model.review_notes = review_notes

        self.session.flush()
        return True

    def supersede(
        self,
        old_enrichment_id: int,
        new_enrichment_id: int
    ) -> bool:
        """Mark an enrichment as superseded by a newer one."""
        old_model = self.session.get(LLMEnrichmentModel, old_enrichment_id)
        if not old_model:
            return False

        old_model.superseded_by = new_enrichment_id
        old_model.review_status = "superseded"

        self.session.flush()
        return True

    def delete(self, enrichment_id: int) -> bool:
        """Delete an enrichment by ID."""
        model = self.session.get(LLMEnrichmentModel, enrichment_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def list_pending_review(
        self,
        capability: Optional[str] = None,
        limit: int = 100
    ) -> List[LLMEnrichment]:
        """Get enrichments pending review."""
        query = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.review_status == "pending",
            LLMEnrichmentModel.needs_review.is_(True)
        )

        if capability:
            query = query.filter(LLMEnrichmentModel.capability == capability)

        query = query.order_by(LLMEnrichmentModel.created_at.asc()).limit(limit)
        models = query.all()

        return [self._to_domain(m) for m in models]

    def list_by_capability(
        self,
        capability: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMEnrichment]:
        """List all enrichments for a capability with pagination."""
        models = self.session.query(LLMEnrichmentModel).filter(
            LLMEnrichmentModel.capability == capability
        ).order_by(
            desc(LLMEnrichmentModel.created_at)
        ).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: LLMEnrichmentModel) -> LLMEnrichment:
        """Convert ORM model to domain value object."""
        return LLMEnrichment(
            id=model.id,
            coin_id=model.coin_id,
            capability=model.capability,
            capability_version=model.capability_version,
            model_id=model.model_id,
            model_version=model.model_version,
            input_hash=model.input_hash,
            input_snapshot=model.input_snapshot,
            output_content=model.output_content,
            raw_response=model.raw_response,
            confidence=float(model.confidence) if model.confidence else 0.0,
            needs_review=model.needs_review or False,
            quality_flags=model.quality_flags,
            cost_usd=float(model.cost_usd) if model.cost_usd else 0.0,
            input_tokens=model.input_tokens,
            output_tokens=model.output_tokens,
            cached=model.cached or False,
            review_status=model.review_status or "pending",
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at,
            review_notes=model.review_notes,
            created_at=model.created_at,
            expires_at=model.expires_at,
            superseded_by=model.superseded_by,
            request_id=model.request_id,
            batch_job_id=model.batch_job_id,
        )

    def _to_model(self, enrichment: LLMEnrichment) -> LLMEnrichmentModel:
        """Convert domain value object to ORM model."""
        return LLMEnrichmentModel(
            id=enrichment.id,
            coin_id=enrichment.coin_id,
            capability=enrichment.capability,
            capability_version=enrichment.capability_version,
            model_id=enrichment.model_id,
            model_version=enrichment.model_version,
            input_hash=enrichment.input_hash,
            input_snapshot=enrichment.input_snapshot,
            output_content=enrichment.output_content,
            raw_response=enrichment.raw_response,
            confidence=Decimal(str(enrichment.confidence)),
            needs_review=enrichment.needs_review,
            quality_flags=enrichment.quality_flags,
            cost_usd=Decimal(str(enrichment.cost_usd)),
            input_tokens=enrichment.input_tokens,
            output_tokens=enrichment.output_tokens,
            cached=enrichment.cached,
            review_status=enrichment.review_status,
            reviewed_by=enrichment.reviewed_by,
            reviewed_at=enrichment.reviewed_at,
            review_notes=enrichment.review_notes,
            created_at=enrichment.created_at or datetime.now(timezone.utc),
            expires_at=enrichment.expires_at,
            superseded_by=enrichment.superseded_by,
            request_id=enrichment.request_id,
            batch_job_id=enrichment.batch_job_id,
        )
