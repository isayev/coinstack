"""
Rarity Assessment Router for CoinStack API (Schema V3 Phase 2).

Provides REST endpoints for managing multi-source rarity assessments.
Supports tracking rarity from catalogs, census data, and market analysis.

Endpoints:
- GET /api/v2/coins/{coin_id}/rarity-assessments - List all assessments
- POST /api/v2/coins/{coin_id}/rarity-assessments - Create assessment
- GET /api/v2/coins/{coin_id}/rarity-assessments/primary - Get primary assessment
- GET /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id} - Get single
- PUT /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id} - Update
- DELETE /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id} - Delete
- POST /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id}/set-primary - Mark as primary
"""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.domain.coin import RarityAssessment, RarityContext
from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.rarity_assessment_repository import SqlAlchemyRarityAssessmentRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

router = APIRouter(
    prefix="/api/v2/coins/{coin_id}/rarity-assessments",
    tags=["Rarity Assessments"]
)


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class RarityAssessmentCreateRequest(BaseModel):
    """Request to create a rarity assessment."""
    rarity_code: str = Field(..., description="Rarity code: C, S, R1-R5, RR, RRR, UNIQUE")
    rarity_system: str = Field("ric", description="Rating system: ric, catalog, census, market_frequency")
    source_type: str = Field("catalog", description="Source type: catalog, census_data, auction_analysis, expert_opinion")
    source_name: Optional[str] = Field(None, description="Source name (e.g., RIC II.1, NGC Census)")
    source_url: Optional[str] = Field(None, description="URL to source")
    source_date: Optional[date] = Field(None, description="When data was retrieved/published")
    grade_range_low: Optional[str] = Field(None, description="Applies to grades >= this")
    grade_range_high: Optional[str] = Field(None, description="Applies to grades <= this")
    grade_conditional_notes: Optional[str] = Field(None, description="Grade-conditional notes (e.g., R3 in XF+, R5 in MS)")
    census_total: Optional[int] = Field(None, ge=0, description="Total graded by service")
    census_this_grade: Optional[int] = Field(None, ge=0, description="Graded at this specific grade")
    census_finer: Optional[int] = Field(None, ge=0, description="Graded higher than this grade")
    census_date: Optional[date] = Field(None, description="When census was captured")
    confidence: str = Field("medium", description="Confidence level: high, medium, low")
    notes: Optional[str] = Field(None, description="Additional notes")
    is_primary: bool = Field(False, description="Is this the primary assessment?")
    # Phase 3: Variety Rarity Tracking
    variety_code: Optional[str] = Field(None, description="Die variety code (e.g., RIC 207 var. a)")
    die_id: Optional[int] = Field(None, description="FK to dies catalog")
    die_rarity_notes: Optional[str] = Field(None, description="Die-specific rarity observations")
    condition_rarity_threshold: Optional[str] = Field(None, description="Grade level where coin becomes rare (e.g., VF, EF)")
    rarity_context: Optional[str] = Field(None, description="Rarity context: base_type, variety_within_type, standalone")


class RarityAssessmentUpdateRequest(BaseModel):
    """Request to update a rarity assessment (all fields optional)."""
    rarity_code: Optional[str] = None
    rarity_system: Optional[str] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[date] = None
    grade_range_low: Optional[str] = None
    grade_range_high: Optional[str] = None
    grade_conditional_notes: Optional[str] = None
    census_total: Optional[int] = Field(None, ge=0)
    census_this_grade: Optional[int] = Field(None, ge=0)
    census_finer: Optional[int] = Field(None, ge=0)
    census_date: Optional[date] = None
    confidence: Optional[str] = None
    notes: Optional[str] = None
    is_primary: Optional[bool] = None
    # Phase 3: Variety Rarity Tracking
    variety_code: Optional[str] = None
    die_id: Optional[int] = None
    die_rarity_notes: Optional[str] = None
    condition_rarity_threshold: Optional[str] = None
    rarity_context: Optional[str] = None


class RarityAssessmentResponse(BaseModel):
    """Response for a rarity assessment."""
    id: int
    coin_id: int
    rarity_code: str
    rarity_system: str
    source_type: str
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    source_date: Optional[date] = None
    grade_range_low: Optional[str] = None
    grade_range_high: Optional[str] = None
    grade_conditional_notes: Optional[str] = None
    census_total: Optional[int] = None
    census_this_grade: Optional[int] = None
    census_finer: Optional[int] = None
    census_date: Optional[date] = None
    confidence: str = "medium"
    notes: Optional[str] = None
    is_primary: bool = False
    created_at: Optional[str] = None
    # Phase 3: Variety Rarity Tracking
    variety_code: Optional[str] = None
    die_id: Optional[int] = None
    die_rarity_notes: Optional[str] = None
    condition_rarity_threshold: Optional[str] = None
    rarity_context: Optional[str] = None


class RarityAssessmentListResponse(BaseModel):
    """Response for listing rarity assessments."""
    coin_id: int
    assessments: List[RarityAssessmentResponse]
    total: int
    has_primary: bool = False
    primary_assessment_id: Optional[int] = None


# =============================================================================
# VALID VALUES
# =============================================================================

VALID_RARITY_CODES = {
    "C", "S", "R", "R1", "R2", "R3", "R4", "R5", "RR", "RRR", "UNIQUE",
    # Also allow lowercase
    "c", "s", "r", "r1", "r2", "r3", "r4", "r5", "rr", "rrr", "unique"
}

VALID_RARITY_SYSTEMS = {"ric", "catalog", "census", "market_frequency"}
VALID_SOURCE_TYPES = {"catalog", "census_data", "auction_analysis", "expert_opinion"}
VALID_CONFIDENCE_LEVELS = {"high", "medium", "low"}


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_rarity_repo(db: Session = Depends(get_db)) -> SqlAlchemyRarityAssessmentRepository:
    """Get rarity assessment repository instance."""
    return SqlAlchemyRarityAssessmentRepository(db)


def get_coin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCoinRepository:
    """Get coin repository instance."""
    return SqlAlchemyCoinRepository(db)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def assessment_to_response(assessment: RarityAssessment) -> RarityAssessmentResponse:
    """Convert domain RarityAssessment to API response."""
    return RarityAssessmentResponse(
        id=assessment.id,
        coin_id=assessment.coin_id,
        rarity_code=assessment.rarity_code,
        rarity_system=assessment.rarity_system,
        source_type=assessment.source_type,
        source_name=assessment.source_name,
        source_url=assessment.source_url,
        source_date=assessment.source_date,
        grade_range_low=assessment.grade_range_low,
        grade_range_high=assessment.grade_range_high,
        grade_conditional_notes=assessment.grade_conditional_notes,
        census_total=assessment.census_total,
        census_this_grade=assessment.census_this_grade,
        census_finer=assessment.census_finer,
        census_date=assessment.census_date,
        confidence=assessment.confidence,
        notes=assessment.notes,
        is_primary=assessment.is_primary,
        created_at=assessment.created_at,
        # Phase 3: Variety Rarity Tracking
        variety_code=assessment.variety_code,
        die_id=assessment.die_id,
        die_rarity_notes=assessment.die_rarity_notes,
        condition_rarity_threshold=assessment.condition_rarity_threshold,
        rarity_context=assessment.rarity_context.value if assessment.rarity_context else None,
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
    response_model=RarityAssessmentListResponse,
    summary="List rarity assessments",
    description="Get all rarity assessments for a coin."
)
def list_rarity_assessments(
    coin_id: int,
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """List all rarity assessments for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    assessments = rarity_repo.get_by_coin_id(coin_id)
    response_assessments = [assessment_to_response(a) for a in assessments]

    # Find primary assessment
    primary_id = None
    for assessment in assessments:
        if assessment.is_primary:
            primary_id = assessment.id
            break

    return RarityAssessmentListResponse(
        coin_id=coin_id,
        assessments=response_assessments,
        total=len(response_assessments),
        has_primary=primary_id is not None,
        primary_assessment_id=primary_id,
    )


@router.post(
    "",
    response_model=RarityAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create rarity assessment",
    description="Add a new rarity assessment to a coin."
)
def create_rarity_assessment(
    coin_id: int,
    request: RarityAssessmentCreateRequest,
    db: Session = Depends(get_db),
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Create a rarity assessment.

    Rarity systems:
    - ric: RIC-style codes (C, S, R1-R5, RR, RRR, UNIQUE)
    - catalog: Generic catalog rating
    - census: TPG population-based
    - market_frequency: Auction appearance analysis

    Source types:
    - catalog: Published catalog (RIC, Sear, etc.)
    - census_data: NGC/PCGS population data
    - auction_analysis: Market appearance tracking
    - expert_opinion: Dealer/expert assessment
    """
    validate_coin_exists(coin_id, coin_repo)

    # Validate rarity system
    if request.rarity_system not in VALID_RARITY_SYSTEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rarity_system '{request.rarity_system}'. Must be one of: {', '.join(sorted(VALID_RARITY_SYSTEMS))}"
        )

    # Validate source type
    if request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{request.source_type}'. Must be one of: {', '.join(sorted(VALID_SOURCE_TYPES))}"
        )

    # Validate confidence
    if request.confidence not in VALID_CONFIDENCE_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence '{request.confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE_LEVELS))}"
        )

    # Normalize rarity code to uppercase and validate
    rarity_code = request.rarity_code.upper()
    if rarity_code not in VALID_RARITY_CODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rarity_code '{request.rarity_code}'. Must be one of: C, S, R, R1-R5, RR, RRR, UNIQUE"
        )

    # Validate rarity_context if provided (Phase 3)
    rarity_context = None
    if request.rarity_context:
        try:
            rarity_context = RarityContext(request.rarity_context)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rarity_context '{request.rarity_context}'. Must be one of: base_type, variety_within_type, standalone"
            )

    # Create domain assessment
    assessment = RarityAssessment(
        rarity_code=rarity_code,
        rarity_system=request.rarity_system,
        source_type=request.source_type,
        source_name=request.source_name,
        source_url=request.source_url,
        source_date=request.source_date,
        grade_range_low=request.grade_range_low,
        grade_range_high=request.grade_range_high,
        grade_conditional_notes=request.grade_conditional_notes,
        census_total=request.census_total,
        census_this_grade=request.census_this_grade,
        census_finer=request.census_finer,
        census_date=request.census_date,
        confidence=request.confidence,
        notes=request.notes,
        is_primary=request.is_primary,
        # Phase 3: Variety Rarity Tracking
        variety_code=request.variety_code,
        die_id=request.die_id,
        die_rarity_notes=request.die_rarity_notes,
        condition_rarity_threshold=request.condition_rarity_threshold,
        rarity_context=rarity_context,
    )

    # If marking as primary, clear existing primary
    if request.is_primary:
        rarity_repo.clear_all_primary(coin_id)

    created = rarity_repo.create(coin_id, assessment)

    # If marking as primary, set it properly after creation
    if request.is_primary:
        rarity_repo.set_primary(coin_id, created.id)
        created = rarity_repo.get_by_id(created.id)

    db.commit()

    return assessment_to_response(created)


# =============================================================================
# STATIC ROUTES (must come before parameterized routes)
# =============================================================================

@router.get(
    "/primary",
    response_model=Optional[RarityAssessmentResponse],
    summary="Get primary assessment",
    description="Get the primary rarity assessment for a coin."
)
def get_primary_assessment(
    coin_id: int,
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get the primary rarity assessment for a coin."""
    validate_coin_exists(coin_id, coin_repo)

    primary = rarity_repo.get_primary(coin_id)
    if not primary:
        return None

    return assessment_to_response(primary)


# =============================================================================
# PARAMETERIZED ROUTES (after static routes)
# =============================================================================

@router.get(
    "/{assessment_id}",
    response_model=RarityAssessmentResponse,
    summary="Get rarity assessment",
    description="Get a specific rarity assessment."
)
def get_rarity_assessment(
    coin_id: int,
    assessment_id: int,
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Get a specific rarity assessment."""
    validate_coin_exists(coin_id, coin_repo)

    assessment = rarity_repo.get_by_id(assessment_id)
    if not assessment or assessment.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Rarity assessment {assessment_id} not found for coin {coin_id}")

    return assessment_to_response(assessment)


@router.put(
    "/{assessment_id}",
    response_model=RarityAssessmentResponse,
    summary="Update rarity assessment",
    description="Update an existing rarity assessment."
)
def update_rarity_assessment(
    coin_id: int,
    assessment_id: int,
    request: RarityAssessmentUpdateRequest,
    db: Session = Depends(get_db),
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Update a rarity assessment. Only provided fields will be updated."""
    validate_coin_exists(coin_id, coin_repo)

    existing = rarity_repo.get_by_id(assessment_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Rarity assessment {assessment_id} not found for coin {coin_id}")

    # Validate updates if provided
    if request.rarity_system and request.rarity_system not in VALID_RARITY_SYSTEMS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rarity_system '{request.rarity_system}'. Must be one of: {', '.join(sorted(VALID_RARITY_SYSTEMS))}"
        )

    if request.source_type and request.source_type not in VALID_SOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid source_type '{request.source_type}'. Must be one of: {', '.join(sorted(VALID_SOURCE_TYPES))}"
        )

    if request.confidence and request.confidence not in VALID_CONFIDENCE_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid confidence '{request.confidence}'. Must be one of: {', '.join(sorted(VALID_CONFIDENCE_LEVELS))}"
        )

    # Normalize rarity code if provided and validate
    if request.rarity_code:
        rarity_code = request.rarity_code.upper()
        if rarity_code not in VALID_RARITY_CODES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rarity_code '{request.rarity_code}'. Must be one of: C, S, R, R1-R5, RR, RRR, UNIQUE"
            )
    else:
        rarity_code = existing.rarity_code

    # Validate rarity_context if provided (Phase 3)
    rarity_context = existing.rarity_context
    if request.rarity_context is not None:
        try:
            rarity_context = RarityContext(request.rarity_context)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid rarity_context '{request.rarity_context}'. Must be one of: base_type, variety_within_type, standalone"
            )

    # Build updated assessment (merge with existing)
    updated_assessment = RarityAssessment(
        id=existing.id,
        coin_id=existing.coin_id,
        rarity_code=rarity_code,
        rarity_system=request.rarity_system if request.rarity_system is not None else existing.rarity_system,
        source_type=request.source_type if request.source_type is not None else existing.source_type,
        source_name=request.source_name if request.source_name is not None else existing.source_name,
        source_url=request.source_url if request.source_url is not None else existing.source_url,
        source_date=request.source_date if request.source_date is not None else existing.source_date,
        grade_range_low=request.grade_range_low if request.grade_range_low is not None else existing.grade_range_low,
        grade_range_high=request.grade_range_high if request.grade_range_high is not None else existing.grade_range_high,
        grade_conditional_notes=request.grade_conditional_notes if request.grade_conditional_notes is not None else existing.grade_conditional_notes,
        census_total=request.census_total if request.census_total is not None else existing.census_total,
        census_this_grade=request.census_this_grade if request.census_this_grade is not None else existing.census_this_grade,
        census_finer=request.census_finer if request.census_finer is not None else existing.census_finer,
        census_date=request.census_date if request.census_date is not None else existing.census_date,
        confidence=request.confidence if request.confidence is not None else existing.confidence,
        notes=request.notes if request.notes is not None else existing.notes,
        is_primary=request.is_primary if request.is_primary is not None else existing.is_primary,
        created_at=existing.created_at,
        # Phase 3: Variety Rarity Tracking
        variety_code=request.variety_code if request.variety_code is not None else existing.variety_code,
        die_id=request.die_id if request.die_id is not None else existing.die_id,
        die_rarity_notes=request.die_rarity_notes if request.die_rarity_notes is not None else existing.die_rarity_notes,
        condition_rarity_threshold=request.condition_rarity_threshold if request.condition_rarity_threshold is not None else existing.condition_rarity_threshold,
        rarity_context=rarity_context,
    )

    updated = rarity_repo.update(assessment_id, updated_assessment)
    db.commit()

    return assessment_to_response(updated)


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete rarity assessment",
    description="Delete a rarity assessment."
)
def delete_rarity_assessment(
    coin_id: int,
    assessment_id: int,
    db: Session = Depends(get_db),
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """Delete a rarity assessment."""
    validate_coin_exists(coin_id, coin_repo)

    existing = rarity_repo.get_by_id(assessment_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Rarity assessment {assessment_id} not found for coin {coin_id}")

    rarity_repo.delete(assessment_id)
    db.commit()

    return None


@router.post(
    "/{assessment_id}/set-primary",
    response_model=RarityAssessmentResponse,
    summary="Set as primary assessment",
    description="Mark a rarity assessment as the primary assessment for this coin."
)
def set_primary_assessment(
    coin_id: int,
    assessment_id: int,
    db: Session = Depends(get_db),
    rarity_repo: SqlAlchemyRarityAssessmentRepository = Depends(get_rarity_repo),
    coin_repo: SqlAlchemyCoinRepository = Depends(get_coin_repo),
):
    """
    Mark a rarity assessment as the primary assessment.

    This clears the is_primary flag on all other assessments for this coin.
    """
    validate_coin_exists(coin_id, coin_repo)

    existing = rarity_repo.get_by_id(assessment_id)
    if not existing or existing.coin_id != coin_id:
        raise HTTPException(status_code=404, detail=f"Rarity assessment {assessment_id} not found for coin {coin_id}")

    success = rarity_repo.set_primary(coin_id, assessment_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to set primary assessment")

    db.commit()

    # Refetch to get updated state
    updated = rarity_repo.get_by_id(assessment_id)
    return assessment_to_response(updated)
