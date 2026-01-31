"""
Coin Valuation Router for CoinStack API (Schema V3 Phase 5).

Provides REST endpoints for per-coin valuation snapshots.

Endpoints:
- GET    /api/v2/coins/{coin_id}/valuations        - List valuations for coin
- GET    /api/v2/coins/{coin_id}/valuations/latest - Get latest valuation
- POST   /api/v2/coins/{coin_id}/valuations        - Create valuation
- GET    /api/v2/coins/{coin_id}/valuations/{id}   - Get valuation
- PUT    /api/v2/coins/{coin_id}/valuations/{id}   - Update valuation
- DELETE /api/v2/coins/{coin_id}/valuations/{id}   - Delete valuation
- GET    /api/v2/valuations/portfolio-summary      - Portfolio totals and trends
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import CoinValuation
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.coin_valuation_repository import SqlAlchemyCoinValuationRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(
    tags=["Coin Valuations"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CoinValuationCreateRequest(BaseModel):
    """Request to create a coin valuation."""
    valuation_date: date = Field(..., description="Date of valuation")
    purchase_price: Optional[float] = None
    purchase_currency: Optional[str] = None
    purchase_date: Optional[date] = None
    current_market_value: Optional[float] = None
    value_currency: str = "USD"
    market_confidence: Optional[str] = Field(None, description="low, medium, high, strong")
    comparable_count: Optional[int] = None
    comparable_avg_price: Optional[float] = None
    comparable_date_range: Optional[str] = None
    price_trend_6mo: Optional[float] = None
    price_trend_12mo: Optional[float] = None
    price_trend_36mo: Optional[float] = None
    gain_loss_usd: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    valuation_method: Optional[str] = Field(None, description="comparable_sales, dealer_estimate, insurance, user_estimate, llm_estimate")
    notes: Optional[str] = None


class CoinValuationUpdateRequest(BaseModel):
    """Request to update a coin valuation (all fields optional)."""
    valuation_date: Optional[date] = None
    purchase_price: Optional[float] = None
    purchase_currency: Optional[str] = None
    purchase_date: Optional[date] = None
    current_market_value: Optional[float] = None
    value_currency: Optional[str] = None
    market_confidence: Optional[str] = None
    comparable_count: Optional[int] = None
    comparable_avg_price: Optional[float] = None
    comparable_date_range: Optional[str] = None
    price_trend_6mo: Optional[float] = None
    price_trend_12mo: Optional[float] = None
    price_trend_36mo: Optional[float] = None
    gain_loss_usd: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    valuation_method: Optional[str] = None
    notes: Optional[str] = None


class CoinValuationResponse(BaseModel):
    """Response for a coin valuation."""
    id: int
    coin_id: int
    valuation_date: date
    purchase_price: Optional[float] = None
    purchase_currency: Optional[str] = None
    purchase_date: Optional[date] = None
    current_market_value: Optional[float] = None
    value_currency: str
    market_confidence: Optional[str] = None
    comparable_count: Optional[int] = None
    comparable_avg_price: Optional[float] = None
    comparable_date_range: Optional[str] = None
    price_trend_6mo: Optional[float] = None
    price_trend_12mo: Optional[float] = None
    price_trend_36mo: Optional[float] = None
    gain_loss_usd: Optional[float] = None
    gain_loss_pct: Optional[float] = None
    valuation_method: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


class CoinValuationListResponse(BaseModel):
    """Response for listing valuations."""
    coin_id: int
    valuations: List[CoinValuationResponse]
    total: int


class PortfolioSummaryResponse(BaseModel):
    """Response for portfolio summary."""
    total_coins: int
    total_purchase_value: float
    total_current_value: float
    total_gain_loss_usd: float
    total_gain_loss_pct: Optional[float] = None


# =============================================================================
# VALID VALUES
# =============================================================================

VALID_CONFIDENCE = {"low", "medium", "high", "strong"}
VALID_METHODS = {"comparable_sales", "dealer_estimate", "insurance", "user_estimate", "llm_estimate"}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_valuation_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinValuationRepository:
    """Get valuation repository instance."""
    return SqlAlchemyCoinValuationRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def valuation_to_response(v: CoinValuation) -> CoinValuationResponse:
    """Convert domain CoinValuation to API response."""
    return CoinValuationResponse(
        id=v.id,
        coin_id=v.coin_id,
        valuation_date=v.valuation_date,
        purchase_price=float(v.purchase_price) if v.purchase_price else None,
        purchase_currency=v.purchase_currency,
        purchase_date=v.purchase_date,
        current_market_value=float(v.current_market_value) if v.current_market_value else None,
        value_currency=v.value_currency,
        market_confidence=v.market_confidence,
        comparable_count=v.comparable_count,
        comparable_avg_price=float(v.comparable_avg_price) if v.comparable_avg_price else None,
        comparable_date_range=v.comparable_date_range,
        price_trend_6mo=float(v.price_trend_6mo) if v.price_trend_6mo else None,
        price_trend_12mo=float(v.price_trend_12mo) if v.price_trend_12mo else None,
        price_trend_36mo=float(v.price_trend_36mo) if v.price_trend_36mo else None,
        gain_loss_usd=float(v.gain_loss_usd) if v.gain_loss_usd else None,
        gain_loss_pct=float(v.gain_loss_pct) if v.gain_loss_pct else None,
        valuation_method=v.valuation_method,
        notes=v.notes,
        created_at=v.created_at.isoformat() if v.created_at else None,
    )


def validate_coin_exists(coin_id: int, coin_repo: SqlAlchemyCoinRepository) -> None:
    """Verify coin exists, raise 404 if not."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")


# =============================================================================
# PORTFOLIO SUMMARY ENDPOINT
# =============================================================================

@router.get(
    "/api/v2/valuations/portfolio-summary",
    response_model=PortfolioSummaryResponse,
    summary="Portfolio summary",
    description="Get portfolio-wide valuation summary."
)
def get_portfolio_summary(
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
):
    """Get portfolio valuation summary."""
    summary = repo.get_portfolio_summary()

    return PortfolioSummaryResponse(
        total_coins=summary["total_coins"],
        total_purchase_value=float(summary["total_purchase_value"]),
        total_current_value=float(summary["total_current_value"]),
        total_gain_loss_usd=float(summary["total_gain_loss_usd"]),
        total_gain_loss_pct=float(summary["total_gain_loss_pct"]) if summary["total_gain_loss_pct"] else None,
    )


# =============================================================================
# COIN VALUATION ENDPOINTS
# =============================================================================

@router.get(
    "/api/v2/coins/{coin_id}/valuations",
    response_model=CoinValuationListResponse,
    summary="List valuations",
    description="Get all valuations for a coin."
)
def list_valuations(
    coin_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """List valuations for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    valuations = repo.get_by_coin_id(coin_id, skip=skip, limit=limit)
    total = repo.count_by_coin_id(coin_id)

    return CoinValuationListResponse(
        coin_id=coin_id,
        valuations=[valuation_to_response(v) for v in valuations],
        total=total,
    )


@router.get(
    "/api/v2/coins/{coin_id}/valuations/latest",
    response_model=Optional[CoinValuationResponse],
    summary="Get latest valuation",
    description="Get the most recent valuation for a coin."
)
def get_latest_valuation(
    coin_id: int,
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get the latest valuation for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    latest = repo.get_latest(coin_id)
    if not latest:
        return None

    return valuation_to_response(latest)


@router.post(
    "/api/v2/coins/{coin_id}/valuations",
    response_model=CoinValuationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create valuation",
    description="Create a new valuation snapshot for a coin."
)
def create_valuation(
    coin_id: int,
    request: CoinValuationCreateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Create a valuation."""
    validate_coin_exists(coin_id, coin_repo)

    # Validate confidence
    if request.market_confidence and request.market_confidence not in VALID_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market_confidence '{request.market_confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE))}"
        )

    # Validate method
    if request.valuation_method and request.valuation_method not in VALID_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid valuation_method '{request.valuation_method}'. Must be one of: {', '.join(sorted(VALID_METHODS))}"
        )

    valuation = CoinValuation(
        valuation_date=request.valuation_date,
        purchase_price=Decimal(str(request.purchase_price)) if request.purchase_price else None,
        purchase_currency=request.purchase_currency,
        purchase_date=request.purchase_date,
        current_market_value=Decimal(str(request.current_market_value)) if request.current_market_value else None,
        value_currency=request.value_currency,
        market_confidence=request.market_confidence,
        comparable_count=request.comparable_count,
        comparable_avg_price=Decimal(str(request.comparable_avg_price)) if request.comparable_avg_price else None,
        comparable_date_range=request.comparable_date_range,
        price_trend_6mo=Decimal(str(request.price_trend_6mo)) if request.price_trend_6mo else None,
        price_trend_12mo=Decimal(str(request.price_trend_12mo)) if request.price_trend_12mo else None,
        price_trend_36mo=Decimal(str(request.price_trend_36mo)) if request.price_trend_36mo else None,
        gain_loss_usd=Decimal(str(request.gain_loss_usd)) if request.gain_loss_usd else None,
        gain_loss_pct=Decimal(str(request.gain_loss_pct)) if request.gain_loss_pct else None,
        valuation_method=request.valuation_method,
        notes=request.notes,
    )

    created = repo.create(coin_id, valuation)
    db.commit()

    return valuation_to_response(created)


@router.get(
    "/api/v2/coins/{coin_id}/valuations/{valuation_id}",
    response_model=CoinValuationResponse,
    summary="Get valuation",
    description="Get a specific valuation."
)
def get_valuation(
    coin_id: int,
    valuation_id: int,
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get a specific valuation."""
    validate_coin_exists(coin_id, coin_repo)

    valuation = repo.get_by_id(valuation_id)
    if not valuation or valuation.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Valuation {valuation_id} not found for coin {coin_id}")

    return valuation_to_response(valuation)


@router.put(
    "/api/v2/coins/{coin_id}/valuations/{valuation_id}",
    response_model=CoinValuationResponse,
    summary="Update valuation",
    description="Update an existing valuation."
)
def update_valuation(
    coin_id: int,
    valuation_id: int,
    request: CoinValuationUpdateRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Update a valuation."""
    validate_coin_exists(coin_id, coin_repo)

    existing = repo.get_by_id(valuation_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Valuation {valuation_id} not found for coin {coin_id}")

    # Validate confidence
    if request.market_confidence and request.market_confidence not in VALID_CONFIDENCE:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid market_confidence '{request.market_confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE))}"
        )

    # Validate method
    if request.valuation_method and request.valuation_method not in VALID_METHODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid valuation_method '{request.valuation_method}'. Must be one of: {', '.join(sorted(VALID_METHODS))}"
        )

    updated_valuation = CoinValuation(
        id=existing.id,
        coin_id=existing.coin_id,
        valuation_date=request.valuation_date if request.valuation_date else existing.valuation_date,
        purchase_price=Decimal(str(request.purchase_price)) if request.purchase_price is not None else existing.purchase_price,
        purchase_currency=request.purchase_currency if request.purchase_currency is not None else existing.purchase_currency,
        purchase_date=request.purchase_date if request.purchase_date is not None else existing.purchase_date,
        current_market_value=Decimal(str(request.current_market_value)) if request.current_market_value is not None else existing.current_market_value,
        value_currency=request.value_currency if request.value_currency is not None else existing.value_currency,
        market_confidence=request.market_confidence if request.market_confidence is not None else existing.market_confidence,
        comparable_count=request.comparable_count if request.comparable_count is not None else existing.comparable_count,
        comparable_avg_price=Decimal(str(request.comparable_avg_price)) if request.comparable_avg_price is not None else existing.comparable_avg_price,
        comparable_date_range=request.comparable_date_range if request.comparable_date_range is not None else existing.comparable_date_range,
        price_trend_6mo=Decimal(str(request.price_trend_6mo)) if request.price_trend_6mo is not None else existing.price_trend_6mo,
        price_trend_12mo=Decimal(str(request.price_trend_12mo)) if request.price_trend_12mo is not None else existing.price_trend_12mo,
        price_trend_36mo=Decimal(str(request.price_trend_36mo)) if request.price_trend_36mo is not None else existing.price_trend_36mo,
        gain_loss_usd=Decimal(str(request.gain_loss_usd)) if request.gain_loss_usd is not None else existing.gain_loss_usd,
        gain_loss_pct=Decimal(str(request.gain_loss_pct)) if request.gain_loss_pct is not None else existing.gain_loss_pct,
        valuation_method=request.valuation_method if request.valuation_method is not None else existing.valuation_method,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = repo.update(valuation_id, updated_valuation)
    db.commit()

    return valuation_to_response(updated)


@router.delete(
    "/api/v2/coins/{coin_id}/valuations/{valuation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete valuation",
    description="Delete a valuation."
)
def delete_valuation(
    coin_id: int,
    valuation_id: int,
    db: Session = Depends(get_db),
    repo: SqlAlchemyCoinValuationRepository = Depends(get_valuation_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Delete a valuation."""
    validate_coin_exists(coin_id, coin_repo)

    existing = repo.get_by_id(valuation_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Valuation {valuation_id} not found for coin {coin_id}")

    repo.delete(valuation_id)
    db.commit()

    return None
