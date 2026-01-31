"""
Price Alert Repository Implementation.

Handles persistence of user alert configurations.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import PriceAlert
from src.infrastructure.persistence.orm import PriceAlertModel


class SqlAlchemyPriceAlertRepository:
    """
    Repository for managing price alerts.

    Provides CRUD operations for alert configurations.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, alert_id: int) -> Optional[PriceAlert]:
        """Get an alert by ID."""
        model = self.session.get(PriceAlertModel, alert_id)
        return self._to_domain(model) if model else None

    def get_active(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceAlert]:
        """Get all active alerts."""
        models = self.session.query(PriceAlertModel).filter(
            PriceAlertModel.status == "active"
        ).order_by(desc(PriceAlertModel.created_at)).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def get_by_coin_id(self, coin_id: int) -> List[PriceAlert]:
        """Get all alerts for a specific coin."""
        models = self.session.query(PriceAlertModel).filter(
            PriceAlertModel.coin_id == coin_id
        ).order_by(desc(PriceAlertModel.created_at)).all()

        return [self._to_domain(m) for m in models]

    def get_by_wishlist_item_id(self, wishlist_item_id: int) -> List[PriceAlert]:
        """Get all alerts for a wishlist item."""
        models = self.session.query(PriceAlertModel).filter(
            PriceAlertModel.wishlist_item_id == wishlist_item_id
        ).order_by(desc(PriceAlertModel.created_at)).all()

        return [self._to_domain(m) for m in models]

    def list_all(
        self,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PriceAlert]:
        """
        List alerts with optional filters.

        Returns alerts ordered by created_at desc.
        """
        query = self.session.query(PriceAlertModel)

        if status:
            query = query.filter(PriceAlertModel.status == status)
        if trigger_type:
            query = query.filter(PriceAlertModel.trigger_type == trigger_type)

        query = query.order_by(desc(PriceAlertModel.created_at))
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def count(self, status: Optional[str] = None) -> int:
        """Count alerts matching filters."""
        query = self.session.query(PriceAlertModel)

        if status:
            query = query.filter(PriceAlertModel.status == status)

        return query.count()

    def create(self, alert: PriceAlert) -> PriceAlert:
        """Create a new alert. Returns alert with ID assigned."""
        model = self._to_model(alert)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, alert_id: int, alert: PriceAlert) -> Optional[PriceAlert]:
        """Update an existing alert."""
        model = self.session.get(PriceAlertModel, alert_id)
        if not model:
            return None

        # Update fields
        model.attribution_key = alert.attribution_key
        model.coin_id = alert.coin_id
        model.wishlist_item_id = alert.wishlist_item_id
        model.trigger_type = alert.trigger_type
        model.threshold_value = alert.threshold_value
        model.threshold_pct = alert.threshold_pct
        model.threshold_grade = alert.threshold_grade
        model.status = alert.status
        model.expires_at = alert.expires_at
        model.notification_channel = alert.notification_channel
        model.cooldown_hours = alert.cooldown_hours
        model.notes = alert.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, alert_id: int) -> bool:
        """Delete an alert by ID."""
        model = self.session.get(PriceAlertModel, alert_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def trigger(self, alert_id: int) -> Optional[PriceAlert]:
        """Mark an alert as triggered."""
        model = self.session.get(PriceAlertModel, alert_id)
        if not model:
            return None

        now = datetime.now(timezone.utc)
        model.status = "triggered"
        model.triggered_at = now
        model.last_triggered_at = now
        model.notification_sent = True
        model.notification_sent_at = now

        self.session.flush()
        return self._to_domain(model)

    def pause(self, alert_id: int) -> Optional[PriceAlert]:
        """Pause an alert."""
        model = self.session.get(PriceAlertModel, alert_id)
        if not model:
            return None

        model.status = "paused"

        self.session.flush()
        return self._to_domain(model)

    def reactivate(self, alert_id: int) -> Optional[PriceAlert]:
        """Reactivate a paused alert."""
        model = self.session.get(PriceAlertModel, alert_id)
        if not model:
            return None

        model.status = "active"
        model.triggered_at = None
        model.notification_sent = False
        model.notification_sent_at = None

        self.session.flush()
        return self._to_domain(model)

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: PriceAlertModel) -> PriceAlert:
        """Convert ORM model to domain entity."""
        return PriceAlert(
            id=model.id,
            attribution_key=model.attribution_key,
            coin_id=model.coin_id,
            wishlist_item_id=model.wishlist_item_id,
            trigger_type=model.trigger_type,
            threshold_value=model.threshold_value,
            threshold_pct=model.threshold_pct,
            threshold_grade=model.threshold_grade,
            status=model.status or "active",
            created_at=model.created_at,
            triggered_at=model.triggered_at,
            expires_at=model.expires_at,
            notification_sent=model.notification_sent or False,
            notification_sent_at=model.notification_sent_at,
            notification_channel=model.notification_channel,
            cooldown_hours=model.cooldown_hours or 24,
            last_triggered_at=model.last_triggered_at,
            notes=model.notes,
        )

    def _to_model(self, alert: PriceAlert) -> PriceAlertModel:
        """Convert domain entity to ORM model."""
        return PriceAlertModel(
            id=alert.id,
            attribution_key=alert.attribution_key,
            coin_id=alert.coin_id,
            wishlist_item_id=alert.wishlist_item_id,
            trigger_type=alert.trigger_type,
            threshold_value=alert.threshold_value,
            threshold_pct=alert.threshold_pct,
            threshold_grade=alert.threshold_grade,
            status=alert.status,
            created_at=alert.created_at or datetime.now(timezone.utc),
            triggered_at=alert.triggered_at,
            expires_at=alert.expires_at,
            notification_sent=alert.notification_sent,
            notification_sent_at=alert.notification_sent_at,
            notification_channel=alert.notification_channel,
            cooldown_hours=alert.cooldown_hours,
            last_triggered_at=alert.last_triggered_at,
            notes=alert.notes,
        )
