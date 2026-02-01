"""Concrete repository implementation for iconography compositions."""

from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
import sqlalchemy as sa

from src.domain.coin import IconographyComposition, CompositionCategory
from src.domain.repositories_iconography import IIconographyCompositionRepository
from src.infrastructure.persistence.orm import (
    IconographyCompositionModel,
    CompositionElementModel,
    CoinIconographyModel
)


class SqlAlchemyIconographyCompositionRepository(IIconographyCompositionRepository):
    """SQLAlchemy implementation of iconography composition repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, composition_id: int) -> Optional[IconographyComposition]:
        """Get composition by ID with eager loading of elements and attributes."""
        model = (
            self.session.query(IconographyCompositionModel)
            .options(
                selectinload(IconographyCompositionModel.composition_elements)
                .selectinload(CompositionElementModel.element),
                selectinload(IconographyCompositionModel.composition_elements)
                .selectinload(CompositionElementModel.element_attributes)
            )
            .filter(IconographyCompositionModel.id == composition_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyComposition]:
        """List all compositions with pagination."""
        models = (
            self.session.query(IconographyCompositionModel)
            .order_by(IconographyCompositionModel.composition_name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[IconographyComposition]:
        """List compositions by category with pagination."""
        models = (
            self.session.query(IconographyCompositionModel)
            .filter(IconographyCompositionModel.category == category)
            .order_by(IconographyCompositionModel.composition_name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def search(self, query: str, category: Optional[str] = None) -> List[IconographyComposition]:
        """Search compositions by name or canonical description."""
        q = self.session.query(IconographyCompositionModel).filter(
            sa.or_(
                IconographyCompositionModel.composition_name.ilike(f'%{query}%'),
                IconographyCompositionModel.canonical_description.ilike(f'%{query}%')
            )
        )

        if category:
            q = q.filter(IconographyCompositionModel.category == category)

        models = q.order_by(IconographyCompositionModel.composition_name).limit(50).all()
        return [self._to_domain(m) for m in models]

    def create(self, composition: IconographyComposition) -> IconographyComposition:
        """Create new composition (elements/attributes handled separately for now)."""
        model = self._to_model(composition)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, composition_id: int, composition: IconographyComposition) -> Optional[IconographyComposition]:
        """Update existing composition."""
        model = (
            self.session.query(IconographyCompositionModel)
            .filter(IconographyCompositionModel.id == composition_id)
            .first()
        )

        if not model:
            return None

        # Update fields
        model.composition_name = composition.composition_name
        model.canonical_description = composition.canonical_description
        model.category = composition.category.value if composition.category else None
        model.composition_json = composition.composition_json
        model.reference_system = composition.reference_system
        model.reference_numbers = composition.reference_numbers  # JSON string
        # Don't update usage_count - managed by increment/decrement

        self.session.flush()
        return self._to_domain(model)

    def delete(self, composition_id: int) -> bool:
        """Delete composition."""
        model = (
            self.session.query(IconographyCompositionModel)
            .filter(IconographyCompositionModel.id == composition_id)
            .first()
        )

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def increment_usage(self, composition_id: int) -> None:
        """Atomically increment usage count (prevents race conditions)."""
        self.session.execute(
            sa.update(IconographyCompositionModel)
            .where(IconographyCompositionModel.id == composition_id)
            .values(usage_count=IconographyCompositionModel.usage_count + 1)
        )
        self.session.flush()

    def decrement_usage(self, composition_id: int) -> None:
        """Atomically decrement usage count (prevents race conditions)."""
        self.session.execute(
            sa.update(IconographyCompositionModel)
            .where(IconographyCompositionModel.id == composition_id)
            .values(usage_count=sa.func.max(0, IconographyCompositionModel.usage_count - 1))
        )
        self.session.flush()

    def get_coins_using_composition(self, composition_id: int) -> List[int]:
        """Get list of coin IDs using this composition."""
        coin_ids = (
            self.session.query(CoinIconographyModel.coin_id)
            .filter(CoinIconographyModel.composition_id == composition_id)
            .distinct()
            .all()
        )
        return [coin_id for (coin_id,) in coin_ids]

    def _to_domain(self, model: IconographyCompositionModel) -> IconographyComposition:
        """Convert ORM model to domain entity."""
        import json

        # Parse reference_numbers JSON
        reference_numbers = []
        if model.reference_numbers:
            try:
                reference_numbers = json.loads(model.reference_numbers)
            except (json.JSONDecodeError, TypeError):
                reference_numbers = []

        return IconographyComposition(
            id=model.id,
            composition_name=model.composition_name,
            canonical_description=model.canonical_description,
            category=CompositionCategory(model.category) if model.category else None,
            composition_json=model.composition_json,
            reference_system=model.reference_system,
            reference_numbers=reference_numbers,
            usage_count=model.usage_count,
            elements=[]  # Elements loaded separately if needed
        )

    def _to_model(self, composition: IconographyComposition) -> IconographyCompositionModel:
        """Convert domain entity to ORM model."""
        import json

        return IconographyCompositionModel(
            id=composition.id,
            composition_name=composition.composition_name,
            canonical_description=composition.canonical_description,
            category=composition.category.value if composition.category else None,
            composition_json=composition.composition_json,
            reference_system=composition.reference_system,
            reference_numbers=json.dumps(composition.reference_numbers) if composition.reference_numbers else None,
            usage_count=composition.usage_count
        )
