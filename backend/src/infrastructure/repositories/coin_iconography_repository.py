"""Concrete repository implementation for coin-iconography links."""

from typing import Optional, List
from sqlalchemy.orm import Session, selectinload
import sqlalchemy as sa

from src.domain.coin import CoinIconography, CoinSide, IconographyPosition
from src.domain.repositories_iconography import ICoinIconographyRepository
from src.infrastructure.persistence.orm import CoinIconographyModel


class SqlAlchemyCoinIconographyRepository(ICoinIconographyRepository):
    """SQLAlchemy implementation of coin-iconography link repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, link_id: int) -> Optional[CoinIconography]:
        """Get link by ID with eager loading."""
        model = (
            self.session.query(CoinIconographyModel)
            .options(
                selectinload(CoinIconographyModel.coin),
                selectinload(CoinIconographyModel.composition)
            )
            .filter(CoinIconographyModel.id == link_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_coin_id(self, coin_id: int) -> List[CoinIconography]:
        """Get all iconography links for a coin."""
        models = (
            self.session.query(CoinIconographyModel)
            .options(selectinload(CoinIconographyModel.composition))
            .filter(CoinIconographyModel.coin_id == coin_id)
            .order_by(CoinIconographyModel.coin_side)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_composition_id(self, composition_id: int) -> List[CoinIconography]:
        """Get all coins using a composition."""
        models = (
            self.session.query(CoinIconographyModel)
            .options(selectinload(CoinIconographyModel.coin))
            .filter(CoinIconographyModel.composition_id == composition_id)
            .order_by(CoinIconographyModel.coin_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, link: CoinIconography) -> CoinIconography:
        """Create new coin-composition link."""
        model = self._to_model(link)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, link_id: int, link: CoinIconography) -> Optional[CoinIconography]:
        """Update existing link (side, position, notes)."""
        model = (
            self.session.query(CoinIconographyModel)
            .filter(CoinIconographyModel.id == link_id)
            .first()
        )

        if not model:
            return None

        # Update fields (coin_id and composition_id are immutable)
        model.coin_side = link.coin_side.value if link.coin_side else None
        model.position = link.position.value if link.position else None
        model.notes = link.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, link_id: int) -> bool:
        """Delete link."""
        model = (
            self.session.query(CoinIconographyModel)
            .filter(CoinIconographyModel.id == link_id)
            .first()
        )

        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def find_duplicate(self, coin_id: int, composition_id: int, coin_side: str) -> Optional[CoinIconography]:
        """Find duplicate link (coin_id, composition_id, coin_side must be unique)."""
        model = (
            self.session.query(CoinIconographyModel)
            .filter(
                CoinIconographyModel.coin_id == coin_id,
                CoinIconographyModel.composition_id == composition_id,
                CoinIconographyModel.coin_side == coin_side
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def _to_domain(self, model: CoinIconographyModel) -> CoinIconography:
        """Convert ORM model to domain entity."""
        return CoinIconography(
            id=model.id,
            coin_id=model.coin_id,
            composition_id=model.composition_id,
            coin_side=CoinSide(model.coin_side) if model.coin_side else None,
            position=IconographyPosition(model.position) if model.position else None,
            notes=model.notes
        )

    def _to_model(self, link: CoinIconography) -> CoinIconographyModel:
        """Convert domain entity to ORM model."""
        return CoinIconographyModel(
            id=link.id,
            coin_id=link.coin_id,
            composition_id=link.composition_id,
            coin_side=link.coin_side.value if link.coin_side else None,
            position=link.position.value if link.position else None,
            notes=link.notes
        )
