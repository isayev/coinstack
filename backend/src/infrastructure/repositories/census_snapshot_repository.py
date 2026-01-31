"""
Census Snapshot Repository Implementation.

Handles persistence of NGC/PCGS population census snapshots.
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import CensusSnapshot
from src.domain.repositories import ICensusSnapshotRepository
from src.infrastructure.persistence.orm import CensusSnapshotModel


class SqlAlchemyCensusSnapshotRepository(ICensusSnapshotRepository):
    """
    Repository for managing census snapshots.

    Provides population tracking over time for TPG-graded coins.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, snapshot_id: int) -> Optional[CensusSnapshot]:
        """Get a specific census snapshot by ID."""
        model = self.session.get(CensusSnapshotModel, snapshot_id)
        return self._to_domain(model) if model else None

    def get_by_coin_id(
        self,
        coin_id: int,
        service: Optional[str] = None,
    ) -> List[CensusSnapshot]:
        """
        Get all census snapshots for a coin, optionally filtered by service.

        Returns snapshots ordered by date desc (newest first).
        """
        query = self.session.query(CensusSnapshotModel).filter(
            CensusSnapshotModel.coin_id == coin_id
        )

        if service:
            query = query.filter(CensusSnapshotModel.service == service)

        query = query.order_by(desc(CensusSnapshotModel.snapshot_date))
        models = query.all()

        return [self._to_domain(m) for m in models]

    def get_latest(
        self,
        coin_id: int,
        service: Optional[str] = None,
    ) -> Optional[CensusSnapshot]:
        """
        Get the most recent census snapshot for a coin.

        Optionally filter by service (ngc, pcgs).
        """
        query = self.session.query(CensusSnapshotModel).filter(
            CensusSnapshotModel.coin_id == coin_id
        )

        if service:
            query = query.filter(CensusSnapshotModel.service == service)

        model = query.order_by(desc(CensusSnapshotModel.snapshot_date)).first()
        return self._to_domain(model) if model else None

    def create(self, coin_id: int, snapshot: CensusSnapshot) -> CensusSnapshot:
        """Create a new census snapshot. Returns snapshot with ID assigned."""
        model = self._to_model(snapshot)
        model.id = None  # Ensure new record
        model.coin_id = coin_id

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(
        self,
        snapshot_id: int,
        snapshot: CensusSnapshot
    ) -> Optional[CensusSnapshot]:
        """Update an existing census snapshot."""
        model = self.session.get(CensusSnapshotModel, snapshot_id)
        if not model:
            return None

        # Update fields
        model.service = snapshot.service
        model.snapshot_date = snapshot.snapshot_date
        model.total_graded = snapshot.total_graded
        model.grade_breakdown = snapshot.grade_breakdown
        model.coins_at_grade = snapshot.coins_at_grade
        model.coins_finer = snapshot.coins_finer
        model.percentile = snapshot.percentile
        model.catalog_reference = snapshot.catalog_reference
        model.notes = snapshot.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, snapshot_id: int) -> bool:
        """Delete a census snapshot by ID."""
        model = self.session.get(CensusSnapshotModel, snapshot_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def list_by_service(
        self,
        service: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CensusSnapshot]:
        """List all snapshots for a service with pagination."""
        models = self.session.query(CensusSnapshotModel).filter(
            CensusSnapshotModel.service == service
        ).order_by(
            desc(CensusSnapshotModel.snapshot_date)
        ).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def list_by_date_range(
        self,
        coin_id: int,
        start_date: date,
        end_date: date,
    ) -> List[CensusSnapshot]:
        """Get snapshots within a date range for trend analysis."""
        models = self.session.query(CensusSnapshotModel).filter(
            CensusSnapshotModel.coin_id == coin_id,
            CensusSnapshotModel.snapshot_date >= start_date,
            CensusSnapshotModel.snapshot_date <= end_date,
        ).order_by(CensusSnapshotModel.snapshot_date).all()

        return [self._to_domain(m) for m in models]

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: CensusSnapshotModel) -> CensusSnapshot:
        """Convert ORM model to domain entity."""
        return CensusSnapshot(
            id=model.id,
            coin_id=model.coin_id,
            service=model.service,
            snapshot_date=model.snapshot_date,
            total_graded=model.total_graded,
            grade_breakdown=model.grade_breakdown,
            coins_at_grade=model.coins_at_grade,
            coins_finer=model.coins_finer,
            percentile=float(model.percentile) if model.percentile else None,
            catalog_reference=model.catalog_reference,
            notes=model.notes,
        )

    def _to_model(self, snapshot: CensusSnapshot) -> CensusSnapshotModel:
        """Convert domain entity to ORM model."""
        return CensusSnapshotModel(
            id=snapshot.id,
            coin_id=snapshot.coin_id,
            service=snapshot.service,
            snapshot_date=snapshot.snapshot_date,
            total_graded=snapshot.total_graded,
            grade_breakdown=snapshot.grade_breakdown,
            coins_at_grade=snapshot.coins_at_grade,
            coins_finer=snapshot.coins_finer,
            percentile=Decimal(str(snapshot.percentile)) if snapshot.percentile else None,
            catalog_reference=snapshot.catalog_reference,
            notes=snapshot.notes,
        )
