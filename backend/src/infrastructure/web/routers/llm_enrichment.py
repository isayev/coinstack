"""
LLM Enrichment API Router (Phase 4).

Manages centralized LLM enrichments with versioning, review workflow,
prompt templates, feedback, and usage analytics.
"""

import re
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.dependencies import get_db
from src.infrastructure.repositories.llm_enrichment_repository import (
    SqlAlchemyLLMEnrichmentRepository,
)
from src.infrastructure.repositories.prompt_template_repository import (
    SqlAlchemyPromptTemplateRepository,
)
from src.infrastructure.repositories.llm_feedback_repository import (
    SqlAlchemyLLMFeedbackRepository,
)
from src.infrastructure.repositories.llm_usage_repository import (
    SqlAlchemyLLMUsageRepository,
)
from src.domain.coin import (
    LLMEnrichment,
    PromptTemplate,
    LLMFeedback,
    LLMUsageDaily,
    LLMReviewStatus,
    LLMFeedbackType,
    LLMQualityFlags,
    CAPABILITY_CONFIDENCE_THRESHOLDS,
)
from src.infrastructure.persistence.orm import CoinModel

# Date format pattern for usage endpoints (YYYY-MM-DD)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def get_confidence_threshold(capability: str) -> float:
    """Get the confidence threshold for auto-provisional approval."""
    return CAPABILITY_CONFIDENCE_THRESHOLDS.get(
        capability, CAPABILITY_CONFIDENCE_THRESHOLDS["default"]
    )


def should_auto_provision(capability: str, confidence: float, quality_flags: str | None) -> bool:
    """Determine if an enrichment should be auto-provisioned based on confidence.

    Returns True if:
    - Confidence meets or exceeds capability threshold
    - No blocking quality flags present
    """
    threshold = get_confidence_threshold(capability)
    if confidence < threshold:
        return False

    # Check for blocking quality flags
    if quality_flags:
        blocking_flags = {
            LLMQualityFlags.HALLUCINATION_RISK,
            LLMQualityFlags.CONFLICTING_DATA,
            LLMQualityFlags.LOW_CONFIDENCE,
        }
        flag_list = [f.strip() for f in quality_flags.split(",")]
        if any(flag in blocking_flags for flag in flag_list):
            return False

    return True

router = APIRouter(prefix="/api/v2/llm-enrichments", tags=["llm-enrichments"])


# =============================================================================
# Dependencies
# =============================================================================


def get_enrichment_repo(db: Session = Depends(get_db)) -> SqlAlchemyLLMEnrichmentRepository:
    """Dependency for enrichment repository."""
    return SqlAlchemyLLMEnrichmentRepository(db)


def get_template_repo(db: Session = Depends(get_db)) -> SqlAlchemyPromptTemplateRepository:
    """Dependency for prompt template repository."""
    return SqlAlchemyPromptTemplateRepository(db)


def get_feedback_repo(db: Session = Depends(get_db)) -> SqlAlchemyLLMFeedbackRepository:
    """Dependency for feedback repository."""
    return SqlAlchemyLLMFeedbackRepository(db)


def get_usage_repo(db: Session = Depends(get_db)) -> SqlAlchemyLLMUsageRepository:
    """Dependency for usage repository."""
    return SqlAlchemyLLMUsageRepository(db)


# =============================================================================
# Request/Response Models
# =============================================================================


class EnrichmentResponse(BaseModel):
    """LLM enrichment response."""

    id: int
    coin_id: int
    capability: str
    capability_version: int
    model_id: str
    model_version: Optional[str] = None
    input_hash: str
    output_content: str
    confidence: float
    needs_review: bool = False
    quality_flags: Optional[str] = None
    cost_usd: float = 0.0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached: bool = False
    review_status: str = "pending"
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    superseded_by: Optional[int] = None

    class Config:
        from_attributes = True


class CreateEnrichmentRequest(BaseModel):
    """Request to create a new enrichment."""

    coin_id: int
    capability: str
    capability_version: int = 1
    model_id: str
    model_version: Optional[str] = None
    input_hash: str
    input_snapshot: Optional[str] = None
    output_content: str
    raw_response: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_review: bool = False
    quality_flags: Optional[str] = None
    cost_usd: float = 0.0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached: bool = False
    request_id: Optional[str] = None
    batch_job_id: Optional[str] = None


class UpdateReviewStatusRequest(BaseModel):
    """Request to update review status."""

    review_status: LLMReviewStatus
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None


class EnrichmentsListResponse(BaseModel):
    """Response with list of enrichments."""

    enrichments: List[EnrichmentResponse]
    total_count: int


# =============================================================================
# Prompt Template Models
# =============================================================================


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""

    id: int
    capability: str
    version: int
    system_prompt: str
    user_template: str
    parameters: Optional[str] = None
    requires_vision: bool = False
    output_schema: Optional[str] = None
    variant_name: str = "default"
    traffic_weight: float = 1.0
    is_active: bool = True
    created_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class CreatePromptTemplateRequest(BaseModel):
    """Request to create a new prompt template."""

    capability: str
    version: int
    system_prompt: str
    user_template: str
    parameters: Optional[str] = None
    requires_vision: bool = False
    output_schema: Optional[str] = None
    variant_name: str = "default"
    traffic_weight: float = Field(1.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class TemplatesListResponse(BaseModel):
    """Response with list of templates."""

    templates: List[PromptTemplateResponse]
    total_count: int


# =============================================================================
# Feedback Models
# =============================================================================


class FeedbackResponse(BaseModel):
    """LLM feedback response."""

    id: int
    enrichment_id: int
    feedback_type: str
    field_path: Optional[str] = None
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    user_id: Optional[str] = None
    feedback_notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CreateFeedbackRequest(BaseModel):
    """Request to create feedback."""

    enrichment_id: int
    feedback_type: LLMFeedbackType
    field_path: Optional[str] = None
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    user_id: Optional[str] = None
    feedback_notes: Optional[str] = None


class FeedbackListResponse(BaseModel):
    """Response with list of feedback."""

    feedback: List[FeedbackResponse]
    total_count: int


# =============================================================================
# Usage Models
# =============================================================================


class UsageDailyResponse(BaseModel):
    """Daily usage metrics response."""

    date: str
    capability: str
    model_id: str
    request_count: int = 0
    cache_hits: int = 0
    error_count: int = 0
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    avg_confidence: Optional[float] = None
    review_approved: int = 0
    review_rejected: int = 0
    avg_latency_ms: Optional[float] = None

    class Config:
        from_attributes = True


class UsageSummaryResponse(BaseModel):
    """Usage summary response by capability."""

    by_capability: dict
    total_cost_usd: float
    total_requests: int
    start_date: str
    end_date: str


# =============================================================================
# Enrichment Endpoints
# =============================================================================


@router.get("/coin/{coin_id}", response_model=EnrichmentsListResponse)
def get_coin_enrichments(
    coin_id: int,
    capability: Optional[str] = None,
    review_status: Optional[LLMReviewStatus] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Get all enrichments for a coin with optional filtering and pagination."""
    review_status_str = review_status.value if review_status else None
    enrichments = repo.get_by_coin_id(coin_id, capability, review_status_str)

    # Apply pagination
    total_count = len(enrichments)
    paginated = enrichments[skip : skip + limit]

    return EnrichmentsListResponse(
        enrichments=[_to_enrichment_response(e) for e in paginated],
        total_count=total_count,
    )


@router.get("/coin/{coin_id}/current/{capability}", response_model=Optional[EnrichmentResponse])
def get_current_enrichment(
    coin_id: int,
    capability: str,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Get the current active enrichment for a coin/capability."""
    enrichment = repo.get_current(coin_id, capability)

    if not enrichment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No enrichment found for coin {coin_id} and capability {capability}",
        )

    return _to_enrichment_response(enrichment)


@router.get("/cache", response_model=Optional[EnrichmentResponse])
def check_cache(
    capability: str,
    input_hash: str,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Check if an enrichment exists in cache by input hash."""
    enrichment = repo.get_by_input_hash(capability, input_hash)

    if not enrichment:
        return None

    return _to_enrichment_response(enrichment)


@router.get("/pending-review", response_model=EnrichmentsListResponse)
def get_pending_review(
    capability: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Get enrichments pending review."""
    enrichments = repo.list_pending_review(capability, limit)

    return EnrichmentsListResponse(
        enrichments=[_to_enrichment_response(e) for e in enrichments],
        total_count=len(enrichments),
    )


@router.post("/", response_model=EnrichmentResponse, status_code=status.HTTP_201_CREATED)
def create_enrichment(
    request: CreateEnrichmentRequest,
    db: Session = Depends(get_db),
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Create a new LLM enrichment."""
    # Validate coin exists (FK constraint)
    coin = db.query(CoinModel).filter(CoinModel.id == request.coin_id).first()
    if not coin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coin {request.coin_id} not found",
        )

    enrichment = repo.create(
        LLMEnrichment(
            coin_id=request.coin_id,
            capability=request.capability,
            capability_version=request.capability_version,
            model_id=request.model_id,
            model_version=request.model_version,
            input_hash=request.input_hash,
            input_snapshot=request.input_snapshot,
            output_content=request.output_content,
            raw_response=request.raw_response,
            confidence=request.confidence,
            needs_review=request.needs_review,
            quality_flags=request.quality_flags,
            cost_usd=request.cost_usd,
            input_tokens=request.input_tokens,
            output_tokens=request.output_tokens,
            cached=request.cached,
            request_id=request.request_id,
            batch_job_id=request.batch_job_id,
        )
    )

    return _to_enrichment_response(enrichment)


@router.post("/{enrichment_id}/auto-provision", response_model=EnrichmentResponse)
def auto_provision_enrichment(
    enrichment_id: int,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Auto-provision an enrichment based on confidence thresholds.

    Checks if the enrichment meets the confidence threshold for its capability
    and has no blocking quality flags. If so, updates status to PROVISIONAL.
    """
    enrichment = repo.get_by_id(enrichment_id)
    if not enrichment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {enrichment_id} not found",
        )

    # Only pending enrichments can be auto-provisioned
    if enrichment.review_status != LLMReviewStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Only pending enrichments can be auto-provisioned. Current status: {enrichment.review_status}",
        )

    if should_auto_provision(enrichment.capability, enrichment.confidence, enrichment.quality_flags):
        repo.update_review_status(
            enrichment_id,
            LLMReviewStatus.PROVISIONAL.value,
            "system:auto-provision",
            f"Auto-provisioned: confidence {enrichment.confidence:.2f} >= threshold {get_confidence_threshold(enrichment.capability):.2f}",
        )
        enrichment = repo.get_by_id(enrichment_id)
        return _to_enrichment_response(enrichment)
    else:
        threshold = get_confidence_threshold(enrichment.capability)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Enrichment does not meet auto-provision criteria. Confidence: {enrichment.confidence:.2f}, Threshold: {threshold:.2f}, Quality Flags: {enrichment.quality_flags or 'none'}",
        )


@router.get("/quality-flags/list")
def list_quality_flags():
    """List all standardized quality flags and their descriptions."""
    return {
        "flags": {
            LLMQualityFlags.UNCERTAIN: "Model expressed uncertainty in output",
            LLMQualityFlags.LOW_CONFIDENCE: "Confidence below capability threshold",
            LLMQualityFlags.HALLUCINATION_RISK: "Potential hallucination detected",
            LLMQualityFlags.NEEDS_CITATION: "Attribution requires source verification",
            LLMQualityFlags.AMBIGUOUS_INPUT: "Input data was ambiguous",
            LLMQualityFlags.PARTIAL_DATA: "Some expected fields missing",
            LLMQualityFlags.CONFLICTING_DATA: "Input contained contradictions",
            LLMQualityFlags.RARE_TYPE: "Unusual coin type, extra verification needed",
        },
        "blocking_flags": [
            LLMQualityFlags.HALLUCINATION_RISK,
            LLMQualityFlags.CONFLICTING_DATA,
            LLMQualityFlags.LOW_CONFIDENCE,
        ],
    }


@router.get("/confidence-thresholds/list")
def list_confidence_thresholds():
    """List confidence thresholds by capability for auto-provisional approval."""
    return {
        "thresholds": CAPABILITY_CONFIDENCE_THRESHOLDS,
        "description": "Confidence must meet or exceed threshold for auto-provisional approval",
    }


@router.get("/{enrichment_id}", response_model=EnrichmentResponse)
def get_enrichment(
    enrichment_id: int,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Get a specific enrichment by ID."""
    enrichment = repo.get_by_id(enrichment_id)

    if not enrichment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {enrichment_id} not found",
        )

    return _to_enrichment_response(enrichment)


@router.put("/{enrichment_id}/review", response_model=EnrichmentResponse)
def update_review_status(
    enrichment_id: int,
    request: UpdateReviewStatusRequest,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Update the review status of an enrichment."""
    if not repo.update_review_status(
        enrichment_id,
        request.review_status.value,
        request.reviewed_by,
        request.review_notes,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {enrichment_id} not found",
        )

    enrichment = repo.get_by_id(enrichment_id)
    return _to_enrichment_response(enrichment)


@router.post("/{old_id}/supersede/{new_id}", status_code=status.HTTP_200_OK)
def supersede_enrichment(
    old_id: int,
    new_id: int,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Mark an enrichment as superseded by a newer one."""

    # Validate both enrichments exist
    old_enrichment = repo.get_by_id(old_id)
    if not old_enrichment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {old_id} not found",
        )

    new_enrichment = repo.get_by_id(new_id)
    if not new_enrichment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"New enrichment {new_id} not found",
        )

    # Validate they are for the same coin and capability
    if old_enrichment.coin_id != new_enrichment.coin_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Enrichments must be for the same coin. Old: {old_enrichment.coin_id}, New: {new_enrichment.coin_id}",
        )

    if old_enrichment.capability != new_enrichment.capability:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Enrichments must be for the same capability. Old: {old_enrichment.capability}, New: {new_enrichment.capability}",
        )

    if not repo.supersede(old_id, new_id):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to supersede enrichment {old_id}",
        )

    return {"status": LLMReviewStatus.SUPERSEDED.value, "old_id": old_id, "new_id": new_id}


@router.delete("/{enrichment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_enrichment(
    enrichment_id: int,
    repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
):
    """Delete an enrichment."""
    if not repo.delete(enrichment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {enrichment_id} not found",
        )


# =============================================================================
# Prompt Template Endpoints
# =============================================================================


@router.get("/templates/{capability}", response_model=TemplatesListResponse)
def list_templates(
    capability: str,
    include_deprecated: bool = False,
    repo: SqlAlchemyPromptTemplateRepository = Depends(get_template_repo),
):
    """List all templates for a capability."""
    templates = repo.list_by_capability(capability, include_deprecated)

    return TemplatesListResponse(
        templates=[_to_template_response(t) for t in templates],
        total_count=len(templates),
    )


@router.get("/templates/{capability}/active", response_model=Optional[PromptTemplateResponse])
def get_active_template(
    capability: str,
    variant_name: str = "default",
    repo: SqlAlchemyPromptTemplateRepository = Depends(get_template_repo),
):
    """Get the active template for a capability."""
    template = repo.get_active(capability, variant_name)

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active template found for {capability}/{variant_name}",
        )

    return _to_template_response(template)


@router.post("/templates", response_model=PromptTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    request: CreatePromptTemplateRequest,
    repo: SqlAlchemyPromptTemplateRepository = Depends(get_template_repo),
):
    """Create a new prompt template."""
    template = repo.create(
        PromptTemplate(
            capability=request.capability,
            version=request.version,
            system_prompt=request.system_prompt,
            user_template=request.user_template,
            parameters=request.parameters,
            requires_vision=request.requires_vision,
            output_schema=request.output_schema,
            variant_name=request.variant_name,
            traffic_weight=request.traffic_weight,
            notes=request.notes,
        )
    )

    return _to_template_response(template)


@router.post("/templates/{template_id}/deprecate", status_code=status.HTTP_200_OK)
def deprecate_template(
    template_id: int,
    repo: SqlAlchemyPromptTemplateRepository = Depends(get_template_repo),
):
    """Mark a template as deprecated."""
    if not repo.deprecate(template_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )

    return {"status": "deprecated", "template_id": template_id}


# =============================================================================
# Feedback Endpoints
# =============================================================================


@router.get("/feedback/enrichment/{enrichment_id}", response_model=FeedbackListResponse)
def get_enrichment_feedback(
    enrichment_id: int,
    repo: SqlAlchemyLLMFeedbackRepository = Depends(get_feedback_repo),
):
    """Get all feedback for an enrichment."""
    feedback = repo.get_by_enrichment_id(enrichment_id)

    return FeedbackListResponse(
        feedback=[_to_feedback_response(f) for f in feedback],
        total_count=len(feedback),
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(
    request: CreateFeedbackRequest,
    enrichment_repo: SqlAlchemyLLMEnrichmentRepository = Depends(get_enrichment_repo),
    repo: SqlAlchemyLLMFeedbackRepository = Depends(get_feedback_repo),
):
    """Create feedback for an enrichment."""
    # Validate enrichment exists (FK constraint)
    if not enrichment_repo.get_by_id(request.enrichment_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment {request.enrichment_id} not found",
        )

    feedback = repo.create(
        LLMFeedback(
            enrichment_id=request.enrichment_id,
            feedback_type=request.feedback_type.value,
            field_path=request.field_path,
            original_value=request.original_value,
            corrected_value=request.corrected_value,
            user_id=request.user_id,
            feedback_notes=request.feedback_notes,
        )
    )

    return _to_feedback_response(feedback)


@router.get("/feedback/type/{feedback_type}", response_model=FeedbackListResponse)
def list_feedback_by_type(
    feedback_type: LLMFeedbackType = Path(..., description="Feedback type to filter by"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    repo: SqlAlchemyLLMFeedbackRepository = Depends(get_feedback_repo),
):
    """List feedback by type."""
    feedback = repo.list_by_type(feedback_type.value, skip, limit)

    return FeedbackListResponse(
        feedback=[_to_feedback_response(f) for f in feedback],
        total_count=len(feedback),
    )


# =============================================================================
# Usage Analytics Endpoints
# =============================================================================


def _validate_date_format(date_str: str, field_name: str) -> None:
    """Validate date string format (YYYY-MM-DD)."""
    if not DATE_PATTERN.match(date_str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid {field_name} format. Expected YYYY-MM-DD, got: {date_str}",
        )


@router.get("/usage/daily", response_model=List[UsageDailyResponse])
def get_daily_usage(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    capability: Optional[str] = None,
    model_id: Optional[str] = None,
    repo: SqlAlchemyLLMUsageRepository = Depends(get_usage_repo),
):
    """Get daily usage metrics for a date range."""
    _validate_date_format(start_date, "start_date")
    _validate_date_format(end_date, "end_date")

    usage = repo.list_by_date_range(start_date, end_date, capability, model_id)

    return [_to_usage_response(u) for u in usage]


@router.get("/usage/summary", response_model=UsageSummaryResponse)
def get_usage_summary(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    repo: SqlAlchemyLLMUsageRepository = Depends(get_usage_repo),
):
    """Get usage summary by capability for a date range."""
    _validate_date_format(start_date, "start_date")
    _validate_date_format(end_date, "end_date")

    summary = repo.get_capability_summary(start_date, end_date)
    total_cost = repo.get_total_cost(start_date, end_date)

    total_requests = sum(cap.get("total_requests", 0) for cap in summary.values())

    return UsageSummaryResponse(
        by_capability=summary,
        total_cost_usd=total_cost,
        total_requests=total_requests,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/usage/record", status_code=status.HTTP_200_OK)
def record_usage(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    capability: str = Query(..., description="Capability name"),
    model_id: str = Query(..., description="Model identifier"),
    request_count: int = Query(1, ge=0),
    cache_hits: int = Query(0, ge=0),
    error_count: int = Query(0, ge=0),
    cost_usd: float = Query(0.0, ge=0.0),
    input_tokens: int = Query(0, ge=0),
    output_tokens: int = Query(0, ge=0),
    repo: SqlAlchemyLLMUsageRepository = Depends(get_usage_repo),
):
    """Record LLM usage (increment counters)."""
    _validate_date_format(date, "date")

    usage = repo.increment(
        date=date,
        capability=capability,
        model_id=model_id,
        request_count=request_count,
        cache_hits=cache_hits,
        error_count=error_count,
        cost_usd=cost_usd,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

    return _to_usage_response(usage)


# =============================================================================
# Helper Functions
# =============================================================================


def _to_enrichment_response(enrichment: LLMEnrichment) -> EnrichmentResponse:
    """Convert domain entity to response model."""
    return EnrichmentResponse(
        id=enrichment.id or 0,
        coin_id=enrichment.coin_id,
        capability=enrichment.capability,
        capability_version=enrichment.capability_version,
        model_id=enrichment.model_id,
        model_version=enrichment.model_version,
        input_hash=enrichment.input_hash,
        output_content=enrichment.output_content,
        confidence=enrichment.confidence,
        needs_review=enrichment.needs_review,
        quality_flags=enrichment.quality_flags,
        cost_usd=enrichment.cost_usd,
        input_tokens=enrichment.input_tokens,
        output_tokens=enrichment.output_tokens,
        cached=enrichment.cached,
        review_status=enrichment.review_status,
        reviewed_by=enrichment.reviewed_by,
        reviewed_at=enrichment.reviewed_at,
        review_notes=enrichment.review_notes,
        created_at=enrichment.created_at,
        superseded_by=enrichment.superseded_by,
    )


def _to_template_response(template: PromptTemplate) -> PromptTemplateResponse:
    """Convert domain entity to response model."""
    return PromptTemplateResponse(
        id=template.id or 0,
        capability=template.capability,
        version=template.version,
        system_prompt=template.system_prompt,
        user_template=template.user_template,
        parameters=template.parameters,
        requires_vision=template.requires_vision,
        output_schema=template.output_schema,
        variant_name=template.variant_name,
        traffic_weight=template.traffic_weight,
        is_active=template.is_active,
        created_at=template.created_at,
        deprecated_at=template.deprecated_at,
        notes=template.notes,
    )


def _to_feedback_response(feedback: LLMFeedback) -> FeedbackResponse:
    """Convert domain entity to response model."""
    return FeedbackResponse(
        id=feedback.id or 0,
        enrichment_id=feedback.enrichment_id,
        feedback_type=feedback.feedback_type,
        field_path=feedback.field_path,
        original_value=feedback.original_value,
        corrected_value=feedback.corrected_value,
        user_id=feedback.user_id,
        feedback_notes=feedback.feedback_notes,
        created_at=feedback.created_at,
    )


def _to_usage_response(usage: LLMUsageDaily) -> UsageDailyResponse:
    """Convert domain entity to response model."""
    return UsageDailyResponse(
        date=usage.date,
        capability=usage.capability,
        model_id=usage.model_id,
        request_count=usage.request_count,
        cache_hits=usage.cache_hits,
        error_count=usage.error_count,
        total_cost_usd=usage.total_cost_usd,
        total_input_tokens=usage.total_input_tokens,
        total_output_tokens=usage.total_output_tokens,
        avg_confidence=usage.avg_confidence,
        review_approved=usage.review_approved,
        review_rejected=usage.review_rejected,
        avg_latency_ms=usage.avg_latency_ms,
    )
