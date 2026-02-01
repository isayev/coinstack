"""
Die Varieties Router for CoinStack API (Die Study Module Phase 1.5d).

Provides REST endpoints for managing die variety classifications.

Endpoints:
- GET /api/v2/coins/{coin_id}/die-varieties - List all varieties for a coin
- POST /api/v2/coins/{coin_id}/die-varieties - Create variety
- GET /api/v2/die-varieties/{variety_id} - Get single variety
- PUT /api/v2/die-varieties/{variety_id} - Update variety
- DELETE /api/v2/die-varieties/{variety_id} - Delete variety
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import DieVariety
from src.infrastructure.web.dependencies import get_db, get_die_variety_repo, get_coin_repo, get_die_repo
from src.domain.repositories_die_study import IDieVarietyRepository, IDieRepository
from src.domain.repositories import ICoinRepository

router = APIRouter(tags=["Die Study"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class DieVarietyCreateRequest(BaseModel):
    """Request to create a die variety."""
    die_id: Optional[int] = Field(None, description="Die ID from dies catalog")
    variety_code: str = Field(..., description="Variety code (e.g., RIC 207 var. a)")
    variety_description: Optional[str] = Field(None, description="Brief description")
    distinguishing_features: Optional[str] = Field(None, description="What makes this variety unique")
    reference: Optional[str] = Field(None, description="Source catalog")
    notes: Optional[str] = Field(None, description="Additional notes")


class DieVarietyUpdateRequest(BaseModel):
    """Request to update a die variety (all fields optional)."""
    die_id: Optional[int] = None
    variety_code: Optional[str] = None
    variety_description: Optional[str] = None
    distinguishing_features: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class DieVarietyResponse(BaseModel):
    """Response for a die variety."""
    id: int
    coin_id: int
    die_id: Optional[int] = None
    variety_code: str
    variety_description: Optional[str] = None
    distinguishing_features: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/api/v2/coins/{coin_id}/die-varieties", response_model=list[DieVarietyResponse], status_code=status.HTTP_200_OK)
def list_die_varieties_for_coin(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    repo: IDieVarietyRepository = Depends(get_die_variety_repo)
):
    """List all die varieties for a specific coin."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    varieties = repo.get_by_coin_id(coin_id)

    return [
        DieVarietyResponse(
            id=variety.id,
            coin_id=variety.coin_id,
            die_id=variety.die_id,
            variety_code=variety.variety_code,
            variety_description=variety.variety_description,
            distinguishing_features=variety.distinguishing_features,
            reference=variety.reference,
            notes=variety.notes
        )
        for variety in varieties
    ]


@router.post("/api/v2/coins/{coin_id}/die-varieties", response_model=DieVarietyResponse, status_code=status.HTTP_201_CREATED)
def create_die_variety(
    coin_id: int,
    request: DieVarietyCreateRequest,
    repo: IDieVarietyRepository = Depends(get_die_variety_repo),
    coin_repo: ICoinRepository = Depends(get_coin_repo),
    die_repo: IDieRepository = Depends(get_die_repo)
):
    """Create a new die variety for a coin."""
    # Verify coin exists
    if not coin_repo.get_by_id(coin_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {coin_id} not found"
        )

    # Verify die exists if provided (CRITICAL FIX from code review)
    if request.die_id and not die_repo.get_by_id(request.die_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {request.die_id} not found"
        )

    # Create die variety
    variety = DieVariety(
        coin_id=coin_id,
        die_id=request.die_id,
        variety_code=request.variety_code,
        variety_description=request.variety_description,
        distinguishing_features=request.distinguishing_features,
        reference=request.reference,
        notes=request.notes
    )

    created_variety = repo.create(variety)

    return DieVarietyResponse(
        id=created_variety.id,
        coin_id=created_variety.coin_id,
        die_id=created_variety.die_id,
        variety_code=created_variety.variety_code,
        variety_description=created_variety.variety_description,
        distinguishing_features=created_variety.distinguishing_features,
        reference=created_variety.reference,
        notes=created_variety.notes
    )


@router.get("/api/v2/die-varieties/{variety_id}", response_model=DieVarietyResponse, status_code=status.HTTP_200_OK)
def get_die_variety(
    variety_id: int,
    repo: IDieVarietyRepository = Depends(get_die_variety_repo)
):
    """Get a single die variety by ID."""
    variety = repo.get_by_id(variety_id)

    if not variety:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die variety {variety_id} not found"
        )

    return DieVarietyResponse(
        id=variety.id,
        coin_id=variety.coin_id,
        die_id=variety.die_id,
        variety_code=variety.variety_code,
        variety_description=variety.variety_description,
        distinguishing_features=variety.distinguishing_features,
        reference=variety.reference,
        notes=variety.notes
    )


@router.put("/api/v2/die-varieties/{variety_id}", response_model=DieVarietyResponse, status_code=status.HTTP_200_OK)
def update_die_variety(
    variety_id: int,
    request: DieVarietyUpdateRequest,
    repo: IDieVarietyRepository = Depends(get_die_variety_repo),
    die_repo: IDieRepository = Depends(get_die_repo)
):
    """Update an existing die variety."""
    existing = repo.get_by_id(variety_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die variety {variety_id} not found"
        )

    # Verify die exists if being updated (CRITICAL FIX from code review)
    if request.die_id and not die_repo.get_by_id(request.die_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {request.die_id} not found"
        )

    # Update die variety
    updated_variety = DieVariety(
        id=existing.id,
        coin_id=existing.coin_id,
        die_id=request.die_id if request.die_id is not None else existing.die_id,
        variety_code=request.variety_code or existing.variety_code,
        variety_description=request.variety_description if request.variety_description is not None else existing.variety_description,
        distinguishing_features=request.distinguishing_features if request.distinguishing_features is not None else existing.distinguishing_features,
        reference=request.reference if request.reference is not None else existing.reference,
        notes=request.notes if request.notes is not None else existing.notes
    )

    result = repo.update(variety_id, updated_variety)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update die variety"
        )

    return DieVarietyResponse(
        id=result.id,
        coin_id=result.coin_id,
        die_id=result.die_id,
        variety_code=result.variety_code,
        variety_description=result.variety_description,
        distinguishing_features=result.distinguishing_features,
        reference=result.reference,
        notes=result.notes
    )


@router.delete("/api/v2/die-varieties/{variety_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_die_variety(
    variety_id: int,
    repo: IDieVarietyRepository = Depends(get_die_variety_repo)
):
    """Delete a die variety."""
    success = repo.delete(variety_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die variety {variety_id} not found"
        )
