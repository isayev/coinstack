"""Concrete repository implementation for die catalog."""

from typing import Optional
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import Die, DieSide, DieState
from src.domain.repositories_die_study import IDieRepository
from src.infrastructure.persistence.orm import DieModel


class SqlAlchemyDieRepository(IDieRepository):
    """SQLAlchemy implementation of die repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, die_id: int) -> Optional[Die]:
        """Get die by ID with eager loading."""
        model = (
            self.session.query(DieModel)
            .options(
                selectinload(DieModel.die_links),
                selectinload(DieModel.die_varieties)
            )
            .filter(DieModel.id == die_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_identifier(self, identifier: str) -> Optional[Die]:
        """Get die by canonical identifier."""
        model = (
            self.session.query(DieModel)
            .options(
                selectinload(DieModel.die_links),
                selectinload(DieModel.die_varieties)
            )
            .filter(DieModel.die_identifier == identifier)
            .first()
        )
        return self._to_domain(model) if model else None

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Die]:
        """List all dies with pagination."""
        models = (
            self.session.query(DieModel)
            .options(
                selectinload(DieModel.die_links),
                selectinload(DieModel.die_varieties)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def search(self, query: str, die_side: str | None = None) -> list[Die]:
        """Search dies by identifier or notes."""
        q = self.session.query(DieModel).options(
            selectinload(DieModel.die_links),
            selectinload(DieModel.die_varieties)
        )

        # Filter by die_side if provided
        if die_side:
            q = q.filter(DieModel.die_side == die_side)

        # Search in identifier or notes
        search_term = f"%{query}%"
        q = q.filter(
            (DieModel.die_identifier.ilike(search_term)) |
            (DieModel.notes.ilike(search_term))
        )

        models = q.all()
        return [self._to_domain(m) for m in models]

    def create(self, die: Die) -> Die:
        """Create new die entry."""
        model = self._to_model(die)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, die_id: int, die: Die) -> Optional[Die]:
        """Update existing die entry."""
        model = self.session.query(DieModel).filter(DieModel.id == die_id).first()
        if not model:
            return None

        # Update fields
        model.die_identifier = die.die_identifier or model.die_identifier
        model.die_side = die.die_side.value if die.die_side else model.die_side
        model.die_state = die.die_state.value if die.die_state else model.die_state
        model.has_die_crack = die.has_die_crack
        model.has_die_clash = die.has_die_clash
        model.die_rotation_angle = die.die_rotation_angle if die.die_rotation_angle is not None else model.die_rotation_angle
        model.reference_system = die.reference_system if die.reference_system is not None else model.reference_system
        model.reference_number = die.reference_number if die.reference_number is not None else model.reference_number
        model.notes = die.notes if die.notes is not None else model.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, die_id: int) -> bool:
        """Delete die entry."""
        model = self.session.query(DieModel).filter(DieModel.id == die_id).first()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def _to_domain(self, model: DieModel) -> Die:
        """Convert ORM model to domain entity."""
        return Die(
            id=model.id,
            die_identifier=model.die_identifier,
            die_side=DieSide(model.die_side) if model.die_side else None,
            die_state=DieState(model.die_state) if model.die_state else None,
            has_die_crack=model.has_die_crack,
            has_die_clash=model.has_die_clash,
            die_rotation_angle=model.die_rotation_angle,
            reference_system=model.reference_system,
            reference_number=model.reference_number,
            notes=model.notes
        )

    def _to_model(self, die: Die) -> DieModel:
        """Convert domain entity to ORM model."""
        return DieModel(
            id=die.id,
            die_identifier=die.die_identifier,
            die_side=die.die_side.value if die.die_side else None,
            die_state=die.die_state.value if die.die_state else None,
            has_die_crack=die.has_die_crack,
            has_die_clash=die.has_die_clash,
            die_rotation_angle=die.die_rotation_angle,
            reference_system=die.reference_system,
            reference_number=die.reference_number,
            notes=die.notes
        )
