"""
Market Price Router for CoinStack API (Schema V3 Phase 5).

Provides REST endpoints for market prices and data points.

Endpoints:
- GET    /api/v2/market/prices                     - List market prices
- GET    /api/v2/market/prices/{id}                - Get market price by ID
- GET    /api/v2/market/prices/by-attribution      - Get by attribution key
- POST   /api/v2/market/prices                     - Create market price
- PUT    /api/v2/market/prices/{id}                - Update market price
- DELETE /api/v2/market/prices/{id}                - Delete market price
- GET    /api/v2/market/prices/{id}/data-points    - List data points
- POST   /api/v2/market/prices/{id}/data-points    - Add data point
- GET    /api/v2/market/data-points/{id}           - Get data point
- PUT    /api/v2/market/data-points/{id}           - Update data point
- DELETE /api/v2/market/data-points/{id}           - Delete data point
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import MarketPrice, MarketDataPoint
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.market_price_repository import SqlAlchemyMarketPriceRepository
from src.infrastructure.repositories.market_data_point_repository import SqlAlchemyMarketDataPointRepository

router = APIRouter(
    prefix="/api/v2/market",
    tags=["Market Prices"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class MarketPriceCreateRequest(BaseModel):
    """Request to create a market price."""
    attribution_key: str = Field(..., description="Unique key for this price aggregate")
    issuer: Optional[str] = None
    denomination: Optional[str] = None
    mint: Optional[str] = None
    metal: Optional[str] = None
    catalog_ref: Optional[str] = None
    avg_price_vf: Optional[float] = None
    avg_price_ef: Optional[float] = None
    avg_price_au: Optional[float] = None
    min_price_seen: Optional[float] = None
    max_price_seen: Optional[float] = None
    median_price: Optional[float] = None
    data_point_count: int = 0
    last_sale_date: Optional[date] = None


class MarketPriceUpdateRequest(BaseModel):
    """Request to update a market price (all fields optional)."""
    attribution_key: Optional[str] = None
    issuer: Optional[str] = None
    denomination: Optional[str] = None
    mint: Optional[str] = None
    metal: Optional[str] = None
    catalog_ref: Optional[str] = None
    avg_price_vf: Optional[float] = None
    avg_price_ef: Optional[float] = None
    avg_price_au: Optional[float] = None
    min_price_seen: Optional[float] = None
    max_price_seen: Optional[float] = None
    median_price: Optional[float] = None
    data_point_count: Optional[int] = None
    last_sale_date: Optional[date] = None


class MarketPriceResponse(BaseModel):
    """Response for a market price."""
    id: int
    attribution_key: str
    issuer: Optional[str] = None
    denomination: Optional[str] = None
    mint: Optional[str] = None
    metal: Optional[str] = None
    catalog_ref: Optional[str] = None
    avg_price_vf: Optional[float] = None
    avg_price_ef: Optional[float] = None
    avg_price_au: Optional[float] = None
    min_price_seen: Optional[float] = None
    max_price_seen: Optional[float] = None
    median_price: Optional[float] = None
    data_point_count: int = 0
    last_sale_date: Optional[date] = None
    last_updated: Optional[str] = None


class MarketPriceListResponse(BaseModel):
    """Response for listing market prices."""
    prices: List[MarketPriceResponse]
    total: int
    skip: int
    limit: int


class MarketDataPointCreateRequest(BaseModel):
    """Request to create a data point."""
    price: float = Field(..., gt=0)
    currency: str = "USD"
    price_usd: Optional[float] = None
    source_type: str = Field(..., description="auction_realized, auction_unsold, dealer_asking, private_sale, estimate")
    date: date
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    auction_house: Optional[str] = None
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    lot_url: Optional[str] = None
    dealer_name: Optional[str] = None
    confidence: str = "medium"
    notes: Optional[str] = None


class MarketDataPointUpdateRequest(BaseModel):
    """Request to update a data point (all fields optional)."""
    price: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = None
    price_usd: Optional[float] = None
    source_type: Optional[str] = None
    date: Optional[date] = None
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    auction_house: Optional[str] = None
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    lot_url: Optional[str] = None
    dealer_name: Optional[str] = None
    confidence: Optional[str] = None
    notes: Optional[str] = None


class MarketDataPointResponse(BaseModel):
    """Response for a data point."""
    id: int
    market_price_id: int
    price: float
    currency: str
    price_usd: Optional[float] = None
    source_type: str
    date: date
    grade: Optional[str] = None
    grade_numeric: Optional[int] = None
    condition_notes: Optional[str] = None
    auction_house: Optional[str] = None
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    lot_url: Optional[str] = None
    dealer_name: Optional[str] = None
    confidence: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


class MarketDataPointListResponse(BaseModel):
    """Response for listing data points."""
    data_points: List[MarketDataPointResponse]
    total: int


# =============================================================================
# VALID VALUES
# =============================================================================

VALID_SOURCE_TYPES = {"auction_realized", "auction_unsold", "dealer_asking", "private_sale", "estimate"}
VALID_CONFIDENCE = {"low", "medium", "high", "verified"}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_market_price_repo(db: Session = Depends(get_db)) -> SqlAlchemyMarketPriceRepository:
    """Get market price repository instance."""
    return SqlAlchemyMarketPriceRepository(db)


def get_data_point_repo(db: Session = Depends(get_db)) -> SqlAlchemyMarketDataPointRepository:
    """Get data point repository instance."""
    return SqlAlchemyMarketDataPointRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def price_to_response(price: MarketPrice) -> MarketPriceResponse:
    """Convert domain MarketPrice to API response."""
    return MarketPriceResponse(
        id=price.id,
        attribution_key=price.attribution_key,
        issuer=price.issuer,
        denomination=price.denomination,
        mint=price.mint,
        metal=price.metal,
        catalog_ref=price.catalog_ref,
        avg_price_vf=float(price.avg_price_vf) if price.avg_price_vf else None,
        avg_price_ef=float(price.avg_price_ef) if price.avg_price_ef else None,
        avg_price_au=float(price.avg_price_au) if price.avg_price_au else None,
        min_price_seen=float(price.min_price_seen) if price.min_price_seen else None,
        max_price_seen=float(price.max_price_seen) if price.max_price_seen else None,
        median_price=float(price.median_price) if price.median_price else None,
        data_point_count=price.data_point_count,
        last_sale_date=price.last_sale_date,
        last_updated=price.last_updated.isoformat() if price.last_updated else None,
    )


def data_point_to_response(dp: MarketDataPoint) -> MarketDataPointResponse:
    """Convert domain MarketDataPoint to API response."""
    return MarketDataPointResponse(
        id=dp.id,
        market_price_id=dp.market_price_id,
        price=float(dp.price),
        currency=dp.currency,
        price_usd=float(dp.price_usd) if dp.price_usd else None,
        source_type=dp.source_type,
        date=dp.date,
        grade=dp.grade,
        grade_numeric=dp.grade_numeric,
        condition_notes=dp.condition_notes,
        auction_house=dp.auction_house,
        sale_name=dp.sale_name,
        lot_number=dp.lot_number,
        lot_url=dp.lot_url,
        dealer_name=dp.dealer_name,
        confidence=dp.confidence,
        notes=dp.notes,
        created_at=dp.created_at.isoformat() if dp.created_at else None,
    )


# =============================================================================
# MARKET PRICE ENDPOINTS
# =============================================================================

@router.get(
    "/prices",
    response_model=MarketPriceListResponse,
    summary="List market prices",
    description="Get all market prices with optional filters."
)
def list_market_prices(
    issuer: Optional[str] = Query(None, description="Filter by issuer"),
    denomination: Optional[str] = Query(None, description="Filter by denomination"),
    metal: Optional[str] = Query(None, description="Filter by metal"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """List market prices with pagination and filters."""
    prices = repo.list_all(issuer=issuer, denomination=denomination, metal=metal, skip=skip, limit=limit)
    total = repo.count(issuer=issuer, denomination=denomination, metal=metal)

    return MarketPriceListResponse(
        prices=[price_to_response(p) for p in prices],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/prices/by-attribution",
    response_model=Optional[MarketPriceResponse],
    summary="Get by attribution key",
    description="Get market price by attribution key."
)
def get_market_price_by_attribution(
    attribution_key: str = Query(..., description="Attribution key"),
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """Get market price by attribution key."""
    price = repo.get_by_attribution_key(attribution_key)
    if not price:
        return None
    return price_to_response(price)


@router.get(
    "/prices/{price_id}",
    response_model=MarketPriceResponse,
    summary="Get market price",
    description="Get a market price by ID."
)
def get_market_price(
    price_id: int,
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """Get a market price by ID."""
    price = repo.get_by_id(price_id)
    if not price:
        raise HTTPException(status_code=404, detail=f"Market price {price_id} not found")
    return price_to_response(price)


@router.post(
    "/prices",
    response_model=MarketPriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create market price",
    description="Create a new market price aggregate."
)
def create_market_price(
    request: MarketPriceCreateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """Create a new market price."""
    # Check for duplicate attribution key
    existing = repo.get_by_attribution_key(request.attribution_key)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Market price with attribution key '{request.attribution_key}' already exists"
        )

    price = MarketPrice(
        attribution_key=request.attribution_key,
        issuer=request.issuer,
        denomination=request.denomination,
        mint=request.mint,
        metal=request.metal,
        catalog_ref=request.catalog_ref,
        avg_price_vf=Decimal(str(request.avg_price_vf)) if request.avg_price_vf else None,
        avg_price_ef=Decimal(str(request.avg_price_ef)) if request.avg_price_ef else None,
        avg_price_au=Decimal(str(request.avg_price_au)) if request.avg_price_au else None,
        min_price_seen=Decimal(str(request.min_price_seen)) if request.min_price_seen else None,
        max_price_seen=Decimal(str(request.max_price_seen)) if request.max_price_seen else None,
        median_price=Decimal(str(request.median_price)) if request.median_price else None,
        data_point_count=request.data_point_count,
        last_sale_date=request.last_sale_date,
    )

    created = repo.create(price)
    db.commit()

    return price_to_response(created)


@router.put(
    "/prices/{price_id}",
    response_model=MarketPriceResponse,
    summary="Update market price",
    description="Update an existing market price."
)
def update_market_price(
    price_id: int,
    request: MarketPriceUpdateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """Update a market price."""
    existing = repo.get_by_id(price_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Market price {price_id} not found")

    updated_price = MarketPrice(
        id=existing.id,
        attribution_key=request.attribution_key if request.attribution_key else existing.attribution_key,
        issuer=request.issuer if request.issuer is not None else existing.issuer,
        denomination=request.denomination if request.denomination is not None else existing.denomination,
        mint=request.mint if request.mint is not None else existing.mint,
        metal=request.metal if request.metal is not None else existing.metal,
        catalog_ref=request.catalog_ref if request.catalog_ref is not None else existing.catalog_ref,
        avg_price_vf=Decimal(str(request.avg_price_vf)) if request.avg_price_vf is not None else existing.avg_price_vf,
        avg_price_ef=Decimal(str(request.avg_price_ef)) if request.avg_price_ef is not None else existing.avg_price_ef,
        avg_price_au=Decimal(str(request.avg_price_au)) if request.avg_price_au is not None else existing.avg_price_au,
        min_price_seen=Decimal(str(request.min_price_seen)) if request.min_price_seen is not None else existing.min_price_seen,
        max_price_seen=Decimal(str(request.max_price_seen)) if request.max_price_seen is not None else existing.max_price_seen,
        median_price=Decimal(str(request.median_price)) if request.median_price is not None else existing.median_price,
        data_point_count=request.data_point_count if request.data_point_count is not None else existing.data_point_count,
        last_sale_date=request.last_sale_date if request.last_sale_date is not None else existing.last_sale_date,
    )

    updated = repo.update(price_id, updated_price)
    db.commit()

    return price_to_response(updated)


@router.delete(
    "/prices/{price_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete market price",
    description="Delete a market price."
)
def delete_market_price(
    price_id: int,
    db: Session = Depends(get_db),
    repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
):
    """Delete a market price."""
    existing = repo.get_by_id(price_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Market price {price_id} not found")

    repo.delete(price_id)
    db.commit()

    return None


# =============================================================================
# DATA POINT ENDPOINTS
# =============================================================================

@router.get(
    "/prices/{price_id}/data-points",
    response_model=MarketDataPointListResponse,
    summary="List data points",
    description="Get all data points for a market price."
)
def list_data_points(
    price_id: int,
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    price_repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
    dp_repo: SqlAlchemyMarketDataPointRepository = Depends(get_data_point_repo),
):
    """List data points for a market price."""
    # Verify price exists
    price = price_repo.get_by_id(price_id)
    if not price:
        raise HTTPException(status_code=404, detail=f"Market price {price_id} not found")

    if source_type and source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{source_type}'. Must be one of: {', '.join(sorted(VALID_SOURCE_TYPES))}"
        )

    data_points = dp_repo.get_by_market_price_id(price_id, source_type=source_type, skip=skip, limit=limit)
    total = dp_repo.count_by_market_price_id(price_id)

    return MarketDataPointListResponse(
        data_points=[data_point_to_response(dp) for dp in data_points],
        total=total,
    )


@router.post(
    "/prices/{price_id}/data-points",
    response_model=MarketDataPointResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create data point",
    description="Add a new data point to a market price."
)
def create_data_point(
    price_id: int,
    request: MarketDataPointCreateRequest,
    db: Session = Depends(get_db),
    price_repo: SqlAlchemyMarketPriceRepository = Depends(get_market_price_repo),
    dp_repo: SqlAlchemyMarketDataPointRepository = Depends(get_data_point_repo),
):
    """Create a data point."""
    # Verify price exists
    price = price_repo.get_by_id(price_id)
    if not price:
        raise HTTPException(status_code=404, detail=f"Market price {price_id} not found")

    # Validate source_type
    if request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{request.source_type}'. Must be one of: {', '.join(sorted(VALID_SOURCE_TYPES))}"
        )

    # Validate confidence
    if request.confidence not in VALID_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence '{request.confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE))}"
        )

    data_point = MarketDataPoint(
        price=Decimal(str(request.price)),
        currency=request.currency,
        price_usd=Decimal(str(request.price_usd)) if request.price_usd else None,
        source_type=request.source_type,
        date=request.date,
        grade=request.grade,
        grade_numeric=request.grade_numeric,
        condition_notes=request.condition_notes,
        auction_house=request.auction_house,
        sale_name=request.sale_name,
        lot_number=request.lot_number,
        lot_url=request.lot_url,
        dealer_name=request.dealer_name,
        confidence=request.confidence,
        notes=request.notes,
    )

    created = dp_repo.create(price_id, data_point)
    db.commit()

    return data_point_to_response(created)


@router.get(
    "/data-points/{data_point_id}",
    response_model=MarketDataPointResponse,
    summary="Get data point",
    description="Get a data point by ID."
)
def get_data_point(
    data_point_id: int,
    dp_repo: SqlAlchemyMarketDataPointRepository = Depends(get_data_point_repo),
):
    """Get a data point by ID."""
    dp = dp_repo.get_by_id(data_point_id)
    if not dp:
        raise HTTPException(status_code=404, detail=f"Data point {data_point_id} not found")
    return data_point_to_response(dp)


@router.put(
    "/data-points/{data_point_id}",
    response_model=MarketDataPointResponse,
    summary="Update data point",
    description="Update an existing data point."
)
def update_data_point(
    data_point_id: int,
    request: MarketDataPointUpdateRequest,
    db: Session = Depends(get_db),
    dp_repo: SqlAlchemyMarketDataPointRepository = Depends(get_data_point_repo),
):
    """Update a data point."""
    existing = dp_repo.get_by_id(data_point_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Data point {data_point_id} not found")

    # Validate source_type if provided
    if request.source_type and request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{request.source_type}'. Must be one of: {', '.join(sorted(VALID_SOURCE_TYPES))}"
        )

    # Validate confidence if provided
    if request.confidence and request.confidence not in VALID_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence '{request.confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE))}"
        )

    updated_dp = MarketDataPoint(
        id=existing.id,
        market_price_id=existing.market_price_id,
        price=Decimal(str(request.price)) if request.price is not None else existing.price,
        currency=request.currency if request.currency is not None else existing.currency,
        price_usd=Decimal(str(request.price_usd)) if request.price_usd is not None else existing.price_usd,
        source_type=request.source_type if request.source_type is not None else existing.source_type,
        date=request.date if request.date is not None else existing.date,
        grade=request.grade if request.grade is not None else existing.grade,
        grade_numeric=request.grade_numeric if request.grade_numeric is not None else existing.grade_numeric,
        condition_notes=request.condition_notes if request.condition_notes is not None else existing.condition_notes,
        auction_house=request.auction_house if request.auction_house is not None else existing.auction_house,
        sale_name=request.sale_name if request.sale_name is not None else existing.sale_name,
        lot_number=request.lot_number if request.lot_number is not None else existing.lot_number,
        lot_url=request.lot_url if request.lot_url is not None else existing.lot_url,
        dealer_name=request.dealer_name if request.dealer_name is not None else existing.dealer_name,
        confidence=request.confidence if request.confidence is not None else existing.confidence,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = dp_repo.update(data_point_id, updated_dp)
    db.commit()

    return data_point_to_response(updated)


@router.delete(
    "/data-points/{data_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete data point",
    description="Delete a data point."
)
def delete_data_point(
    data_point_id: int,
    db: Session = Depends(get_db),
    dp_repo: SqlAlchemyMarketDataPointRepository = Depends(get_data_point_repo),
):
    """Delete a data point."""
    existing = dp_repo.get_by_id(data_point_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Data point {data_point_id} not found")

    dp_repo.delete(data_point_id)
    db.commit()

    return None
