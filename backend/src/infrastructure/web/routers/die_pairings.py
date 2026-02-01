"""
Die Pairings Router for CoinStack API (Die Study Module Phase 1.5d).

Provides REST endpoints for managing obverse-reverse die combinations.

Endpoints:
- GET /api/v2/die-pairings - List all die pairings
- POST /api/v2/die-pairings - Create a die pairing
- GET /api/v2/die-pairings/{pairing_id} - Get single pairing
- PUT /api/v2/die-pairings/{pairing_id} - Update pairing
- DELETE /api/v2/die-pairings/{pairing_id} - Delete pairing
- GET /api/v2/dies/{die_id}/pairings - Get all pairings for a die
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import DiePairing
from src.infrastructure.web.dependencies import get_db, get_die_pairing_repo, get_die_repo
from src.domain.repositories_die_study import IDiePairingRepository, IDieRepository

router = APIRouter(tags=["Die Study"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class DiePairingCreateRequest(BaseModel):
    """Request to create a die pairing."""
    obverse_die_id: int = Field(..., description="Obverse die ID")
    reverse_die_id: int = Field(..., description="Reverse die ID")
    reference_system: Optional[str] = Field(None, description="Catalog system (RIC, Crawford, etc.)")
    reference_number: Optional[str] = Field(None, description="Type reference number")
    rarity_notes: Optional[str] = Field(None, description="Pairing-specific rarity notes")
    specimen_count: Optional[int] = Field(None, ge=0, description="Known examples of this pairing")
    notes: Optional[str] = Field(None, description="Additional notes")


class DiePairingUpdateRequest(BaseModel):
    """Request to update a die pairing (all fields optional)."""
    reference_system: Optional[str] = None
    reference_number: Optional[str] = None
    rarity_notes: Optional[str] = None
    specimen_count: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class DiePairingResponse(BaseModel):
    """Response for a die pairing."""
    id: int
    obverse_die_id: int
    reverse_die_id: int
    reference_system: Optional[str] = None
    reference_number: Optional[str] = None
    rarity_notes: Optional[str] = None
    specimen_count: Optional[int] = None
    notes: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _to_response(pairing: DiePairing) -> DiePairingResponse:
    """Convert domain DiePairing to API response."""
    return DiePairingResponse(
        id=pairing.id,
        obverse_die_id=pairing.obverse_die_id,
        reverse_die_id=pairing.reverse_die_id,
        reference_system=pairing.reference_system,
        reference_number=pairing.reference_number,
        rarity_notes=pairing.rarity_notes,
        specimen_count=pairing.specimen_count,
        notes=pairing.notes
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/api/v2/die-pairings", response_model=list[DiePairingResponse], status_code=status.HTTP_200_OK)
def list_die_pairings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    repo: IDiePairingRepository = Depends(get_die_pairing_repo)
) -> list[DiePairingResponse]:
    """List all die pairings with pagination."""
    # Note: This would need a list_all method in the repository interface
    # For now, we'll use a workaround - in production, add list_all to interface
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="List all pairings not yet implemented - use GET /api/v2/dies/{die_id}/pairings"
    )


@router.post("/api/v2/die-pairings", response_model=DiePairingResponse, status_code=status.HTTP_201_CREATED)
def create_die_pairing(
    request: DiePairingCreateRequest,
    pairing_repo: IDiePairingRepository = Depends(get_die_pairing_repo),
    die_repo: IDieRepository = Depends(get_die_repo)
) -> DiePairingResponse:
    """Create a new die pairing."""
    # Validate both dies exist
    obverse_die = die_repo.get_by_id(request.obverse_die_id)
    if not obverse_die:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Obverse die {request.obverse_die_id} not found"
        )

    # Validate obverse die is actually obverse side
    if obverse_die.die_side and obverse_die.die_side.value != "obverse":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Die {request.obverse_die_id} is not an obverse die (side: {obverse_die.die_side.value})"
        )

    reverse_die = die_repo.get_by_id(request.reverse_die_id)
    if not reverse_die:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reverse die {request.reverse_die_id} not found"
        )

    # Validate reverse die is actually reverse side
    if reverse_die.die_side and reverse_die.die_side.value != "reverse":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Die {request.reverse_die_id} is not a reverse die (side: {reverse_die.die_side.value})"
        )

    # Check for duplicate pairing
    existing = pairing_repo.get_by_dies(request.obverse_die_id, request.reverse_die_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Die pairing already exists between obverse die {request.obverse_die_id} and reverse die {request.reverse_die_id}"
        )

    # Create die pairing
    pairing = DiePairing(
        obverse_die_id=request.obverse_die_id,
        reverse_die_id=request.reverse_die_id,
        reference_system=request.reference_system,
        reference_number=request.reference_number,
        rarity_notes=request.rarity_notes,
        specimen_count=request.specimen_count,
        notes=request.notes
    )

    created_pairing = pairing_repo.create(pairing)
    return _to_response(created_pairing)


@router.get("/api/v2/die-pairings/{pairing_id}", response_model=DiePairingResponse, status_code=status.HTTP_200_OK)
def get_die_pairing(
    pairing_id: int,
    repo: IDiePairingRepository = Depends(get_die_pairing_repo)
) -> DiePairingResponse:
    """Get a single die pairing by ID."""
    pairing = repo.get_by_id(pairing_id)

    if not pairing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die pairing {pairing_id} not found"
        )

    return _to_response(pairing)


@router.put("/api/v2/die-pairings/{pairing_id}", response_model=DiePairingResponse, status_code=status.HTTP_200_OK)
def update_die_pairing(
    pairing_id: int,
    request: DiePairingUpdateRequest,
    repo: IDiePairingRepository = Depends(get_die_pairing_repo)
) -> DiePairingResponse:
    """Update an existing die pairing."""
    existing = repo.get_by_id(pairing_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die pairing {pairing_id} not found"
        )

    # Update die pairing
    updated_pairing = DiePairing(
        id=existing.id,
        obverse_die_id=existing.obverse_die_id,
        reverse_die_id=existing.reverse_die_id,
        reference_system=request.reference_system if request.reference_system is not None else existing.reference_system,
        reference_number=request.reference_number if request.reference_number is not None else existing.reference_number,
        rarity_notes=request.rarity_notes if request.rarity_notes is not None else existing.rarity_notes,
        specimen_count=request.specimen_count if request.specimen_count is not None else existing.specimen_count,
        notes=request.notes if request.notes is not None else existing.notes
    )

    result = repo.update(pairing_id, updated_pairing)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update die pairing"
        )

    return _to_response(result)


@router.delete("/api/v2/die-pairings/{pairing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_die_pairing(
    pairing_id: int,
    repo: IDiePairingRepository = Depends(get_die_pairing_repo)
):
    """Delete a die pairing."""
    success = repo.delete(pairing_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die pairing {pairing_id} not found"
        )


@router.get("/api/v2/dies/{die_id}/pairings", response_model=list[DiePairingResponse], status_code=status.HTTP_200_OK)
def get_pairings_for_die(
    die_id: int,
    side: str = Query(..., description="Die side (obverse or reverse)"),
    die_repo: IDieRepository = Depends(get_die_repo),
    pairing_repo: IDiePairingRepository = Depends(get_die_pairing_repo)
) -> list[DiePairingResponse]:
    """Get all pairings for a specific die."""
    # Verify die exists
    die = die_repo.get_by_id(die_id)
    if not die:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )

    # Validate side parameter
    if side not in ["obverse", "reverse"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid side parameter: {side}. Must be 'obverse' or 'reverse'"
        )

    # Get pairings based on die side
    if side == "obverse":
        pairings = pairing_repo.list_by_obverse(die_id)
    else:
        pairings = pairing_repo.list_by_reverse(die_id)

    return [_to_response(pairing) for pairing in pairings]
