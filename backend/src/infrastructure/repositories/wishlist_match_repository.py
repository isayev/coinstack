"""
Wishlist Match Repository Implementation.

Handles persistence of matched auction lots for wishlists.
"""

from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import desc
from sqlalchemy.orm import Session

from src.domain.coin import WishlistMatch
from src.infrastructure.persistence.orm import WishlistMatchModel


class SqlAlchemyWishlistMatchRepository:
    """
    Repository for managing wishlist matches.

    Provides CRUD operations for matched lots.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, match_id: int) -> Optional[WishlistMatch]:
        """Get a match by ID."""
        model = self.session.get(WishlistMatchModel, match_id)
        return self._to_domain(model) if model else None

    def get_by_wishlist_item_id(
        self,
        wishlist_item_id: int,
        include_dismissed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistMatch]:
        """
        Get all matches for a wishlist item.

        Returns matches ordered by match_score desc, then created_at desc.
        """
        query = self.session.query(WishlistMatchModel).filter(
            WishlistMatchModel.wishlist_item_id == wishlist_item_id
        )

        if not include_dismissed:
            query = query.filter(WishlistMatchModel.dismissed.is_(False))

        query = query.order_by(
            desc(WishlistMatchModel.match_score),
            desc(WishlistMatchModel.created_at)
        )
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def get_saved(
        self,
        wishlist_item_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WishlistMatch]:
        """Get saved matches, optionally filtered by wishlist item."""
        query = self.session.query(WishlistMatchModel).filter(
            WishlistMatchModel.saved.is_(True)
        )

        if wishlist_item_id:
            query = query.filter(WishlistMatchModel.wishlist_item_id == wishlist_item_id)

        query = query.order_by(desc(WishlistMatchModel.created_at))
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def count_by_wishlist_item_id(
        self,
        wishlist_item_id: int,
        include_dismissed: bool = False,
    ) -> int:
        """Count matches for a wishlist item."""
        query = self.session.query(WishlistMatchModel).filter(
            WishlistMatchModel.wishlist_item_id == wishlist_item_id
        )

        if not include_dismissed:
            query = query.filter(WishlistMatchModel.dismissed.is_(False))

        return query.count()

    def create(self, wishlist_item_id: int, match: WishlistMatch) -> WishlistMatch:
        """Create a new match. Returns match with ID assigned."""
        model = self._to_model(match)
        model.id = None  # Ensure new record
        model.wishlist_item_id = wishlist_item_id

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, match_id: int, match: WishlistMatch) -> Optional[WishlistMatch]:
        """Update an existing match."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        # Update fields
        model.match_type = match.match_type
        model.match_source = match.match_source
        model.match_id = match.match_id
        model.match_url = match.match_url
        model.title = match.title
        model.description = match.description
        model.image_url = match.image_url
        model.grade = match.grade
        model.grade_numeric = match.grade_numeric
        model.condition_notes = match.condition_notes
        model.price = match.price
        model.estimate_low = match.estimate_low
        model.estimate_high = match.estimate_high
        model.currency = match.currency
        model.current_bid = match.current_bid
        model.auction_date = match.auction_date
        model.end_time = match.end_time
        model.match_score = match.match_score
        model.match_confidence = match.match_confidence
        model.match_reasons = match.match_reasons
        model.is_below_budget = match.is_below_budget
        model.is_below_market = match.is_below_market
        model.value_score = match.value_score
        model.notes = match.notes

        self.session.flush()
        return self._to_domain(model)

    def dismiss(self, match_id: int) -> Optional[WishlistMatch]:
        """Dismiss a match."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        model.dismissed = True
        model.dismissed_at = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def undismiss(self, match_id: int) -> Optional[WishlistMatch]:
        """Undismiss a match."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        model.dismissed = False
        model.dismissed_at = None

        self.session.flush()
        return self._to_domain(model)

    def save(self, match_id: int) -> Optional[WishlistMatch]:
        """Save/bookmark a match."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        model.saved = True

        self.session.flush()
        return self._to_domain(model)

    def unsave(self, match_id: int) -> Optional[WishlistMatch]:
        """Remove save/bookmark from a match."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        model.saved = False

        self.session.flush()
        return self._to_domain(model)

    def mark_notified(self, match_id: int) -> Optional[WishlistMatch]:
        """Mark a match as notified."""
        model = self.session.get(WishlistMatchModel, match_id)
        if not model:
            return None

        model.notified = True
        model.notified_at = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def delete(self, match_id: int) -> bool:
        """Delete a match by ID."""
        model = self.session.get(WishlistMatchModel, match_id)
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def get_by_match_id(
        self,
        match_source: str,
        external_match_id: str,
    ) -> Optional[WishlistMatch]:
        """Find a match by source and external ID (for deduplication)."""
        model = self.session.query(WishlistMatchModel).filter(
            WishlistMatchModel.match_source == match_source,
            WishlistMatchModel.match_id == external_match_id,
        ).first()

        return self._to_domain(model) if model else None

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    def _to_domain(self, model: WishlistMatchModel) -> WishlistMatch:
        """Convert ORM model to domain entity."""
        return WishlistMatch(
            id=model.id,
            wishlist_item_id=model.wishlist_item_id,
            match_type=model.match_type,
            match_source=model.match_source,
            match_id=model.match_id,
            match_url=model.match_url,
            title=model.title,
            description=model.description,
            image_url=model.image_url,
            grade=model.grade,
            grade_numeric=model.grade_numeric,
            condition_notes=model.condition_notes,
            price=model.price,
            estimate_low=model.estimate_low,
            estimate_high=model.estimate_high,
            currency=model.currency or "USD",
            current_bid=model.current_bid,
            auction_date=model.auction_date,
            end_time=model.end_time,
            match_score=model.match_score,
            match_confidence=model.match_confidence,
            match_reasons=model.match_reasons,
            is_below_budget=model.is_below_budget,
            is_below_market=model.is_below_market,
            value_score=model.value_score,
            notified=model.notified or False,
            notified_at=model.notified_at,
            dismissed=model.dismissed or False,
            dismissed_at=model.dismissed_at,
            saved=model.saved or False,
            notes=model.notes,
            created_at=model.created_at,
        )

    def _to_model(self, match: WishlistMatch) -> WishlistMatchModel:
        """Convert domain entity to ORM model."""
        return WishlistMatchModel(
            id=match.id,
            wishlist_item_id=match.wishlist_item_id,
            match_type=match.match_type,
            match_source=match.match_source,
            match_id=match.match_id,
            match_url=match.match_url,
            title=match.title,
            description=match.description,
            image_url=match.image_url,
            grade=match.grade,
            grade_numeric=match.grade_numeric,
            condition_notes=match.condition_notes,
            price=match.price,
            estimate_low=match.estimate_low,
            estimate_high=match.estimate_high,
            currency=match.currency,
            current_bid=match.current_bid,
            auction_date=match.auction_date,
            end_time=match.end_time,
            match_score=match.match_score,
            match_confidence=match.match_confidence,
            match_reasons=match.match_reasons,
            is_below_budget=match.is_below_budget,
            is_below_market=match.is_below_market,
            value_score=match.value_score,
            notified=match.notified,
            notified_at=match.notified_at,
            dismissed=match.dismissed,
            dismissed_at=match.dismissed_at,
            saved=match.saved,
            notes=match.notes,
            created_at=match.created_at or datetime.now(timezone.utc),
        )
