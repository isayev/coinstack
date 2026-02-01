"""
Mapper for Countermark domain entity <-> ORM model conversion.

Phase 1.5b: Countermark System
"""
import logging
from src.domain.coin import Countermark, CountermarkType, CountermarkPosition, CountermarkCondition, PunchShape
from src.infrastructure.persistence.orm import CountermarkModel

logger = logging.getLogger(__name__)


class CountermarkMapper:
    """Handles mapping between Countermark domain entity and ORM model."""

    @staticmethod
    def to_domain(model: CountermarkModel) -> Countermark:
        """Convert ORM model to domain entity."""
        # Parse enums safely with logging for invalid values
        countermark_type = None
        if model.countermark_type:
            try:
                countermark_type = CountermarkType(model.countermark_type)
            except ValueError:
                logger.warning(
                    "Invalid countermark_type '%s' for countermark id=%s, defaulting to None",
                    model.countermark_type, model.id
                )

        position = None
        if model.position:
            try:
                position = CountermarkPosition(model.position)
            except ValueError:
                logger.warning(
                    "Invalid position '%s' for countermark id=%s, defaulting to None",
                    model.position, model.id
                )

        condition = None
        if model.condition:
            try:
                condition = CountermarkCondition(model.condition)
            except ValueError:
                logger.warning(
                    "Invalid condition '%s' for countermark id=%s, defaulting to None",
                    model.condition, model.id
                )

        punch_shape = None
        if model.punch_shape:
            try:
                punch_shape = PunchShape(model.punch_shape)
            except ValueError:
                logger.warning(
                    "Invalid punch_shape '%s' for countermark id=%s, defaulting to None",
                    model.punch_shape, model.id
                )

        return Countermark(
            id=model.id,
            coin_id=model.coin_id,
            countermark_type=countermark_type,
            position=position,
            condition=condition,
            punch_shape=punch_shape,
            description=model.description,
            authority=model.authority,
            reference=model.reference,
            date_applied=model.date_applied,
            notes=model.notes,
        )

    @staticmethod
    def to_model(countermark: Countermark, coin_id: int | None = None) -> CountermarkModel:
        """Convert domain entity to ORM model."""
        return CountermarkModel(
            id=countermark.id,
            coin_id=coin_id or countermark.coin_id,
            # Core required fields (with defaults for database constraints)
            countermark_type=countermark.countermark_type.value if countermark.countermark_type else "uncertain",
            description=countermark.description or "",
            placement=countermark.position.value if countermark.position else "obverse",  # Map position -> placement
            # Optional fields
            position=countermark.position.value if countermark.position else None,
            condition=countermark.condition.value if countermark.condition else None,
            punch_shape=countermark.punch_shape.value if countermark.punch_shape else None,
            authority=countermark.authority,
            reference=countermark.reference,
            date_applied=countermark.date_applied,
            notes=countermark.notes,
        )
