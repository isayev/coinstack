"""
Collections API Router.

Provides REST endpoints for managing coin collections with support for:
- Custom collections (manual membership)
- Smart collections (dynamic based on criteria)
- Hierarchical nesting (limited to 3 levels)
- Batch operations and statistics
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict, field_validator

from src.infrastructure.web.dependencies import get_collection_repo
from src.domain.coin import Collection, SmartCriteria, CollectionStatistics, CollectionCoin
from src.domain.repositories import ICollectionRepository


router = APIRouter(prefix="/api/v2/collections", tags=["collections"])

# Valid enum values for validation
VALID_COLLECTION_TYPES = {"custom", "smart", "series", "type_set", "system"}
VALID_PURPOSES = {"study", "display", "type_set", "duplicates", "reserves", "insurance", "general"}


# =============================================================================
# Request/Response Models
# =============================================================================

class SmartCriteriaInput(BaseModel):
    """Input model for smart collection criteria."""
    match: str = Field(default="all", description="Match mode: 'all' (AND) or 'any' (OR)")
    conditions: List[dict] = Field(default_factory=list, description="Filter conditions")


class CollectionCreate(BaseModel):
    """Request model for creating a collection."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, max_length=100)
    collection_type: str = Field(default="custom")
    purpose: str = Field(default="general")
    smart_criteria: Optional[SmartCriteriaInput] = None
    is_type_set: bool = False
    type_set_definition: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_coin_id: Optional[int] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    display_order: int = 0
    default_sort: str = "custom"
    default_view: Optional[str] = None
    is_favorite: bool = False
    storage_location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("collection_type")
    @classmethod
    def validate_collection_type(cls, v: str) -> str:
        if v not in VALID_COLLECTION_TYPES:
            raise ValueError(f"Invalid collection_type. Must be one of: {', '.join(VALID_COLLECTION_TYPES)}")
        return v

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        if v not in VALID_PURPOSES:
            raise ValueError(f"Invalid purpose. Must be one of: {', '.join(VALID_PURPOSES)}")
        return v


class CollectionUpdate(BaseModel):
    """Request model for updating a collection."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, max_length=100)
    collection_type: Optional[str] = None
    purpose: Optional[str] = None
    smart_criteria: Optional[SmartCriteriaInput] = None
    is_type_set: Optional[bool] = None
    type_set_definition: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_coin_id: Optional[int] = None
    color: Optional[str] = Field(None, max_length=20)
    icon: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    display_order: Optional[int] = None
    default_sort: Optional[str] = None
    default_view: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_hidden: Optional[bool] = None
    is_public: Optional[bool] = None
    storage_location: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("collection_type")
    @classmethod
    def validate_collection_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_COLLECTION_TYPES:
            raise ValueError(f"Invalid collection_type. Must be one of: {', '.join(VALID_COLLECTION_TYPES)}")
        return v

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PURPOSES:
            raise ValueError(f"Invalid purpose. Must be one of: {', '.join(VALID_PURPOSES)}")
        return v


class CollectionResponse(BaseModel):
    """Response model for a collection."""
    id: int
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    collection_type: str
    purpose: str
    smart_criteria: Optional[dict] = None
    is_type_set: bool = False
    type_set_definition: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_coin_id: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    parent_id: Optional[int] = None
    level: int = 0
    display_order: int = 0
    default_sort: str = "custom"
    default_view: Optional[str] = None
    coin_count: int = 0
    total_value: Optional[float] = None
    completion_percentage: Optional[float] = None
    is_favorite: bool = False
    is_hidden: bool = False
    is_public: bool = False
    storage_location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CollectionListResponse(BaseModel):
    """Response model for collection list."""
    collections: List[CollectionResponse]
    total: int
    skip: int
    limit: int


class AddCoinsRequest(BaseModel):
    """Request model for adding coins to a collection."""
    coin_ids: List[int] = Field(..., min_length=1)


class UpdateMembershipRequest(BaseModel):
    """Request model for updating a coin's membership in a collection."""
    notes: Optional[str] = None
    is_featured: Optional[bool] = None
    is_placeholder: Optional[bool] = None
    position: Optional[int] = None
    fulfills_type: Optional[str] = None
    exclude_from_stats: Optional[bool] = None


class ReorderCoinsRequest(BaseModel):
    """Request model for reordering coins in a collection."""
    coin_order: List[int] = Field(..., description="Ordered list of coin IDs")


class CollectionCoinResponse(BaseModel):
    """Response model for a coin membership."""
    collection_id: int
    coin_id: int
    added_at: Optional[datetime] = None
    notes: Optional[str] = None
    position: Optional[int] = None
    custom_order: Optional[int] = None
    is_featured: bool = False
    is_cover_coin: bool = False
    is_placeholder: bool = False
    exclude_from_stats: bool = False
    fulfills_type: Optional[str] = None


class CollectionCoinsResponse(BaseModel):
    """Response model for coins in a collection."""
    collection_id: int
    coins: List[CollectionCoinResponse]
    total: int
    skip: int
    limit: int


class CollectionStatsResponse(BaseModel):
    """Response model for collection statistics."""
    collection_id: int
    coin_count: int = 0
    total_value: Optional[float] = None
    total_cost: Optional[float] = None
    unrealized_gain_loss: Optional[float] = None
    metal_breakdown: Optional[dict] = None
    denomination_breakdown: Optional[dict] = None
    category_breakdown: Optional[dict] = None
    grade_distribution: Optional[dict] = None
    average_grade: Optional[float] = None
    slabbed_count: int = 0
    raw_count: int = 0
    earliest_coin_year: Optional[int] = None
    latest_coin_year: Optional[int] = None
    completion_percentage: Optional[float] = None


# =============================================================================
# Helper Functions
# =============================================================================

def collection_to_response(collection: Collection) -> CollectionResponse:
    """Convert domain collection to response model."""
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        slug=collection.slug,
        collection_type=collection.collection_type,
        purpose=collection.purpose,
        smart_criteria=collection.smart_criteria.to_dict() if collection.smart_criteria else None,
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
        total_value=float(collection.total_value) if collection.total_value else None,
        completion_percentage=collection.completion_percentage,
        is_favorite=collection.is_favorite,
        is_hidden=collection.is_hidden,
        is_public=collection.is_public,
        storage_location=collection.storage_location,
        notes=collection.notes,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


def stats_to_response(collection_id: int, stats: CollectionStatistics) -> CollectionStatsResponse:
    """Convert domain statistics to response model."""
    return CollectionStatsResponse(
        collection_id=collection_id,
        coin_count=stats.coin_count,
        total_value=float(stats.total_value) if stats.total_value else None,
        total_cost=float(stats.total_cost) if stats.total_cost else None,
        unrealized_gain_loss=float(stats.unrealized_gain_loss) if stats.unrealized_gain_loss else None,
        metal_breakdown=stats.metal_breakdown,
        denomination_breakdown=stats.denomination_breakdown,
        category_breakdown=stats.category_breakdown,
        grade_distribution=stats.grade_distribution,
        average_grade=stats.average_grade,
        slabbed_count=stats.slabbed_count,
        raw_count=stats.raw_count,
        earliest_coin_year=stats.earliest_coin_year,
        latest_coin_year=stats.latest_coin_year,
        completion_percentage=stats.completion_percentage,
    )


# =============================================================================
# Collection CRUD Endpoints
# =============================================================================

@router.get("", response_model=CollectionListResponse)
def list_collections(
    parent_id: Optional[int] = Query(None, description="Filter by parent collection (None = top-level)"),
    collection_type: Optional[str] = Query(None, description="Filter by type: custom, smart, series, type_set"),
    purpose: Optional[str] = Query(None, description="Filter by purpose"),
    include_hidden: bool = Query(False, description="Include hidden collections"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """List collections with optional filters."""
    collections = repo.list_all(
        parent_id=parent_id,
        collection_type=collection_type,
        purpose=purpose,
        include_hidden=include_hidden,
        skip=skip,
        limit=limit,
    )
    total = repo.count(
        parent_id=parent_id,
        collection_type=collection_type,
        include_hidden=include_hidden,
    )

    return CollectionListResponse(
        collections=[collection_to_response(c) for c in collections],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/tree", response_model=List[CollectionResponse])
def get_collection_tree(
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Get complete collection hierarchy as a tree structure."""
    collections = repo.list_tree()
    return [collection_to_response(c) for c in collections]


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(
    data: CollectionCreate,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Create a new collection."""
    # Build smart criteria if provided
    smart_criteria = None
    if data.smart_criteria:
        smart_criteria = SmartCriteria(
            match=data.smart_criteria.match,
            conditions=tuple(data.smart_criteria.conditions),
        )

    collection = Collection(
        name=data.name,
        description=data.description,
        slug=data.slug,
        collection_type=data.collection_type,
        purpose=data.purpose,
        smart_criteria=smart_criteria,
        is_type_set=data.is_type_set,
        type_set_definition=data.type_set_definition,
        cover_image_url=data.cover_image_url,
        cover_coin_id=data.cover_coin_id,
        color=data.color,
        icon=data.icon,
        parent_id=data.parent_id,
        display_order=data.display_order,
        default_sort=data.default_sort,
        default_view=data.default_view,
        is_favorite=data.is_favorite,
        storage_location=data.storage_location,
        notes=data.notes,
    )

    try:
        created = repo.create(collection)
        return collection_to_response(created)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{collection_id}", response_model=CollectionResponse)
def get_collection(
    collection_id: int,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Get a collection by ID."""
    collection = repo.get_by_id(collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return collection_to_response(collection)


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Update a collection."""
    existing = repo.get_by_id(collection_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Build updated collection
    smart_criteria = existing.smart_criteria
    if data.smart_criteria is not None:
        smart_criteria = SmartCriteria(
            match=data.smart_criteria.match,
            conditions=tuple(data.smart_criteria.conditions),
        )

    updated = Collection(
        id=collection_id,
        name=data.name if data.name is not None else existing.name,
        description=data.description if data.description is not None else existing.description,
        slug=data.slug if data.slug is not None else existing.slug,
        collection_type=data.collection_type if data.collection_type is not None else existing.collection_type,
        purpose=data.purpose if data.purpose is not None else existing.purpose,
        smart_criteria=smart_criteria,
        is_type_set=data.is_type_set if data.is_type_set is not None else existing.is_type_set,
        type_set_definition=data.type_set_definition if data.type_set_definition is not None else existing.type_set_definition,
        cover_image_url=data.cover_image_url if data.cover_image_url is not None else existing.cover_image_url,
        cover_coin_id=data.cover_coin_id if data.cover_coin_id is not None else existing.cover_coin_id,
        color=data.color if data.color is not None else existing.color,
        icon=data.icon if data.icon is not None else existing.icon,
        parent_id=data.parent_id if data.parent_id is not None else existing.parent_id,
        level=existing.level,  # Recalculated in repo
        display_order=data.display_order if data.display_order is not None else existing.display_order,
        default_sort=data.default_sort if data.default_sort is not None else existing.default_sort,
        default_view=data.default_view if data.default_view is not None else existing.default_view,
        coin_count=existing.coin_count,
        total_value=existing.total_value,
        is_favorite=data.is_favorite if data.is_favorite is not None else existing.is_favorite,
        is_hidden=data.is_hidden if data.is_hidden is not None else existing.is_hidden,
        is_public=data.is_public if data.is_public is not None else existing.is_public,
        storage_location=data.storage_location if data.storage_location is not None else existing.storage_location,
        notes=data.notes if data.notes is not None else existing.notes,
    )

    try:
        result = repo.update(collection_id, updated)
        return collection_to_response(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{collection_id}", status_code=204)
def delete_collection(
    collection_id: int,
    promote_children: bool = Query(True, description="Move children to parent (True) or make top-level (False)"),
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Delete a collection."""
    if not repo.delete(collection_id, promote_children=promote_children):
        raise HTTPException(status_code=404, detail="Collection not found")


# =============================================================================
# Coin Membership Endpoints
# =============================================================================

@router.get("/{collection_id}/coins", response_model=CollectionCoinsResponse)
def get_coins_in_collection(
    collection_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Get coins in a collection with membership details."""
    # Verify collection exists
    if not repo.get_by_id(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    memberships = repo.get_coins_in_collection(collection_id, skip=skip, limit=limit)
    total = repo.count_coins_in_collection(collection_id)

    return CollectionCoinsResponse(
        collection_id=collection_id,
        coins=[
            CollectionCoinResponse(
                collection_id=m.collection_id,
                coin_id=m.coin_id,
                added_at=m.added_at,
                notes=m.notes,
                position=m.position,
                custom_order=m.custom_order,
                is_featured=m.is_featured,
                is_cover_coin=m.is_cover_coin,
                is_placeholder=m.is_placeholder,
                exclude_from_stats=m.exclude_from_stats,
                fulfills_type=m.fulfills_type,
            )
            for m in memberships
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/{collection_id}/coins", status_code=201)
def add_coins_to_collection(
    collection_id: int,
    data: AddCoinsRequest,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Add coins to a collection (batch operation)."""
    # Verify collection exists
    if not repo.get_by_id(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    count = repo.add_coins_bulk(collection_id, data.coin_ids)
    return {"added": count, "collection_id": collection_id}


@router.delete("/{collection_id}/coins/{coin_id}", status_code=204)
def remove_coin_from_collection(
    collection_id: int,
    coin_id: int,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Remove a coin from a collection."""
    if not repo.remove_coin(collection_id, coin_id):
        raise HTTPException(status_code=404, detail="Membership not found")


@router.put("/{collection_id}/coins/{coin_id}", response_model=CollectionCoinResponse)
def update_coin_membership(
    collection_id: int,
    coin_id: int,
    data: UpdateMembershipRequest,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Update a coin's membership details in a collection."""
    if not repo.update_coin_membership(
        collection_id,
        coin_id,
        notes=data.notes,
        is_featured=data.is_featured,
        is_placeholder=data.is_placeholder,
        position=data.position,
        fulfills_type=data.fulfills_type,
        exclude_from_stats=data.exclude_from_stats,
    ):
        raise HTTPException(status_code=404, detail="Membership not found")

    # Return updated membership using efficient single-row query
    membership = repo.get_membership(collection_id, coin_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found after update")

    return CollectionCoinResponse(
        collection_id=membership.collection_id,
        coin_id=membership.coin_id,
        added_at=membership.added_at,
        notes=membership.notes,
        position=membership.position,
        custom_order=membership.custom_order,
        is_featured=membership.is_featured,
        is_cover_coin=membership.is_cover_coin,
        is_placeholder=membership.is_placeholder,
        exclude_from_stats=membership.exclude_from_stats,
        fulfills_type=membership.fulfills_type,
    )


@router.put("/{collection_id}/coins/order")
def reorder_coins_in_collection(
    collection_id: int,
    data: ReorderCoinsRequest,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Reorder coins within a collection."""
    # Verify collection exists
    if not repo.get_by_id(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    repo.reorder_coins(collection_id, data.coin_order)
    return {"success": True, "collection_id": collection_id}


# =============================================================================
# Statistics Endpoints
# =============================================================================

@router.get("/{collection_id}/stats", response_model=CollectionStatsResponse)
def get_collection_statistics(
    collection_id: int,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Get statistics for a collection."""
    # Verify collection exists
    if not repo.get_by_id(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    stats = repo.get_statistics(collection_id)
    return stats_to_response(collection_id, stats)


@router.post("/{collection_id}/refresh-stats", status_code=200)
def refresh_collection_stats(
    collection_id: int,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Refresh cached statistics for a collection."""
    if not repo.update_cached_stats(collection_id):
        raise HTTPException(status_code=404, detail="Collection not found")

    return {"success": True, "collection_id": collection_id}


# =============================================================================
# Reverse Lookup
# =============================================================================

@router.get("/by-coin/{coin_id}", response_model=List[CollectionResponse])
def get_collections_containing_coin(
    coin_id: int,
    repo: ICollectionRepository = Depends(get_collection_repo),
):
    """Get all collections that contain a specific coin."""
    collections = repo.get_collections_for_coin(coin_id)
    return [collection_to_response(c) for c in collections]
