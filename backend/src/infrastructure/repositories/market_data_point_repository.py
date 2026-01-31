"""
Market Data Point Repository Implementation.

Handles persistence of individual price observations.
"""

from typing import Optional, List
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import MarketDataPoint
from src.infrastructure.persistence.orm import MarketDataPointModel


class SqlAlchemyMarketDataPointRepository:
    """
    Repository for managing market data points.

    Provides CRUD operations for individual price observations.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, data_point_id: int) -> Optional[MarketDataPoint]:
        """Get a data point by ID."""
        model = self.session.get(MarketDataPointModel, data_point_id)
        return self._to_domain(model) if model else None

    def get_by_market_price_id(
        self,
        market_price_id: int,
        source_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketDataPoint]:
        """
        Get all data points for a market price.

        Returns points ordered by date desc (newest first).
        """
        query = self.session.query(MarketDataPointModel).filter(
            MarketDataPointModel.market_price_id == market_price_id
        )

        if source_type:
            query = query.filter(MarketDataPointModel.source_type == source_type)

        query = query.order_by(desc(MarketDataPointModel.date))
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def get_recent(
        self,
        market_price_id: int,
        days: int = 365,
    ) -> List[MarketDataPoint]:
        """Get recent data points within a date range."""
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)

        models = self.session.query(MarketDataPointModel).filter(
            MarketDataPointModel.market_price_id == market_price_id,
            MarketDataPointModel.date >= cutoff,
        ).order_by(MarketDataPointModel.date).all()

        return [self._to_domain(m) for m in models]

    def create(self, market_price_id: int, data_point: MarketDataPoint) -> MarketDataPoint:
        """Create a new data point. Returns point with ID assigned."""
        model = self._to_model(data_point)
        model.id = None  # Ensure new record
        model.market_price_id = market_price_id

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, data_point_id: int, data_point: MarketDataPoint) -> Optional[MarketDataPoint]:
        """Update an existing data point."""
        model = self.session.get(MarketDataPointModel, data_point_id)
        if not model:
            return None

        # Update fields
        model.price = data_point.price
        model.currency = data_point.currency
        model.price_usd = data_point.price_usd
        model.source_type = data_point.source_type
        model.date = data_point.date
        model.grade = data_point.grade
        model.grade_numeric = data_point.grade_numeric
        model.condition_notes = data_point.condition_notes
        model.auction_house = data_point.auction_house
        model.sale_name = data_point.sale_name
        model.lot_number = data_point.lot_number
        model.lot_url = data_point.lot_url
        model.dealer_name = data_point.dealer_name
        model.is_hammer_price = data_point.is_hammer_price
        model.buyers_premium_pct = data_point.buyers_premium_pct
        model.is_slabbed = data_point.is_slabbed
        model.grading_service = data_point.grading_service
        model.certification_number = data_point.certification_number
        model.confidence = data_point.confidence
        model.notes = data_point.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, data_point_id: int) -> bool:
        """Delete a data point by ID."""
        model = self.session.get(MarketDataPointModel, data_point_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def count_by_market_price_id(self, market_price_id: int) -> int:
        """Count data points for a market price."""
        return self.session.query(MarketDataPointModel).filter(
            MarketDataPointModel.market_price_id == market_price_id
        ).count()

    def list_by_source_type(
        self,
        source_type: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketDataPoint]:
        """List data points by source type."""
        models = self.session.query(MarketDataPointModel).filter(
            MarketDataPointModel.source_type == source_type
        ).order_by(desc(MarketDataPointModel.date)).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: MarketDataPointModel) -> MarketDataPoint:
        """Convert ORM model to domain entity."""
        return MarketDataPoint(
            id=model.id,
            market_price_id=model.market_price_id,
            price=model.price,
            currency=model.currency or "USD",
            price_usd=model.price_usd,
            source_type=model.source_type,
            date=model.date,
            grade=model.grade,
            grade_numeric=model.grade_numeric,
            condition_notes=model.condition_notes,
            auction_house=model.auction_house,
            sale_name=model.sale_name,
            lot_number=model.lot_number,
            lot_url=model.lot_url,
            dealer_name=model.dealer_name,
            is_hammer_price=model.is_hammer_price if model.is_hammer_price is not None else True,
            buyers_premium_pct=model.buyers_premium_pct,
            is_slabbed=model.is_slabbed if model.is_slabbed is not None else False,
            grading_service=model.grading_service,
            certification_number=model.certification_number,
            confidence=model.confidence or "medium",
            notes=model.notes,
            created_at=model.created_at,
        )

    def _to_model(self, data_point: MarketDataPoint) -> MarketDataPointModel:
        """Convert domain entity to ORM model."""
        return MarketDataPointModel(
            id=data_point.id,
            market_price_id=data_point.market_price_id,
            price=data_point.price,
            currency=data_point.currency,
            price_usd=data_point.price_usd,
            source_type=data_point.source_type,
            date=data_point.date,
            grade=data_point.grade,
            grade_numeric=data_point.grade_numeric,
            condition_notes=data_point.condition_notes,
            auction_house=data_point.auction_house,
            sale_name=data_point.sale_name,
            lot_number=data_point.lot_number,
            lot_url=data_point.lot_url,
            dealer_name=data_point.dealer_name,
            is_hammer_price=data_point.is_hammer_price,
            buyers_premium_pct=data_point.buyers_premium_pct,
            is_slabbed=data_point.is_slabbed,
            grading_service=data_point.grading_service,
            certification_number=data_point.certification_number,
            confidence=data_point.confidence,
            notes=data_point.notes,
            created_at=data_point.created_at or datetime.now(timezone.utc),
        )
