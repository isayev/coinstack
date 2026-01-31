"""
Grading History Repository Implementation.

Handles persistence of grading history (TPG lifecycle) events for coins.
Implements IGradingHistoryRepository protocol.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from src.domain.coin import GradingHistoryEntry
from src.domain.repositories import IGradingHistoryRepository
from src.infrastructure.persistence.orm import GradingHistoryModel


class SqlAlchemyGradingHistoryRepository(IGradingHistoryRepository):
    """
    Repository for managing coin grading history events.

    Tracks the complete TPG lifecycle from initial submission through
    crossovers, regrades, and crack-outs.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_coin_id(self, coin_id: int) -> List[GradingHistoryEntry]:
        """
        Get all grading history entries for a coin, ordered by sequence_order.

        Returns complete timeline from initial grading to current state.
        """
        models = self.session.query(GradingHistoryModel).filter(
            GradingHistoryModel.coin_id == coin_id
        ).order_by(
            GradingHistoryModel.sequence_order.asc(),
            GradingHistoryModel.graded_date.asc().nulls_last()
        ).all()

        return [self._to_domain(m) for m in models]

    def get_by_id(self, entry_id: int) -> Optional[GradingHistoryEntry]:
        """Get a specific grading history entry by ID."""
        model = self.session.get(GradingHistoryModel, entry_id)
        return self._to_domain(model) if model else None

    def create(self, coin_id: int, entry: GradingHistoryEntry) -> GradingHistoryEntry:
        """
        Create a new grading history entry for a coin.

        Returns entry with ID assigned.
        """
        model = self._to_model(entry)
        model.coin_id = coin_id
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()  # Get ID without committing

        return self._to_domain(model)

    def update(self, entry_id: int, entry: GradingHistoryEntry) -> Optional[GradingHistoryEntry]:
        """Update an existing grading history entry."""
        model = self.session.get(GradingHistoryModel, entry_id)
        if not model:
            return None

        # Update all fields from domain object
        model.grading_state = entry.grading_state
        model.grade = entry.grade
        model.grade_service = entry.grade_service
        model.certification_number = entry.certification_number
        model.strike_quality = entry.strike_quality
        model.surface_quality = entry.surface_quality
        model.grade_numeric = entry.grade_numeric
        model.designation = entry.designation
        model.has_star = entry.has_star
        model.photo_cert = entry.photo_cert
        model.verification_url = entry.verification_url
        model.event_type = entry.event_type
        model.graded_date = entry.graded_date
        model.submitter = entry.submitter
        model.turnaround_days = entry.turnaround_days
        model.grading_fee = entry.grading_fee
        model.notes = entry.notes
        model.sequence_order = entry.sequence_order
        model.is_current = entry.is_current

        self.session.flush()
        return self._to_domain(model)

    def delete(self, entry_id: int) -> bool:
        """Delete a grading history entry by ID."""
        model = self.session.get(GradingHistoryModel, entry_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def clear_all_current(self, coin_id: int) -> None:
        """
        Clear is_current flag on all grading history entries for a coin.

        Use this before creating a new entry that should be marked as current.
        """
        self.session.query(GradingHistoryModel).filter(
            GradingHistoryModel.coin_id == coin_id
        ).update({"is_current": False})
        self.session.flush()

    def set_current(self, coin_id: int, entry_id: int) -> bool:
        """
        Mark a grading history entry as the current grading state.

        Clears is_current flag on all other entries for this coin.
        Returns True if successful, False if entry not found.
        """
        # Clear is_current on all entries for this coin
        self.session.query(GradingHistoryModel).filter(
            GradingHistoryModel.coin_id == coin_id
        ).update({"is_current": False})

        # Set is_current on the target entry
        model = self.session.get(GradingHistoryModel, entry_id)
        if model and model.coin_id == coin_id:
            model.is_current = True
            self.session.flush()
            return True
        return False

    def get_current(self, coin_id: int) -> Optional[GradingHistoryEntry]:
        """Get the current (active) grading state for a coin."""
        model = self.session.query(GradingHistoryModel).filter(
            GradingHistoryModel.coin_id == coin_id,
            GradingHistoryModel.is_current.is_(True)
        ).first()

        return self._to_domain(model) if model else None

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: GradingHistoryModel) -> GradingHistoryEntry:
        """Convert ORM model to domain value object."""
        return GradingHistoryEntry(
            id=model.id,
            coin_id=model.coin_id,
            grading_state=model.grading_state,
            grade=model.grade,
            grade_service=model.grade_service,
            certification_number=model.certification_number,
            strike_quality=model.strike_quality,
            surface_quality=model.surface_quality,
            grade_numeric=model.grade_numeric,
            designation=model.designation,
            has_star=model.has_star or False,
            photo_cert=model.photo_cert or False,
            verification_url=model.verification_url,
            event_type=model.event_type,
            graded_date=model.graded_date,
            recorded_at=model.recorded_at.isoformat() if model.recorded_at else None,
            submitter=model.submitter,
            turnaround_days=model.turnaround_days,
            grading_fee=model.grading_fee,
            notes=model.notes,
            sequence_order=model.sequence_order,
            is_current=model.is_current,
        )

    def _to_model(self, entry: GradingHistoryEntry) -> GradingHistoryModel:
        """Convert domain value object to ORM model."""
        return GradingHistoryModel(
            id=entry.id,
            coin_id=entry.coin_id,
            grading_state=entry.grading_state,
            grade=entry.grade,
            grade_service=entry.grade_service,
            certification_number=entry.certification_number,
            strike_quality=entry.strike_quality,
            surface_quality=entry.surface_quality,
            grade_numeric=entry.grade_numeric,
            designation=entry.designation,
            has_star=entry.has_star,
            photo_cert=entry.photo_cert,
            verification_url=entry.verification_url,
            event_type=entry.event_type,
            graded_date=entry.graded_date,
            recorded_at=datetime.now(timezone.utc),
            submitter=entry.submitter,
            turnaround_days=entry.turnaround_days,
            grading_fee=entry.grading_fee,
            notes=entry.notes,
            sequence_order=entry.sequence_order,
            is_current=entry.is_current,
        )
