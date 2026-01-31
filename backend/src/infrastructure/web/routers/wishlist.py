"""
Wishlist Router for CoinStack API (Schema V3 Phase 5).

Provides REST endpoints for wishlists, matches, and price alerts.

Endpoints:
- GET    /api/v2/wishlist                          - List wishlist items
- POST   /api/v2/wishlist                          - Create wishlist item
- GET    /api/v2/wishlist/{id}                     - Get wishlist item
- PUT    /api/v2/wishlist/{id}                     - Update wishlist item
- DELETE /api/v2/wishlist/{id}                     - Delete wishlist item
- POST   /api/v2/wishlist/{id}/mark-acquired       - Mark as acquired

- GET    /api/v2/wishlist/{id}/matches             - List matches for item
- POST   /api/v2/wishlist/{id}/matches             - Add match
- PUT    /api/v2/wishlist/matches/{id}             - Update match
- POST   /api/v2/wishlist/matches/{id}/dismiss     - Dismiss match
- POST   /api/v2/wishlist/matches/{id}/save        - Save match

- GET    /api/v2/price-alerts                      - List alerts
- POST   /api/v2/price-alerts                      - Create alert
- GET    /api/v2/price-alerts/{id}                 - Get alert
- PUT    /api/v2/price-alerts/{id}                 - Update alert
- DELETE /api/v2/price-alerts/{id}                 - Delete alert
- POST   /api/v2/price-alerts/{id}/trigger         - Manually trigger alert
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import WishlistItem, WishlistMatch, PriceAlert
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.wishlist_item_repository import SqlAlchemyWishlistItemRepository
from src.infrastructure.repositories.wishlist_match_repository import SqlAlchemyWishlistMatchRepository
from src.infrastructure.repositories.price_alert_repository import SqlAlchemyPriceAlertRepository

router = APIRouter(
    prefix="/api/v2",
    tags=["Wishlist"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS - WISHLIST ITEMS
# =============================================================================

class WishlistItemCreateRequest(BaseModel):
    """Request to create a wishlist item."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    issuer: Optional[str] = None
    issuer_id: Optional[int] = None
    mint: Optional[str] = None
    mint_id: Optional[int] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    category: Optional[str] = None
    catalog_ref: Optional[str] = None
    catalog_ref_pattern: Optional[str] = None
    min_grade: Optional[str] = None
    min_grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    max_price: Optional[float] = None
    target_price: Optional[float] = None
    currency: str = "USD"
    priority: int = Field(2, ge=1, le=4)
    tags: Optional[str] = None
    series_slot_id: Optional[int] = None
    notify_on_match: bool = True
    notify_email: bool = False
    notes: Optional[str] = None


class WishlistItemUpdateRequest(BaseModel):
    """Request to update a wishlist item (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    issuer: Optional[str] = None
    issuer_id: Optional[int] = None
    mint: Optional[str] = None
    mint_id: Optional[int] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    category: Optional[str] = None
    catalog_ref: Optional[str] = None
    catalog_ref_pattern: Optional[str] = None
    min_grade: Optional[str] = None
    min_grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    max_price: Optional[float] = None
    target_price: Optional[float] = None
    currency: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=4)
    tags: Optional[str] = None
    series_slot_id: Optional[int] = None
    status: Optional[str] = None
    notify_on_match: Optional[bool] = None
    notify_email: Optional[bool] = None
    notes: Optional[str] = None


class WishlistItemResponse(BaseModel):
    """Response for a wishlist item."""
    id: int
    title: str
    description: Optional[str] = None
    issuer: Optional[str] = None
    issuer_id: Optional[int] = None
    mint: Optional[str] = None
    mint_id: Optional[int] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    category: Optional[str] = None
    catalog_ref: Optional[str] = None
    catalog_ref_pattern: Optional[str] = None
    min_grade: Optional[str] = None
    min_grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    max_price: Optional[float] = None
    target_price: Optional[float] = None
    currency: str
    priority: int
    tags: Optional[str] = None
    series_slot_id: Optional[int] = None
    status: str
    acquired_coin_id: Optional[int] = None
    acquired_at: Optional[str] = None
    acquired_price: Optional[float] = None
    notify_on_match: bool
    notify_email: bool
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WishlistItemListResponse(BaseModel):
    """Response for listing wishlist items."""
    items: List[WishlistItemResponse]
    total: int
    skip: int
    limit: int


class MarkAcquiredRequest(BaseModel):
    """Request to mark item as acquired."""
    coin_id: int
    acquired_price: Optional[float] = None


# =============================================================================
# REQUEST/RESPONSE SCHEMAS - MATCHES
# =============================================================================

class WishlistMatchCreateRequest(BaseModel):
    """Request to create a match."""
    match_type: str = Field(..., description="auction_lot, dealer_listing, ebay_listing, vcoins")
    match_source: Optional[str] = None
    match_id: str
    match_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    price: Optional[float] = None
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    currency: str = "USD"
    current_bid: Optional[float] = None
    auction_date: Optional[date] = None
    end_time: Optional[datetime] = None
    match_score: Optional[float] = None
    match_confidence: Optional[str] = None
    match_reasons: Optional[str] = None
    is_below_budget: Optional[bool] = None
    is_below_market: Optional[bool] = None
    value_score: Optional[float] = None
    notes: Optional[str] = None


class WishlistMatchUpdateRequest(BaseModel):
    """Request to update a match (all fields optional)."""
    match_type: Optional[str] = None
    match_source: Optional[str] = None
    match_url: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    price: Optional[float] = None
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    currency: Optional[str] = None
    current_bid: Optional[float] = None
    auction_date: Optional[date] = None
    end_time: Optional[datetime] = None
    match_score: Optional[float] = None
    match_confidence: Optional[str] = None
    match_reasons: Optional[str] = None
    is_below_budget: Optional[bool] = None
    is_below_market: Optional[bool] = None
    value_score: Optional[float] = None
    notes: Optional[str] = None


class WishlistMatchResponse(BaseModel):
    """Response for a match."""
    id: int
    wishlist_item_id: int
    match_type: str
    match_source: Optional[str] = None
    match_id: str
    match_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    price: Optional[float] = None
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    currency: str
    current_bid: Optional[float] = None
    auction_date: Optional[date] = None
    end_time: Optional[str] = None
    match_score: Optional[float] = None
    match_confidence: Optional[str] = None
    match_reasons: Optional[str] = None
    is_below_budget: Optional[bool] = None
    is_below_market: Optional[bool] = None
    value_score: Optional[float] = None
    notified: bool
    notified_at: Optional[str] = None
    dismissed: bool
    dismissed_at: Optional[str] = None
    saved: bool
    notes: Optional[str] = None
    created_at: Optional[str] = None


class WishlistMatchListResponse(BaseModel):
    """Response for listing matches."""
    wishlist_item_id: int
    matches: List[WishlistMatchResponse]
    total: int


# =============================================================================
# REQUEST/RESPONSE SCHEMAS - PRICE ALERTS
# =============================================================================

class PriceAlertCreateRequest(BaseModel):
    """Request to create a price alert."""
    attribution_key: Optional[str] = None
    coin_id: Optional[int] = None
    wishlist_item_id: Optional[int] = None
    trigger_type: str = Field(..., description="price_below, price_above, price_change_pct, new_listing, auction_soon")
    threshold_value: Optional[float] = None
    threshold_pct: Optional[float] = None
    threshold_grade: Optional[str] = None
    expires_at: Optional[datetime] = None
    notification_channel: Optional[str] = None
    cooldown_hours: int = 24
    notes: Optional[str] = None


class PriceAlertUpdateRequest(BaseModel):
    """Request to update a price alert (all fields optional)."""
    attribution_key: Optional[str] = None
    coin_id: Optional[int] = None
    wishlist_item_id: Optional[int] = None
    trigger_type: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_pct: Optional[float] = None
    threshold_grade: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    notification_channel: Optional[str] = None
    cooldown_hours: Optional[int] = None
    notes: Optional[str] = None


class PriceAlertResponse(BaseModel):
    """Response for a price alert."""
    id: int
    attribution_key: Optional[str] = None
    coin_id: Optional[int] = None
    wishlist_item_id: Optional[int] = None
    trigger_type: str
    threshold_value: Optional[float] = None
    threshold_pct: Optional[float] = None
    threshold_grade: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    triggered_at: Optional[str] = None
    expires_at: Optional[str] = None
    notification_sent: bool
    notification_sent_at: Optional[str] = None
    notification_channel: Optional[str] = None
    cooldown_hours: int
    last_triggered_at: Optional[str] = None
    notes: Optional[str] = None


class PriceAlertListResponse(BaseModel):
    """Response for listing alerts."""
    alerts: List[PriceAlertResponse]
    total: int
    skip: int
    limit: int


# =============================================================================
# VALID VALUES
# =============================================================================

VALID_STATUSES = {"wanted", "watching", "bidding", "acquired", "cancelled"}
VALID_MATCH_TYPES = {"auction_lot", "dealer_listing", "ebay_listing", "vcoins"}
VALID_MATCH_CONFIDENCE = {"exact", "high", "medium", "possible"}
VALID_TRIGGER_TYPES = {"price_below", "price_above", "price_change_pct", "new_listing", "auction_soon"}
VALID_ALERT_STATUSES = {"active", "triggered", "paused", "expired", "deleted"}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_wishlist_repo(db: Session = Depends(get_db)) -> SqlAlchemyWishlistItemRepository:
    """Get wishlist item repository instance."""
    return SqlAlchemyWishlistItemRepository(db)


def get_match_repo(db: Session = Depends(get_db)) -> SqlAlchemyWishlistMatchRepository:
    """Get match repository instance."""
    return SqlAlchemyWishlistMatchRepository(db)


def get_alert_repo(db: Session = Depends(get_db)) -> SqlAlchemyPriceAlertRepository:
    """Get alert repository instance."""
    return SqlAlchemyPriceAlertRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def item_to_response(item: WishlistItem) -> WishlistItemResponse:
    """Convert domain WishlistItem to API response."""
    return WishlistItemResponse(
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
        max_price=float(item.max_price) if item.max_price else None,
        target_price=float(item.target_price) if item.target_price else None,
        currency=item.currency,
        priority=item.priority,
        tags=item.tags,
        series_slot_id=item.series_slot_id,
        status=item.status,
        acquired_coin_id=item.acquired_coin_id,
        acquired_at=item.acquired_at.isoformat() if item.acquired_at else None,
        acquired_price=float(item.acquired_price) if item.acquired_price else None,
        notify_on_match=item.notify_on_match,
        notify_email=item.notify_email,
        notes=item.notes,
        created_at=item.created_at.isoformat() if item.created_at else None,
        updated_at=item.updated_at.isoformat() if item.updated_at else None,
    )


def match_to_response(match: WishlistMatch) -> WishlistMatchResponse:
    """Convert domain WishlistMatch to API response."""
    return WishlistMatchResponse(
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
        price=float(match.price) if match.price else None,
        estimate_low=float(match.estimate_low) if match.estimate_low else None,
        estimate_high=float(match.estimate_high) if match.estimate_high else None,
        currency=match.currency,
        current_bid=float(match.current_bid) if match.current_bid else None,
        auction_date=match.auction_date,
        end_time=match.end_time.isoformat() if match.end_time else None,
        match_score=float(match.match_score) if match.match_score else None,
        match_confidence=match.match_confidence,
        match_reasons=match.match_reasons,
        is_below_budget=match.is_below_budget,
        is_below_market=match.is_below_market,
        value_score=float(match.value_score) if match.value_score else None,
        notified=match.notified,
        notified_at=match.notified_at.isoformat() if match.notified_at else None,
        dismissed=match.dismissed,
        dismissed_at=match.dismissed_at.isoformat() if match.dismissed_at else None,
        saved=match.saved,
        notes=match.notes,
        created_at=match.created_at.isoformat() if match.created_at else None,
    )


def alert_to_response(alert: PriceAlert) -> PriceAlertResponse:
    """Convert domain PriceAlert to API response."""
    return PriceAlertResponse(
        id=alert.id,
        attribution_key=alert.attribution_key,
        coin_id=alert.coin_id,
        wishlist_item_id=alert.wishlist_item_id,
        trigger_type=alert.trigger_type,
        threshold_value=float(alert.threshold_value) if alert.threshold_value else None,
        threshold_pct=float(alert.threshold_pct) if alert.threshold_pct else None,
        threshold_grade=alert.threshold_grade,
        status=alert.status,
        created_at=alert.created_at.isoformat() if alert.created_at else None,
        triggered_at=alert.triggered_at.isoformat() if alert.triggered_at else None,
        expires_at=alert.expires_at.isoformat() if alert.expires_at else None,
        notification_sent=alert.notification_sent,
        notification_sent_at=alert.notification_sent_at.isoformat() if alert.notification_sent_at else None,
        notification_channel=alert.notification_channel,
        cooldown_hours=alert.cooldown_hours,
        last_triggered_at=alert.last_triggered_at.isoformat() if alert.last_triggered_at else None,
        notes=alert.notes,
    )


# =============================================================================
# WISHLIST ITEM ENDPOINTS
# =============================================================================

@router.get(
    "/wishlist",
    response_model=WishlistItemListResponse,
    summary="List wishlist items",
    description="Get all wishlist items with optional filters."
)
def list_wishlist_items(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, ge=1, le=4, description="Filter by priority"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """List wishlist items."""
    if status and status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    items = repo.list_all(status=status, priority=priority, category=category, skip=skip, limit=limit)
    total = repo.count(status=status, priority=priority)

    return WishlistItemListResponse(
        items=[item_to_response(i) for i in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/wishlist",
    response_model=WishlistItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create wishlist item",
    description="Create a new wishlist item."
)
def create_wishlist_item(
    request: WishlistItemCreateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """Create a wishlist item."""
    item = WishlistItem(
        title=request.title,
        description=request.description,
        issuer=request.issuer,
        issuer_id=request.issuer_id,
        mint=request.mint,
        mint_id=request.mint_id,
        year_start=request.year_start,
        year_end=request.year_end,
        denomination=request.denomination,
        metal=request.metal,
        category=request.category,
        catalog_ref=request.catalog_ref,
        catalog_ref_pattern=request.catalog_ref_pattern,
        min_grade=request.min_grade,
        min_grade_numeric=request.min_grade_numeric,
        condition_notes=request.condition_notes,
        max_price=Decimal(str(request.max_price)) if request.max_price else None,
        target_price=Decimal(str(request.target_price)) if request.target_price else None,
        currency=request.currency,
        priority=request.priority,
        tags=request.tags,
        series_slot_id=request.series_slot_id,
        notify_on_match=request.notify_on_match,
        notify_email=request.notify_email,
        notes=request.notes,
    )

    created = repo.create(item)
    db.commit()

    return item_to_response(created)


@router.get(
    "/wishlist/{item_id}",
    response_model=WishlistItemResponse,
    summary="Get wishlist item",
    description="Get a wishlist item by ID."
)
def get_wishlist_item(
    item_id: int,
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """Get a wishlist item."""
    item = repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")
    return item_to_response(item)


@router.put(
    "/wishlist/{item_id}",
    response_model=WishlistItemResponse,
    summary="Update wishlist item",
    description="Update an existing wishlist item."
)
def update_wishlist_item(
    item_id: int,
    request: WishlistItemUpdateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """Update a wishlist item."""
    existing = repo.get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")

    if request.status and request.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{request.status}'. Must be one of: {', '.join(sorted(VALID_STATUSES))}"
        )

    updated_item = WishlistItem(
        id=existing.id,
        title=request.title if request.title is not None else existing.title,
        description=request.description if request.description is not None else existing.description,
        issuer=request.issuer if request.issuer is not None else existing.issuer,
        issuer_id=request.issuer_id if request.issuer_id is not None else existing.issuer_id,
        mint=request.mint if request.mint is not None else existing.mint,
        mint_id=request.mint_id if request.mint_id is not None else existing.mint_id,
        year_start=request.year_start if request.year_start is not None else existing.year_start,
        year_end=request.year_end if request.year_end is not None else existing.year_end,
        denomination=request.denomination if request.denomination is not None else existing.denomination,
        metal=request.metal if request.metal is not None else existing.metal,
        category=request.category if request.category is not None else existing.category,
        catalog_ref=request.catalog_ref if request.catalog_ref is not None else existing.catalog_ref,
        catalog_ref_pattern=request.catalog_ref_pattern if request.catalog_ref_pattern is not None else existing.catalog_ref_pattern,
        min_grade=request.min_grade if request.min_grade is not None else existing.min_grade,
        min_grade_numeric=request.min_grade_numeric if request.min_grade_numeric is not None else existing.min_grade_numeric,
        condition_notes=request.condition_notes if request.condition_notes is not None else existing.condition_notes,
        max_price=Decimal(str(request.max_price)) if request.max_price is not None else existing.max_price,
        target_price=Decimal(str(request.target_price)) if request.target_price is not None else existing.target_price,
        currency=request.currency if request.currency is not None else existing.currency,
        priority=request.priority if request.priority is not None else existing.priority,
        tags=request.tags if request.tags is not None else existing.tags,
        series_slot_id=request.series_slot_id if request.series_slot_id is not None else existing.series_slot_id,
        status=request.status if request.status is not None else existing.status,
        notify_on_match=request.notify_on_match if request.notify_on_match is not None else existing.notify_on_match,
        notify_email=request.notify_email if request.notify_email is not None else existing.notify_email,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = repo.update(item_id, updated_item)
    db.commit()

    return item_to_response(updated)


@router.delete(
    "/wishlist/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete wishlist item",
    description="Delete a wishlist item."
)
def delete_wishlist_item(
    item_id: int,
    db: Session = Depends(get_db),
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """Delete a wishlist item."""
    existing = repo.get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")

    repo.delete(item_id)
    db.commit()

    return None


@router.post(
    "/wishlist/{item_id}/mark-acquired",
    response_model=WishlistItemResponse,
    summary="Mark as acquired",
    description="Mark a wishlist item as acquired."
)
def mark_wishlist_item_acquired(
    item_id: int,
    request: MarkAcquiredRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
):
    """Mark a wishlist item as acquired."""
    existing = repo.get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")

    acquired_price = Decimal(str(request.acquired_price)) if request.acquired_price else None
    updated = repo.mark_acquired(item_id, request.coin_id, acquired_price)
    db.commit()

    return item_to_response(updated)


# =============================================================================
# MATCH ENDPOINTS
# =============================================================================

@router.get(
    "/wishlist/{item_id}/matches",
    response_model=WishlistMatchListResponse,
    summary="List matches",
    description="Get all matches for a wishlist item."
)
def list_matches(
    item_id: int,
    include_dismissed: bool = Query(False, description="Include dismissed matches"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    wishlist_repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
    match_repo: SqlAlchemyWishlistMatchRepository = Depends(get_match_repo),
):
    """List matches for a wishlist item."""
    item = wishlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")

    matches = match_repo.get_by_wishlist_item_id(item_id, include_dismissed=include_dismissed, skip=skip, limit=limit)
    total = match_repo.count_by_wishlist_item_id(item_id, include_dismissed=include_dismissed)

    return WishlistMatchListResponse(
        wishlist_item_id=item_id,
        matches=[match_to_response(m) for m in matches],
        total=total,
    )


@router.post(
    "/wishlist/{item_id}/matches",
    response_model=WishlistMatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create match",
    description="Add a match to a wishlist item."
)
def create_match(
    item_id: int,
    request: WishlistMatchCreateRequest,
    db: Session = Depends(get_db),
    wishlist_repo: SqlAlchemyWishlistItemRepository = Depends(get_wishlist_repo),
    match_repo: SqlAlchemyWishlistMatchRepository = Depends(get_match_repo),
):
    """Create a match."""
    item = wishlist_repo.get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Wishlist item {item_id} not found")

    if request.match_type not in VALID_MATCH_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid match_type '{request.match_type}'. Must be one of: {', '.join(sorted(VALID_MATCH_TYPES))}"
        )

    if request.match_confidence and request.match_confidence not in VALID_MATCH_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid match_confidence '{request.match_confidence}'. Must be one of: {', '.join(sorted(VALID_MATCH_CONFIDENCE))}"
        )

    match = WishlistMatch(
        match_type=request.match_type,
        match_source=request.match_source,
        match_id=request.match_id,
        match_url=request.match_url,
        title=request.title,
        description=request.description,
        image_url=request.image_url,
        grade=request.grade,
        grade_numeric=request.grade_numeric,
        condition_notes=request.condition_notes,
        price=Decimal(str(request.price)) if request.price else None,
        estimate_low=Decimal(str(request.estimate_low)) if request.estimate_low else None,
        estimate_high=Decimal(str(request.estimate_high)) if request.estimate_high else None,
        currency=request.currency,
        current_bid=Decimal(str(request.current_bid)) if request.current_bid else None,
        auction_date=request.auction_date,
        end_time=request.end_time,
        match_score=Decimal(str(request.match_score)) if request.match_score else None,
        match_confidence=request.match_confidence,
        match_reasons=request.match_reasons,
        is_below_budget=request.is_below_budget,
        is_below_market=request.is_below_market,
        value_score=Decimal(str(request.value_score)) if request.value_score else None,
        notes=request.notes,
    )

    created = match_repo.create(item_id, match)
    db.commit()

    return match_to_response(created)


@router.put(
    "/wishlist/matches/{match_id}",
    response_model=WishlistMatchResponse,
    summary="Update match",
    description="Update an existing match."
)
def update_match(
    match_id: int,
    request: WishlistMatchUpdateRequest,
    db: Session = Depends(get_db),
    match_repo: SqlAlchemyWishlistMatchRepository = Depends(get_match_repo),
):
    """Update a match."""
    existing = match_repo.get_by_id(match_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    if request.match_type and request.match_type not in VALID_MATCH_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid match_type '{request.match_type}'. Must be one of: {', '.join(sorted(VALID_MATCH_TYPES))}"
        )

    if request.match_confidence and request.match_confidence not in VALID_MATCH_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid match_confidence '{request.match_confidence}'. Must be one of: {', '.join(sorted(VALID_MATCH_CONFIDENCE))}"
        )

    updated_match = WishlistMatch(
        id=existing.id,
        wishlist_item_id=existing.wishlist_item_id,
        match_type=request.match_type if request.match_type is not None else existing.match_type,
        match_source=request.match_source if request.match_source is not None else existing.match_source,
        match_id=existing.match_id,
        match_url=request.match_url if request.match_url is not None else existing.match_url,
        title=request.title if request.title is not None else existing.title,
        description=request.description if request.description is not None else existing.description,
        image_url=request.image_url if request.image_url is not None else existing.image_url,
        grade=request.grade if request.grade is not None else existing.grade,
        grade_numeric=request.grade_numeric if request.grade_numeric is not None else existing.grade_numeric,
        condition_notes=request.condition_notes if request.condition_notes is not None else existing.condition_notes,
        price=Decimal(str(request.price)) if request.price is not None else existing.price,
        estimate_low=Decimal(str(request.estimate_low)) if request.estimate_low is not None else existing.estimate_low,
        estimate_high=Decimal(str(request.estimate_high)) if request.estimate_high is not None else existing.estimate_high,
        currency=request.currency if request.currency is not None else existing.currency,
        current_bid=Decimal(str(request.current_bid)) if request.current_bid is not None else existing.current_bid,
        auction_date=request.auction_date if request.auction_date is not None else existing.auction_date,
        end_time=request.end_time if request.end_time is not None else existing.end_time,
        match_score=Decimal(str(request.match_score)) if request.match_score is not None else existing.match_score,
        match_confidence=request.match_confidence if request.match_confidence is not None else existing.match_confidence,
        match_reasons=request.match_reasons if request.match_reasons is not None else existing.match_reasons,
        is_below_budget=request.is_below_budget if request.is_below_budget is not None else existing.is_below_budget,
        is_below_market=request.is_below_market if request.is_below_market is not None else existing.is_below_market,
        value_score=Decimal(str(request.value_score)) if request.value_score is not None else existing.value_score,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = match_repo.update(match_id, updated_match)
    db.commit()

    return match_to_response(updated)


@router.post(
    "/wishlist/matches/{match_id}/dismiss",
    response_model=WishlistMatchResponse,
    summary="Dismiss match",
    description="Dismiss a match."
)
def dismiss_match(
    match_id: int,
    db: Session = Depends(get_db),
    match_repo: SqlAlchemyWishlistMatchRepository = Depends(get_match_repo),
):
    """Dismiss a match."""
    existing = match_repo.get_by_id(match_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    updated = match_repo.dismiss(match_id)
    db.commit()

    return match_to_response(updated)


@router.post(
    "/wishlist/matches/{match_id}/save",
    response_model=WishlistMatchResponse,
    summary="Save match",
    description="Save/bookmark a match."
)
def save_match(
    match_id: int,
    db: Session = Depends(get_db),
    match_repo: SqlAlchemyWishlistMatchRepository = Depends(get_match_repo),
):
    """Save a match."""
    existing = match_repo.get_by_id(match_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found")

    updated = match_repo.save(match_id)
    db.commit()

    return match_to_response(updated)


# =============================================================================
# PRICE ALERT ENDPOINTS
# =============================================================================

@router.get(
    "/price-alerts",
    response_model=PriceAlertListResponse,
    summary="List alerts",
    description="Get all price alerts."
)
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status"),
    trigger_type: Optional[str] = Query(None, description="Filter by trigger type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """List price alerts."""
    if status and status not in VALID_ALERT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{status}'. Must be one of: {', '.join(sorted(VALID_ALERT_STATUSES))}"
        )

    if trigger_type and trigger_type not in VALID_TRIGGER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_type '{trigger_type}'. Must be one of: {', '.join(sorted(VALID_TRIGGER_TYPES))}"
        )

    alerts = repo.list_all(status=status, trigger_type=trigger_type, skip=skip, limit=limit)
    total = repo.count(status=status)

    return PriceAlertListResponse(
        alerts=[alert_to_response(a) for a in alerts],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/price-alerts",
    response_model=PriceAlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert",
    description="Create a new price alert."
)
def create_alert(
    request: PriceAlertCreateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """Create a price alert."""
    if request.trigger_type not in VALID_TRIGGER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_type '{request.trigger_type}'. Must be one of: {', '.join(sorted(VALID_TRIGGER_TYPES))}"
        )

    alert = PriceAlert(
        attribution_key=request.attribution_key,
        coin_id=request.coin_id,
        wishlist_item_id=request.wishlist_item_id,
        trigger_type=request.trigger_type,
        threshold_value=Decimal(str(request.threshold_value)) if request.threshold_value else None,
        threshold_pct=Decimal(str(request.threshold_pct)) if request.threshold_pct else None,
        threshold_grade=request.threshold_grade,
        expires_at=request.expires_at,
        notification_channel=request.notification_channel,
        cooldown_hours=request.cooldown_hours,
        notes=request.notes,
    )

    created = repo.create(alert)
    db.commit()

    return alert_to_response(created)


@router.get(
    "/price-alerts/{alert_id}",
    response_model=PriceAlertResponse,
    summary="Get alert",
    description="Get a price alert by ID."
)
def get_alert(
    alert_id: int,
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """Get a price alert."""
    alert = repo.get_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert_to_response(alert)


@router.put(
    "/price-alerts/{alert_id}",
    response_model=PriceAlertResponse,
    summary="Update alert",
    description="Update an existing price alert."
)
def update_alert(
    alert_id: int,
    request: PriceAlertUpdateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """Update a price alert."""
    existing = repo.get_by_id(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    if request.trigger_type and request.trigger_type not in VALID_TRIGGER_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid trigger_type '{request.trigger_type}'. Must be one of: {', '.join(sorted(VALID_TRIGGER_TYPES))}"
        )

    if request.status and request.status not in VALID_ALERT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{request.status}'. Must be one of: {', '.join(sorted(VALID_ALERT_STATUSES))}"
        )

    updated_alert = PriceAlert(
        id=existing.id,
        attribution_key=request.attribution_key if request.attribution_key is not None else existing.attribution_key,
        coin_id=request.coin_id if request.coin_id is not None else existing.coin_id,
        wishlist_item_id=request.wishlist_item_id if request.wishlist_item_id is not None else existing.wishlist_item_id,
        trigger_type=request.trigger_type if request.trigger_type is not None else existing.trigger_type,
        threshold_value=Decimal(str(request.threshold_value)) if request.threshold_value is not None else existing.threshold_value,
        threshold_pct=Decimal(str(request.threshold_pct)) if request.threshold_pct is not None else existing.threshold_pct,
        threshold_grade=request.threshold_grade if request.threshold_grade is not None else existing.threshold_grade,
        status=request.status if request.status is not None else existing.status,
        expires_at=request.expires_at if request.expires_at is not None else existing.expires_at,
        notification_channel=request.notification_channel if request.notification_channel is not None else existing.notification_channel,
        cooldown_hours=request.cooldown_hours if request.cooldown_hours is not None else existing.cooldown_hours,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = repo.update(alert_id, updated_alert)
    db.commit()

    return alert_to_response(updated)


@router.delete(
    "/price-alerts/{alert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete alert",
    description="Delete a price alert."
)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """Delete a price alert."""
    existing = repo.get_by_id(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    repo.delete(alert_id)
    db.commit()

    return None


@router.post(
    "/price-alerts/{alert_id}/trigger",
    response_model=PriceAlertResponse,
    summary="Trigger alert",
    description="Manually trigger a price alert."
)
def trigger_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    repo: SqlAlchemyPriceAlertRepository = Depends(get_alert_repo),
):
    """Manually trigger a price alert."""
    existing = repo.get_by_id(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    updated = repo.trigger(alert_id)
    db.commit()

    return alert_to_response(updated)
