"""Concrete repository implementation for die pairings."""

from typing import Optional
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import DiePairing
from src.domain.repositories_die_study import IDiePairingRepository
from src.infrastructure.persistence.orm import DiePairingModel


class SqlAlchemyDiePairingRepository(IDiePairingRepository):
    """SQLAlchemy implementation of die pairing repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, pairing_id: int) -> Optional[DiePairing]:
        """Get die pairing by ID with eager loading."""
        model = (
            self.session.query(DiePairingModel)
            .options(
                selectinload(DiePairingModel.obverse_die),
                selectinload(DiePairingModel.reverse_die)
            )
            .filter(DiePairingModel.id == pairing_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_dies(self, obverse_die_id: int, reverse_die_id: int) -> Optional[DiePairing]:
        """Get die pairing by obverse and reverse die IDs."""
        model = (
            self.session.query(DiePairingModel)
            .options(
                selectinload(DiePairingModel.obverse_die),
                selectinload(DiePairingModel.reverse_die)
            )
            .filter(
                DiePairingModel.obverse_die_id == obverse_die_id,
                DiePairingModel.reverse_die_id == reverse_die_id
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def list_by_obverse(self, obverse_die_id: int) -> list[DiePairing]:
        """List all pairings for an obverse die."""
        models = (
            self.session.query(DiePairingModel)
            .options(
                selectinload(DiePairingModel.obverse_die),
                selectinload(DiePairingModel.reverse_die)
            )
            .filter(DiePairingModel.obverse_die_id == obverse_die_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_reverse(self, reverse_die_id: int) -> list[DiePairing]:
        """List all pairings for a reverse die."""
        models = (
            self.session.query(DiePairingModel)
            .options(
                selectinload(DiePairingModel.obverse_die),
                selectinload(DiePairingModel.reverse_die)
            )
            .filter(DiePairingModel.reverse_die_id == reverse_die_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, pairing: DiePairing) -> DiePairing:
        """Create new die pairing."""
        model = self._to_model(pairing)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, pairing_id: int, pairing: DiePairing) -> Optional[DiePairing]:
        """Update existing die pairing."""
        model = self.session.query(DiePairingModel).filter(DiePairingModel.id == pairing_id).first()
        if not model:
            return None

        # Update fields
        model.reference_system = pairing.reference_system if pairing.reference_system is not None else model.reference_system
        model.reference_number = pairing.reference_number if pairing.reference_number is not None else model.reference_number
        model.rarity_notes = pairing.rarity_notes if pairing.rarity_notes is not None else model.rarity_notes
        model.specimen_count = pairing.specimen_count if pairing.specimen_count is not None else model.specimen_count
        model.notes = pairing.notes if pairing.notes is not None else model.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, pairing_id: int) -> bool:
        """Delete die pairing."""
        model = self.session.query(DiePairingModel).filter(DiePairingModel.id == pairing_id).first()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def _to_domain(self, model: DiePairingModel) -> DiePairing:
        """Convert ORM model to domain entity."""
        return DiePairing(
            id=model.id,
            obverse_die_id=model.obverse_die_id,
            reverse_die_id=model.reverse_die_id,
            reference_system=model.reference_system,
            reference_number=model.reference_number,
            rarity_notes=model.rarity_notes,
            specimen_count=model.specimen_count,
            notes=model.notes
        )

    def _to_model(self, pairing: DiePairing) -> DiePairingModel:
        """Convert domain entity to ORM model."""
        return DiePairingModel(
            id=pairing.id,
            obverse_die_id=pairing.obverse_die_id,
            reverse_die_id=pairing.reverse_die_id,
            reference_system=pairing.reference_system,
            reference_number=pairing.reference_number,
            rarity_notes=pairing.rarity_notes,
            specimen_count=pairing.specimen_count,
            notes=pairing.notes
        )
