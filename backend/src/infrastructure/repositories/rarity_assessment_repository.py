"""
Rarity Assessment Repository Implementation.

Handles persistence of multi-source rarity assessments for coins.
Implements IRarityAssessmentRepository protocol.
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.domain.coin import RarityAssessment
from src.domain.repositories import IRarityAssessmentRepository
from src.infrastructure.persistence.orm import RarityAssessmentModel


class SqlAlchemyRarityAssessmentRepository(IRarityAssessmentRepository):
    """
    Repository for managing coin rarity assessments.

    Supports tracking rarity from multiple sources (catalogs, census data,
    market analysis) with grade-conditional support.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_coin_id(self, coin_id: int) -> List[RarityAssessment]:
        """
        Get all rarity assessments for a coin.

        Returns assessments ordered by is_primary desc, then by source_date desc.
        """
        models = self.session.query(RarityAssessmentModel).filter(
            RarityAssessmentModel.coin_id == coin_id
        ).order_by(
            RarityAssessmentModel.is_primary.desc(),
            RarityAssessmentModel.source_date.desc().nulls_last(),
            RarityAssessmentModel.created_at.desc()
        ).all()

        return [self._to_domain(m) for m in models]

    def get_by_id(self, assessment_id: int) -> Optional[RarityAssessment]:
        """Get a specific rarity assessment by ID."""
        model = self.session.get(RarityAssessmentModel, assessment_id)
        return self._to_domain(model) if model else None

    def create(self, coin_id: int, assessment: RarityAssessment) -> RarityAssessment:
        """
        Create a new rarity assessment for a coin.

        Returns assessment with ID assigned.
        """
        model = self._to_model(assessment)
        model.coin_id = coin_id
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()  # Get ID without committing

        return self._to_domain(model)

    def update(self, assessment_id: int, assessment: RarityAssessment) -> Optional[RarityAssessment]:
        """Update an existing rarity assessment."""
        model = self.session.get(RarityAssessmentModel, assessment_id)
        if not model:
            return None

        # Update all fields from domain object
        model.rarity_code = assessment.rarity_code
        model.rarity_system = assessment.rarity_system
        model.source_type = assessment.source_type
        model.source_name = assessment.source_name
        model.source_url = assessment.source_url
        model.source_date = assessment.source_date
        model.grade_range_low = assessment.grade_range_low
        model.grade_range_high = assessment.grade_range_high
        model.grade_conditional_notes = assessment.grade_conditional_notes
        model.census_total = assessment.census_total
        model.census_this_grade = assessment.census_this_grade
        model.census_finer = assessment.census_finer
        model.census_date = assessment.census_date
        model.confidence = assessment.confidence
        model.notes = assessment.notes
        model.is_primary = assessment.is_primary

        self.session.flush()
        return self._to_domain(model)

    def delete(self, assessment_id: int) -> bool:
        """Delete a rarity assessment by ID."""
        model = self.session.get(RarityAssessmentModel, assessment_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def clear_all_primary(self, coin_id: int) -> None:
        """
        Clear is_primary flag on all rarity assessments for a coin.

        Use this before creating a new assessment that should be marked as primary.
        """
        self.session.query(RarityAssessmentModel).filter(
            RarityAssessmentModel.coin_id == coin_id
        ).update({"is_primary": False})
        self.session.flush()

    def set_primary(self, coin_id: int, assessment_id: int) -> bool:
        """
        Mark a rarity assessment as the primary assessment.

        Clears is_primary flag on all other assessments for this coin.
        Returns True if successful, False if assessment not found.
        """
        # Clear is_primary on all assessments for this coin
        self.session.query(RarityAssessmentModel).filter(
            RarityAssessmentModel.coin_id == coin_id
        ).update({"is_primary": False})

        # Set is_primary on the target assessment
        model = self.session.get(RarityAssessmentModel, assessment_id)
        if model and model.coin_id == coin_id:
            model.is_primary = True
            self.session.flush()
            return True
        return False

    def get_primary(self, coin_id: int) -> Optional[RarityAssessment]:
        """Get the primary rarity assessment for a coin."""
        model = self.session.query(RarityAssessmentModel).filter(
            RarityAssessmentModel.coin_id == coin_id,
            RarityAssessmentModel.is_primary.is_(True)
        ).first()

        return self._to_domain(model) if model else None

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: RarityAssessmentModel) -> RarityAssessment:
        """Convert ORM model to domain value object."""
        return RarityAssessment(
            id=model.id,
            coin_id=model.coin_id,
            rarity_code=model.rarity_code,
            rarity_system=model.rarity_system,
            source_type=model.source_type,
            source_name=model.source_name,
            source_url=model.source_url,
            source_date=model.source_date,
            grade_range_low=model.grade_range_low,
            grade_range_high=model.grade_range_high,
            grade_conditional_notes=model.grade_conditional_notes,
            census_total=model.census_total,
            census_this_grade=model.census_this_grade,
            census_finer=model.census_finer,
            census_date=model.census_date,
            confidence=model.confidence or "medium",
            notes=model.notes,
            is_primary=model.is_primary or False,
            created_at=model.created_at.isoformat() if model.created_at else None,
        )

    def _to_model(self, assessment: RarityAssessment) -> RarityAssessmentModel:
        """Convert domain value object to ORM model."""
        return RarityAssessmentModel(
            id=assessment.id,
            coin_id=assessment.coin_id,
            rarity_code=assessment.rarity_code,
            rarity_system=assessment.rarity_system,
            source_type=assessment.source_type,
            source_name=assessment.source_name,
            source_url=assessment.source_url,
            source_date=assessment.source_date,
            grade_range_low=assessment.grade_range_low,
            grade_range_high=assessment.grade_range_high,
            grade_conditional_notes=assessment.grade_conditional_notes,
            census_total=assessment.census_total,
            census_this_grade=assessment.census_this_grade,
            census_finer=assessment.census_finer,
            census_date=assessment.census_date,
            confidence=assessment.confidence,
            notes=assessment.notes,
            is_primary=assessment.is_primary,
            created_at=datetime.now(timezone.utc),
        )
