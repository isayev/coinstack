"""
Attribution Hypotheses Router for CoinStack API (Phase 2: Attribution Confidence).

Provides REST endpoints for managing multi-hypothesis attributions with field-level confidence.

Endpoints:
- GET /api/v2/coins/{coin_id}/attribution-hypotheses - List all hypotheses for a coin
- POST /api/v2/coins/{coin_id}/attribution-hypotheses - Create hypothesis
- GET /api/v2/coins/{coin_id}/attribution-hypotheses/primary - Get primary hypothesis
- GET /api/v2/attribution-hypotheses/{hypothesis_id} - Get single hypothesis
- PUT /api/v2/attribution-hypotheses/{hypothesis_id} - Update hypothesis
- DELETE /api/v2/attribution-hypotheses/{hypothesis_id} - Delete hypothesis
- POST /api/v2/attribution-hypotheses/{hypothesis_id}/set-primary - Promote to primary
- PUT /api/v2/coins/{coin_id}/attribution-certainty - Update coin-level certainty
"""

from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import AttributionHypothesis, AttributionCertainty
from src.infrastructure.web.dependencies import get_db, get_coin_repo
from src.domain.repositories import ICoinRepository
from src.domain.repositories_attribution import IAttributionHypothesisRepository
from src.infrastructure.repositories.attribution_hypothesis_repository import SqlAlchemyAttributionHypothesisRepository

router = APIRouter(tags=["Attribution Confidence"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class AttributionHypothesisCreateRequest(BaseModel):
    """Request to create an attribution hypothesis."""
    hypothesis_rank: int = Field(..., ge=1, description="Hypothesis rank (1=primary)")

    # Field-level attribution with confidence
    issuer: Optional[str] = Field(None, description="Issuer name")
    issuer_confidence: Optional[str] = Field(None, description="Issuer confidence level")

    mint: Optional[str] = Field(None, description="Mint location")
    mint_confidence: Optional[str] = Field(None, description="Mint confidence level")

    year_start: Optional[int] = Field(None, description="Start year (negative for BC)")
    year_end: Optional[int] = Field(None, description="End year (negative for BC)")
    date_confidence: Optional[str] = Field(None, description="Date confidence level")

    denomination: Optional[str] = Field(None, description="Denomination")
    denomination_confidence: Optional[str] = Field(None, description="Denomination confidence level")

    # Overall confidence
    overall_certainty: Optional[str] = Field(None, description="Overall certainty level")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score (0.00-1.00)")

    # Evidence
    attribution_notes: Optional[str] = Field(None, description="Attribution reasoning/notes")
    reference_support: Optional[str] = Field(None, description="Supporting references")
    source: Optional[str] = Field(None, description="Source: llm, expert, user, catalog")


class AttributionHypothesisUpdateRequest(BaseModel):
    """Request to update an attribution hypothesis (all fields optional)."""
    issuer: Optional[str] = None
    issuer_confidence: Optional[str] = None

    mint: Optional[str] = None
    mint_confidence: Optional[str] = None

    year_start: Optional[int] = None
    year_end: Optional[int] = None
    date_confidence: Optional[str] = None

    denomination: Optional[str] = None
    denomination_confidence: Optional[str] = None

    overall_certainty: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)

    attribution_notes: Optional[str] = None
    reference_support: Optional[str] = None
    source: Optional[str] = None


class AttributionHypothesisResponse(BaseModel):
    """Response for an attribution hypothesis."""
    id: int
    coin_id: int
    hypothesis_rank: int

    issuer: Optional[str] = None
    issuer_confidence: Optional[str] = None

    mint: Optional[str] = None
    mint_confidence: Optional[str] = None

    year_start: Optional[int] = None
    year_end: Optional[int] = None
    date_confidence: Optional[str] = None

    denomination: Optional[str] = None
    denomination_confidence: Optional[str] = None

    overall_certainty: Optional[str] = None
    confidence_score: Optional[Decimal] = None

    attribution_notes: Optional[str] = None
    reference_support: Optional[str] = None
    source: Optional[str] = None


class CoinAttributionCertaintyRequest(BaseModel):
    """Request to update coin-level attribution certainty."""
    attribution_certainty: str = Field(..., description="Attribution certainty: certain, probable, possible, tentative, contested")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_attribution_hypothesis_repo(db: Session = Depends(get_db)) -> IAttributionHypothesisRepository:
    """Dependency injection for attribution hypothesis repository."""
    return SqlAlchemyAttributionHypothesisRepository(db)


def _to_response(hypothesis: AttributionHypothesis) -> AttributionHypothesisResponse:
    """Convert domain AttributionHypothesis to API response."""
    return AttributionHypothesisResponse(
        id=hypothesis.id,
        coin_id=hypothesis.coin_id,
        hypothesis_rank=hypothesis.hypothesis_rank,
        issuer=hypothesis.issuer,
        issuer_confidence=hypothesis.issuer_confidence.value if hypothesis.issuer_confidence else None,
        mint=hypothesis.mint,
        mint_confidence=hypothesis.mint_confidence.value if hypothesis.mint_confidence else None,
        year_start=hypothesis.year_start,
        year_end=hypothesis.year_end,
        date_confidence=hypothesis.date_confidence.value if hypothesis.date_confidence else None,
        denomination=hypothesis.denomination,
        denomination_confidence=hypothesis.denomination_confidence.value if hypothesis.denomination_confidence else None,
        overall_certainty=hypothesis.overall_certainty.value if hypothesis.overall_certainty else None,
        confidence_score=hypothesis.confidence_score,
        attribution_notes=hypothesis.attribution_notes,
        reference_support=hypothesis.reference_support,
        source=hypothesis.source
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/api/v2/coins/{coin_id}/attribution-hypotheses", response_model=list[AttributionHypothesisResponse], status_code=status.HTTP_200_OK)
def list_attribution_hypotheses(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> list[AttributionHypothesisResponse]:
    """List all attribution hypotheses for a coin (ordered by rank)."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    hypotheses = repo.get_by_coin_id(coin_id)
    return [_to_response(h) for h in hypotheses]


@router.post("/api/v2/coins/{coin_id}/attribution-hypotheses", response_model=AttributionHypothesisResponse, status_code=status.HTTP_201_CREATED)
def create_attribution_hypothesis(
    coin_id: int,
    request: AttributionHypothesisCreateRequest,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> AttributionHypothesisResponse:
    """Create a new attribution hypothesis for a coin."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    # Validate confidence enums
    issuer_conf = AttributionCertainty(request.issuer_confidence) if request.issuer_confidence else None
    mint_conf = AttributionCertainty(request.mint_confidence) if request.mint_confidence else None
    date_conf = AttributionCertainty(request.date_confidence) if request.date_confidence else None
    denom_conf = AttributionCertainty(request.denomination_confidence) if request.denomination_confidence else None
    overall_cert = AttributionCertainty(request.overall_certainty) if request.overall_certainty else None

    # Create hypothesis
    hypothesis = AttributionHypothesis(
        coin_id=coin_id,
        hypothesis_rank=request.hypothesis_rank,
        issuer=request.issuer,
        issuer_confidence=issuer_conf,
        mint=request.mint,
        mint_confidence=mint_conf,
        year_start=request.year_start,
        year_end=request.year_end,
        date_confidence=date_conf,
        denomination=request.denomination,
        denomination_confidence=denom_conf,
        overall_certainty=overall_cert,
        confidence_score=Decimal(str(request.confidence_score)) if request.confidence_score else None,
        attribution_notes=request.attribution_notes,
        reference_support=request.reference_support,
        source=request.source
    )

    try:
        created_hypothesis = repo.create(hypothesis)
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Hypothesis with rank {request.hypothesis_rank} already exists for coin {coin_id}"
            )
        raise

    return _to_response(created_hypothesis)


@router.get("/api/v2/coins/{coin_id}/attribution-hypotheses/primary", response_model=AttributionHypothesisResponse, status_code=status.HTTP_200_OK)
def get_primary_hypothesis(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> AttributionHypothesisResponse:
    """Get the primary attribution hypothesis (rank=1) for a coin."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    hypothesis = repo.get_primary(coin_id)
    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No primary hypothesis found for coin {coin_id}"
        )

    return _to_response(hypothesis)


@router.get("/api/v2/attribution-hypotheses/{hypothesis_id}", response_model=AttributionHypothesisResponse, status_code=status.HTTP_200_OK)
def get_attribution_hypothesis(
    hypothesis_id: int,
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> AttributionHypothesisResponse:
    """Get a single attribution hypothesis by ID."""
    hypothesis = repo.get_by_id(hypothesis_id)

    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribution hypothesis {hypothesis_id} not found"
        )

    return _to_response(hypothesis)


@router.put("/api/v2/attribution-hypotheses/{hypothesis_id}", response_model=AttributionHypothesisResponse, status_code=status.HTTP_200_OK)
def update_attribution_hypothesis(
    hypothesis_id: int,
    request: AttributionHypothesisUpdateRequest,
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> AttributionHypothesisResponse:
    """Update an existing attribution hypothesis."""
    existing = repo.get_by_id(hypothesis_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribution hypothesis {hypothesis_id} not found"
        )

    # Validate confidence enums if provided
    issuer_conf = existing.issuer_confidence
    if request.issuer_confidence:
        issuer_conf = AttributionCertainty(request.issuer_confidence)

    mint_conf = existing.mint_confidence
    if request.mint_confidence:
        mint_conf = AttributionCertainty(request.mint_confidence)

    date_conf = existing.date_confidence
    if request.date_confidence:
        date_conf = AttributionCertainty(request.date_confidence)

    denom_conf = existing.denomination_confidence
    if request.denomination_confidence:
        denom_conf = AttributionCertainty(request.denomination_confidence)

    overall_cert = existing.overall_certainty
    if request.overall_certainty:
        overall_cert = AttributionCertainty(request.overall_certainty)

    # Update hypothesis
    updated_hypothesis = AttributionHypothesis(
        id=existing.id,
        coin_id=existing.coin_id,
        hypothesis_rank=existing.hypothesis_rank,
        issuer=request.issuer if request.issuer is not None else existing.issuer,
        issuer_confidence=issuer_conf,
        mint=request.mint if request.mint is not None else existing.mint,
        mint_confidence=mint_conf,
        year_start=request.year_start if request.year_start is not None else existing.year_start,
        year_end=request.year_end if request.year_end is not None else existing.year_end,
        date_confidence=date_conf,
        denomination=request.denomination if request.denomination is not None else existing.denomination,
        denomination_confidence=denom_conf,
        overall_certainty=overall_cert,
        confidence_score=Decimal(str(request.confidence_score)) if request.confidence_score is not None else existing.confidence_score,
        attribution_notes=request.attribution_notes if request.attribution_notes is not None else existing.attribution_notes,
        reference_support=request.reference_support if request.reference_support is not None else existing.reference_support,
        source=request.source if request.source is not None else existing.source
    )

    result = repo.update(hypothesis_id, updated_hypothesis)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update attribution hypothesis"
        )

    return _to_response(result)


@router.delete("/api/v2/attribution-hypotheses/{hypothesis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attribution_hypothesis(
    hypothesis_id: int,
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
):
    """Delete an attribution hypothesis."""
    success = repo.delete(hypothesis_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribution hypothesis {hypothesis_id} not found"
        )


@router.post("/api/v2/attribution-hypotheses/{hypothesis_id}/set-primary", response_model=AttributionHypothesisResponse, status_code=status.HTTP_200_OK)
def set_primary_hypothesis(
    hypothesis_id: int,
    repo: IAttributionHypothesisRepository = Depends(get_attribution_hypothesis_repo)
) -> AttributionHypothesisResponse:
    """Promote a hypothesis to primary (rank=1), shifting others down."""
    try:
        result = repo.set_primary(hypothesis_id)
        return _to_response(result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/api/v2/coins/{coin_id}/attribution-certainty", status_code=status.HTTP_204_NO_CONTENT)
def update_coin_attribution_certainty(
    coin_id: int,
    request: CoinAttributionCertaintyRequest,
    coin_repo: ICoinRepository = Depends(get_coin_repo)
):
    """Update coin-level attribution certainty."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    # Validate certainty enum
    try:
        AttributionCertainty(request.attribution_certainty)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid attribution_certainty value: {request.attribution_certainty}"
        )

    # TODO: Update coin attribution_certainty field when CoinModel is updated
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Coin-level attribution_certainty update not yet implemented in coin repository"
    )
