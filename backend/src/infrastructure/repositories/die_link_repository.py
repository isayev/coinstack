"""Concrete repository implementation for die links."""

from typing import Optional
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import DieLink, DieLinkConfidence
from src.domain.repositories_die_study import IDieLinkRepository
from src.infrastructure.persistence.orm import DieLinkModel


class SqlAlchemyDieLinkRepository(IDieLinkRepository):
    """SQLAlchemy implementation of die link repository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, link_id: int) -> Optional[DieLink]:
        """Get die link by ID with eager loading."""
        model = (
            self.session.query(DieLinkModel)
            .options(
                selectinload(DieLinkModel.die),
                selectinload(DieLinkModel.coin_a),
                selectinload(DieLinkModel.coin_b)
            )
            .filter(DieLinkModel.id == link_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_by_coin_id(self, coin_id: int) -> list[DieLink]:
        """Get all die links for a coin."""
        models = (
            self.session.query(DieLinkModel)
            .options(
                selectinload(DieLinkModel.die),
                selectinload(DieLinkModel.coin_a),
                selectinload(DieLinkModel.coin_b)
            )
            .filter(
                (DieLinkModel.coin_a_id == coin_id) |
                (DieLinkModel.coin_b_id == coin_id)
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_by_die_id(self, die_id: int) -> list[DieLink]:
        """Get all die links for a specific die."""
        models = (
            self.session.query(DieLinkModel)
            .options(
                selectinload(DieLinkModel.die),
                selectinload(DieLinkModel.coin_a),
                selectinload(DieLinkModel.coin_b)
            )
            .filter(DieLinkModel.die_id == die_id)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_linked_coins(self, coin_id: int, die_id: int) -> list[int]:
        """Get all coin IDs directly linked to this coin via shared die."""
        links = (
            self.session.query(DieLinkModel)
            .filter(
                DieLinkModel.die_id == die_id,
                (DieLinkModel.coin_a_id == coin_id) |
                (DieLinkModel.coin_b_id == coin_id)
            )
            .all()
        )

        linked_coins = []
        for link in links:
            if link.coin_a_id == coin_id:
                linked_coins.append(link.coin_b_id)
            else:
                linked_coins.append(link.coin_a_id)

        return linked_coins

    def get_die_network(self, coin_id: int, die_id: int, max_depth: int = 3) -> list[int]:
        """Get all coins transitively linked via shared die (BFS up to max_depth).

        Uses breadth-first search to find all coins connected through die links,
        preventing infinite loops and respecting max depth.
        """
        visited = {coin_id}
        queue = [(coin_id, 0)]
        result = []

        while queue:
            current_coin, depth = queue.pop(0)

            # Stop if we've reached max depth
            if depth >= max_depth:
                continue

            # Find directly linked coins
            links = (
                self.session.query(DieLinkModel)
                .filter(
                    DieLinkModel.die_id == die_id,
                    (DieLinkModel.coin_a_id == current_coin) |
                    (DieLinkModel.coin_b_id == current_coin)
                )
                .all()
            )

            for link in links:
                # Determine the other coin in the link
                next_coin = link.coin_b_id if link.coin_a_id == current_coin else link.coin_a_id

                # Only process if not already visited
                if next_coin not in visited:
                    visited.add(next_coin)
                    result.append(next_coin)
                    queue.append((next_coin, depth + 1))

        return result

    def create(self, link: DieLink) -> DieLink:
        """Create new die link (enforces coin_a_id < coin_b_id ordering)."""
        # Enforce canonical ordering (smaller ID first)
        coin_a = min(link.coin_a_id, link.coin_b_id)
        coin_b = max(link.coin_a_id, link.coin_b_id)

        # Check for duplicate
        existing = self.find_duplicate(link.die_id, coin_a, coin_b)
        if existing:
            raise ValueError(f"Die link already exists between coins {coin_a} and {coin_b}")

        model = DieLinkModel(
            die_id=link.die_id,
            coin_a_id=coin_a,  # Always smaller ID
            coin_b_id=coin_b,  # Always larger ID
            confidence=link.confidence.value if link.confidence else None,
            notes=link.notes
        )
        self.session.add(model)
        self.session.flush()
        return self._to_domain(model)

    def update(self, link_id: int, link: DieLink) -> Optional[DieLink]:
        """Update existing die link."""
        model = self.session.query(DieLinkModel).filter(DieLinkModel.id == link_id).first()
        if not model:
            return None

        # Update fields (preserve coin ordering)
        model.confidence = link.confidence.value if link.confidence else model.confidence
        model.notes = link.notes if link.notes is not None else model.notes

        self.session.flush()
        return self._to_domain(model)

    def delete(self, link_id: int) -> bool:
        """Delete die link."""
        model = self.session.query(DieLinkModel).filter(DieLinkModel.id == link_id).first()
        if not model:
            return False

        self.session.delete(model)
        self.session.flush()
        return True

    def find_duplicate(self, die_id: int, coin_a_id: int, coin_b_id: int) -> Optional[DieLink]:
        """Check if die link already exists between two coins."""
        # Ensure canonical ordering
        coin_a = min(coin_a_id, coin_b_id)
        coin_b = max(coin_a_id, coin_b_id)

        model = (
            self.session.query(DieLinkModel)
            .filter(
                DieLinkModel.die_id == die_id,
                DieLinkModel.coin_a_id == coin_a,
                DieLinkModel.coin_b_id == coin_b
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def _to_domain(self, model: DieLinkModel) -> DieLink:
        """Convert ORM model to domain entity."""
        return DieLink(
            id=model.id,
            die_id=model.die_id,
            coin_a_id=model.coin_a_id,
            coin_b_id=model.coin_b_id,
            confidence=DieLinkConfidence(model.confidence) if model.confidence else None,
            notes=model.notes
        )
