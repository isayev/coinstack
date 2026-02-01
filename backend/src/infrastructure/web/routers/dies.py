"""
Dies Catalog Router for CoinStack API (Die Study Module Phase 1.5d).

Provides REST endpoints for managing the master die catalog.

Endpoints:
- GET /api/v2/dies - List all dies with pagination
- POST /api/v2/dies - Create a die
- GET /api/v2/dies/{die_id} - Get single die
- PUT /api/v2/dies/{die_id} - Update die
- DELETE /api/v2/dies/{die_id} - Delete die
- GET /api/v2/dies/search - Search dies by identifier or notes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import Die, DieSide, DieState
from src.infrastructure.web.dependencies import get_db, get_die_repo
from src.domain.repositories_die_study import IDieRepository
from src.infrastructure.pagination_config import get_pagination_config

router = APIRouter(tags=["Die Study"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class DieCreateRequest(BaseModel):
    """Request to create a die."""
    die_identifier: str = Field(..., description="Canonical die ID (e.g., RIC_207_OBV_A)")
    die_side: Optional[str] = Field(None, description="Side: obverse, reverse")
    die_state: Optional[str] = Field(None, description="State: early, middle, late, broken, repaired")
    has_die_crack: bool = Field(False, description="Die shows cracks")
    has_die_clash: bool = Field(False, description="Die shows clash marks")
    die_rotation_angle: Optional[int] = Field(None, ge=0, le=360, description="Die rotation angle (0-360)")
    reference_system: Optional[str] = Field(None, description="Catalog system (RIC, Crawford, etc.)")
    reference_number: Optional[str] = Field(None, description="Type reference number")
    notes: Optional[str] = Field(None, description="Additional notes")


class DieUpdateRequest(BaseModel):
    """Request to update a die (all fields optional)."""
    die_identifier: Optional[str] = None
    die_side: Optional[str] = None
    die_state: Optional[str] = None
    has_die_crack: Optional[bool] = None
    has_die_clash: Optional[bool] = None
    die_rotation_angle: Optional[int] = Field(None, ge=0, le=360)
    reference_system: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class DieResponse(BaseModel):
    """Response for a die."""
    id: int
    die_identifier: str
    die_side: Optional[str] = None
    die_state: Optional[str] = None
    has_die_crack: bool = False
    has_die_clash: bool = False
    die_rotation_angle: Optional[int] = None
    reference_system: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _to_response(die: Die) -> DieResponse:
    """Convert domain Die to API response."""
    return DieResponse(
        id=die.id,
        die_identifier=die.die_identifier,
        die_side=die.die_side.value if die.die_side else None,
        die_state=die.die_state.value if die.die_state else None,
        has_die_crack=die.has_die_crack,
        has_die_clash=die.has_die_clash,
        die_rotation_angle=die.die_rotation_angle,
        reference_system=die.reference_system,
        reference_number=die.reference_number,
        notes=die.notes
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/api/v2/dies", response_model=list[DieResponse], status_code=status.HTTP_200_OK)
def list_dies(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: Optional[int] = Query(None, description="Max records to return"),
    repo: IDieRepository = Depends(get_die_repo)
) -> list[DieResponse]:
    """List all dies with pagination."""
    config = get_pagination_config()

    # Use default if not specified
    if limit is None:
        limit = config.default_limit

    # Validate limit is positive
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be greater than 0"
        )

    # Enforce maximum
    if limit > config.max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit exceeds maximum of {config.max_limit}"
        )

    dies = repo.list_all(skip=skip, limit=limit)
    return [_to_response(die) for die in dies]


@router.post("/api/v2/dies", response_model=DieResponse, status_code=status.HTTP_201_CREATED)
def create_die(
    request: DieCreateRequest,
    repo: IDieRepository = Depends(get_die_repo)
) -> DieResponse:
    """Create a new die entry."""
    # Validate enums
    die_side = None
    if request.die_side:
        try:
            die_side = DieSide(request.die_side)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid die_side: {request.die_side}"
            )

    die_state = None
    if request.die_state:
        try:
            die_state = DieState(request.die_state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid die_state: {request.die_state}"
            )

    # Create die
    die = Die(
        die_identifier=request.die_identifier,
        die_side=die_side,
        die_state=die_state,
        has_die_crack=request.has_die_crack,
        has_die_clash=request.has_die_clash,
        die_rotation_angle=request.die_rotation_angle,
        reference_system=request.reference_system,
        reference_number=request.reference_number,
        notes=request.notes
    )

    try:
        created_die = repo.create(die)
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Die '{request.die_identifier}' already exists"
            )
        raise

    return _to_response(created_die)


@router.get("/api/v2/dies/search", response_model=list[DieResponse], status_code=status.HTTP_200_OK)
def search_dies(
    q: str = Query(..., min_length=1, description="Search query"),
    die_side: Optional[str] = Query(None, description="Filter by die side (obverse/reverse)"),
    repo: IDieRepository = Depends(get_die_repo)
) -> list[DieResponse]:
    """Search dies by identifier or notes."""
    # Validate die_side if provided
    if die_side:
        try:
            DieSide(die_side)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid die_side: {die_side}"
            )

    dies = repo.search(query=q, die_side=die_side)
    return [_to_response(die) for die in dies]


@router.get("/api/v2/dies/{die_id}", response_model=DieResponse, status_code=status.HTTP_200_OK)
def get_die(
    die_id: int,
    repo: IDieRepository = Depends(get_die_repo)
) -> DieResponse:
    """Get a single die by ID."""
    die = repo.get_by_id(die_id)

    if not die:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )

    return _to_response(die)


@router.put("/api/v2/dies/{die_id}", response_model=DieResponse, status_code=status.HTTP_200_OK)
def update_die(
    die_id: int,
    request: DieUpdateRequest,
    repo: IDieRepository = Depends(get_die_repo)
) -> DieResponse:
    """Update an existing die entry."""
    existing = repo.get_by_id(die_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )

    # Validate enums if provided
    die_side = existing.die_side
    if request.die_side:
        try:
            die_side = DieSide(request.die_side)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid die_side: {request.die_side}"
            )

    die_state = existing.die_state
    if request.die_state:
        try:
            die_state = DieState(request.die_state)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid die_state: {request.die_state}"
            )

    # Update die
    updated_die = Die(
        id=existing.id,
        die_identifier=request.die_identifier or existing.die_identifier,
        die_side=die_side,
        die_state=die_state,
        has_die_crack=request.has_die_crack if request.has_die_crack is not None else existing.has_die_crack,
        has_die_clash=request.has_die_clash if request.has_die_clash is not None else existing.has_die_clash,
        die_rotation_angle=request.die_rotation_angle if request.die_rotation_angle is not None else existing.die_rotation_angle,
        reference_system=request.reference_system if request.reference_system is not None else existing.reference_system,
        reference_number=request.reference_number if request.reference_number is not None else existing.reference_number,
        notes=request.notes if request.notes is not None else existing.notes
    )

    try:
        result = repo.update(die_id, updated_die)
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Die identifier '{updated_die.die_identifier}' already exists"
            )
        raise

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )

    return _to_response(result)


@router.delete("/api/v2/dies/{die_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_die(
    die_id: int,
    repo: IDieRepository = Depends(get_die_repo)
):
    """Delete a die entry."""
    success = repo.delete(die_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Die {die_id} not found"
        )
