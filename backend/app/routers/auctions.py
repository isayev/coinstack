"""API router for auction data management."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import auction as auction_crud
from app.schemas.auction import (
    AuctionDataCreate,
    AuctionDataUpdate,
    AuctionDataOut,
    AuctionDataListItem,
    PaginatedAuctions,
    AuctionFilters,
    PriceTrendResponse,
)

router = APIRouter(prefix="/auctions", tags=["auctions"])


@router.get("", response_model=PaginatedAuctions)
def list_auctions(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("auction_date"),
    sort_order: str = Query("desc"),
    # Filters
    auction_house: str | None = None,
    coin_id: int | None = None,
    reference_type_id: int | None = None,
    sold: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
):
    """
    List auction records with filtering and pagination.
    """
    filters = AuctionFilters(
        auction_house=auction_house,
        coin_id=coin_id,
        reference_type_id=reference_type_id,
        sold=sold,
        min_price=min_price,
        max_price=max_price,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )
    
    items, total = auction_crud.get_auctions(
        db,
        filters=filters,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    pages = (total + per_page - 1) // per_page
    
    return PaginatedAuctions(
        items=[AuctionDataListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/houses", response_model=list[str])
def list_auction_houses(db: Session = Depends(get_db)):
    """Get list of distinct auction houses."""
    return auction_crud.get_auction_houses(db)


@router.get("/coin/{coin_id}", response_model=list[AuctionDataOut])
def get_coin_auctions(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """Get all auction records for a specific coin."""
    return auction_crud.get_auctions_for_coin(db, coin_id)


@router.get("/comparables/{reference_type_id}", response_model=list[AuctionDataListItem])
def get_comparables(
    reference_type_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    """Get comparable auction records for a reference type."""
    items = auction_crud.get_comparables(db, reference_type_id, limit=limit)
    return [AuctionDataListItem.model_validate(item) for item in items]


@router.get("/stats/{reference_type_id}")
def get_price_stats(
    reference_type_id: int,
    db: Session = Depends(get_db),
    date_from: date | None = None,
    date_to: date | None = None,
):
    """Get price statistics for a reference type."""
    return auction_crud.get_price_stats(
        db,
        reference_type_id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{auction_id}", response_model=AuctionDataOut)
def get_auction(
    auction_id: int,
    db: Session = Depends(get_db),
):
    """Get a single auction record by ID."""
    auction = auction_crud.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


@router.post("", response_model=AuctionDataOut, status_code=201)
def create_auction(
    data: AuctionDataCreate,
    db: Session = Depends(get_db),
):
    """Create a new auction record manually."""
    # Check for duplicate URL
    existing = auction_crud.get_auction_by_url(db, data.url)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Auction with URL already exists (ID: {existing.id})",
        )
    
    return auction_crud.create_auction(db, data)


@router.put("/{auction_id}", response_model=AuctionDataOut)
def update_auction(
    auction_id: int,
    data: AuctionDataUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing auction record."""
    auction = auction_crud.update_auction(db, auction_id, data)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    return auction


@router.delete("/{auction_id}", status_code=204)
def delete_auction(
    auction_id: int,
    db: Session = Depends(get_db),
):
    """Delete an auction record."""
    if not auction_crud.delete_auction(db, auction_id):
        raise HTTPException(status_code=404, detail="Auction not found")


@router.post("/{auction_id}/link/{coin_id}", response_model=AuctionDataOut)
def link_auction_to_coin(
    auction_id: int,
    coin_id: int,
    db: Session = Depends(get_db),
):
    """Link an auction record to a coin."""
    auction = auction_crud.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    # Update the coin_id
    data = AuctionDataUpdate(coin_id=coin_id)
    return auction_crud.update_auction(db, auction_id, data)


@router.delete("/{auction_id}/link", response_model=AuctionDataOut)
def unlink_auction_from_coin(
    auction_id: int,
    db: Session = Depends(get_db),
):
    """Unlink an auction record from its coin."""
    auction = auction_crud.get_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=404, detail="Auction not found")
    
    auction.coin_id = None
    db.commit()
    db.refresh(auction)
    return auction
