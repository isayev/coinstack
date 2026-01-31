"""
Grading History Router for CoinStack API (Schema V3 Phase 2).

Provides REST endpoints for managing coin grading history (TPG lifecycle).
Tracks initial submissions, crossovers, regrades, and crack-outs.

Endpoints:
- GET /api/v2/coins/{coin_id}/grading-history - List all grading entries
- GET /api/v2/coins/{coin_id}/grading-history/current - Get current grading
- POST /api/v2/coins/{coin_id}/grading-history - Create entry
- GET /api/v2/coins/{coin_id}/grading-history/{entry_id} - Get single entry
- PUT /api/v2/coins/{coin_id}/grading-history/{entry_id} - Update entry
- DELETE /api/v2/coins/{coin_id}/grading-history/{entry_id} - Delete entry
- POST /api/v2/coins/{coin_id}/grading-history/{entry_id}/set-current - Mark as current
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import GradingHistoryEntry, GradingEventType
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.grading_history_repository import SqlAlchemyGradingHistoryRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(
    prefix="/api/v2/coins/{coin_id}/grading-history",
    tags=["Grading History"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class GradingHistoryCreateRequest(BaseModel):
    """Request to create a grading history entry."""
    grading_state: str = Field(..., description="Grading state: raw, slabbed, capsule, flip")
    event_type: str = Field("initial", description="Event type: initial, crossover, regrade, crack_out")
    grade: Optional[str] = Field(None, description="Grade (e.g., Ch XF, MS 63)")
    grade_service: Optional[str] = Field(None, description="Grading service: ngc, pcgs, icg, anacs")
    certification_number: Optional[str] = Field(None, description="TPG certification number")
    strike_quality: Optional[str] = Field(None, description="Strike quality (1-5 scale)")
    surface_quality: Optional[str] = Field(None, description="Surface quality (1-5 scale)")
    grade_numeric: Optional[int] = Field(None, ge=1, le=70, description="Numeric grade (1-70)")
    designation: Optional[str] = Field(None, description="Designation: Fine Style, Choice, Gem, etc.")
    has_star: bool = Field(False, description="NGC star designation")
    photo_cert: bool = Field(False, description="Photo certificate")
    verification_url: Optional[str] = Field(None, description="NGC/PCGS verification URL")
    graded_date: Optional[date] = Field(None, description="Date grading occurred")
    submitter: Optional[str] = Field(None, description="Who submitted for grading")
    turnaround_days: Optional[int] = Field(None, ge=0, description="Days from submission to receipt")
    grading_fee: Optional[float] = Field(None, ge=0, description="Cost of grading service")
    notes: Optional[str] = Field(None, description="Additional notes")
    sequence_order: int = Field(0, ge=0, description="Order in timeline")
    is_current: bool = Field(False, description="Is this the current grading state?")


class GradingHistoryUpdateRequest(BaseModel):
    """Request to update a grading history entry (all fields optional)."""
    grading_state: Optional[str] = None
    event_type: Optional[str] = None
    grade: Optional[str] = None
    grade_service: Optional[str] = None
    certification_number: Optional[str] = None
    strike_quality: Optional[str] = None
    surface_quality: Optional[str] = None
    grade_numeric: Optional[int] = Field(None, ge=1, le=70)
    designation: Optional[str] = None
    has_star: Optional[bool] = None
    photo_cert: Optional[bool] = None
    verification_url: Optional[str] = None
    graded_date: Optional[date] = None
    submitter: Optional[str] = None
    turnaround_days: Optional[int] = Field(None, ge=0)
    grading_fee: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None
    sequence_order: Optional[int] = Field(None, ge=0)
    is_current: Optional[bool] = None


class GradingHistoryResponse(BaseModel):
    """Response for a grading history entry."""
    id: int
    coin_id: int
    grading_state: Optional[str] = None
    event_type: str
    grade: Optional[str] = None
    grade_service: Optional[str] = None
    certification_number: Optional[str] = None
    strike_quality: Optional[str] = None
    surface_quality: Optional[str] = None
    grade_numeric: Optional[int] = None
    designation: Optional[str] = None
    has_star: bool = False
    photo_cert: bool = False
    verification_url: Optional[str] = None
    graded_date: Optional[date] = None
    recorded_at: Optional[str] = None
    submitter: Optional[str] = None
    turnaround_days: Optional[int] = None
    grading_fee: Optional[float] = None
    notes: Optional[str] = None
    sequence_order: int = 0
    is_current: bool = False


class GradingHistoryListResponse(BaseModel):
    """Response for listing grading history entries."""
    coin_id: int
    entries: List[GradingHistoryResponse]
    total: int
    has_current: bool = False
    current_entry_id: Optional[int] = None


# =============================================================================
# VALID VALUES - Use enum values to prevent drift
# =============================================================================

VALID_GRADING_STATES = {"raw", "slabbed", "capsule", "flip"}
VALID_EVENT_TYPES = {e.value for e in GradingEventType}  # Use enum values
VALID_GRADE_SERVICES = {"ngc", "pcgs", "icg", "anacs", "none", None}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_grading_history_repo(db: Session = Depends(get_db)) -> SqlAlchemyGradingHistoryRepository:
    """Get grading history repository instance."""
    return SqlAlchemyGradingHistoryRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def entry_to_response(entry: GradingHistoryEntry) -> GradingHistoryResponse:
    """Convert domain GradingHistoryEntry to API response."""
    return GradingHistoryResponse(
        id=entry.id,
        coin_id=entry.coin_id,
        grading_state=entry.grading_state,
        event_type=entry.event_type,
        grade=entry.grade,
        grade_service=entry.grade_service,
        certification_number=entry.certification_number,
        strike_quality=entry.strike_quality,
        surface_quality=entry.surface_quality,
        grade_numeric=entry.grade_numeric,
        designation=entry.designation,
        has_star=entry.has_star,
        photo_cert=entry.photo_cert,
        verification_url=entry.verification_url,
        graded_date=entry.graded_date,
        recorded_at=entry.recorded_at,
        submitter=entry.submitter,
        turnaround_days=entry.turnaround_days,
        grading_fee=float(entry.grading_fee) if entry.grading_fee else None,
        notes=entry.notes,
        sequence_order=entry.sequence_order,
        is_current=entry.is_current,
    )


def validate_coin_exists(coin_id: int, coin_repo: SqlAlchemyCoinRepository) -> None:
    """Verify coin exists, raise 404 if not."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")


# =============================================================================
# ENDPOINTS
# Note: Static routes (/current) MUST be defined BEFORE parameterized routes (/{entry_id})
# =============================================================================

@router.get(
    "",
    response_model=GradingHistoryListResponse,
    summary="List grading history",
    description="Get all grading history entries for a coin, ordered by sequence."
)
def list_grading_history(
    coin_id: int,
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """List all grading history entries for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    entries = grading_repo.get_by_coin_id(coin_id)
    response_entries = [entry_to_response(e) for e in entries]

    # Find current entry
    current_entry_id = None
    for entry in entries:
        if entry.is_current:
            current_entry_id = entry.id
            break

    return GradingHistoryListResponse(
        coin_id=coin_id,
        entries=response_entries,
        total=len(response_entries),
        has_current=current_entry_id is not None,
        current_entry_id=current_entry_id,
    )


# CRITICAL: This route MUST be before /{entry_id} routes to prevent "current" being matched as entry_id
@router.get(
    "/current",
    response_model=Optional[GradingHistoryResponse],
    summary="Get current grading",
    description="Get the current (active) grading state for a coin."
)
def get_current_grading(
    coin_id: int,
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get the current grading state for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    current = grading_repo.get_current(coin_id)
    if not current:
        return None

    return entry_to_response(current)


@router.post(
    "",
    response_model=GradingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create grading history entry",
    description="Add a new grading event to a coin's TPG lifecycle."
)
def create_grading_history(
    coin_id: int,
    request: GradingHistoryCreateRequest,
    db: Session = Depends(get_db),
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Create a grading history entry.

    Valid event_type values:
    - initial: First submission to TPG
    - crossover: Moving from one TPG service to another
    - regrade: Resubmission to same service
    - crack_out: Removed from slab (returned to raw)
    """
    validate_coin_exists(coin_id, coin_repo)

    # Validate grading state
    if request.grading_state not in VALID_GRADING_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grading_state '{request.grading_state}'. Must be one of: {', '.join(sorted(VALID_GRADING_STATES))}"
        )

    # Validate event type
    if request.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type '{request.event_type}'. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
        )

    # Validate grade service if provided
    if request.grade_service and request.grade_service not in VALID_GRADE_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grade_service '{request.grade_service}'. Must be one of: ngc, pcgs, icg, anacs, none"
        )

    # If marking as current, clear existing current entries first
    if request.is_current:
        grading_repo.clear_all_current(coin_id)

    # Create domain entry
    entry = GradingHistoryEntry(
        grading_state=request.grading_state,
        event_type=request.event_type,
        grade=request.grade,
        grade_service=request.grade_service,
        certification_number=request.certification_number,
        strike_quality=request.strike_quality,
        surface_quality=request.surface_quality,
        grade_numeric=request.grade_numeric,
        designation=request.designation,
        has_star=request.has_star,
        photo_cert=request.photo_cert,
        verification_url=request.verification_url,
        graded_date=request.graded_date,
        submitter=request.submitter,
        turnaround_days=request.turnaround_days,
        grading_fee=Decimal(str(request.grading_fee)) if request.grading_fee else None,
        notes=request.notes,
        sequence_order=request.sequence_order,
        is_current=request.is_current,
    )

    created = grading_repo.create(coin_id, entry)
    db.commit()

    return entry_to_response(created)


@router.get(
    "/{entry_id}",
    response_model=GradingHistoryResponse,
    summary="Get grading history entry",
    description="Get a specific grading history entry."
)
def get_grading_history_entry(
    coin_id: int,
    entry_id: int,
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get a specific grading history entry."""
    validate_coin_exists(coin_id, coin_repo)

    entry = grading_repo.get_by_id(entry_id)
    if not entry or entry.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Grading history entry {entry_id} not found for coin {coin_id}")

    return entry_to_response(entry)


@router.put(
    "/{entry_id}",
    response_model=GradingHistoryResponse,
    summary="Update grading history entry",
    description="Update an existing grading history entry."
)
def update_grading_history_entry(
    coin_id: int,
    entry_id: int,
    request: GradingHistoryUpdateRequest,
    db: Session = Depends(get_db),
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Update a grading history entry. Only provided fields will be updated."""
    validate_coin_exists(coin_id, coin_repo)

    existing = grading_repo.get_by_id(entry_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Grading history entry {entry_id} not found for coin {coin_id}")

    # Validate updates if provided
    if request.grading_state and request.grading_state not in VALID_GRADING_STATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grading_state '{request.grading_state}'. Must be one of: {', '.join(sorted(VALID_GRADING_STATES))}"
        )

    if request.event_type and request.event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type '{request.event_type}'. Must be one of: {', '.join(sorted(VALID_EVENT_TYPES))}"
        )

    if request.grade_service and request.grade_service not in VALID_GRADE_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid grade_service '{request.grade_service}'. Must be one of: ngc, pcgs, icg, anacs, none"
        )

    # Build updated entry (merge with existing)
    updated_entry = GradingHistoryEntry(
        id=existing.id,
        coin_id=existing.coin_id,
        grading_state=request.grading_state if request.grading_state is not None else existing.grading_state,
        event_type=request.event_type if request.event_type is not None else existing.event_type,
        grade=request.grade if request.grade is not None else existing.grade,
        grade_service=request.grade_service if request.grade_service is not None else existing.grade_service,
        certification_number=request.certification_number if request.certification_number is not None else existing.certification_number,
        strike_quality=request.strike_quality if request.strike_quality is not None else existing.strike_quality,
        surface_quality=request.surface_quality if request.surface_quality is not None else existing.surface_quality,
        grade_numeric=request.grade_numeric if request.grade_numeric is not None else existing.grade_numeric,
        designation=request.designation if request.designation is not None else existing.designation,
        has_star=request.has_star if request.has_star is not None else existing.has_star,
        photo_cert=request.photo_cert if request.photo_cert is not None else existing.photo_cert,
        verification_url=request.verification_url if request.verification_url is not None else existing.verification_url,
        graded_date=request.graded_date if request.graded_date is not None else existing.graded_date,
        recorded_at=existing.recorded_at,
        submitter=request.submitter if request.submitter is not None else existing.submitter,
        turnaround_days=request.turnaround_days if request.turnaround_days is not None else existing.turnaround_days,
        grading_fee=Decimal(str(request.grading_fee)) if request.grading_fee is not None else existing.grading_fee,
        notes=request.notes if request.notes is not None else existing.notes,
        sequence_order=request.sequence_order if request.sequence_order is not None else existing.sequence_order,
        is_current=request.is_current if request.is_current is not None else existing.is_current,
    )

    updated = grading_repo.update(entry_id, updated_entry)
    db.commit()

    return entry_to_response(updated)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete grading history entry",
    description="Delete a grading history entry."
)
def delete_grading_history_entry(
    coin_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Delete a grading history entry."""
    validate_coin_exists(coin_id, coin_repo)

    existing = grading_repo.get_by_id(entry_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Grading history entry {entry_id} not found for coin {coin_id}")

    grading_repo.delete(entry_id)
    db.commit()

    return None


@router.post(
    "/{entry_id}/set-current",
    response_model=GradingHistoryResponse,
    summary="Set as current grading",
    description="Mark a grading history entry as the current (active) grading state."
)
def set_current_grading(
    coin_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    grading_repo: SqlAlchemyGradingHistoryRepository = Depends(get_grading_history_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Mark a grading history entry as the current grading state.

    This clears the is_current flag on all other entries for this coin.
    """
    validate_coin_exists(coin_id, coin_repo)

    existing = grading_repo.get_by_id(entry_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Grading history entry {entry_id} not found for coin {coin_id}")

    success = grading_repo.set_current(coin_id, entry_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set current grading")

    db.commit()

    # Refetch to get updated state
    updated = grading_repo.get_by_id(entry_id)
    return entry_to_response(updated)
