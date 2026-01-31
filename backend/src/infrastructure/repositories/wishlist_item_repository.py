"""
Wishlist Item Repository Implementation.

Handles persistence of acquisition targets.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import WishlistItem
from src.infrastructure.persistence.orm import WishlistItemModel


def _escape_like(value: str) -> str:
    """Escape special LIKE pattern characters to prevent LIKE injection."""
    return value.replace('%', r'\%').replace('_', r'\_')


class SqlAlchemyWishlistItemRepository:
    """
    Repository for managing wishlist items.

    Provides CRUD operations for acquisition targets.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, item_id: int) -> Optional[WishlistItem]:
        """Get a wishlist item by ID."""
        model = self.session.get(WishlistItemModel, item_id)
        return self._to_domain(model) if model else None

    def list_all(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistItem]:
        """
        List wishlist items with optional filters.

        Returns items ordered by priority asc, then created_at desc.
        """
        query = self.session.query(WishlistItemModel)

        if status:
            query = query.filter(WishlistItemModel.status == status)
        if priority is not None:
            query = query.filter(WishlistItemModel.priority == priority)
        if category:
            query = query.filter(WishlistItemModel.category == category)

        query = query.order_by(WishlistItemModel.priority, desc(WishlistItemModel.created_at))
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def list_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistItem]:
        """List wishlist items by status."""
        return self.list_all(status=status, skip=skip, limit=limit)

    def count(
        self,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count wishlist items matching filters."""
        query = self.session.query(WishlistItemModel)

        if status:
            query = query.filter(WishlistItemModel.status == status)
        if priority is not None:
            query = query.filter(WishlistItemModel.priority == priority)
        if category:
            query = query.filter(WishlistItemModel.category == category)

        return query.count()

    def create(self, item: WishlistItem) -> WishlistItem:
        """Create a new wishlist item. Returns item with ID assigned."""
        model = self._to_model(item)
        model.id = None  # Ensure new record

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, item_id: int, item: WishlistItem) -> Optional[WishlistItem]:
        """Update an existing wishlist item."""
        model = self.session.get(WishlistItemModel, item_id)
        if not model:
            return None

        # Update fields
        model.title = item.title
        model.description = item.description
        model.issuer = item.issuer
        model.issuer_id = item.issuer_id
        model.mint = item.mint
        model.mint_id = item.mint_id
        model.year_start = item.year_start
        model.year_end = item.year_end
        model.denomination = item.denomination
        model.metal = item.metal
        model.category = item.category
        model.catalog_ref = item.catalog_ref
        model.catalog_ref_pattern = item.catalog_ref_pattern
        model.min_grade = item.min_grade
        model.min_grade_numeric = item.min_grade_numeric
        model.condition_notes = item.condition_notes
        model.max_price = item.max_price
        model.target_price = item.target_price
        model.currency = item.currency
        model.priority = item.priority
        model.tags = item.tags
        model.series_slot_id = item.series_slot_id
        model.status = item.status
        model.notify_on_match = item.notify_on_match
        model.notify_email = item.notify_email
        model.notes = item.notes
        model.updated_at = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def delete(self, item_id: int) -> bool:
        """Delete a wishlist item by ID."""
        model = self.session.get(WishlistItemModel, item_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def mark_acquired(
        self,
        item_id: int,
        coin_id: int,
        acquired_price: Optional[Decimal] = None,
    ) -> Optional[WishlistItem]:
        """Mark a wishlist item as acquired."""
        model = self.session.get(WishlistItemModel, item_id)
        if not model:
            return None

        model.status = "acquired"
        model.acquired_coin_id = coin_id
        model.acquired_at = datetime.now(timezone.utc)
        model.acquired_price = acquired_price
        model.updated_at = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistItem]:
        """Search wishlist items by title, issuer, or catalog reference."""
        escaped_query = _escape_like(query)
        models = self.session.query(WishlistItemModel).filter(
            (WishlistItemModel.title.ilike(f"%{escaped_query}%")) |
            (WishlistItemModel.issuer.ilike(f"%{escaped_query}%")) |
            (WishlistItemModel.catalog_ref.ilike(f"%{escaped_query}%"))
        ).order_by(WishlistItemModel.priority).offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: WishlistItemModel) -> WishlistItem:
        """Convert ORM model to domain entity."""
        return WishlistItem(
            id=model.id,
            title=model.title,
            description=model.description,
            issuer=model.issuer,
            issuer_id=model.issuer_id,
            mint=model.mint,
            mint_id=model.mint_id,
            year_start=model.year_start,
            year_end=model.year_end,
            denomination=model.denomination,
            metal=model.metal,
            category=model.category,
            catalog_ref=model.catalog_ref,
            catalog_ref_pattern=model.catalog_ref_pattern,
            min_grade=model.min_grade,
            min_grade_numeric=model.min_grade_numeric,
            condition_notes=model.condition_notes,
            max_price=model.max_price,
            target_price=model.target_price,
            currency=model.currency or "USD",
            priority=model.priority or 2,
            tags=model.tags,
            series_slot_id=model.series_slot_id,
            status=model.status or "wanted",
            acquired_coin_id=model.acquired_coin_id,
            acquired_at=model.acquired_at,
            acquired_price=model.acquired_price,
            notify_on_match=model.notify_on_match if model.notify_on_match is not None else True,
            notify_email=model.notify_email or False,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, item: WishlistItem) -> WishlistItemModel:
        """Convert domain entity to ORM model."""
        return WishlistItemModel(
            id=item.id,
            title=item.title,
            description=item.description,
            issuer=item.issuer,
            issuer_id=item.issuer_id,
            mint=item.mint,
            mint_id=item.mint_id,
            year_start=item.year_start,
            year_end=item.year_end,
            denomination=item.denomination,
            metal=item.metal,
            category=item.category,
            catalog_ref=item.catalog_ref,
            catalog_ref_pattern=item.catalog_ref_pattern,
            min_grade=item.min_grade,
            min_grade_numeric=item.min_grade_numeric,
            condition_notes=item.condition_notes,
            max_price=item.max_price,
            target_price=item.target_price,
            currency=item.currency,
            priority=item.priority,
            tags=item.tags,
            series_slot_id=item.series_slot_id,
            status=item.status,
            acquired_coin_id=item.acquired_coin_id,
            acquired_at=item.acquired_at,
            acquired_price=item.acquired_price,
            notify_on_match=item.notify_on_match,
            notify_email=item.notify_email,
            notes=item.notes,
            created_at=item.created_at or datetime.now(timezone.utc),
            updated_at=item.updated_at,
        )
