"""
Census Snapshot Router for CoinStack API (Schema V3 Phase 2).

Provides REST endpoints for managing NGC/PCGS population census data.
Enables tracking population trends over time for specific coin types.

Endpoints:
- GET /api/v2/coins/{coin_id}/census - List all census snapshots
- GET /api/v2/coins/{coin_id}/census/latest - Get most recent snapshot
- POST /api/v2/coins/{coin_id}/census - Create snapshot
- GET /api/v2/coins/{coin_id}/census/{snapshot_id} - Get single snapshot
- PUT /api/v2/coins/{coin_id}/census/{snapshot_id} - Update snapshot
- DELETE /api/v2/coins/{coin_id}/census/{snapshot_id} - Delete snapshot
"""

from typing import Optional, List
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import CensusSnapshot
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.census_snapshot_repository import SqlAlchemyCensusSnapshotRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(
    prefix="/api/v2/coins/{coin_id}/census",
    tags=["Census Snapshots"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class CensusSnapshotCreateRequest(BaseModel):
    """Request to create a census snapshot."""
    service: str = Field(..., description="Grading service: ngc, pcgs")
    snapshot_date: date = Field(..., description="Date census was captured")
    total_graded: int = Field(..., ge=0, description="Total coins graded by service")
    grade_breakdown: Optional[str] = Field(None, description="JSON breakdown by grade, e.g., {\"VF\": 10, \"EF\": 5}")
    coins_at_grade: Optional[int] = Field(None, ge=0, description="Population at this coin's grade")
    coins_finer: Optional[int] = Field(None, ge=0, description="Population at finer grades")
    percentile: Optional[float] = Field(None, ge=0, le=100, description="Where this coin ranks (top X%)")
    catalog_reference: Optional[str] = Field(None, description="Catalog reference used for lookup (e.g., RIC III 42)")
    notes: Optional[str] = Field(None, description="Additional notes")


class CensusSnapshotUpdateRequest(BaseModel):
    """Request to update a census snapshot (all fields optional)."""
    service: Optional[str] = None
    snapshot_date: Optional[date] = None
    total_graded: Optional[int] = Field(None, ge=0)
    grade_breakdown: Optional[str] = None
    coins_at_grade: Optional[int] = Field(None, ge=0)
    coins_finer: Optional[int] = Field(None, ge=0)
    percentile: Optional[float] = Field(None, ge=0, le=100)
    catalog_reference: Optional[str] = None
    notes: Optional[str] = None


class CensusSnapshotResponse(BaseModel):
    """Response for a census snapshot."""
    id: int
    coin_id: int
    service: str
    snapshot_date: date
    total_graded: int
    grade_breakdown: Optional[str] = None
    coins_at_grade: Optional[int] = None
    coins_finer: Optional[int] = None
    percentile: Optional[float] = None
    catalog_reference: Optional[str] = None
    notes: Optional[str] = None


class CensusSnapshotListResponse(BaseModel):
    """Response for listing census snapshots."""
    coin_id: int
    snapshots: List[CensusSnapshotResponse]
    total: int
    has_ngc: bool = False
    has_pcgs: bool = False


# =============================================================================
# VALID VALUES
# =============================================================================

VALID_SERVICES = {"ngc", "pcgs"}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_census_repo(db: Session = Depends(get_db)) -> SqlAlchemyCensusSnapshotRepository:
    """Get census snapshot repository instance."""
    return SqlAlchemyCensusSnapshotRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def snapshot_to_response(snapshot: CensusSnapshot) -> CensusSnapshotResponse:
    """Convert domain CensusSnapshot to API response."""
    return CensusSnapshotResponse(
        id=snapshot.id,
        coin_id=snapshot.coin_id,
        service=snapshot.service,
        snapshot_date=snapshot.snapshot_date,
        total_graded=snapshot.total_graded,
        grade_breakdown=snapshot.grade_breakdown,
        coins_at_grade=snapshot.coins_at_grade,
        coins_finer=snapshot.coins_finer,
        percentile=float(snapshot.percentile) if snapshot.percentile else None,
        catalog_reference=snapshot.catalog_reference,
        notes=snapshot.notes,
    )


def validate_coin_exists(coin_id: int, coin_repo: SqlAlchemyCoinRepository) -> None:
    """Verify coin exists, raise 404 if not."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get(
    "",
    response_model=CensusSnapshotListResponse,
    summary="List census snapshots",
    description="Get all census snapshots for a coin, optionally filtered by service."
)
def list_census_snapshots(
    coin_id: int,
    service: Optional[str] = Query(None, description="Filter by service: ngc, pcgs"),
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """List all census snapshots for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    if service and service not in VALID_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{service}'. Must be one of: {', '.join(sorted(VALID_SERVICES))}"
        )

    snapshots = census_repo.get_by_coin_id(coin_id, service=service)
    response_snapshots = [snapshot_to_response(s) for s in snapshots]

    # Check which services have data
    services_present = {s.service for s in snapshots}

    return CensusSnapshotListResponse(
        coin_id=coin_id,
        snapshots=response_snapshots,
        total=len(response_snapshots),
        has_ngc="ngc" in services_present,
        has_pcgs="pcgs" in services_present,
    )


@router.get(
    "/latest",
    response_model=Optional[CensusSnapshotResponse],
    summary="Get latest census",
    description="Get the most recent census snapshot for a coin."
)
def get_latest_census(
    coin_id: int,
    service: Optional[str] = Query(None, description="Filter by service: ngc, pcgs"),
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get the most recent census snapshot for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    if service and service not in VALID_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{service}'. Must be one of: {', '.join(sorted(VALID_SERVICES))}"
        )

    latest = census_repo.get_latest(coin_id, service=service)
    if not latest:
        return None

    return snapshot_to_response(latest)


@router.post(
    "",
    response_model=CensusSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create census snapshot",
    description="Add a new census population snapshot for a coin."
)
def create_census_snapshot(
    coin_id: int,
    request: CensusSnapshotCreateRequest,
    db: Session = Depends(get_db),
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Create a census snapshot.

    Records NGC/PCGS population data at a specific point in time.
    """
    validate_coin_exists(coin_id, coin_repo)

    # Validate service
    if request.service not in VALID_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{request.service}'. Must be one of: {', '.join(sorted(VALID_SERVICES))}"
        )

    # Create domain entity
    snapshot = CensusSnapshot(
        service=request.service,
        snapshot_date=request.snapshot_date,
        total_graded=request.total_graded,
        grade_breakdown=request.grade_breakdown,
        coins_at_grade=request.coins_at_grade,
        coins_finer=request.coins_finer,
        percentile=Decimal(str(request.percentile)) if request.percentile else None,
        catalog_reference=request.catalog_reference,
        notes=request.notes,
    )

    created = census_repo.create(coin_id, snapshot)
    db.commit()

    return snapshot_to_response(created)


@router.get(
    "/{snapshot_id}",
    response_model=CensusSnapshotResponse,
    summary="Get census snapshot",
    description="Get a specific census snapshot."
)
def get_census_snapshot(
    coin_id: int,
    snapshot_id: int,
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get a specific census snapshot."""
    validate_coin_exists(coin_id, coin_repo)

    snapshot = census_repo.get_by_id(snapshot_id)
    if not snapshot or snapshot.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Census snapshot {snapshot_id} not found for coin {coin_id}")

    return snapshot_to_response(snapshot)


@router.put(
    "/{snapshot_id}",
    response_model=CensusSnapshotResponse,
    summary="Update census snapshot",
    description="Update an existing census snapshot."
)
def update_census_snapshot(
    coin_id: int,
    snapshot_id: int,
    request: CensusSnapshotUpdateRequest,
    db: Session = Depends(get_db),
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Update a census snapshot. Only provided fields will be updated."""
    validate_coin_exists(coin_id, coin_repo)

    existing = census_repo.get_by_id(snapshot_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Census snapshot {snapshot_id} not found for coin {coin_id}")

    # Validate service if provided
    if request.service and request.service not in VALID_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service '{request.service}'. Must be one of: {', '.join(sorted(VALID_SERVICES))}"
        )

    # Build updated snapshot (merge with existing)
    updated_snapshot = CensusSnapshot(
        id=existing.id,
        coin_id=existing.coin_id,
        service=request.service if request.service is not None else existing.service,
        snapshot_date=request.snapshot_date if request.snapshot_date is not None else existing.snapshot_date,
        total_graded=request.total_graded if request.total_graded is not None else existing.total_graded,
        grade_breakdown=request.grade_breakdown if request.grade_breakdown is not None else existing.grade_breakdown,
        coins_at_grade=request.coins_at_grade if request.coins_at_grade is not None else existing.coins_at_grade,
        coins_finer=request.coins_finer if request.coins_finer is not None else existing.coins_finer,
        percentile=Decimal(str(request.percentile)) if request.percentile is not None else existing.percentile,
        catalog_reference=request.catalog_reference if request.catalog_reference is not None else existing.catalog_reference,
        notes=request.notes if request.notes is not None else existing.notes,
    )

    updated = census_repo.update(snapshot_id, updated_snapshot)
    db.commit()

    return snapshot_to_response(updated)


@router.delete(
    "/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete census snapshot",
    description="Delete a census snapshot."
)
def delete_census_snapshot(
    coin_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    census_repo: SqlAlchemyCensusSnapshotRepository = Depends(get_census_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Delete a census snapshot."""
    validate_coin_exists(coin_id, coin_repo)

    existing = census_repo.get_by_id(snapshot_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Census snapshot {snapshot_id} not found for coin {coin_id}")

    census_repo.delete(snapshot_id)
    db.commit()

    return None
