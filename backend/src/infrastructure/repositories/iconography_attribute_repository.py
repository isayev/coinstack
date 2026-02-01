"""Concrete repository implementation for iconography attributes."""

from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
import sqlalchemy as sa

from src.domain.coin import IconographyAttribute, AttributeType
from src.domain.repositories_iconography import IIconographyAttributeRepository
from src.infrastructure.persistence.orm import IconographyAttributeModel


class SqlAlchemyIconographyAttributeRepository(IIconographyAttributeRepository):
    """SQLAlchemy implementation of iconography attribute repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, attribute_id: int) -> Optional[IconographyAttribute]:
        """Get attribute by ID with eager loading."""
        model = (
            self.session.query(IconographyAttributeModel)
            .options(selectinload(IconographyAttributeModel.element_attributes))
            .filter(IconographyAttributeModel.id == attribute_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def list_all(self, skip: int = 0, limit: int = 100) -> List[IconographyAttribute]:
        """List all attributes with pagination."""
        models = (
            self.session.query(IconographyAttributeModel)
            .order_by(
                IconographyAttributeModel.attribute_type,
                IconographyAttributeModel.attribute_value
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_type(self, attribute_type: str, skip: int = 0, limit: int = 100) -> List[IconographyAttribute]:
        """List attributes by type with pagination."""
        models = (
            self.session.query(IconographyAttributeModel)
            .filter(IconographyAttributeModel.attribute_type == attribute_type)
            .order_by(IconographyAttributeModel.attribute_value)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def search(self, query: str, attribute_type: Optional[str] = None) -> List[IconographyAttribute]:
        """Search attributes by value or display name."""
        q = self.session.query(IconographyAttributeModel).filter(
            sa.or_(
                IconographyAttributeModel.attribute_value.ilike(f'%{query}%'),
                IconographyAttributeModel.display_name.ilike(f'%{query}%')
            )
        )

        if attribute_type:
            q = q.filter(IconographyAttributeModel.attribute_type == attribute_type)

        models = q.order_by(
            IconographyAttributeModel.attribute_type,
            IconographyAttributeModel.attribute_value
        ).limit(50).all()
        return [self._to_domain(m) for m in models]

    def create(self, attribute: IconographyAttribute) -> IconographyAttribute:
        """Create new attribute."""
        model = self._to_model(attribute)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, attribute_id: int, attribute: IconographyAttribute) -> Optional[IconographyAttribute]:
        """Update existing attribute."""
        model = (
            self.session.query(IconographyAttributeModel)
            .filter(IconographyAttributeModel.id == attribute_id)
            .first()
        )

        if not model:
            return None

        # Update fields
        model.attribute_type = attribute.attribute_type.value if attribute.attribute_type else None
        model.attribute_value = attribute.attribute_value
        model.display_name = attribute.display_name
        model.description = attribute.description

        self.session.flush()
        return self._to_domain(model)

    def delete(self, attribute_id: int) -> bool:
        """Delete attribute."""
        model = (
            self.session.query(IconographyAttributeModel)
            .filter(IconographyAttributeModel.id == attribute_id)
            .first()
        )

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def _to_domain(self, model: IconographyAttributeModel) -> IconographyAttribute:
        """Convert ORM model to domain entity."""
        return IconographyAttribute(
            id=model.id,
            attribute_type=AttributeType(model.attribute_type) if model.attribute_type else None,
            attribute_value=model.attribute_value,
            display_name=model.display_name or "",
            description=model.description
        )

    def _to_model(self, attribute: IconographyAttribute) -> IconographyAttributeModel:
        """Convert domain entity to ORM model."""
        return IconographyAttributeModel(
            id=attribute.id,
            attribute_type=attribute.attribute_type.value if attribute.attribute_type else None,
            attribute_value=attribute.attribute_value,
            display_name=attribute.display_name,
            description=attribute.description
        )
