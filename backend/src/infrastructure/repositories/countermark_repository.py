"""
SQLAlchemy implementation of countermark repository.

Phase 1.5b: Countermark System
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from src.domain.coin import Countermark
from src.domain.repositories import ICountermarkRepository
from src.infrastructure.persistence.orm import CountermarkModel
from src.infrastructure.mappers.countermark_mapper import CountermarkMapper


class SqlAlchemyCountermarkRepository(ICountermarkRepository):
    """SQLAlchemy implementation of countermark repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, countermark_id: int) -> Optional[Countermark]:
        """Get a specific countermark by ID."""
        model = self.session.query(CountermarkModel).filter(
            CountermarkModel.id == countermark_id
        ).first()
        return CountermarkMapper.to_domain(model) if model else None

    def get_by_coin_id(self, coin_id: int) -> List[Countermark]:
        """Get all countermarks for a coin."""
        models = self.session.query(CountermarkModel).filter(
            CountermarkModel.coin_id == coin_id
        ).order_by(CountermarkModel.id).all()
        return [CountermarkMapper.to_domain(m) for m in models]

    def create(self, coin_id: int, countermark: Countermark) -> Countermark:
        """Create a new countermark for a coin. Returns countermark with ID assigned."""
        model = CountermarkMapper.to_model(countermark, coin_id=coin_id)
        model.id = None  # Ensure new record
        self.session.add(model)
        self.session.flush()  # Get ID without committing
        return CountermarkMapper.to_domain(model)

    def update(self, countermark_id: int, countermark: Countermark) -> Optional[Countermark]:
        """Update an existing countermark. All fields are updated (allows clearing)."""
        model = self.session.query(CountermarkModel).filter(
            CountermarkModel.id == countermark_id
        ).first()
        if not model:
            return None

        # Update all fields - allows clearing by passing None or empty string
        model.countermark_type = countermark.countermark_type.value if countermark.countermark_type else None
        model.position = countermark.position.value if countermark.position else None
        model.condition = countermark.condition.value if countermark.condition else None
        model.punch_shape = countermark.punch_shape.value if countermark.punch_shape else None
        model.description = countermark.description
        model.authority = countermark.authority
        model.reference = countermark.reference
        model.date_applied = countermark.date_applied
        model.notes = countermark.notes

        self.session.flush()
        return CountermarkMapper.to_domain(model)

    def delete(self, countermark_id: int) -> bool:
        """Delete a countermark by ID."""
        model = self.session.query(CountermarkModel).filter(
            CountermarkModel.id == countermark_id
        ).first()
        if not model:
            return False
        self.session.delete(model)
        self.session.flush()
        return True
