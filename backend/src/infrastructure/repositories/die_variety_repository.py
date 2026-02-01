"""Concrete repository implementation for die varieties."""

from typing import Optional
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import DieVariety
from src.domain.repositories_die_study import IDieVarietyRepository
from src.infrastructure.persistence.orm import DieVarietyModel


class SqlAlchemyDieVarietyRepository(IDieVarietyRepository):
    """SQLAlchemy implementation of die variety repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, variety_id: int) -> Optional[DieVariety]:
        """Get die variety by ID with eager loading."""
        model = (
            self.session.query(DieVarietyModel)
            .options(
                selectinload(DieVarietyModel.coin),
                selectinload(DieVarietyModel.die)
            )
            .filter(DieVarietyModel.id == variety_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_coin_id(self, coin_id: int) -> list[DieVariety]:
        """Get all die varieties for a coin."""
        models = (
            self.session.query(DieVarietyModel)
            .options(
                selectinload(DieVarietyModel.coin),
                selectinload(DieVarietyModel.die)
            )
            .filter(DieVarietyModel.coin_id == coin_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_die_id(self, die_id: int) -> list[DieVariety]:
        """Get all varieties using a specific die."""
        models = (
            self.session.query(DieVarietyModel)
            .options(
                selectinload(DieVarietyModel.coin),
                selectinload(DieVarietyModel.die)
            )
            .filter(DieVarietyModel.die_id == die_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_variety_code(self, code: str) -> list[DieVariety]:
        """List all varieties with matching code."""
        models = (
            self.session.query(DieVarietyModel)
            .options(
                selectinload(DieVarietyModel.coin),
                selectinload(DieVarietyModel.die)
            )
            .filter(DieVarietyModel.variety_code == code)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def create(self, variety: DieVariety) -> DieVariety:
        """Create new die variety."""
        model = self._to_model(variety)
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, variety_id: int, variety: DieVariety) -> Optional[DieVariety]:
        """Update existing die variety."""
        model = self.session.query(DieVarietyModel).filter(DieVarietyModel.id == variety_id).first()
        if not model:
            return None

        # Update fields
        model.die_id = variety.die_id if variety.die_id is not None else model.die_id
        model.variety_code = variety.variety_code or model.variety_code
        model.variety_description = variety.variety_description if variety.variety_description is not None else model.variety_description
        model.distinguishing_features = variety.distinguishing_features if variety.distinguishing_features is not None else model.distinguishing_features
        model.reference = variety.reference if variety.reference is not None else model.reference
        model.notes = variety.notes if variety.notes is not None else model.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, variety_id: int) -> bool:
        """Delete die variety."""
        model = self.session.query(DieVarietyModel).filter(DieVarietyModel.id == variety_id).first()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def _to_domain(self, model: DieVarietyModel) -> DieVariety:
        """Convert ORM model to domain entity."""
        return DieVariety(
            id=model.id,
            coin_id=model.coin_id,
            die_id=model.die_id,
            variety_code=model.variety_code,
            variety_description=model.variety_description,
            distinguishing_features=model.distinguishing_features,
            reference=model.reference,
            notes=model.notes
        )

    def _to_model(self, variety: DieVariety) -> DieVarietyModel:
        """Convert domain entity to ORM model."""
        return DieVarietyModel(
            id=variety.id,
            coin_id=variety.coin_id,
            die_id=variety.die_id,
            variety_code=variety.variety_code,
            variety_description=variety.variety_description,
            distinguishing_features=variety.distinguishing_features,
            reference=variety.reference,
            notes=variety.notes
        )
