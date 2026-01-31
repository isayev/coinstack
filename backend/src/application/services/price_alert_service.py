"""
PriceAlertService - Monitor price conditions and trigger alerts.

Checks price alerts against current market data and manages
notification cooldowns to prevent alert fatigue.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List

from src.domain.coin import PriceAlert, MarketPrice
from src.domain.repositories import IPriceAlertRepository, IMarketPriceRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AlertCheckResult:
    """Result of checking a single price alert."""
    alert_id: int
    triggered: bool
    reason: Optional[str] = None
    current_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None


class PriceAlertService:
    """
    Service for monitoring price alerts and triggering notifications.

    Supports multiple trigger types:
    - price_below: Current price drops below threshold
    - price_above: Current price rises above threshold
    - price_change_pct: Price changes by percentage threshold
    - new_listing: New items appear matching criteria
    - auction_soon: Auction ending within time threshold

    Implements cooldown to prevent repeated alerts for the same condition.
    """

    # Default cooldown period in hours if not specified on alert
    DEFAULT_COOLDOWN_HOURS = 24

    def __init__(
        self,
        alert_repo: IPriceAlertRepository,
        market_repo: IMarketPriceRepository,
    ):
        self._alert_repo = alert_repo
        self._market_repo = market_repo

    def check_alerts(self) -> List[AlertCheckResult]:
        """
        Check all active alerts against current market data.

        Returns:
            List of AlertCheckResult for each active alert
        """
        active_alerts = self._alert_repo.get_active()
        results: List[AlertCheckResult] = []

        for alert in active_alerts:
            result = self._check_single_alert(alert)
            results.append(result)

            # Trigger if conditions met and not in cooldown
            if result.triggered and self.should_notify(alert):
                self.trigger_alert(alert.id, result.reason or "Alert condition met")

        return results

    def check_alerts_for_coin(self, coin_id: int) -> List[AlertCheckResult]:
        """
        Check alerts for a specific coin.

        Args:
            coin_id: ID of the coin to check alerts for

        Returns:
            List of AlertCheckResult for alerts on this coin
        """
        alerts = self._alert_repo.get_by_coin_id(coin_id)
        results: List[AlertCheckResult] = []

        for alert in alerts:
            if alert.status != "active":
                continue

            result = self._check_single_alert(alert)
            results.append(result)

            if result.triggered and self.should_notify(alert):
                self.trigger_alert(alert.id, result.reason or "Alert condition met")

        return results

    def trigger_alert(self, alert_id: int, reason: str) -> Optional[PriceAlert]:
        """
        Mark an alert as triggered and update timestamps.

        Args:
            alert_id: ID of the alert to trigger
            reason: Human-readable reason for the trigger (logged for audit)

        Returns:
            Updated PriceAlert if successful, None if not found
        """
        logger.info(f"Triggering alert {alert_id}: {reason}")
        return self._alert_repo.trigger(alert_id)

    def should_notify(self, alert: PriceAlert) -> bool:
        """
        Check if an alert is outside its cooldown period.

        Args:
            alert: The alert to check

        Returns:
            True if notification should be sent, False if in cooldown
        """
        if alert.last_triggered_at is None:
            return True

        cooldown_hours = alert.cooldown_hours or self.DEFAULT_COOLDOWN_HOURS
        cooldown_end = alert.last_triggered_at + timedelta(hours=cooldown_hours)

        return datetime.now(timezone.utc) >= cooldown_end

    def _check_single_alert(self, alert: PriceAlert) -> AlertCheckResult:
        """
        Check a single alert against current market conditions.

        Args:
            alert: The alert to check

        Returns:
            AlertCheckResult with triggered status and details
        """
        # Skip expired alerts
        if alert.expires_at and datetime.now(timezone.utc) > alert.expires_at:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="Alert expired",
            )

        # Get market data
        if not alert.attribution_key:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No attribution key configured",
            )

        market_price = self._market_repo.get_by_attribution_key(alert.attribution_key)

        if not market_price:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No market data available",
            )

        # Get current price (use median as representative)
        current_price = market_price.median_price
        if current_price is None:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No price data available",
            )

        # Check based on trigger type
        trigger_type = alert.trigger_type

        if trigger_type == "price_below":
            return self._check_price_below(alert, current_price)
        elif trigger_type == "price_above":
            return self._check_price_above(alert, current_price)
        elif trigger_type == "price_change_pct":
            return self._check_price_change_pct(alert, market_price)
        elif trigger_type == "new_listing":
            # New listing detection requires external data source
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="New listing check requires external scan",
            )
        elif trigger_type == "auction_soon":
            # Auction timing requires external auction data
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="Auction timing check requires external scan",
            )
        else:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason=f"Unknown trigger type: {trigger_type}",
            )

    def _check_price_below(
        self,
        alert: PriceAlert,
        current_price: Decimal,
    ) -> AlertCheckResult:
        """Check if current price is below threshold."""
        if alert.threshold_value is None:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No threshold value configured",
            )

        if current_price < alert.threshold_value:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=True,
                reason=f"Price ${current_price} is below threshold ${alert.threshold_value}",
                current_value=current_price,
                threshold_value=alert.threshold_value,
            )

        return AlertCheckResult(
            alert_id=alert.id,
            triggered=False,
            current_value=current_price,
            threshold_value=alert.threshold_value,
        )

    def _check_price_above(
        self,
        alert: PriceAlert,
        current_price: Decimal,
    ) -> AlertCheckResult:
        """Check if current price is above threshold."""
        if alert.threshold_value is None:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No threshold value configured",
            )

        if current_price > alert.threshold_value:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=True,
                reason=f"Price ${current_price} is above threshold ${alert.threshold_value}",
                current_value=current_price,
                threshold_value=alert.threshold_value,
            )

        return AlertCheckResult(
            alert_id=alert.id,
            triggered=False,
            current_value=current_price,
            threshold_value=alert.threshold_value,
        )

    def _check_price_change_pct(
        self,
        alert: PriceAlert,
        market_price: MarketPrice,
    ) -> AlertCheckResult:
        """Check if price has changed by percentage threshold."""
        if alert.threshold_pct is None:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="No percentage threshold configured",
            )

        # Use min/max seen to calculate range
        if market_price.min_price_seen is None or market_price.max_price_seen is None:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="Insufficient price history for percentage calculation",
            )

        if market_price.min_price_seen == 0:
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=False,
                reason="Invalid minimum price",
            )

        price_range_pct = (
            (market_price.max_price_seen - market_price.min_price_seen)
            / market_price.min_price_seen
            * 100
        )

        if abs(price_range_pct) >= abs(alert.threshold_pct):
            return AlertCheckResult(
                alert_id=alert.id,
                triggered=True,
                reason=f"Price range {price_range_pct:.1f}% exceeds threshold {alert.threshold_pct}%",
                current_value=market_price.median_price,
                threshold_value=alert.threshold_pct,
            )

        return AlertCheckResult(
            alert_id=alert.id,
            triggered=False,
            current_value=market_price.median_price,
            threshold_value=alert.threshold_pct,
        )
