"""
LLM Feedback Repository Implementation.

Handles persistence of user feedback on LLM enrichment quality.
Implements ILLMFeedbackRepository protocol.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.domain.coin import LLMFeedback
from src.domain.repositories import ILLMFeedbackRepository
from src.infrastructure.persistence.orm import LLMFeedbackModel, LLMEnrichmentModel


class SqlAlchemyLLMFeedbackRepository(ILLMFeedbackRepository):
    """
    Repository for managing LLM feedback.

    Tracks user corrections and quality feedback for continuous improvement.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, feedback_id: int) -> Optional[LLMFeedback]:
        """Get a specific feedback entry by ID."""
        model = self.session.get(LLMFeedbackModel, feedback_id)
        return self._to_domain(model) if model else None

    def get_by_enrichment_id(self, enrichment_id: int) -> List[LLMFeedback]:
        """Get all feedback for an enrichment."""
        models = self.session.query(LLMFeedbackModel).filter(
            LLMFeedbackModel.enrichment_id == enrichment_id
        ).order_by(desc(LLMFeedbackModel.created_at)).all()

        return [self._to_domain(m) for m in models]

    def create(self, feedback: LLMFeedback) -> LLMFeedback:
        """Create a new feedback entry. Returns feedback with ID assigned."""
        model = self._to_model(feedback)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def delete(self, feedback_id: int) -> bool:
        """Delete a feedback entry by ID."""
        model = self.session.get(LLMFeedbackModel, feedback_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def list_by_type(
        self,
        feedback_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMFeedback]:
        """List feedback entries by type."""
        models = self.session.query(LLMFeedbackModel).filter(
            LLMFeedbackModel.feedback_type == feedback_type
        ).order_by(
            desc(LLMFeedbackModel.created_at)
        ).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def list_by_capability(
        self,
        capability: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[LLMFeedback]:
        """List feedback for enrichments of a specific capability."""
        models = self.session.query(LLMFeedbackModel).join(
            LLMEnrichmentModel,
            LLMFeedbackModel.enrichment_id == LLMEnrichmentModel.id
        ).filter(
            LLMEnrichmentModel.capability == capability
        ).order_by(
            desc(LLMFeedbackModel.created_at)
        ).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def count_by_type(self, feedback_type: str) -> int:
        """Count feedback entries by type."""
        return self.session.query(func.count(LLMFeedbackModel.id)).filter(
            LLMFeedbackModel.feedback_type == feedback_type
        ).scalar() or 0

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: LLMFeedbackModel) -> LLMFeedback:
        """Convert ORM model to domain value object."""
        return LLMFeedback(
            id=model.id,
            enrichment_id=model.enrichment_id,
            feedback_type=model.feedback_type,
            field_path=model.field_path,
            original_value=model.original_value,
            corrected_value=model.corrected_value,
            user_id=model.user_id,
            feedback_notes=model.feedback_notes,
            created_at=model.created_at,
        )

    def _to_model(self, feedback: LLMFeedback) -> LLMFeedbackModel:
        """Convert domain value object to ORM model."""
        return LLMFeedbackModel(
            id=feedback.id,
            enrichment_id=feedback.enrichment_id,
            feedback_type=feedback.feedback_type,
            field_path=feedback.field_path,
            original_value=feedback.original_value,
            corrected_value=feedback.corrected_value,
            user_id=feedback.user_id,
            feedback_notes=feedback.feedback_notes,
            created_at=feedback.created_at or datetime.now(timezone.utc),
        )
