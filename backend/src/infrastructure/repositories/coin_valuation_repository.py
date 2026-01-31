"""
Coin Valuation Repository Implementation.

Handles persistence of per-coin valuation snapshots.
"""

from typing import Optional, List, Dict
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from src.domain.coin import CoinValuation
from src.infrastructure.persistence.orm import CoinValuationModel


class SqlAlchemyCoinValuationRepository:
    """
    Repository for managing coin valuations.

    Provides CRUD operations for valuation snapshots.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, valuation_id: int) -> Optional[CoinValuation]:
        """Get a valuation by ID."""
        model = self.session.get(CoinValuationModel, valuation_id)
        return self._to_domain(model) if model else None

    def get_by_coin_id(
        self,
        coin_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CoinValuation]:
        """
        Get all valuations for a coin.

        Returns valuations ordered by date desc (newest first).
        """
        models = self.session.query(CoinValuationModel).filter(
            CoinValuationModel.coin_id == coin_id
        ).order_by(desc(CoinValuationModel.valuation_date)).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def get_latest(self, coin_id: int) -> Optional[CoinValuation]:
        """Get the most recent valuation for a coin."""
        model = self.session.query(CoinValuationModel).filter(
            CoinValuationModel.coin_id == coin_id
        ).order_by(desc(CoinValuationModel.valuation_date)).first()

        return self._to_domain(model) if model else None

    def get_latest_batch(self, coin_ids: List[int]) -> Dict[int, CoinValuation]:
        """
        Get the most recent valuations for multiple coins in a single query.

        Uses a window function to efficiently fetch the latest valuation
        for each coin, avoiding N+1 queries.

        Args:
            coin_ids: List of coin IDs to get valuations for

        Returns:
            Dict mapping coin_id to its latest CoinValuation (missing coins not included)
        """
        if not coin_ids:
            return {}

        # Subquery to get max valuation_date per coin
        subquery = self.session.query(
            CoinValuationModel.coin_id,
            func.max(CoinValuationModel.valuation_date).label("max_date")
        ).filter(
            CoinValuationModel.coin_id.in_(coin_ids)
        ).group_by(CoinValuationModel.coin_id).subquery()

        # Join to get full valuation records
        models = self.session.query(CoinValuationModel).join(
            subquery,
            (CoinValuationModel.coin_id == subquery.c.coin_id) &
            (CoinValuationModel.valuation_date == subquery.c.max_date)
        ).all()

        return {
            model.coin_id: self._to_domain(model)
            for model in models
        }

    def create(self, coin_id: int, valuation: CoinValuation) -> CoinValuation:
        """Create a new valuation. Returns valuation with ID assigned."""
        model = self._to_model(valuation)
        model.id = None  # Ensure new record
        model.coin_id = coin_id

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, valuation_id: int, valuation: CoinValuation) -> Optional[CoinValuation]:
        """Update an existing valuation."""
        model = self.session.get(CoinValuationModel, valuation_id)
        if not model:
            return None

        # Update fields
        model.valuation_date = valuation.valuation_date
        model.purchase_price = valuation.purchase_price
        model.purchase_currency = valuation.purchase_currency
        model.purchase_date = valuation.purchase_date
        model.current_market_value = valuation.current_market_value
        model.value_currency = valuation.value_currency
        model.market_confidence = valuation.market_confidence
        model.comparable_count = valuation.comparable_count
        model.comparable_avg_price = valuation.comparable_avg_price
        model.comparable_date_range = valuation.comparable_date_range
        model.price_trend_6mo = valuation.price_trend_6mo
        model.price_trend_12mo = valuation.price_trend_12mo
        model.price_trend_36mo = valuation.price_trend_36mo
        model.gain_loss_usd = valuation.gain_loss_usd
        model.gain_loss_pct = valuation.gain_loss_pct
        model.valuation_method = valuation.valuation_method
        model.notes = valuation.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, valuation_id: int) -> bool:
        """Delete a valuation by ID."""
        model = self.session.get(CoinValuationModel, valuation_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def count_by_coin_id(self, coin_id: int) -> int:
        """Count valuations for a specific coin."""
        return self.session.query(CoinValuationModel).filter(
            CoinValuationModel.coin_id == coin_id
        ).count()

    def get_portfolio_summary(self) -> dict:
        """
        Calculate portfolio-wide valuation summary.

        Returns totals, averages, and gain/loss across all coins.
        """
        # Get latest valuation for each coin
        subquery = self.session.query(
            CoinValuationModel.coin_id,
            func.max(CoinValuationModel.valuation_date).label("max_date")
        ).group_by(CoinValuationModel.coin_id).subquery()

        latest_valuations = self.session.query(CoinValuationModel).join(
            subquery,
            (CoinValuationModel.coin_id == subquery.c.coin_id) &
            (CoinValuationModel.valuation_date == subquery.c.max_date)
        ).all()

        if not latest_valuations:
            return {
                "total_coins": 0,
                "total_purchase_value": Decimal("0"),
                "total_current_value": Decimal("0"),
                "total_gain_loss_usd": Decimal("0"),
                "total_gain_loss_pct": None,
            }

        total_purchase = sum(
            v.purchase_price for v in latest_valuations if v.purchase_price
        ) or Decimal("0")
        total_current = sum(
            v.current_market_value for v in latest_valuations if v.current_market_value
        ) or Decimal("0")
        total_gain_loss = total_current - total_purchase
        total_gain_loss_pct = (
            (total_gain_loss / total_purchase * 100) if total_purchase else None
        )

        return {
            "total_coins": len(latest_valuations),
            "total_purchase_value": total_purchase,
            "total_current_value": total_current,
            "total_gain_loss_usd": total_gain_loss,
            "total_gain_loss_pct": total_gain_loss_pct,
        }

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: CoinValuationModel) -> CoinValuation:
        """Convert ORM model to domain entity."""
        return CoinValuation(
            id=model.id,
            coin_id=model.coin_id,
            valuation_date=model.valuation_date,
            purchase_price=model.purchase_price,
            purchase_currency=model.purchase_currency,
            purchase_date=model.purchase_date,
            current_market_value=model.current_market_value,
            value_currency=model.value_currency or "USD",
            market_confidence=model.market_confidence,
            comparable_count=model.comparable_count,
            comparable_avg_price=model.comparable_avg_price,
            comparable_date_range=model.comparable_date_range,
            price_trend_6mo=model.price_trend_6mo,
            price_trend_12mo=model.price_trend_12mo,
            price_trend_36mo=model.price_trend_36mo,
            gain_loss_usd=model.gain_loss_usd,
            gain_loss_pct=model.gain_loss_pct,
            valuation_method=model.valuation_method,
            notes=model.notes,
            created_at=model.created_at,
        )

    def _to_model(self, valuation: CoinValuation) -> CoinValuationModel:
        """Convert domain entity to ORM model."""
        return CoinValuationModel(
            id=valuation.id,
            coin_id=valuation.coin_id,
            valuation_date=valuation.valuation_date or date.today(),
            purchase_price=valuation.purchase_price,
            purchase_currency=valuation.purchase_currency,
            purchase_date=valuation.purchase_date,
            current_market_value=valuation.current_market_value,
            value_currency=valuation.value_currency,
            market_confidence=valuation.market_confidence,
            comparable_count=valuation.comparable_count,
            comparable_avg_price=valuation.comparable_avg_price,
            comparable_date_range=valuation.comparable_date_range,
            price_trend_6mo=valuation.price_trend_6mo,
            price_trend_12mo=valuation.price_trend_12mo,
            price_trend_36mo=valuation.price_trend_36mo,
            gain_loss_usd=valuation.gain_loss_usd,
            gain_loss_pct=valuation.gain_loss_pct,
            valuation_method=valuation.valuation_method,
            notes=valuation.notes,
            created_at=valuation.created_at or datetime.now(timezone.utc),
        )
