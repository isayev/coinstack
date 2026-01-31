"""
Reference Concordance Repository - SQLAlchemy implementation.

Manages cross-reference linking between equivalent catalog references.
Example: RIC 207 = RSC 112 = BMC 298 = Cohen 169
"""

import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.domain.coin import ReferenceConcordance
from src.domain.repositories import IConcordanceRepository
from src.infrastructure.persistence.orm import ReferenceConcordanceModel


class SqlAlchemyConcordanceRepository(IConcordanceRepository):
    """SQLAlchemy implementation of IConcordanceRepository."""

    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ReferenceConcordanceModel) -> ReferenceConcordance:
        """Convert ORM model to domain entity."""
        return ReferenceConcordance(
            id=model.id,
            concordance_group_id=model.concordance_group_id,
            reference_type_id=model.reference_type_id,
            confidence=float(model.confidence) if model.confidence else 1.0,
            source=model.source,
            notes=model.notes,
            created_at=model.created_at,
        )

    def _to_model(self, entity: ReferenceConcordance) -> ReferenceConcordanceModel:
        """Convert domain entity to ORM model."""
        model = ReferenceConcordanceModel(
            concordance_group_id=entity.concordance_group_id,
            reference_type_id=entity.reference_type_id,
            confidence=entity.confidence,
            source=entity.source,
            notes=entity.notes,
        )
        if entity.id:
            model.id = entity.id
        return model

    def get_by_group_id(self, group_id: str) -> List[ReferenceConcordance]:
        """Get all concordance entries in a group."""
        models = (
            self.session.query(ReferenceConcordanceModel)
            .filter(ReferenceConcordanceModel.concordance_group_id == group_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_reference_type_id(self, reference_type_id: int) -> List[ReferenceConcordance]:
        """Get concordance entries for a specific reference type."""
        models = (
            self.session.query(ReferenceConcordanceModel)
            .filter(ReferenceConcordanceModel.reference_type_id == reference_type_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, concordance: ReferenceConcordance) -> ReferenceConcordance:
        """Create a new concordance entry."""
        model = self._to_model(concordance)
        model.created_at = datetime.utcnow()
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def create_group(
        self,
        reference_type_ids: List[int],
        source: str = "user",
        confidence: float = 1.0,
        notes: Optional[str] = None
    ) -> str:
        """Create a concordance group linking multiple reference types."""
        group_id = str(uuid.uuid4())

        for ref_type_id in reference_type_ids:
            model = ReferenceConcordanceModel(
                concordance_group_id=group_id,
                reference_type_id=ref_type_id,
                confidence=confidence,
                source=source,
                notes=notes,
                created_at=datetime.utcnow(),
            )
            self.session.add(model)

        self.session.flush()
        return group_id

    def delete(self, concordance_id: int) -> bool:
        """Delete a concordance entry by ID."""
        model = self.session.query(ReferenceConcordanceModel).get(concordance_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def delete_group(self, group_id: str) -> int:
        """Delete all concordance entries in a group."""
        count = (
            self.session.query(ReferenceConcordanceModel)
            .filter(ReferenceConcordanceModel.concordance_group_id == group_id)
            .delete()
        )
        self.session.flush()
        return count

    def find_equivalent_references(self, reference_type_id: int) -> List[int]:
        """Find all reference_type_ids equivalent to the given reference."""
        # First, find all group IDs this reference belongs to
        entries = self.get_by_reference_type_id(reference_type_id)

        if not entries:
            return []

        # Collect all equivalent reference type IDs
        equivalent_ids = set()
        for entry in entries:
            group_entries = self.get_by_group_id(entry.concordance_group_id)
            for ge in group_entries:
                if ge.reference_type_id != reference_type_id:
                    equivalent_ids.add(ge.reference_type_id)

        return list(equivalent_ids)
