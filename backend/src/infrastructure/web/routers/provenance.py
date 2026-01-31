"""
Provenance Router for CoinStack API (V3).

Provides REST endpoints for managing coin provenance (pedigree/ownership history).
Uses unified source_name field and supports ACQUISITION event type for current ownership.

Endpoints:
- GET /api/v2/coins/{coin_id}/provenance - Get pedigree timeline for a coin
- POST /api/v2/coins/{coin_id}/provenance - Add provenance entry
- PUT /api/v2/provenance/{id} - Update provenance entry
- DELETE /api/v2/provenance/{id} - Delete provenance entry
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.domain.coin import ProvenanceEntry, ProvenanceEventType, ProvenanceSource
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.provenance_repository import SqlAlchemyProvenanceRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(tags=["Provenance"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS (V3)
# =============================================================================

class ProvenanceEntryCreate(BaseModel):
    """Request to create a provenance entry."""
    event_type: str = Field(
        ...,
        description="Type: auction, dealer, collection, private_sale, publication, hoard_find, estate, acquisition"
    )
    source_name: str = Field(..., description="Name of auction house, dealer, collection, etc.")
    event_date: Optional[date] = Field(None, description="Exact date of the event")
    date_string: Optional[str] = Field(None, description="Flexible date string (e.g. '1920s', 'circa 1840')")
    sale_name: Optional[str] = Field(None, description="Sale name (e.g. 'January 2024 NYINC')")
    sale_number: Optional[str] = Field(None, description="Auction catalog number")
    lot_number: Optional[str] = Field(None, description="Lot number if auction")
    catalog_reference: Optional[str] = Field(None, description="Full catalog reference")
    hammer_price: Optional[float] = Field(None, description="Hammer price", ge=0)
    buyers_premium_pct: Optional[float] = Field(None, description="Buyer's premium %", ge=0, le=100)
    total_price: Optional[float] = Field(None, description="Total price including premium", ge=0)
    currency: Optional[str] = Field(None, description="Currency code (USD, EUR, GBP)", max_length=3)
    notes: Optional[str] = Field(None, description="Additional notes")
    url: Optional[str] = Field(None, description="URL to source documentation")
    receipt_available: bool = Field(False, description="Is receipt available?")
    sort_order: int = Field(0, description="Display order (0 = earliest, 999 = acquisition)")

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError("Currency must be 3-letter ISO 4217 code")
        return v.upper() if v else None


class ProvenanceEntryUpdate(BaseModel):
    """Request to update a provenance entry (all fields optional)."""
    event_type: Optional[str] = None
    source_name: Optional[str] = None
    event_date: Optional[date] = None
    date_string: Optional[str] = None
    sale_name: Optional[str] = None
    sale_number: Optional[str] = None
    lot_number: Optional[str] = None
    catalog_reference: Optional[str] = None
    hammer_price: Optional[float] = Field(None, ge=0)
    buyers_premium_pct: Optional[float] = Field(None, ge=0, le=100)
    total_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    notes: Optional[str] = None
    url: Optional[str] = None
    receipt_available: Optional[bool] = None
    sort_order: Optional[int] = None


class ProvenanceEntryResponse(BaseModel):
    """Response for a provenance entry."""
    id: int
    coin_id: int
    event_type: str
    source_name: str
    event_date: Optional[date] = None
    date_string: Optional[str] = None
    sale_name: Optional[str] = None
    sale_number: Optional[str] = None
    lot_number: Optional[str] = None
    catalog_reference: Optional[str] = None
    hammer_price: Optional[float] = None
    buyers_premium_pct: Optional[float] = None
    total_price: Optional[float] = None
    computed_total: Optional[float] = None  # Computed from hammer + premium
    currency: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    receipt_available: bool = False
    source_origin: str = "manual_entry"
    sort_order: int = 0
    raw_text: str = ""  # Display string
    is_acquisition: bool = False  # True if this is current ownership


class ProvenanceChainResponse(BaseModel):
    """Response for a coin's full pedigree timeline."""
    coin_id: int
    entries: List[ProvenanceEntryResponse]
    earliest_known_year: Optional[int] = Field(None, description="Year of earliest known provenance")
    has_acquisition: bool = Field(False, description="Whether coin has current ownership entry")
    total_entries: int = 0


# =============================================================================
# VALID EVENT TYPES
# =============================================================================

VALID_EVENT_TYPES = {
    "auction", "dealer", "collection", "private_sale",
    "publication", "hoard_find", "estate", "acquisition", "unknown"
}


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
# HELPER FUNCTIONS
# =============================================================================

def entry_to_response(entry: ProvenanceEntry, coin_id: int) -> ProvenanceEntryResponse:
    """Convert domain ProvenanceEntry to API response."""
    # Compute total price if not set
    computed_total = None
    if entry.total_price:
        computed_total = float(entry.total_price)
    elif entry.hammer_price and entry.buyers_premium_pct:
        premium = entry.hammer_price * (entry.buyers_premium_pct / Decimal(100))
        computed_total = float(entry.hammer_price + premium)
    elif entry.hammer_price:
        computed_total = float(entry.hammer_price)

    # Build display text
    raw_text = entry.build_raw_text() if hasattr(entry, 'build_raw_text') else ""

    return ProvenanceEntryResponse(
        id=entry.id,
        coin_id=coin_id,
        event_type=entry.event_type.value if hasattr(entry.event_type, 'value') else str(entry.event_type),
        source_name=entry.source_name,
        event_date=entry.event_date,
        date_string=entry.date_string,
        sale_name=entry.sale_name,
        sale_number=entry.sale_number,
        lot_number=entry.lot_number,
        catalog_reference=entry.catalog_reference,
        hammer_price=float(entry.hammer_price) if entry.hammer_price else None,
        buyers_premium_pct=float(entry.buyers_premium_pct) if entry.buyers_premium_pct else None,
        total_price=float(entry.total_price) if entry.total_price else None,
        computed_total=computed_total,
        currency=entry.currency,
        notes=entry.notes,
        url=entry.url,
        receipt_available=entry.receipt_available,
        source_origin=entry.source_origin.value if hasattr(entry.source_origin, 'value') else str(entry.source_origin),
        sort_order=entry.sort_order,
        raw_text=raw_text,
        is_acquisition=entry.event_type == ProvenanceEventType.ACQUISITION if hasattr(entry.event_type, 'value') else entry.event_type == "acquisition",
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "/coins/{coin_id}/provenance",
    response_model=ProvenanceChainResponse,
    summary="Get pedigree timeline",
    description="Get the full pedigree (ownership history) timeline for a coin, from earliest known to current ownership.",
)
def get_provenance_chain(
    coin_id: int,
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Get pedigree timeline for a coin.

    Returns all provenance entries ordered by sort_order (earliest first).
    The ACQUISITION entry (if present) represents current ownership and appears last.
    """
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")

    # Get provenance entries via repository
    entries = provenance_repo.get_by_coin_id(coin_id)

    # Build response
    response_entries = []
    earliest_year = None
    has_acquisition = False

    for entry in entries:
        response_entries.append(entry_to_response(entry, coin_id))

        # Check for acquisition
        event_type_value = entry.event_type.value if hasattr(entry.event_type, 'value') else str(entry.event_type)
        if event_type_value == "acquisition":
            has_acquisition = True

        # Track earliest year
        year = entry.display_year if hasattr(entry, 'display_year') else None
        if year is None and entry.event_date:
            year = entry.event_date.year
        if year and (earliest_year is None or year < earliest_year):
            earliest_year = year

    return ProvenanceChainResponse(
        coin_id=coin_id,
        entries=response_entries,
        earliest_known_year=earliest_year,
        has_acquisition=has_acquisition,
        total_entries=len(response_entries),
    )


@router.post(
    "/coins/{coin_id}/provenance",
    response_model=ProvenanceEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add provenance entry",
    description="Add a new provenance entry to a coin's pedigree timeline.",
)
def add_provenance_entry(
    coin_id: int,
    request: ProvenanceEntryCreate,
    db: Session = Depends(get_db),
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
    - publication: Publication citation
    - hoard_find: Archaeological find
    - estate: Estate sale
    - acquisition: Current ownership (your purchase)
    """
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")

    # Validate event type
    if request.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type '{request.event_type}'. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
        )

    # Check if adding acquisition when one already exists
    if request.event_type == "acquisition":
        existing_acq = provenance_repo.get_acquisition_by_coin(coin_id)
        if existing_acq:
            raise HTTPException(
                status_code=400,
                detail="Coin already has an acquisition entry. Update or delete it first."
            )

    # Parse event type
    try:
        event_type = ProvenanceEventType(request.event_type)
    except ValueError:
        event_type = ProvenanceEventType.UNKNOWN

    # Create domain entry
    entry = ProvenanceEntry(
        event_type=event_type,
        source_name=request.source_name,
        event_date=request.event_date,
        date_string=request.date_string,
        sale_name=request.sale_name,
        sale_number=request.sale_number,
        lot_number=request.lot_number,
        catalog_reference=request.catalog_reference,
        hammer_price=Decimal(str(request.hammer_price)) if request.hammer_price else None,
        buyers_premium_pct=Decimal(str(request.buyers_premium_pct)) if request.buyers_premium_pct else None,
        total_price=Decimal(str(request.total_price)) if request.total_price else None,
        currency=request.currency,
        notes=request.notes,
        url=request.url,
        receipt_available=request.receipt_available,
        source_origin=ProvenanceSource.MANUAL_ENTRY,
        sort_order=request.sort_order,
    )

    # Persist
    created = provenance_repo.create(coin_id, entry)
    db.commit()

    return entry_to_response(created, coin_id)


@router.put(
    "/provenance/{provenance_id}",
    response_model=ProvenanceEntryResponse,
    summary="Update provenance entry",
    description="Update an existing provenance entry.",
)
def update_provenance_entry(
    provenance_id: int,
    request: ProvenanceEntryUpdate,
    db: Session = Depends(get_db),
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
):
    """
    Update a provenance entry.

    Only provided fields will be updated.
    """
    # Get existing entry
    existing = provenance_repo.get_by_id(provenance_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Provenance entry {provenance_id} not found")

    # Parse event type if provided
    event_type = existing.event_type
    if request.event_type:
        if request.event_type not in VALID_EVENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type '{request.event_type}'. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
            )
        try:
            event_type = ProvenanceEventType(request.event_type)
        except ValueError:
            event_type = ProvenanceEventType.UNKNOWN

    # Build updated entry (merge with existing)
    updated_entry = ProvenanceEntry(
        id=existing.id,
        event_type=event_type,
        source_name=request.source_name if request.source_name is not None else existing.source_name,
        event_date=request.event_date if request.event_date is not None else existing.event_date,
        date_string=request.date_string if request.date_string is not None else existing.date_string,
        sale_name=request.sale_name if request.sale_name is not None else existing.sale_name,
        sale_number=request.sale_number if request.sale_number is not None else existing.sale_number,
        lot_number=request.lot_number if request.lot_number is not None else existing.lot_number,
        catalog_reference=request.catalog_reference if request.catalog_reference is not None else existing.catalog_reference,
        hammer_price=Decimal(str(request.hammer_price)) if request.hammer_price is not None else existing.hammer_price,
        buyers_premium_pct=Decimal(str(request.buyers_premium_pct)) if request.buyers_premium_pct is not None else existing.buyers_premium_pct,
        total_price=Decimal(str(request.total_price)) if request.total_price is not None else existing.total_price,
        currency=request.currency if request.currency is not None else existing.currency,
        notes=request.notes if request.notes is not None else existing.notes,
        url=request.url if request.url is not None else existing.url,
        receipt_available=request.receipt_available if request.receipt_available is not None else existing.receipt_available,
        source_origin=existing.source_origin,  # Never change origin
        auction_data_id=existing.auction_data_id,  # Never change link
        sort_order=request.sort_order if request.sort_order is not None else existing.sort_order,
    )

    # Persist
    updated = provenance_repo.update(provenance_id, updated_entry)
    db.commit()

    # Get coin_id from ORM model for response
    from src.infrastructure.persistence.orm import ProvenanceEventModel
    model = db.get(ProvenanceEventModel, provenance_id)
    coin_id = model.coin_id if model else 0

    return entry_to_response(updated, coin_id)


@router.delete(
    "/provenance/{provenance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete provenance entry",
    description="Delete a provenance entry from a coin's pedigree timeline.",
)
def delete_provenance_entry(
    provenance_id: int,
    db: Session = Depends(get_db),
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
):
    """
    Delete a provenance entry.

    This permanently removes the entry from the coin's pedigree timeline.
    Note: Deleting an ACQUISITION entry will remove the current ownership record.
    """
    deleted = provenance_repo.delete(provenance_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Provenance entry {provenance_id} not found")

    db.commit()
    return None


@router.get(
    "/coins/{coin_id}/provenance/acquisition",
    response_model=Optional[ProvenanceEntryResponse],
    summary="Get acquisition entry",
    description="Get the current ownership (acquisition) entry for a coin.",
)
def get_acquisition_entry(
    coin_id: int,
    provenance_repo: SqlAlchemyProvenanceRepository = Depends(get_provenance_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Get the acquisition (current ownership) entry for a coin.

    Returns null if coin has no acquisition entry.
    """
    # Verify coin exists
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")

    acquisition = provenance_repo.get_acquisition_by_coin(coin_id)
    if not acquisition:
        return None

    return entry_to_response(acquisition, coin_id)
