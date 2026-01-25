"""
Provenance Router for CoinStack API.

Provides REST endpoints for managing coin provenance (ownership history).

Endpoints:
- GET /api/v2/coins/{coin_id}/provenance - Get provenance chain for a coin
- POST /api/v2/coins/{coin_id}/provenance - Add provenance entry
- PUT /api/v2/provenance/{id} - Update provenance entry
- DELETE /api/v2/provenance/{id} - Delete provenance entry
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.provenance_repository import SqlAlchemyProvenanceRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(tags=["Provenance"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class ProvenanceEntryCreate(BaseModel):
    """Request to create a provenance entry."""
    event_type: str = Field(..., description="Type: auction, dealer, collection, private_sale")
    source_name: str = Field(..., description="Name of auction house, dealer, or collection")
    event_date: Optional[date] = Field(None, description="Date of the event")
    lot_number: Optional[str] = Field(None, description="Lot number if auction")
    hammer_price: Optional[float] = Field(None, description="Hammer price")
    total_price: Optional[float] = Field(None, description="Total price including premium")
    currency: Optional[str] = Field(None, description="Currency code (USD, EUR, GBP)")
    notes: Optional[str] = Field(None, description="Additional notes")
    url: Optional[str] = Field(None, description="URL to source documentation")
    sort_order: int = Field(0, description="Display order (0 = earliest)")


class ProvenanceEntryUpdate(BaseModel):
    """Request to update a provenance entry."""
    event_type: Optional[str] = None
    source_name: Optional[str] = None
    event_date: Optional[date] = None
    lot_number: Optional[str] = None
    hammer_price: Optional[float] = None
    total_price: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    sort_order: Optional[int] = None


class ProvenanceEntryResponse(BaseModel):
    """Response for a provenance entry."""
    id: int
    coin_id: int
    event_type: str
    source_name: str
    event_date: Optional[date]
    lot_number: Optional[str]
    hammer_price: Optional[float]
    total_price: Optional[float]
    currency: Optional[str]
    notes: Optional[str]
    url: Optional[str]
    sort_order: int


class ProvenanceChainResponse(BaseModel):
    """Response for a coin's full provenance chain."""
    coin_id: int
    entries: List[ProvenanceEntryResponse]
    earliest_known: Optional[int] = Field(None, description="Year of earliest known provenance")


# =============================================================================
# DEPENDENCY
# =============================================================================

def get_provenance_repo(db: Session = Depends(get_db)) -> SqlAlchemyProvenanceRepository:
    """Get provenance repository instance."""
    return SqlAlchemyProvenanceRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/coins/{coin_id}/provenance",
    response_model=ProvenanceChainResponse,
    summary="Get provenance chain",
    description="Get the full provenance (ownership history) chain for a coin.",
)
def get_provenance(
    coin_id: int,
    db: Session = Depends(get_db),
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Get provenance chain for a coin.
    
    Returns all provenance entries ordered by sort_order (earliest first).
    """
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    # Get provenance entries from ORM directly for full details
    from src.infrastructure.persistence.orm import ProvenanceEventModel
    models = db.query(ProvenanceEventModel).filter(
        ProvenanceEventModel.coin_id == coin_id
    ).order_by(ProvenanceEventModel.sort_order.asc()).all()
    
    entries = []
    earliest_year = None
    
    for m in models:
        # Determine source name
        source_name = ""
        if m.event_type == "auction":
            source_name = m.auction_house or ""
        elif m.event_type == "dealer":
            source_name = m.dealer_name or ""
        elif m.event_type == "collection":
            source_name = m.collection_name or ""
        else:
            source_name = m.auction_house or m.dealer_name or m.collection_name or ""
        
        entries.append(ProvenanceEntryResponse(
            id=m.id,
            coin_id=m.coin_id,
            event_type=m.event_type,
            source_name=source_name,
            event_date=m.event_date,
            lot_number=m.lot_number,
            hammer_price=float(m.hammer_price) if m.hammer_price else None,
            total_price=float(m.total_price) if m.total_price else None,
            currency=m.currency,
            notes=m.notes,
            url=m.url,
            sort_order=m.sort_order or 0,
        ))
        
        # Track earliest year
        if m.event_date:
            year = m.event_date.year
            if earliest_year is None or year < earliest_year:
                earliest_year = year
    
    return ProvenanceChainResponse(
        coin_id=coin_id,
        entries=entries,
        earliest_known=earliest_year,
    )


@router.post(
    "/coins/{coin_id}/provenance",
    response_model=ProvenanceEntryResponse,
    status_code=201,
    summary="Add provenance entry",
    description="Add a new provenance entry to a coin's ownership history.",
)
def add_provenance(
    coin_id: int,
    request: ProvenanceEntryCreate,
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Add a provenance entry to a coin.
    
    Valid event_type values:
    - auction: Auction house sale
    - dealer: Dealer purchase/sale
    - collection: Named collection
    - private_sale: Private transaction
    """
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    # Validate event type
    valid_types = {"auction", "dealer", "collection", "private_sale", "publication"}
    if request.event_type not in valid_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid event_type. Must be one of: {', '.join(valid_types)}"
        )
    
    model = provenance_repo.add(
        coin_id=coin_id,
        event_type=request.event_type,
        source_name=request.source_name,
        event_date=request.event_date,
        lot_number=request.lot_number,
        hammer_price=Decimal(str(request.hammer_price)) if request.hammer_price else None,
        total_price=Decimal(str(request.total_price)) if request.total_price else None,
        currency=request.currency,
        notes=request.notes,
        url=request.url,
        sort_order=request.sort_order,
    )
    
    return ProvenanceEntryResponse(
        id=model.id,
        coin_id=model.coin_id,
        event_type=model.event_type,
        source_name=request.source_name,
        event_date=model.event_date,
        lot_number=model.lot_number,
        hammer_price=float(model.hammer_price) if model.hammer_price else None,
        total_price=float(model.total_price) if model.total_price else None,
        currency=model.currency,
        notes=model.notes,
        url=model.url,
        sort_order=model.sort_order or 0,
    )


@router.put(
    "/provenance/{provenance_id}",
    response_model=ProvenanceEntryResponse,
    summary="Update provenance entry",
    description="Update an existing provenance entry.",
)
def update_provenance(
    provenance_id: int,
    request: ProvenanceEntryUpdate,
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
):
    """
    Update a provenance entry.
    
    Only provided fields will be updated.
    """
    model = provenance_repo.update(
        provenance_id=provenance_id,
        event_type=request.event_type,
        source_name=request.source_name,
        event_date=request.event_date,
        lot_number=request.lot_number,
        hammer_price=Decimal(str(request.hammer_price)) if request.hammer_price else None,
        total_price=Decimal(str(request.total_price)) if request.total_price else None,
        currency=request.currency,
        notes=request.notes,
        url=request.url,
        sort_order=request.sort_order,
    )
    
    if not model:
        raise HTTPException(status_code=404, detail=f"Provenance entry {provenance_id} not found")
    
    # Determine source name for response
    source_name = ""
    if model.event_type == "auction":
        source_name = model.auction_house or ""
    elif model.event_type == "dealer":
        source_name = model.dealer_name or ""
    elif model.event_type == "collection":
        source_name = model.collection_name or ""
    else:
        source_name = model.auction_house or model.dealer_name or model.collection_name or ""
    
    return ProvenanceEntryResponse(
        id=model.id,
        coin_id=model.coin_id,
        event_type=model.event_type,
        source_name=source_name,
        event_date=model.event_date,
        lot_number=model.lot_number,
        hammer_price=float(model.hammer_price) if model.hammer_price else None,
        total_price=float(model.total_price) if model.total_price else None,
        currency=model.currency,
        notes=model.notes,
        url=model.url,
        sort_order=model.sort_order or 0,
    )


@router.delete(
    "/provenance/{provenance_id}",
    status_code=204,
    summary="Delete provenance entry",
    description="Delete a provenance entry from a coin's history.",
)
def delete_provenance(
    provenance_id: int,
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
):
    """
    Delete a provenance entry.
    
    This permanently removes the entry from the coin's provenance chain.
    """
    deleted = provenance_repo.delete(provenance_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Provenance entry {provenance_id} not found")
    
    return None
