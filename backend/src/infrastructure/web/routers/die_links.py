"""
Die Links Router for CoinStack API (Die Study Module Phase 1.5d).

Provides REST endpoints for managing die links between coins.

Endpoints:
- GET /api/v2/die-links/{link_id} - Get single die link
- GET /api/v2/coins/{coin_id}/die-links - List all die links for a coin
- POST /api/v2/die-links - Create die link
- PUT /api/v2/die-links/{link_id} - Update die link
- DELETE /api/v2/die-links/{link_id} - Delete die link
- GET /api/v2/coins/{coin_id}/die-network - Get transitive die network
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import DieLink, DieLinkConfidence
from src.infrastructure.web.dependencies import get_db, get_die_link_repo, get_coin_repo, get_die_repo
from src.domain.repositories_die_study import IDieLinkRepository, IDieRepository
from src.domain.repositories import ICoinRepository

router = APIRouter(tags=["Die Study"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class DieLinkCreateRequest(BaseModel):
    """Request to create a die link."""
    die_id: int = Field(..., description="Die ID from dies catalog")
    coin_a_id: int = Field(..., description="First coin ID")
    coin_b_id: int = Field(..., description="Second coin ID")
    confidence: str = Field(..., description="Confidence: certain, probable, possible")
    notes: Optional[str] = Field(None, description="Additional notes")


class DieLinkUpdateRequest(BaseModel):
    """Request to update a die link (all fields optional)."""
    confidence: Optional[str] = None
    notes: Optional[str] = None


class DieLinkResponse(BaseModel):
    """Response for a die link."""
    id: int
    die_id: int
    coin_a_id: int
    coin_b_id: int
    confidence: str
    notes: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/api/v2/die-links/{link_id}", response_model=DieLinkResponse, status_code=status.HTTP_200_OK)
def get_die_link(
    link_id: int,
    repo: IDieLinkRepository = Depends(get_die_link_repo)
):
    """Get a single die link by ID."""
    link = repo.get_by_id(link_id)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die link {link_id} not found"
        )

    return DieLinkResponse(
        id=link.id,
        die_id=link.die_id,
        coin_a_id=link.coin_a_id,
        coin_b_id=link.coin_b_id,
        confidence=link.confidence.value if link.confidence else "possible",
        notes=link.notes
    )


@router.get("/api/v2/coins/{coin_id}/die-links", response_model=list[DieLinkResponse], status_code=status.HTTP_200_OK)
def list_die_links_for_coin(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: IDieLinkRepository = Depends(get_die_link_repo)
):
    """List all die links for a specific coin."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    links = repo.get_by_coin_id(coin_id)

    return [
        DieLinkResponse(
            id=link.id,
            die_id=link.die_id,
            coin_a_id=link.coin_a_id,
            coin_b_id=link.coin_b_id,
            confidence=link.confidence.value if link.confidence else "possible",
            notes=link.notes
        )
        for link in links
    ]


@router.post("/api/v2/die-links", response_model=DieLinkResponse, status_code=status.HTTP_201_CREATED)
def create_die_link(
    request: DieLinkCreateRequest,
    repo: IDieLinkRepository = Depends(get_die_link_repo),
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    die_repo: IDieRepository = Depends(get_die_repo)
):
    """Create a new die link between two coins."""
    # Validate die exists (CRITICAL FIX from code review)
    if not die_repo.get_by_id(request.die_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {request.die_id} not found"
        )

    # Validate both coins exist
    if not coin_repo.get_by_id(request.coin_a_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {request.coin_a_id} not found"
        )
    if not coin_repo.get_by_id(request.coin_b_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {request.coin_b_id} not found"
        )

    # Prevent self-linking
    if request.coin_a_id == request.coin_b_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot link a coin to itself"
        )

    # Validate confidence enum
    try:
        confidence = DieLinkConfidence(request.confidence)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid confidence value: {request.confidence}"
        )

    # Create die link
    link = DieLink(
        die_id=request.die_id,
        coin_a_id=request.coin_a_id,
        coin_b_id=request.coin_b_id,
        confidence=confidence,
        notes=request.notes
    )

    try:
        created_link = repo.create(link)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

    return DieLinkResponse(
        id=created_link.id,
        die_id=created_link.die_id,
        coin_a_id=created_link.coin_a_id,
        coin_b_id=created_link.coin_b_id,
        confidence=created_link.confidence.value if created_link.confidence else "possible",
        notes=created_link.notes
    )


@router.put("/api/v2/die-links/{link_id}", response_model=DieLinkResponse, status_code=status.HTTP_200_OK)
def update_die_link(
    link_id: int,
    request: DieLinkUpdateRequest,
    repo: IDieLinkRepository = Depends(get_die_link_repo)
):
    """Update an existing die link."""
    existing = repo.get_by_id(link_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die link {link_id} not found"
        )

    # Validate confidence enum if provided
    confidence = existing.confidence
    if request.confidence:
        try:
            confidence = DieLinkConfidence(request.confidence)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid confidence value: {request.confidence}"
            )

    # Update die link
    updated_link = DieLink(
        id=existing.id,
        die_id=existing.die_id,
        coin_a_id=existing.coin_a_id,
        coin_b_id=existing.coin_b_id,
        confidence=confidence,
        notes=request.notes if request.notes is not None else existing.notes
    )

    result = repo.update(link_id, updated_link)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update die link"
        )

    return DieLinkResponse(
        id=result.id,
        die_id=result.die_id,
        coin_a_id=result.coin_a_id,
        coin_b_id=result.coin_b_id,
        confidence=result.confidence.value if result.confidence else "possible",
        notes=result.notes
    )


@router.delete("/api/v2/die-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_die_link(
    link_id: int,
    repo: IDieLinkRepository = Depends(get_die_link_repo)
):
    """Delete a die link."""
    success = repo.delete(link_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die link {link_id} not found"
        )


@router.get("/api/v2/coins/{coin_id}/die-network", response_model=list[int], status_code=status.HTTP_200_OK)
def get_die_network(
    coin_id: int,
    die_id: int,
    max_depth: int = Query(default=3, ge=1, le=10, description="Max BFS depth (1-10)"),
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    die_repo: IDieRepository = Depends(get_die_repo),
    repo: IDieLinkRepository = Depends(get_die_link_repo)
):
    """Get all coins transitively linked via shared die (BFS up to max_depth)."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    # Verify die exists (CRITICAL FIX from code review)
    if not die_repo.get_by_id(die_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )

    network = repo.get_die_network(coin_id, die_id, max_depth)

    return network
