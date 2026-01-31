"""
Collection Repository Implementation.

Handles persistence for collections and collection-coin memberships.
Supports custom (manual) and smart (dynamic) collections with hierarchical nesting.
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session, selectinload

from src.domain.coin import (
    Collection, CollectionCoin, CollectionStatistics, SmartCriteria
)
from src.infrastructure.persistence.orm import (
    CollectionModel, CollectionCoinModel, CoinModel
)


class SqlAlchemyCollectionRepository:
    """
    Repository for managing collections and their coin memberships.

    Provides CRUD operations with support for:
    - Custom collections (manual membership)
    - Smart collections (dynamic based on criteria)
    - Hierarchical nesting (limited to 3 levels)
    - Collection statistics
    """

    def __init__(self, session: Session):
        self.session = session

    # =========================================================================
    # Collection CRUD
    # =========================================================================

    def get_by_id(self, collection_id: int) -> Optional[Collection]:
        """Get a collection by ID with eager loading."""
        model = self.session.query(CollectionModel).options(
            selectinload(CollectionModel.children),
            selectinload(CollectionModel.coin_memberships),
        ).filter(CollectionModel.id == collection_id).first()
        return self._to_domain(model) if model else None

    def get_by_slug(self, slug: str) -> Optional[Collection]:
        """Get a collection by unique slug."""
        model = self.session.query(CollectionModel).filter(
            CollectionModel.slug == slug
        ).first()
        return self._to_domain(model) if model else None

    def list_all(
        self,
        parent_id: Optional[int] = None,
        collection_type: Optional[str] = None,
        purpose: Optional[str] = None,
        include_hidden: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Collection]:
        """
        List collections with optional filters.

        If parent_id is None, returns top-level collections.
        """
        query = self.session.query(CollectionModel)

        # Filter by parent (None = top-level)
        if parent_id is None:
            query = query.filter(CollectionModel.parent_id.is_(None))
        else:
            query = query.filter(CollectionModel.parent_id == parent_id)

        if collection_type:
            query = query.filter(CollectionModel.collection_type == collection_type)

        if purpose:
            query = query.filter(CollectionModel.purpose == purpose)

        if not include_hidden:
            query = query.filter(CollectionModel.is_hidden.is_(False))

        query = query.order_by(
            CollectionModel.display_order.asc().nullslast(),
            CollectionModel.name.asc()
        )
        models = query.offset(skip).limit(limit).all()

        return [self._to_domain(m) for m in models]

    def list_tree(self) -> List[Collection]:
        """
        Get complete collection hierarchy as a tree structure.

        Returns all collections ordered for tree display (by level, then display_order).
        """
        models = self.session.query(CollectionModel).filter(
            CollectionModel.is_hidden.is_(False)
        ).order_by(
            CollectionModel.level.asc(),
            CollectionModel.display_order.asc().nullslast(),
            CollectionModel.name.asc()
        ).all()

        return [self._to_domain(m) for m in models]

    def count(
        self,
        parent_id: Optional[int] = None,
        collection_type: Optional[str] = None,
        include_hidden: bool = False,
    ) -> int:
        """Count collections matching filters."""
        query = self.session.query(CollectionModel)

        if parent_id is None:
            query = query.filter(CollectionModel.parent_id.is_(None))
        else:
            query = query.filter(CollectionModel.parent_id == parent_id)

        if collection_type:
            query = query.filter(CollectionModel.collection_type == collection_type)

        if not include_hidden:
            query = query.filter(CollectionModel.is_hidden.is_(False))

        return query.count()

    def create(self, collection: Collection) -> Collection:
        """Create a new collection. Returns collection with ID assigned."""
        # Validate hierarchy depth
        if collection.parent_id is not None:
            parent = self.session.get(CollectionModel, collection.parent_id)
            if parent and parent.level >= 2:
                raise ValueError("Collection hierarchy limited to 3 levels")
            collection.level = (parent.level + 1) if parent else 0

        model = self._to_model(collection)
        model.id = None  # Ensure new record
        model.created_at = datetime.now(timezone.utc)

        self.session.add(model)
        self.session.flush()

        return self._to_domain(model)

    def update(self, collection_id: int, collection: Collection) -> Optional[Collection]:
        """Update an existing collection."""
        model = self.session.get(CollectionModel, collection_id)
        if not model:
            return None

        # Validate hierarchy depth if parent is changing
        if collection.parent_id != model.parent_id:
            if collection.parent_id is not None:
                new_parent = self.session.get(CollectionModel, collection.parent_id)
                if new_parent and new_parent.level >= 2:
                    raise ValueError("Collection hierarchy limited to 3 levels")
                collection.level = (new_parent.level + 1) if new_parent else 0
            else:
                collection.level = 0

        # Update fields
        model.name = collection.name
        model.description = collection.description
        model.slug = collection.slug
        model.collection_type = collection.collection_type
        model.purpose = collection.purpose
        model.smart_filter = json.dumps(collection.smart_criteria.to_dict()) if collection.smart_criteria else None
        model.is_type_set = collection.is_type_set
        model.type_set_definition = collection.type_set_definition
        model.cover_image_url = collection.cover_image_url
        model.cover_coin_id = collection.cover_coin_id
        model.color = collection.color
        model.icon = collection.icon
        model.display_order = collection.display_order
        model.default_sort = collection.default_sort
        model.default_view = collection.default_view
        model.is_favorite = collection.is_favorite
        model.is_hidden = collection.is_hidden
        model.is_public = collection.is_public
        model.parent_id = collection.parent_id
        model.level = collection.level
        model.storage_location = collection.storage_location
        model.notes = collection.notes
        model.updated_at = datetime.now(timezone.utc)

        self.session.flush()
        return self._to_domain(model)

    def delete(self, collection_id: int, promote_children: bool = True) -> bool:
        """
        Delete a collection by ID.

        If promote_children is True, child collections are moved to
        the deleted collection's parent. Otherwise they become top-level.
        """
        model = self.session.get(CollectionModel, collection_id)
        if not model:
            return False

        # Handle child collections
        children = self.session.query(CollectionModel).filter(
            CollectionModel.parent_id == collection_id
        ).all()

        for child in children:
            if promote_children:
                child.parent_id = model.parent_id
                child.level = max(0, child.level - 1)
            else:
                child.parent_id = None
                child.level = 0

        self.session.delete(model)
        self.session.flush()
        return True

    # =========================================================================
    # Coin membership operations
    # =========================================================================

    def add_coin(
        self,
        collection_id: int,
        coin_id: int,
        notes: Optional[str] = None,
        position: Optional[int] = None,
    ) -> bool:
        """Add a coin to a collection."""
        # Check if already exists
        existing = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.coin_id == coin_id,
        ).first()

        if existing:
            return False  # Already in collection

        membership = CollectionCoinModel(
            collection_id=collection_id,
            coin_id=coin_id,
            added_at=datetime.now(timezone.utc),
            notes=notes,
            position=position,
        )

        self.session.add(membership)

        # Update coin count
        collection = self.session.get(CollectionModel, collection_id)
        if collection:
            collection.coin_count = (collection.coin_count or 0) + 1

        self.session.flush()
        return True

    def add_coins_bulk(
        self,
        collection_id: int,
        coin_ids: List[int],
    ) -> int:
        """Add multiple coins to a collection. Returns count added."""
        # Get existing memberships
        existing = self.session.query(CollectionCoinModel.coin_id).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.coin_id.in_(coin_ids),
        ).all()
        existing_ids = {e[0] for e in existing}

        # Add new memberships
        count = 0
        now = datetime.now(timezone.utc)
        for coin_id in coin_ids:
            if coin_id not in existing_ids:
                membership = CollectionCoinModel(
                    collection_id=collection_id,
                    coin_id=coin_id,
                    added_at=now,
                )
                self.session.add(membership)
                count += 1

        # Update coin count
        if count > 0:
            collection = self.session.get(CollectionModel, collection_id)
            if collection:
                collection.coin_count = (collection.coin_count or 0) + count

        self.session.flush()
        return count

    def remove_coin(self, collection_id: int, coin_id: int) -> bool:
        """Remove a coin from a collection."""
        membership = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.coin_id == coin_id,
        ).first()

        if not membership:
            return False

        self.session.delete(membership)

        # Update coin count
        collection = self.session.get(CollectionModel, collection_id)
        if collection and collection.coin_count:
            collection.coin_count = max(0, collection.coin_count - 1)

        self.session.flush()
        return True

    def get_coins_in_collection(
        self,
        collection_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CollectionCoin]:
        """Get coins in a collection with membership details."""
        memberships = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id
        ).order_by(
            CollectionCoinModel.custom_order.asc().nullslast(),
            CollectionCoinModel.position.asc().nullslast(),
            CollectionCoinModel.added_at.desc()
        ).offset(skip).limit(limit).all()

        return [self._membership_to_domain(m) for m in memberships]

    def get_collections_for_coin(self, coin_id: int) -> List[Collection]:
        """Get all collections containing a specific coin."""
        memberships = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.coin_id == coin_id
        ).all()

        collection_ids = [m.collection_id for m in memberships]
        if not collection_ids:
            return []

        models = self.session.query(CollectionModel).filter(
            CollectionModel.id.in_(collection_ids),
            CollectionModel.is_hidden.is_(False),
        ).all()

        return [self._to_domain(m) for m in models]

    def update_coin_membership(
        self,
        collection_id: int,
        coin_id: int,
        notes: Optional[str] = None,
        is_featured: Optional[bool] = None,
        is_placeholder: Optional[bool] = None,
        position: Optional[int] = None,
        fulfills_type: Optional[str] = None,
        exclude_from_stats: Optional[bool] = None,
    ) -> bool:
        """Update a coin's membership details in a collection."""
        membership = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.coin_id == coin_id,
        ).first()

        if not membership:
            return False

        if notes is not None:
            membership.notes = notes
        if is_featured is not None:
            membership.is_featured = is_featured
        if is_placeholder is not None:
            membership.is_placeholder = is_placeholder
        if position is not None:
            membership.position = position
        if fulfills_type is not None:
            membership.fulfills_type = fulfills_type
        if exclude_from_stats is not None:
            membership.exclude_from_stats = exclude_from_stats

        self.session.flush()
        return True

    def reorder_coins(self, collection_id: int, coin_order: List[int]) -> bool:
        """Reorder coins within a collection."""
        for i, coin_id in enumerate(coin_order):
            membership = self.session.query(CollectionCoinModel).filter(
                CollectionCoinModel.collection_id == collection_id,
                CollectionCoinModel.coin_id == coin_id,
            ).first()

            if membership:
                membership.custom_order = i

        self.session.flush()
        return True

    def count_coins_in_collection(self, collection_id: int) -> int:
        """Count coins in a collection."""
        return self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id
        ).count()

    def get_membership(self, collection_id: int, coin_id: int) -> Optional[CollectionCoin]:
        """Get a single coin membership by collection and coin ID."""
        membership = self.session.query(CollectionCoinModel).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.coin_id == coin_id,
        ).first()
        return self._membership_to_domain(membership) if membership else None

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self, collection_id: int) -> CollectionStatistics:
        """Calculate collection statistics."""
        memberships = self.session.query(CollectionCoinModel).options(
            selectinload(CollectionCoinModel.coin)
        ).filter(
            CollectionCoinModel.collection_id == collection_id,
            CollectionCoinModel.exclude_from_stats.isnot(True),
        ).all()

        if not memberships:
            return CollectionStatistics()

        coin_count = len(memberships)
        total_value = Decimal("0")
        total_cost = Decimal("0")
        metal_breakdown: Dict[str, int] = {}
        denomination_breakdown: Dict[str, int] = {}
        category_breakdown: Dict[str, int] = {}
        grade_distribution: Dict[str, int] = {}
        slabbed_count = 0
        raw_count = 0
        earliest_year: Optional[int] = None
        latest_year: Optional[int] = None
        grade_sum = 0
        grade_count = 0

        for m in memberships:
            coin = m.coin
            if not coin:
                continue

            # Value tracking
            if coin.market_value:
                total_value += coin.market_value
            if coin.acquisition_price:
                total_cost += coin.acquisition_price

            # Metal breakdown
            if coin.metal:
                metal_breakdown[coin.metal] = metal_breakdown.get(coin.metal, 0) + 1

            # Denomination breakdown
            if coin.denomination:
                denomination_breakdown[coin.denomination] = denomination_breakdown.get(coin.denomination, 0) + 1

            # Category breakdown
            if coin.category:
                category_breakdown[coin.category] = category_breakdown.get(coin.category, 0) + 1

            # Grade distribution
            if coin.grade:
                grade_distribution[coin.grade] = grade_distribution.get(coin.grade, 0) + 1

            # Slabbed vs raw
            if coin.grading_state == "slabbed":
                slabbed_count += 1
            else:
                raw_count += 1

            # Chronological range
            if coin.year_start is not None:
                if earliest_year is None or coin.year_start < earliest_year:
                    earliest_year = coin.year_start
                if latest_year is None or coin.year_start > latest_year:
                    latest_year = coin.year_start

            # Grade numeric for average
            if coin.grade_numeric:
                grade_sum += coin.grade_numeric
                grade_count += 1

        # Calculate gain/loss
        unrealized_gain_loss = total_value - total_cost if total_cost > 0 else None

        # Calculate average grade
        average_grade = grade_sum / grade_count if grade_count > 0 else None

        return CollectionStatistics(
            coin_count=coin_count,
            total_value=total_value if total_value > 0 else None,
            total_cost=total_cost if total_cost > 0 else None,
            unrealized_gain_loss=unrealized_gain_loss,
            metal_breakdown=metal_breakdown or None,
            denomination_breakdown=denomination_breakdown or None,
            category_breakdown=category_breakdown or None,
            grade_distribution=grade_distribution or None,
            average_grade=average_grade,
            slabbed_count=slabbed_count,
            raw_count=raw_count,
            earliest_coin_year=earliest_year,
            latest_coin_year=latest_year,
        )

    def update_cached_stats(self, collection_id: int) -> bool:
        """Refresh cached statistics for a collection."""
        collection = self.session.get(CollectionModel, collection_id)
        if not collection:
            return False

        stats = self.get_statistics(collection_id)

        collection.coin_count = stats.coin_count
        collection.total_value = stats.total_value
        collection.completion_percentage = Decimal(str(stats.completion_percentage)) if stats.completion_percentage else None
        collection.stats_updated_at = datetime.now(timezone.utc)

        self.session.flush()
        return True

    # =========================================================================
    # Mappers
    # =========================================================================

    def _to_domain(self, model: CollectionModel) -> Collection:
        """Convert ORM model to domain entity."""
        smart_criteria = None
        if model.smart_filter:
            try:
                criteria_dict = json.loads(model.smart_filter)
                smart_criteria = SmartCriteria.from_dict(criteria_dict)
            except (json.JSONDecodeError, TypeError):
                pass

        return Collection(
            id=model.id,
            name=model.name,
            description=model.description,
            slug=model.slug,
            collection_type=model.collection_type or "custom",
            purpose=model.purpose or "general",
            smart_criteria=smart_criteria,
            is_type_set=model.is_type_set or False,
            type_set_definition=model.type_set_definition,
            cover_image_url=model.cover_image_url,
            cover_coin_id=model.cover_coin_id,
            color=model.color,
            icon=model.icon,
            parent_id=model.parent_id,
            level=model.level or 0,
            display_order=model.display_order or 0,
            default_sort=model.default_sort or "custom",
            default_view=model.default_view,
            coin_count=model.coin_count or 0,
            total_value=model.total_value,
            stats_updated_at=model.stats_updated_at,
            completion_percentage=float(model.completion_percentage) if model.completion_percentage else None,
            is_favorite=model.is_favorite or False,
            is_hidden=model.is_hidden or False,
            is_public=model.is_public or False,
            storage_location=model.storage_location,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, collection: Collection) -> CollectionModel:
        """Convert domain entity to ORM model."""
        smart_filter = None
        if collection.smart_criteria:
            smart_filter = json.dumps(collection.smart_criteria.to_dict())

        return CollectionModel(
            id=collection.id,
            name=collection.name,
            description=collection.description,
            slug=collection.slug,
            collection_type=collection.collection_type,
            purpose=collection.purpose,
            smart_filter=smart_filter,
            is_type_set=collection.is_type_set,
            type_set_definition=collection.type_set_definition,
            cover_image_url=collection.cover_image_url,
            cover_coin_id=collection.cover_coin_id,
            color=collection.color,
            icon=collection.icon,
            parent_id=collection.parent_id,
            level=collection.level,
            display_order=collection.display_order,
            default_sort=collection.default_sort,
            default_view=collection.default_view,
            coin_count=collection.coin_count,
            total_value=collection.total_value,
            stats_updated_at=collection.stats_updated_at,
            completion_percentage=Decimal(str(collection.completion_percentage)) if collection.completion_percentage else None,
            is_favorite=collection.is_favorite,
            is_hidden=collection.is_hidden,
            is_public=collection.is_public,
            storage_location=collection.storage_location,
            notes=collection.notes,
        )

    def _membership_to_domain(self, model: CollectionCoinModel) -> CollectionCoin:
        """Convert membership ORM model to domain entity."""
        return CollectionCoin(
            collection_id=model.collection_id,
            coin_id=model.coin_id,
            added_at=model.added_at,
            added_by=model.added_by,
            position=model.position,
            custom_order=model.custom_order,
            notes=model.notes,
            is_featured=model.is_featured or False,
            is_cover_coin=model.is_cover_coin or False,
            is_placeholder=model.is_placeholder or False,
            exclude_from_stats=model.exclude_from_stats or False,
            fulfills_type=model.fulfills_type,
            series_slot_id=model.series_slot_id,
        )
