"""
ValuationService - Calculate coin valuations and portfolio summaries.

Uses market data to estimate current values for coins and calculate
portfolio-level performance metrics.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, List

from src.domain.coin import CoinValuation, MarketPrice
from src.domain.repositories import IMarketPriceRepository, ICoinValuationRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ValuationResult:
    """Result of a single coin valuation calculation."""
    success: bool
    valuation: Optional[CoinValuation] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class PortfolioSummary:
    """Aggregate portfolio valuation summary."""
    total_value: Decimal
    total_cost: Decimal
    gain_loss_usd: Decimal
    gain_loss_pct: Optional[Decimal]
    coin_count: int
    valued_count: int


class ValuationService:
    """
    Service for calculating coin valuations and portfolio performance.

    Uses market price data to estimate current values based on comparable
    sales and price trends. Supports grade-adjusted valuations.
    """

    def __init__(
        self,
        market_repo: IMarketPriceRepository,
        valuation_repo: ICoinValuationRepository,
    ):
        self._market_repo = market_repo
        self._valuation_repo = valuation_repo

    def calculate_valuation(
        self,
        coin_id: int,
        attribution_key: str,
        grade_numeric: Optional[int] = None,
        purchase_price: Optional[Decimal] = None,
        purchase_currency: Optional[str] = None,
        purchase_date: Optional[date] = None,
    ) -> ValuationResult:
        """
        Calculate current market value for a coin based on comparable sales.

        Args:
            coin_id: ID of the coin to value
            attribution_key: Key for looking up market price data
            grade_numeric: Numeric grade (0-70 scale) for grade adjustment
            purchase_price: Original purchase price for gain/loss calculation
            purchase_currency: Currency of purchase price
            purchase_date: Date of purchase

        Returns:
            ValuationResult with success status and valuation data
        """
        logger.debug("Calculating valuation for coin %d with attribution '%s'", coin_id, attribution_key)

        # Look up market data for this attribution
        market_price = self._market_repo.get_by_attribution_key(attribution_key)

        if not market_price:
            logger.info("No market data found for attribution: %s", attribution_key)
            return ValuationResult(
                success=False,
                error=f"No market data found for attribution: {attribution_key}",
            )

        # Determine base price by grade tier
        base_price = self._select_base_price(market_price, grade_numeric)

        if base_price is None:
            return ValuationResult(
                success=False,
                error="No price data available for this grade tier",
            )

        # Apply grade adjustment
        current_value = self._adjust_for_grade(base_price, grade_numeric)

        # Calculate gain/loss if purchase price available
        gain_loss_usd: Optional[Decimal] = None
        gain_loss_pct: Optional[Decimal] = None

        if purchase_price is not None and purchase_price > 0:
            gain_loss_usd = current_value - purchase_price
            gain_loss_pct = (gain_loss_usd / purchase_price) * 100

        # Determine market confidence based on data points
        data_count = market_price.data_point_count or 0
        if data_count >= 20:
            confidence = "strong"
        elif data_count >= 10:
            confidence = "high"
        elif data_count >= 5:
            confidence = "medium"
        else:
            confidence = "low"

        # Create valuation record
        valuation = CoinValuation(
            coin_id=coin_id,
            valuation_date=date.today(),
            purchase_price=purchase_price,
            purchase_currency=purchase_currency,
            purchase_date=purchase_date,
            current_market_value=current_value,
            value_currency="USD",
            market_confidence=confidence,
            comparable_count=data_count,
            comparable_avg_price=market_price.median_price,
            gain_loss_usd=gain_loss_usd,
            gain_loss_pct=gain_loss_pct,
            valuation_method="comparable_sales",
            created_at=datetime.now(timezone.utc),
        )

        # Persist the valuation
        saved = self._valuation_repo.create(coin_id, valuation)

        return ValuationResult(success=True, valuation=saved)

    def get_portfolio_summary(self, coin_ids: List[int]) -> PortfolioSummary:
        """
        Calculate aggregate portfolio value and performance.

        Uses batch query to avoid N+1 database queries.

        Args:
            coin_ids: List of coin IDs to include in summary

        Returns:
            PortfolioSummary with aggregate metrics
        """
        logger.debug("Calculating portfolio summary for %d coins", len(coin_ids))

        if not coin_ids:
            logger.debug("No coin IDs provided, returning empty summary")
            return PortfolioSummary(
                total_value=Decimal("0"),
                total_cost=Decimal("0"),
                gain_loss_usd=Decimal("0"),
                gain_loss_pct=None,
                coin_count=0,
                valued_count=0,
            )

        # Use batch query to get all latest valuations in one DB call
        latest_valuations = self._valuation_repo.get_latest_batch(coin_ids)

        total_value = Decimal("0")
        total_cost = Decimal("0")
        valued_count = len(latest_valuations)

        for coin_id, valuation in latest_valuations.items():
            if valuation.current_market_value:
                total_value += valuation.current_market_value
            if valuation.purchase_price:
                total_cost += valuation.purchase_price

        gain_loss_usd = total_value - total_cost
        gain_loss_pct = (
            (gain_loss_usd / total_cost * 100) if total_cost > 0 else None
        )

        logger.info(
            "Portfolio summary: %d/%d coins valued, total value $%.2f, gain/loss $%.2f",
            valued_count, len(coin_ids), total_value, gain_loss_usd
        )

        return PortfolioSummary(
            total_value=total_value,
            total_cost=total_cost,
            gain_loss_usd=gain_loss_usd,
            gain_loss_pct=gain_loss_pct,
            coin_count=len(coin_ids),
            valued_count=valued_count,
        )

    def _select_base_price(
        self,
        market_price: MarketPrice,
        grade_numeric: Optional[int],
    ) -> Optional[Decimal]:
        """
        Select the appropriate base price tier for the grade.

        Supports the full range of grades commonly seen in ancient coins:
        - Good/Very Good (4-10): Use median as fallback
        - Fine (12-15): Use VF price with discount
        - Very Fine (20-35): Use VF price
        - Extremely Fine (40-45): Use EF price
        - About Uncirculated (50-58): Use AU price
        - Mint State (60-70): Use MS price
        """
        if grade_numeric is None:
            # Default to VF if no grade specified (common collector grade for ancients)
            return market_price.avg_price_vf or market_price.median_price

        # Map numeric grade to price tier (expanded for ancient coins)
        if grade_numeric >= 60:  # Mint State
            return market_price.avg_price_ms or market_price.avg_price_au or market_price.avg_price_ef
        elif grade_numeric >= 50:  # About Uncirculated
            return market_price.avg_price_au or market_price.avg_price_ef or market_price.avg_price_vf
        elif grade_numeric >= 40:  # Extremely Fine
            return market_price.avg_price_ef or market_price.avg_price_vf
        elif grade_numeric >= 20:  # Very Fine
            return market_price.avg_price_vf or market_price.median_price
        elif grade_numeric >= 12:  # Fine
            # Fine is typically 60-70% of VF price
            vf_price = market_price.avg_price_vf or market_price.median_price
            return vf_price * Decimal("0.65") if vf_price else market_price.median_price
        else:  # Good/Very Good and below
            # G/VG is typically 40-50% of VF price
            vf_price = market_price.avg_price_vf or market_price.median_price
            return vf_price * Decimal("0.45") if vf_price else market_price.median_price

    def _adjust_for_grade(
        self,
        base_price: Decimal,
        grade_numeric: Optional[int],
    ) -> Decimal:
        """
        Apply fine-grained adjustment within grade tier.

        Note: For ancient coins, MS grade premiums are flattened compared to
        modern coins. MS-67+ ancients are extremely rare, so the premium
        curve is much gentler. MS-70 ancients essentially don't exist.
        """
        if grade_numeric is None:
            return base_price

        # For MS grades, apply premium for higher numbers
        # Flattened for ancient coins (MS-67+ is extremely rare for ancients)
        if grade_numeric >= 60:
            premium = Decimal("1.0")
            if grade_numeric >= 63:  # Choice MS
                premium = Decimal("1.15")
            if grade_numeric >= 65:  # Gem MS
                premium = Decimal("1.35")
            if grade_numeric >= 67:  # Superb (very rare for ancients)
                premium = Decimal("1.6")
            if grade_numeric >= 69:  # Near-perfect (essentially nonexistent for ancients)
                premium = Decimal("2.0")
            # MS-70 premium capped at 2.5x for ancients (vs 10x for modern coins)
            # since a true MS-70 ancient coin is essentially theoretical
            if grade_numeric == 70:
                premium = Decimal("2.5")
            return base_price * premium

        # For circulated grades, minor adjustment within tier
        adjustment = Decimal(str(1 + (grade_numeric - 30) * 0.02))
        return base_price * max(Decimal("0.5"), min(Decimal("1.5"), adjustment))
