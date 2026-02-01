"""Concrete repository implementation for iconography elements."""

from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
import sqlalchemy as sa

from src.domain.coin import IconographyElement, IconographyCategory
from src.domain.repositories_iconography import IIconographyElementRepository
from src.infrastructure.persistence.orm import IconographyElementModel


class SqlAlchemyIconographyElementRepository(IIconographyElementRepository):
    """SQLAlchemy implementation of iconography element repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, element_id: int) -> Optional[IconographyElement]:
        """Get element by ID with eager loading."""
        model = (
            self.session.query(IconographyElementModel)
            .options(selectinload(IconographyElementModel.composition_elements))
            .filter(IconographyElementModel.id == element_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_canonical_name(self, name: str) -> Optional[IconographyElement]:
        """Get element by canonical name."""
        model = (
            self.session.query(IconographyElementModel)
            .filter(IconographyElementModel.canonical_name == name)
            .first()
        )
        return self._to_domain(model) if model else None

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyElement]:
        """List all elements with pagination."""
        models = (
            self.session.query(IconographyElementModel)
            .order_by(IconographyElementModel.canonical_name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_category(self, category: str, skip: int = 0, limit: int = 100) -> List[IconographyElement]:
        """List elements by category with pagination."""
        models = (
            self.session.query(IconographyElementModel)
            .filter(IconographyElementModel.category == category)
            .order_by(IconographyElementModel.canonical_name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def search(self, query: str, category: Optional[str] = None) -> List[IconographyElement]:
        """Search elements by name or aliases."""
        q = self.session.query(IconographyElementModel).filter(
            sa.or_(
                IconographyElementModel.canonical_name.ilike(f'%{query}%'),
                IconographyElementModel.display_name.ilike(f'%{query}%'),
                IconographyElementModel.aliases.ilike(f'%{query}%')
            )
        )

        if category:
            q = q.filter(IconographyElementModel.category == category)

        models = q.order_by(IconographyElementModel.canonical_name).limit(50).all()
        return [self._to_domain(m) for m in models]

    def create(self, element: IconographyElement) -> IconographyElement:
        """Create new element."""
        model = self._to_model(element)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, element_id: int, element: IconographyElement) -> Optional[IconographyElement]:
        """Update existing element."""
        model = (
            self.session.query(IconographyElementModel)
            .filter(IconographyElementModel.id == element_id)
            .first()
        )

        if not model:
            return None

        # Update fields
        model.canonical_name = element.canonical_name
        model.display_name = element.display_name
        model.category = element.category.value if element.category else None
        model.description = element.description
        model.aliases = element.aliases  # JSON string
        # Don't update usage_count - managed by increment/decrement

        self.session.flush()
        return self._to_domain(model)

    def delete(self, element_id: int) -> bool:
        """Delete element."""
        model = (
            self.session.query(IconographyElementModel)
            .filter(IconographyElementModel.id == element_id)
            .first()
        )

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def increment_usage(self, element_id: int) -> None:
        """Atomically increment usage count (prevents race conditions)."""
        self.session.execute(
            sa.update(IconographyElementModel)
            .where(IconographyElementModel.id == element_id)
            .values(usage_count=IconographyElementModel.usage_count + 1)
        )
        self.session.flush()

    def decrement_usage(self, element_id: int) -> None:
        """Atomically decrement usage count (prevents race conditions)."""
        self.session.execute(
            sa.update(IconographyElementModel)
            .where(IconographyElementModel.id == element_id)
            .values(usage_count=sa.func.max(0, IconographyElementModel.usage_count - 1))
        )
        self.session.flush()

    def _to_domain(self, model: IconographyElementModel) -> IconographyElement:
        """Convert ORM model to domain entity."""
        import json

        # Parse aliases JSON
        aliases = []
        if model.aliases:
            try:
                aliases = json.loads(model.aliases)
            except (json.JSONDecodeError, TypeError):
                aliases = []

        return IconographyElement(
            id=model.id,
            canonical_name=model.canonical_name,
            display_name=model.display_name or "",
            category=IconographyCategory(model.category) if model.category else None,
            description=model.description,
            aliases=aliases,
            usage_count=model.usage_count
        )

    def _to_model(self, element: IconographyElement) -> IconographyElementModel:
        """Convert domain entity to ORM model."""
        import json

        return IconographyElementModel(
            id=element.id,
            canonical_name=element.canonical_name,
            display_name=element.display_name,
            category=element.category.value if element.category else None,
            description=element.description,
            aliases=json.dumps(element.aliases) if element.aliases else None,
            usage_count=element.usage_count
        )
