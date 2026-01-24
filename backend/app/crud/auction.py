"""CRUD operations for auction data."""

from datetime import date
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session

from app.models.auction_data import AuctionData
from app.schemas.auction import (
    AuctionDataCreate,
    AuctionDataUpdate,
    AuctionFilters,
)


def get_auction(db: Session, auction_id: int) -> AuctionData | None:
    """Get a single auction record by ID."""
    return db.query(AuctionData).filter(AuctionData.id == auction_id).first()


def get_auction_by_url(db: Session, url: str) -> AuctionData | None:
    """Get an auction record by URL."""
    return db.query(AuctionData).filter(AuctionData.url == url).first()


def get_auctions(
    db: Session,
    filters: AuctionFilters | None = None,
    page: int = 1,
    per_page: int = 20,
    sort_by: str = "auction_date",
    sort_order: str = "desc",
) -> tuple[list[AuctionData], int]:
    """
    Get paginated auction records with optional filtering.
    
    Args:
        db: Database session
        filters: Optional filters
        page: Page number (1-indexed)
        per_page: Items per page
        sort_by: Field to sort by
        sort_order: Sort direction (asc/desc)
        
    Returns:
        Tuple of (items, total_count)
    """
    query = db.query(AuctionData)
    
    # Apply filters
    if filters:
        if filters.auction_house:
            query = query.filter(AuctionData.auction_house.ilike(f"%{filters.auction_house}%"))
        
        if filters.coin_id is not None:
            query = query.filter(AuctionData.coin_id == filters.coin_id)
        
        if filters.reference_type_id is not None:
            query = query.filter(AuctionData.reference_type_id == filters.reference_type_id)
        
        if filters.sold is not None:
            query = query.filter(AuctionData.sold == filters.sold)
        
        if filters.min_price is not None:
            query = query.filter(AuctionData.hammer_price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(AuctionData.hammer_price <= filters.max_price)
        
        if filters.date_from:
            query = query.filter(AuctionData.auction_date >= filters.date_from)
        
        if filters.date_to:
            query = query.filter(AuctionData.auction_date <= filters.date_to)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(
                or_(
                    AuctionData.title.ilike(search_term),
                    AuctionData.description.ilike(search_term),
                    AuctionData.auction_house.ilike(search_term),
                    AuctionData.sale_name.ilike(search_term),
                )
            )
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(AuctionData, sort_by, AuctionData.auction_date)
    if sort_order.lower() == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    
    # Handle nulls in sorting
    if sort_order.lower() == "desc":
        query = query.order_by(sort_column.nulls_last())
    else:
        query = query.order_by(sort_column.nulls_first())
    
    # Apply pagination
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    return items, total


def get_auctions_for_coin(db: Session, coin_id: int) -> list[AuctionData]:
    """Get all auction records linked to a specific coin."""
    return (
        db.query(AuctionData)
        .filter(AuctionData.coin_id == coin_id)
        .order_by(AuctionData.auction_date.desc().nulls_last())
        .all()
    )


def get_comparables(
    db: Session,
    reference_type_id: int,
    limit: int = 50,
) -> list[AuctionData]:
    """
    Get comparable auction records for a reference type.
    
    Args:
        db: Database session
        reference_type_id: Reference type ID to find comparables for
        limit: Maximum number of results
        
    Returns:
        List of comparable auction records
    """
    return (
        db.query(AuctionData)
        .filter(
            AuctionData.reference_type_id == reference_type_id,
            AuctionData.sold == True,
            AuctionData.hammer_price.isnot(None),
        )
        .order_by(AuctionData.auction_date.desc().nulls_last())
        .limit(limit)
        .all()
    )


def get_auction_houses(db: Session) -> list[str]:
    """Get list of distinct auction houses."""
    result = (
        db.query(AuctionData.auction_house)
        .distinct()
        .order_by(AuctionData.auction_house)
        .all()
    )
    return [r[0] for r in result if r[0]]


def create_auction(db: Session, data: AuctionDataCreate) -> AuctionData:
    """Create a new auction record."""
    auction = AuctionData(**data.model_dump(exclude_none=True))
    db.add(auction)
    db.commit()
    db.refresh(auction)
    return auction


def update_auction(
    db: Session,
    auction_id: int,
    data: AuctionDataUpdate,
) -> AuctionData | None:
    """Update an existing auction record."""
    auction = get_auction(db, auction_id)
    if not auction:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(auction, key, value)
    
    db.commit()
    db.refresh(auction)
    return auction


def delete_auction(db: Session, auction_id: int) -> bool:
    """Delete an auction record."""
    auction = get_auction(db, auction_id)
    if not auction:
        return False
    
    db.delete(auction)
    db.commit()
    return True


def upsert_auction(
    db: Session,
    url: str,
    data: dict,
) -> tuple[AuctionData, bool]:
    """
    Create or update auction record by URL.
    
    Args:
        db: Database session
        url: Auction URL (unique identifier)
        data: Auction data dict
        
    Returns:
        Tuple of (auction_record, created)
    """
    existing = get_auction_by_url(db, url)
    
    if existing:
        # Update
        for key, value in data.items():
            if value is not None and hasattr(existing, key):
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing, False
    else:
        # Create
        data["url"] = url
        auction = AuctionData(**data)
        db.add(auction)
        db.commit()
        db.refresh(auction)
        return auction, True


def get_price_stats(
    db: Session,
    reference_type_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """
    Get price statistics for a reference type.
    
    Args:
        db: Database session
        reference_type_id: Reference type ID
        date_from: Optional start date
        date_to: Optional end date
        
    Returns:
        Dict with price statistics
    """
    query = db.query(
        func.count(AuctionData.id).label("count"),
        func.min(AuctionData.hammer_price).label("min_price"),
        func.max(AuctionData.hammer_price).label("max_price"),
        func.avg(AuctionData.hammer_price).label("avg_price"),
    ).filter(
        AuctionData.reference_type_id == reference_type_id,
        AuctionData.sold == True,
        AuctionData.hammer_price.isnot(None),
    )
    
    if date_from:
        query = query.filter(AuctionData.auction_date >= date_from)
    if date_to:
        query = query.filter(AuctionData.auction_date <= date_to)
    
    result = query.first()
    
    # Calculate median (SQLite doesn't have built-in median)
    prices_query = db.query(AuctionData.hammer_price).filter(
        AuctionData.reference_type_id == reference_type_id,
        AuctionData.sold == True,
        AuctionData.hammer_price.isnot(None),
    )
    if date_from:
        prices_query = prices_query.filter(AuctionData.auction_date >= date_from)
    if date_to:
        prices_query = prices_query.filter(AuctionData.auction_date <= date_to)
    
    prices = [p[0] for p in prices_query.all()]
    median_price = None
    if prices:
        prices.sort()
        n = len(prices)
        if n % 2 == 0:
            median_price = (prices[n//2 - 1] + prices[n//2]) / 2
        else:
            median_price = prices[n//2]
    
    return {
        "count": result.count if result else 0,
        "min_price": float(result.min_price) if result and result.min_price else None,
        "max_price": float(result.max_price) if result and result.max_price else None,
        "avg_price": float(result.avg_price) if result and result.avg_price else None,
        "median_price": float(median_price) if median_price else None,
    }
