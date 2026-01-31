"""
Market Price Repository Implementation.

Handles persistence of aggregate market pricing by attribution.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import MarketPrice
from src.infrastructure.persistence.orm import MarketPriceModel


def _escape_like(value: str) -> str:
    """Escape special LIKE pattern characters to prevent LIKE injection."""
    return value.replace('%', r'\%').replace('_', r'\_')


class SqlAlchemyMarketPriceRepository:
    """
    Repository for managing market price aggregates.

    Provides CRUD operations for type-level pricing data.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, price_id: int) -> Optional[MarketPrice]:
        """Get a market price by ID."""
        model = self.session.get(MarketPriceModel, price_id)
        return self._to_domain(model) if model else None

    def get_by_attribution_key(self, attribution_key: str) -> Optional[MarketPrice]:
        """Get market price by attribution key."""
        model = self.session.query(MarketPriceModel).filter(
            MarketPriceModel.attribution_key == attribution_key
        ).first()
        return self._to_domain(model) if model else None

    def list_all(
        self,
        issuer: Optional[str] = None,
        denomination: Optional[str] = None,
        metal: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MarketPrice]:
        """
        List market prices with optional filters.

        Returns prices ordered by last_updated desc (newest first).
        """
        query = self.session.query(MarketPriceModel)

        if issuer:
            query = query.filter(MarketPriceModel.issuer.ilike(f"%{_escape_like(issuer)}%"))
        if denomination:
            query = query.filter(MarketPriceModel.denomination.ilike(f"%{_escape_like(denomination)}%"))
        if metal:
            query = query.filter(MarketPriceModel.metal == metal)

        query = query.order_by(desc(MarketPriceModel.last_updated))
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def count(
        self,
        issuer: Optional[str] = None,
        denomination: Optional[str] = None,
        metal: Optional[str] = None,
    ) -> int:
        """Count market prices matching filters."""
        query = self.session.query(MarketPriceModel)

        if issuer:
            query = query.filter(MarketPriceModel.issuer.ilike(f"%{_escape_like(issuer)}%"))
        if denomination:
            query = query.filter(MarketPriceModel.denomination.ilike(f"%{_escape_like(denomination)}%"))
        if metal:
            query = query.filter(MarketPriceModel.metal == metal)

        return query.count()

    def create(self, market_price: MarketPrice) -> MarketPrice:
        """Create a new market price. Returns price with ID assigned."""
        model = self._to_model(market_price)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, price_id: int, market_price: MarketPrice) -> Optional[MarketPrice]:
        """Update an existing market price."""
        model = self.session.get(MarketPriceModel, price_id)
        if not model:
            return None

        # Update fields
        model.attribution_key = market_price.attribution_key
        model.issuer = market_price.issuer
        model.denomination = market_price.denomination
        model.mint = market_price.mint
        model.metal = market_price.metal
        model.category = market_price.category
        model.catalog_ref = market_price.catalog_ref
        model.avg_price_vf = market_price.avg_price_vf
        model.avg_price_ef = market_price.avg_price_ef
        model.avg_price_au = market_price.avg_price_au
        model.avg_price_ms = market_price.avg_price_ms
        model.min_price_seen = market_price.min_price_seen
        model.max_price_seen = market_price.max_price_seen
        model.median_price = market_price.median_price
        model.data_point_count = market_price.data_point_count
        model.last_sale_date = market_price.last_sale_date
        model.last_updated = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def delete(self, price_id: int) -> bool:
        """Delete a market price by ID."""
        model = self.session.get(MarketPriceModel, price_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def search_by_catalog_ref(self, catalog_ref: str) -> List[MarketPrice]:
        """Search market prices by catalog reference pattern."""
        models = self.session.query(MarketPriceModel).filter(
            MarketPriceModel.catalog_ref.ilike(f"%{_escape_like(catalog_ref)}%")
        ).order_by(desc(MarketPriceModel.last_updated)).all()

        return [self._to_domain(m) for m in models]

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: MarketPriceModel) -> MarketPrice:
        """Convert ORM model to domain entity."""
        return MarketPrice(
            id=model.id,
            attribution_key=model.attribution_key,
            issuer=model.issuer,
            denomination=model.denomination,
            mint=model.mint,
            metal=model.metal,
            category=model.category,
            catalog_ref=model.catalog_ref,
            avg_price_vf=model.avg_price_vf,
            avg_price_ef=model.avg_price_ef,
            avg_price_au=model.avg_price_au,
            avg_price_ms=model.avg_price_ms,
            min_price_seen=model.min_price_seen,
            max_price_seen=model.max_price_seen,
            median_price=model.median_price,
            data_point_count=model.data_point_count or 0,
            last_sale_date=model.last_sale_date,
            last_updated=model.last_updated,
        )

    def _to_model(self, market_price: MarketPrice) -> MarketPriceModel:
        """Convert domain entity to ORM model."""
        return MarketPriceModel(
            id=market_price.id,
            attribution_key=market_price.attribution_key,
            issuer=market_price.issuer,
            denomination=market_price.denomination,
            mint=market_price.mint,
            metal=market_price.metal,
            category=market_price.category,
            catalog_ref=market_price.catalog_ref,
            avg_price_vf=market_price.avg_price_vf,
            avg_price_ef=market_price.avg_price_ef,
            avg_price_au=market_price.avg_price_au,
            avg_price_ms=market_price.avg_price_ms,
            min_price_seen=market_price.min_price_seen,
            max_price_seen=market_price.max_price_seen,
            median_price=market_price.median_price,
            data_point_count=market_price.data_point_count,
            last_sale_date=market_price.last_sale_date,
            last_updated=market_price.last_updated or datetime.now(timezone.utc),
        )
