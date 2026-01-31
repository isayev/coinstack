"""
LLM Router for CoinStack API.

Provides REST endpoints for LLM-powered numismatic operations.

P0 Endpoints (MVP):
- POST /api/v2/llm/vocab/normalize - Normalize vocabulary term
- POST /api/v2/llm/legend/expand - Expand Latin legend
- POST /api/v2/llm/auction/parse - Parse auction description
- POST /api/v2/llm/provenance/parse - Extract provenance chain

P1 Endpoints (Core):
- POST /api/v2/llm/identify - Identify coin from image
- POST /api/v2/llm/reference/validate - Validate catalog reference

P2 Endpoints (Advanced):
- POST /api/v2/llm/attribution/assist - Suggest attribution
- POST /api/v2/llm/legend/transcribe - OCR legends from image
- POST /api/v2/llm/catalog/parse - Parse reference string
- POST /api/v2/llm/condition/observe - Describe condition (NOT grades)

Admin Endpoints:
- GET /api/v2/llm/status - Service status
- GET /api/v2/llm/cost-report - Usage and cost breakdown
- GET /api/v2/llm/metrics - Observability metrics
- POST /api/v2/llm/feedback - Submit accuracy feedback
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.infrastructure.web.rarity import normalize_rarity_for_api
from src.domain.llm import (
    LLMCapability,
    LLMError,
    LLMParseError,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
)
from src.domain.coin import LLMEnrichment
from src.infrastructure.repositories.llm_enrichment_repository import SqlAlchemyLLMEnrichmentRepository
from src.infrastructure.web.dependencies import get_db, get_save_llm_enrichment_use_case
from src.application.commands.save_llm_enrichment import SaveLLMEnrichmentUseCase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/llm", tags=["LLM"])


# =============================================================================
# REQUEST/RESPONSE SCHEMAS
# =============================================================================

class VocabNormalizeRequest(BaseModel):
    """Request for vocabulary normalization."""
    raw_text: str = Field(..., description="Raw text to normalize")
    vocab_type: str = Field(..., description="Type: 'issuer', 'mint', or 'denomination'")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context")


class VocabNormalizeResponse(BaseModel):
    """Response from vocabulary normalization."""
    canonical_name: str
    confidence: float
    cost_usd: float
    model_used: str
    cached: bool
    reasoning: List[str]


class LegendExpandRequest(BaseModel):
    """Request for legend expansion."""
    abbreviation: str = Field(..., description="Abbreviated Latin legend")


class LegendExpandResponse(BaseModel):
    """Response from legend expansion."""
    expanded: str
    confidence: float
    cost_usd: float
    model_used: str
    cached: bool


class AuctionParseRequest(BaseModel):
    """Request for auction lot parsing."""
    description: str = Field(..., description="Auction lot description text")
    hints: Optional[Dict[str, Any]] = Field(None, description="Optional hints")


class AuctionParseResponse(BaseModel):
    """Response from auction parsing."""
    issuer: Optional[str]
    denomination: Optional[str]
    metal: Optional[str]
    mint: Optional[str]
    year_start: Optional[int]
    year_end: Optional[int]
    weight_g: Optional[float]
    diameter_mm: Optional[float]
    obverse_legend: Optional[str]
    obverse_description: Optional[str]
    reverse_legend: Optional[str]
    reverse_description: Optional[str]
    references: List[str]
    grade: Optional[str]
    confidence: float
    cost_usd: float


class ProvenanceParseRequest(BaseModel):
    """Request for provenance parsing."""
    description: str = Field(..., description="Text containing provenance")


class ProvenanceEntryResponse(BaseModel):
    """Single provenance entry."""
    source: str
    source_type: str
    year: Optional[int]
    sale: Optional[str]
    lot: Optional[str]


class ProvenanceParseResponse(BaseModel):
    """Response from provenance parsing."""
    provenance_chain: List[ProvenanceEntryResponse]
    earliest_known: Optional[int]
    confidence: float
    cost_usd: float


class CoinIdentifyRequest(BaseModel):
    """Request for coin identification."""
    image_b64: str = Field(..., description="Base64-encoded image")
    hints: Optional[Dict[str, Any]] = Field(None, description="Optional hints")


class CoinIdentifyResponse(BaseModel):
    """Response from coin identification."""
    ruler: Optional[str]
    denomination: Optional[str]
    mint: Optional[str]
    date_range: Optional[str]
    obverse_description: Optional[str]
    reverse_description: Optional[str]
    suggested_references: List[str]
    confidence: float
    cost_usd: float


class ReferenceValidateRequest(BaseModel):
    """Request for reference validation."""
    reference: str = Field(..., description="Catalog reference to validate")
    coin_context: Optional[Dict[str, Any]] = Field(None, description="Optional coin context")


class ReferenceValidateResponse(BaseModel):
    """Response from reference validation."""
    is_valid: bool
    normalized: str
    alternatives: List[str]
    notes: str
    confidence: float
    cost_usd: float


class ContextGenerateRequest(BaseModel):
    """Request for historical context generation."""
    coin_id: int = Field(..., description="Coin ID - will fetch full data from DB")


class ContextSectionResponse(BaseModel):
    """Individual analysis section."""
    key: str
    title: str
    content: str


class SuggestedReferenceResponse(BaseModel):
    """A catalog reference suggested by LLM but not in database."""
    reference: str
    confidence: float = 0.8  # Default confidence for LLM-extracted refs


class RarityInfoResponse(BaseModel):
    """Rarity information extracted from structured LLM response."""
    rarity_code: Optional[str] = None           # Normalized code (C, S, R1-R5, RR, RRR, UNIQUE)
    rarity_description: Optional[str] = None    # Human-readable (Common, Scarce, Rare, etc.)
    specimens_known: Optional[int] = None       # Estimated count if mentioned
    source: Optional[str] = None                # Catalog source (e.g., "RIC IV.1 rates as C")


class ContextGenerateResponse(BaseModel):
    """Response from comprehensive context generation."""
    sections: List[ContextSectionResponse]
    raw_content: str
    confidence: float
    cost_usd: float
    model_used: str
    # Citation tracking
    existing_references: List[str] = []          # References already in DB (passed to LLM)
    all_llm_citations: List[str] = []            # All references LLM cited in response
    suggested_references: List[str] = []         # New refs found by LLM, not in DB (for audit)
    matched_references: List[str] = []           # LLM refs that matched DB refs
    # Rarity tracking
    rarity_info: Optional[RarityInfoResponse] = None  # Extracted rarity data for audit


# Human-readable section titles (module constant)
SECTION_TITLES: Dict[str, str] = {
    "EPIGRAPHY_AND_TITLES": "Epigraphy & Titles",
    "ICONOGRAPHY_AND_SYMBOLISM": "Iconography & Symbolism",
    "ARTISTIC_STYLE": "Artistic Style & Portraiture",
    "PROPAGANDA_AND_MESSAGING": "Propaganda & Political Messaging",
    "ECONOMIC_CONTEXT": "Economic & Monetary Context",
    "DIE_STUDIES_AND_VARIETIES": "Die Studies & Varieties",
    "ARCHAEOLOGICAL_CONTEXT": "Archaeological & Provenance Context",
    "TYPOLOGICAL_RELATIONSHIPS": "Typological Relationships",
    "MILITARY_HISTORY": "Military History",
    "HISTORICAL_CONTEXT": "Historical Context",
    "NUMISMATIC_SIGNIFICANCE": "Numismatic Significance",
}


# =============================================================================
# P2 REQUEST/RESPONSE SCHEMAS
# =============================================================================

class AttributionAssistRequest(BaseModel):
    """Request for attribution assistance."""
    known_info: Dict[str, Any] = Field(..., description="Partial coin information")


class AttributionSuggestionResponse(BaseModel):
    """Single attribution suggestion."""
    attribution: str
    reference: str
    confidence: float
    reasoning: List[str]


class AttributionAssistResponse(BaseModel):
    """Response from attribution assistance."""
    suggestions: List[AttributionSuggestionResponse]
    questions_to_resolve: List[str]
    confidence: float
    cost_usd: float


class LegendTranscribeRequest(BaseModel):
    """Request for legend transcription."""
    image_b64: str = Field(..., description="Base64-encoded coin image")
    hints: Optional[Dict[str, Any]] = Field(None, description="Optional hints")


class LegendTranscribeResponse(BaseModel):
    """Response from legend transcription."""
    obverse_legend: Optional[str]
    obverse_legend_expanded: Optional[str]
    reverse_legend: Optional[str]
    reverse_legend_expanded: Optional[str]
    exergue: Optional[str]
    uncertain_portions: List[str]
    confidence: float
    cost_usd: float


class CatalogParseRequest(BaseModel):
    """Request for catalog reference parsing."""
    reference: str = Field(..., description="Catalog reference string (e.g., 'RIC II 207')")


class CatalogParseResponse(BaseModel):
    """Response from catalog parsing."""
    raw_reference: str
    catalog_system: str
    volume: Optional[str]
    number: str
    issuer: Optional[str]
    mint: Optional[str]
    alternatives: List[str]
    confidence: float
    cost_usd: float


class ConditionObserveRequest(BaseModel):
    """Request for condition observations."""
    image_b64: str = Field(..., description="Base64-encoded coin image")
    hints: Optional[Dict[str, Any]] = Field(None, description="Optional hints")


class ConditionObserveResponse(BaseModel):
    """Response from condition observations (NOT grades)."""
    wear_observations: str
    surface_notes: str
    strike_quality: str
    notable_features: List[str]
    concerns: List[str]
    recommendation: str
    confidence: float
    cost_usd: float


class FeedbackRequest(BaseModel):
    """Request for submitting accuracy feedback."""
    coin_id: int = Field(..., description="Coin ID")
    capability: str = Field(..., description="Capability name")
    field: str = Field(..., description="Field name")
    suggested_value: Any = Field(..., description="The LLM's suggestion")
    action: str = Field(..., description="'accepted', 'rejected', or 'modified'")
    user_value: Optional[Any] = Field(None, description="User's value if modified/rejected")
    reason: Optional[str] = Field(None, description="Optional rejection reason")
    confidence: float = Field(0.0, description="Original confidence")
    model_used: str = Field("", description="Model that made suggestion")


class ProviderKeysStatus(BaseModel):
    """Which provider API keys are set (presence only; values never exposed)."""
    anthropic: bool = False
    openrouter: bool = False
    google: bool = False


class StatusResponse(BaseModel):
    """LLM service status."""
    status: str
    profile: str
    monthly_cost_usd: float
    monthly_budget_usd: float
    budget_remaining_usd: float
    capabilities_available: List[str]
    ollama_available: bool
    provider_keys: Optional[ProviderKeysStatus] = None


class CostReportResponse(BaseModel):
    """Cost and usage report."""
    period_days: int
    total_cost_usd: float
    by_capability: Dict[str, float]
    by_model: Dict[str, float]


class MetricsSummaryResponse(BaseModel):
    """Metrics summary."""
    period_hours: int
    total_calls: int
    successful_calls: int
    failed_calls: int
    cached_calls: int
    total_cost_usd: float
    avg_latency_ms: float
    cache_hit_rate: float
    success_rate: float
    calls_by_capability: Dict[str, int]
    errors_by_type: Dict[str, int]


# =============================================================================
# DEPENDENCIES
# =============================================================================

def get_llm_service():
    """Get LLM service instance."""
    from src.infrastructure.services.llm_service import LLMService
    return LLMService()


def get_event_store():
    """Get event store instance."""
    from src.infrastructure.persistence.event_store import SqliteEventStore
    return SqliteEventStore()


def get_metrics_service():
    """Get metrics service instance."""
    from src.infrastructure.services.llm_metrics import LLMMetrics
    return LLMMetrics()


def _coin_images_dir() -> Path:
    """Backend data/coin_images directory (same as main.py static mount)."""
    backend_root = Path(__file__).resolve().parent.parent.parent.parent
    return backend_root / "data" / "coin_images"


async def _resolve_coin_primary_image_b64(session: Session, coin_id: int) -> Optional[str]:
    """
    Load coin by id, get primary image URL, return its content as base64.
    Supports http(s) URLs (fetched) and /images/... paths (read from data/coin_images).
    """
    from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

    repo = SqlAlchemyCoinRepository(session)
    coin = repo.get_by_id(coin_id)
    if not coin or not coin.images:
        return None
    primary = coin.primary_image or coin.images[0]
    url = primary.url
    if not url or not url.strip():
        return None
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        try:
            import base64
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(url)
                r.raise_for_status()
                return base64.b64encode(r.content).decode("utf-8")
        except Exception as e:
            logger.warning("Failed to fetch coin image URL %s: %s", url[:80], e)
            return None
    # Local path: /images/... or relative
    images_dir = _coin_images_dir()
    if "/images/" in url:
        name = url.split("/images/")[-1].lstrip("/")
        path = images_dir / name
    elif Path(url).is_absolute():
        path = Path(url)
    else:
        path = images_dir / Path(url).name
    if not path.exists():
        logger.warning("Coin image path not found: %s", path)
        return None
    try:
        import base64
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    except Exception as e:
        logger.warning("Failed to read coin image %s: %s", path, e)
        return None


def _parse_date_range(s: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parse date_range string like '268–270' or 'ca. 260-268' -> (year_start, year_end)."""
    if not s or not str(s).strip():
        return (None, None)
    text = str(s).strip()
    numbers = [int(m) for m in re.findall(r"-?\d+", text)]
    if not numbers:
        return (None, None)
    return (numbers[0], numbers[-1] if len(numbers) > 1 else numbers[0])


# =============================================================================
# P0 ENDPOINTS
# =============================================================================

@router.post(
    "/vocab/normalize",
    response_model=VocabNormalizeResponse,
    summary="Normalize vocabulary term",
    description="Normalize raw numismatic text to canonical vocabulary term.",
)
async def normalize_vocab(
    request: VocabNormalizeRequest,
    x_request_id: str = Header(default_factory=lambda: str(uuid4())),
    llm_service = Depends(get_llm_service),
):
    """
    Normalize vocabulary term to canonical form.
    
    Uses LLM to identify the canonical form of issuer, mint, or denomination names.
    Falls back to fuzzy matching if LLM unavailable.
    """
    try:
        result = await llm_service.normalize_vocab(
            raw_text=request.raw_text,
            vocab_type=request.vocab_type,
            context=request.context,
        )
        
        return VocabNormalizeResponse(
            canonical_name=result.canonical_name,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
            reasoning=list(result.reasoning),
        )
    except LLMRateLimitExceeded as e:
        raise HTTPException(
            status_code=429,
            detail=str(e),
            headers={"Retry-After": str(e.retry_after_seconds)},
        )
    except LLMBudgetExceeded as e:
        raise HTTPException(status_code=402, detail=str(e))
    except LLMCapabilityNotAvailable as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMError as e:
        logger.error(f"LLM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/legend/expand",
    response_model=LegendExpandResponse,
    summary="Expand Latin legend",
    description="Expand abbreviated Latin coin legend to full form.",
)
async def expand_legend(
    request: LegendExpandRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Expand abbreviated Latin legend.
    
    Converts abbreviations like IMP CAES AVG to Imperator Caesar Augustus.
    """
    try:
        result = await llm_service.expand_legend(request.abbreviation)
        
        return LegendExpandResponse(
            expanded=result.expanded,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            cached=result.cached,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/auction/parse",
    response_model=AuctionParseResponse,
    summary="Parse auction description",
    description="Extract structured coin data from auction lot description.",
)
async def parse_auction(
    request: AuctionParseRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Parse auction lot description into structured data.
    
    Extracts issuer, denomination, metal, dates, dimensions, legends, and references.
    """
    try:
        result = await llm_service.parse_auction(
            description=request.description,
            hints=request.hints,
        )
        
        return AuctionParseResponse(
            issuer=result.issuer,
            denomination=result.denomination,
            metal=result.metal,
            mint=result.mint,
            year_start=result.year_start,
            year_end=result.year_end,
            weight_g=result.weight_g,
            diameter_mm=result.diameter_mm,
            obverse_legend=result.obverse_legend,
            obverse_description=result.obverse_description,
            reverse_legend=result.reverse_legend,
            reverse_description=result.reverse_description,
            references=list(result.references),
            grade=result.grade,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMParseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/provenance/parse",
    response_model=ProvenanceParseResponse,
    summary="Parse provenance",
    description="Extract provenance chain from auction/catalog text.",
)
async def parse_provenance(
    request: ProvenanceParseRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Extract provenance chain from description text.
    
    Identifies auction sales, collections, and dealers in ownership history.
    """
    try:
        result = await llm_service.parse_provenance(request.description)
        
        chain = [
            ProvenanceEntryResponse(
                source=entry.source,
                source_type=entry.source_type,
                year=entry.year,
                sale=entry.sale,
                lot=entry.lot,
            )
            for entry in result.provenance_chain
        ]
        
        return ProvenanceParseResponse(
            provenance_chain=chain,
            earliest_known=result.earliest_known,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# P1 ENDPOINTS
# =============================================================================

@router.post(
    "/identify",
    response_model=CoinIdentifyResponse,
    summary="Identify coin from image",
    description="Use vision AI to identify a coin from photos.",
)
async def identify_coin(
    request: CoinIdentifyRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Identify coin from image.
    
    Analyzes coin images to determine ruler, denomination, mint, and other details.
    Uses vision models (Gemini) for image analysis.
    """
    try:
        result = await llm_service.identify_coin(
            image_b64=request.image_b64,
            hints=request.hints,
        )
        
        return CoinIdentifyResponse(
            ruler=result.ruler,
            denomination=result.denomination,
            mint=result.mint,
            date_range=result.date_range,
            obverse_description=result.obverse_description,
            reverse_description=result.reverse_description,
            suggested_references=list(result.suggested_references),
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/identify/coin/{coin_id}",
    response_model=CoinIdentifyResponse,
    summary="Identify coin from its primary image",
    description="Run identify on the coin's primary image and save attribution + descriptions + refs as suggestions.",
)
async def identify_coin_for_coin(
    coin_id: int,
    llm_service=Depends(get_llm_service),
    db: Session = Depends(get_db),
    enrichment_use_case: SaveLLMEnrichmentUseCase = Depends(get_save_llm_enrichment_use_case),
):
    """
    Identify coin from its primary image and store in llm_suggested_attribution,
    llm_suggested_design (obverse/reverse descriptions), and llm_suggested_references.
    Sets llm_enriched_at. Merges design delta into existing llm_suggested_design.

    Also writes to llm_enrichments table for audit/history (dual-write).
    """
    from datetime import datetime, timezone
    from src.infrastructure.persistence.orm import CoinModel

    orm_coin = db.query(CoinModel).filter(CoinModel.id == coin_id).first()
    if not orm_coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    image_b64 = await _resolve_coin_primary_image_b64(db, coin_id)
    if not image_b64:
        raise HTTPException(
            status_code=400,
            detail="Coin has no primary image or image could not be loaded",
        )
    result = await llm_service.identify_coin(image_b64=image_b64, hints=None)
    year_start, year_end = _parse_date_range(result.date_range)
    attribution = {
        "issuer": result.ruler,
        "mint": result.mint,
        "denomination": result.denomination,
        "year_start": year_start,
        "year_end": year_end,
    }
    attribution = {k: v for k, v in attribution.items() if v is not None}
    design_delta = {}
    if result.obverse_description is not None:
        design_delta["obverse_description"] = result.obverse_description
    if result.reverse_description is not None:
        design_delta["reverse_description"] = result.reverse_description
    try:
        orm_coin.llm_suggested_attribution = json.dumps(attribution) if attribution else orm_coin.llm_suggested_attribution
        if design_delta:
            existing = {}
            if orm_coin.llm_suggested_design:
                try:
                    existing = json.loads(orm_coin.llm_suggested_design) or {}
                except json.JSONDecodeError:
                    pass
            existing.update(design_delta)
            orm_coin.llm_suggested_design = json.dumps(existing)
        if result.suggested_references:
            existing_refs = []
            if orm_coin.llm_suggested_references:
                try:
                    existing_refs = json.loads(orm_coin.llm_suggested_references) or []
                except json.JSONDecodeError:
                    pass
            merged = list(dict.fromkeys(existing_refs + list(result.suggested_references)))
            orm_coin.llm_suggested_references = json.dumps(merged)
        orm_coin.llm_enriched_at = datetime.now(timezone.utc)

        # Phase 4 Dual-Write: Save to llm_enrichments table via use case
        output_content = {
            "attribution": attribution,
            "design": design_delta,
            "suggested_references": list(result.suggested_references) if result.suggested_references else [],
        }
        # Use 32-char hash for adequate collision resistance
        image_hash = enrichment_use_case.compute_image_hash(image_b64)
        enrichment_use_case.execute(
            coin_id=coin_id,
            capability="identify_coin",
            output_content=output_content,
            input_data={"coin_id": coin_id, "image_hash": image_hash},
            model_id=getattr(result, 'model_used', 'unknown'),
            confidence=getattr(result, 'confidence', None),  # None if unknown, not misleading 0.8
            cost_usd=getattr(result, 'cost_usd', 0.0),
            raw_response=getattr(result, 'content', ''),
            cached=getattr(result, 'cached', False),
        )
        # Note: get_db() handles commit on success, no explicit commit needed
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save identify suggestions for coin %d", coin_id)
        raise HTTPException(status_code=500, detail="Failed to save coin identification results")
    return CoinIdentifyResponse(
        ruler=result.ruler,
        denomination=result.denomination,
        mint=result.mint,
        date_range=result.date_range,
        obverse_description=result.obverse_description,
        reverse_description=result.reverse_description,
        suggested_references=list(result.suggested_references),
        confidence=result.confidence,
        cost_usd=result.cost_usd,
    )


@router.post(
    "/reference/validate",
    response_model=ReferenceValidateResponse,
    summary="Validate catalog reference",
    description="Validate and cross-reference catalog numbers.",
)
async def validate_reference(
    request: ReferenceValidateRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Validate and cross-reference catalog number.
    
    Checks if reference format is valid and suggests alternatives.
    Cross-references between RIC, RSC, Sear, Crawford, etc.
    """
    try:
        result = await llm_service.validate_reference(
            reference=request.reference,
            coin_context=request.coin_context,
        )
        
        return ReferenceValidateResponse(
            is_valid=result.is_valid,
            normalized=result.normalized,
            alternatives=list(result.alternatives),
            notes=result.notes,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/context/generate",
    response_model=ContextGenerateResponse,
    summary="Generate historical context",
    description="Generate historical context narrative for a coin.",
)
async def generate_context(
    request: ContextGenerateRequest,
    llm_service = Depends(get_llm_service),
    db: Session = Depends(get_db),
    enrichment_use_case: SaveLLMEnrichmentUseCase = Depends(get_save_llm_enrichment_use_case),
):
    """
    Generate historical context for a coin.

    Fetches full coin data from DB and generates numismatically-specific
    context including legend analysis, iconographic interpretation,
    and historical significance tied to the actual coin type.

    Also extracts catalog citations from LLM response and compares with
    existing references - new citations are saved for audit/review.
    """
    from datetime import datetime, timezone
    from sqlalchemy import text
    from src.infrastructure.persistence.orm import CoinModel

    try:
        # Fetch full coin data from database using injected session
        coin = db.query(CoinModel).filter(CoinModel.id == request.coin_id).first()
        if not coin:
            raise HTTPException(status_code=404, detail=f"Coin {request.coin_id} not found")

        # Query catalog references (join coin_references with reference_types)
        refs_query = text("""
            SELECT rt.system, rt.volume, rt.number
            FROM coin_references cr
            JOIN reference_types rt ON cr.reference_type_id = rt.id
            WHERE cr.coin_id = :coin_id
        """)
        refs_result = db.execute(refs_query, {"coin_id": request.coin_id}).fetchall()
        existing_references = [
            f"{r[0]} {r[1] or ''} {r[2]}".strip()
            for r in refs_result
        ] if refs_result else []

        # Build comprehensive coin data dict
        coin_data = {
            # Core identification
            "issuer": coin.issuer,
            "denomination": coin.denomination,
            "category": coin.category,
            "metal": coin.metal,
            "mint": coin.mint,

            # Dating
            "year_start": coin.year_start,
            "year_end": coin.year_end,

            # Obverse (front)
            "obverse_legend": coin.obverse_legend,
            "obverse_description": coin.obverse_description,

            # Reverse (back)
            "reverse_legend": coin.reverse_legend,
            "reverse_description": coin.reverse_description,
            "exergue": coin.exergue,

            # Physical
            "weight_g": float(coin.weight_g) if coin.weight_g else None,
            "diameter_mm": float(coin.diameter_mm) if coin.diameter_mm else None,
            "die_axis": coin.die_axis,

            # Existing catalog references (passed to LLM for context)
            "references": existing_references,

            # Grading context
            "grade": coin.grade,
        }

        # Remove None/empty values for cleaner prompt (keep references even if empty)
        coin_data = {k: v for k, v in coin_data.items()
                    if v is not None and v != "" and (k == "references" or v != [])}

        result = await llm_service.generate_context(coin_data)

        # Parse content string back to dict
        try:
            content_dict = json.loads(result.content)
        except json.JSONDecodeError:
            content_dict = {"raw_content": result.content, "sections": {}}

        # Extract citation and enrichment data from parsed content
        llm_found_refs = content_dict.get("llm_citations", [])
        suggested_refs = content_dict.get("suggested_references", [])
        matched_refs = content_dict.get("matched_references", [])

        # Save to database (raw content for backward compat, sections as JSON)
        # Store raw content for backward compatibility (inline columns)
        coin.historical_significance = content_dict.get("raw_content", "")
        # Store sections as JSON string
        coin.llm_analysis_sections = json.dumps(content_dict.get("sections", {}))
        coin.llm_enriched_at = datetime.now(timezone.utc)

        # Store suggested references for audit (new citations not in DB)
        if suggested_refs:
            # Merge with any existing suggestions
            existing_suggestions = []
            if coin.llm_suggested_references:
                try:
                    existing_suggestions = json.loads(coin.llm_suggested_references)
                except json.JSONDecodeError:
                    existing_suggestions = []

            # Deduplicate and merge
            all_suggestions = list(set(existing_suggestions + suggested_refs))
            coin.llm_suggested_references = json.dumps(all_suggestions)
            logger.info("Coin %d: LLM suggested %d new reference(s): %s", request.coin_id, len(suggested_refs), suggested_refs)

        # Store rarity info if found
        rarity_info = content_dict.get("rarity_info", {})
        if rarity_info and (rarity_info.get("rarity_code") or rarity_info.get("rarity_description")):
            coin.llm_suggested_rarity = json.dumps(rarity_info)
            logger.info("Coin %d: LLM identified rarity: %s (%s)", request.coin_id, rarity_info.get('rarity_code'), rarity_info.get('rarity_description'))

        # Phase 4 Dual-Write: Save to llm_enrichments table via use case
        enrichment_use_case.execute(
            coin_id=request.coin_id,
            capability="generate_context",
            output_content=content_dict,
            input_data=coin_data,
            model_id=result.model_used,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            raw_response=result.content,
            cached=result.cached,
            needs_review=result.needs_review,
        )
        logger.info("Saved historical context (%d sections) for coin %d", len(content_dict.get('sections', {})), request.coin_id)

        # Note: get_db() handles commit on success, no explicit commit needed

        # Build response with section objects
        sections_list = [
            ContextSectionResponse(
                key=key,
                title=SECTION_TITLES.get(key, key.replace("_", " ").title()),
                content=content
            )
            for key, content in content_dict.get("sections", {}).items()
        ]

        # Build rarity response if found
        rarity_response = None
        if rarity_info and (rarity_info.get("rarity_code") or rarity_info.get("rarity_description")):
            rarity_response = RarityInfoResponse(
                rarity_code=rarity_info.get("rarity_code"),
                rarity_description=rarity_info.get("rarity_description"),
                specimens_known=rarity_info.get("specimens_known"),
                source=rarity_info.get("source"),
            )

        return ContextGenerateResponse(
            sections=sections_list,
            raw_content=content_dict.get("raw_content", ""),
            confidence=result.confidence,
            cost_usd=result.cost_usd,
            model_used=result.model_used,
            existing_references=existing_references,
            all_llm_citations=llm_found_refs,
            suggested_references=suggested_refs,
            matched_references=matched_refs,
            rarity_info=rarity_response,
        )
    except HTTPException:
        raise
    except LLMError as e:
        raise HTTPException(status_code=500, detail="LLM service error generating context")
    except Exception as e:
        logger.exception("Failed to generate context for coin %d", request.coin_id)
        raise HTTPException(status_code=500, detail="Failed to generate historical context")


# =============================================================================
# P2 ENDPOINTS (Advanced Capabilities)
# =============================================================================

@router.post(
    "/attribution/assist",
    response_model=AttributionAssistResponse,
    summary="Suggest attribution",
    description="Suggest coin attribution from partial information.",
)
async def assist_attribution(
    request: AttributionAssistRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Suggest attribution from partial coin information.
    
    Accepts legend fragments, weight, diameter, design descriptions,
    and returns ranked attribution suggestions with reasoning.
    """
    try:
        result = await llm_service.assist_attribution(
            known_info=request.known_info,
        )
        
        suggestions = [
            AttributionSuggestionResponse(
                attribution=s.attribution,
                reference=s.reference,
                confidence=s.confidence,
                reasoning=list(s.reasoning),
            )
            for s in result.suggestions
        ]
        
        return AttributionAssistResponse(
            suggestions=suggestions,
            questions_to_resolve=list(result.questions_to_resolve),
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/legend/transcribe",
    response_model=LegendTranscribeResponse,
    summary="Transcribe legend from image",
    description="OCR-like legend transcription from coin images.",
)
async def transcribe_legend(
    request: LegendTranscribeRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Transcribe coin legends from image.
    
    Uses vision model to read legend characters. Handles worn/uncertain
    portions with [...] notation and provides expanded abbreviations.
    """
    try:
        result = await llm_service.transcribe_legend(
            image_b64=request.image_b64,
            hints=request.hints,
        )
        
        return LegendTranscribeResponse(
            obverse_legend=result.obverse_legend,
            obverse_legend_expanded=result.obverse_legend_expanded,
            reverse_legend=result.reverse_legend,
            reverse_legend_expanded=result.reverse_legend_expanded,
            exergue=result.exergue,
            uncertain_portions=list(result.uncertain_portions),
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/legend/transcribe/coin/{coin_id}",
    response_model=LegendTranscribeResponse,
    summary="Transcribe legends for coin",
    description="Run legend/transcribe on the coin's primary image and save suggestions to llm_suggested_design.",
)
async def transcribe_legend_for_coin(
    coin_id: int,
    llm_service=Depends(get_llm_service),
    db: Session = Depends(get_db),
    enrichment_use_case: SaveLLMEnrichmentUseCase = Depends(get_save_llm_enrichment_use_case),
):
    """
    Transcribe legends from the coin's primary image and merge into llm_suggested_design.
    Uses the same merge pattern as identify_coin_for_coin so descriptions (or other fields)
    from a prior identify run are preserved. Sets llm_enriched_at.

    Also writes to llm_enrichments table for audit/history (dual-write).
    """
    from datetime import datetime, timezone
    from src.infrastructure.persistence.orm import CoinModel

    orm_coin = db.query(CoinModel).filter(CoinModel.id == coin_id).first()
    if not orm_coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    image_b64 = await _resolve_coin_primary_image_b64(db, coin_id)
    if not image_b64:
        raise HTTPException(
            status_code=400,
            detail="Coin has no primary image or image could not be loaded",
        )
    result = await llm_service.transcribe_legend(image_b64=image_b64, hints=None)
    design_delta = {
        "obverse_legend": result.obverse_legend,
        "reverse_legend": result.reverse_legend,
        "exergue": result.exergue,
        "obverse_legend_expanded": result.obverse_legend_expanded,
        "reverse_legend_expanded": result.reverse_legend_expanded,
    }
    design_delta = {k: v for k, v in design_delta.items() if v is not None}
    try:
        existing = {}
        if orm_coin.llm_suggested_design:
            try:
                existing = json.loads(orm_coin.llm_suggested_design) or {}
            except json.JSONDecodeError:
                pass
        existing.update(design_delta)
        orm_coin.llm_suggested_design = json.dumps(existing) if existing else orm_coin.llm_suggested_design
        orm_coin.llm_enriched_at = datetime.now(timezone.utc)

        # Phase 4 Dual-Write: Save to llm_enrichments table via use case
        output_content = {
            "design": design_delta,
            "uncertain_portions": list(result.uncertain_portions) if result.uncertain_portions else [],
        }
        # Use 32-char hash for adequate collision resistance
        image_hash = enrichment_use_case.compute_image_hash(image_b64)
        enrichment_use_case.execute(
            coin_id=coin_id,
            capability="transcribe_legend",
            output_content=output_content,
            input_data={"coin_id": coin_id, "image_hash": image_hash},
            model_id=getattr(result, 'model_used', 'unknown'),
            confidence=getattr(result, 'confidence', None),  # None if unknown, not misleading 0.8
            cost_usd=getattr(result, 'cost_usd', 0.0),
            raw_response=getattr(result, 'content', ''),
            cached=getattr(result, 'cached', False),
        )
        # Note: get_db() handles commit on success, no explicit commit needed
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save transcribe suggestions for coin %d", coin_id)
        raise HTTPException(status_code=500, detail="Failed to save legend transcription results")
    return LegendTranscribeResponse(
        obverse_legend=result.obverse_legend,
        obverse_legend_expanded=result.obverse_legend_expanded,
        reverse_legend=result.reverse_legend,
        reverse_legend_expanded=result.reverse_legend_expanded,
        exergue=result.exergue,
        uncertain_portions=list(result.uncertain_portions),
        confidence=result.confidence,
        cost_usd=result.cost_usd,
    )


@router.post(
    "/catalog/parse",
    response_model=CatalogParseResponse,
    summary="Parse catalog reference",
    description="Parse catalog reference string into components.",
)
async def parse_catalog(
    request: CatalogParseRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Parse catalog reference string.
    
    Recognizes RIC, RSC, RPC, Crawford, Sear, BMC, Cohen.
    Extracts volume, number, and infers issuer where possible.
    """
    try:
        result = await llm_service.parse_catalog(
            reference=request.reference,
        )
        
        return CatalogParseResponse(
            raw_reference=result.raw_reference,
            catalog_system=result.catalog_system,
            volume=result.volume,
            number=result.number,
            issuer=result.issuer,
            mint=result.mint,
            alternatives=list(result.alternatives),
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/condition/observe",
    response_model=ConditionObserveResponse,
    summary="Observe coin condition",
    description="Describe wear patterns and surface conditions (NOT grades).",
)
async def observe_condition(
    request: ConditionObserveRequest,
    llm_service = Depends(get_llm_service),
):
    """
    Describe coin condition from image.
    
    CRITICAL: Does NOT provide numeric grades (VF/EF/AU).
    Describes observable wear patterns, surface characteristics,
    and strike quality. Always recommends professional grading.
    """
    try:
        result = await llm_service.observe_condition(
            image_b64=request.image_b64,
            hints=request.hints,
        )
        
        return ConditionObserveResponse(
            wear_observations=result.wear_observations,
            surface_notes=result.surface_notes,
            strike_quality=result.strike_quality,
            notable_features=list(result.notable_features),
            concerns=list(result.concerns),
            recommendation=result.recommendation,
            confidence=result.confidence,
            cost_usd=result.cost_usd,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ADMIN ENDPOINTS
# =============================================================================

@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Service status",
    description="Get LLM service status and availability.",
)
async def get_status(
    llm_service = Depends(get_llm_service),
):
    """
    Get LLM service status.
    
    Returns current profile, budget status, and available capabilities.
    """
    monthly_cost = llm_service.get_monthly_cost()
    budget = llm_service.config.monthly_budget
    
    available = [
        cap.value for cap in LLMCapability.mvp_capabilities()
        if llm_service.is_capability_available(cap)
    ]
    
    # Check Ollama availability
    ollama_available = False
    try:
        import httpx
        resp = httpx.get(f"{llm_service.config.settings.get('ollama_host', 'http://127.0.0.1:11434')}/api/version", timeout=2)
        ollama_available = resp.status_code == 200
    except Exception:
        pass

    # Provider key presence only (never expose values)
    provider_keys = ProviderKeysStatus(
        anthropic=bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        openrouter=bool(os.environ.get("OPENROUTER_API_KEY", "").strip()),
        google=bool(os.environ.get("GOOGLE_API_KEY", "").strip()),
    )
    
    return StatusResponse(
        status="operational",
        profile=llm_service.get_active_profile(),
        monthly_cost_usd=monthly_cost,
        monthly_budget_usd=budget,
        budget_remaining_usd=max(0, budget - monthly_cost),
        capabilities_available=available,
        ollama_available=ollama_available,
        provider_keys=provider_keys,
    )


@router.get(
    "/cost-report",
    response_model=CostReportResponse,
    summary="Cost report",
    description="Get cost breakdown by capability and model.",
)
async def get_cost_report(
    days: int = Query(30, ge=1, le=365),
    llm_service = Depends(get_llm_service),
):
    """
    Get cost report.
    
    Shows usage and costs broken down by capability and model.
    """
    if not llm_service.cost_tracker:
        return CostReportResponse(
            period_days=days,
            total_cost_usd=0.0,
            by_capability={},
            by_model={},
        )
    
    by_capability = llm_service.cost_tracker.get_cost_by_capability(days)
    by_model = llm_service.cost_tracker.get_cost_by_model(days)
    total = sum(by_capability.values())
    
    return CostReportResponse(
        period_days=days,
        total_cost_usd=total,
        by_capability=by_capability,
        by_model=by_model,
    )


@router.get(
    "/metrics",
    response_model=MetricsSummaryResponse,
    summary="Metrics summary",
    description="Get performance and error metrics.",
)
async def get_metrics(
    hours: int = Query(24, ge=1, le=168),
    metrics_service = Depends(get_metrics_service),
):
    """
    Get metrics summary.
    
    Returns call counts, latencies, cache rates, and error breakdown.
    """
    summary = metrics_service.get_summary(hours)
    
    return MetricsSummaryResponse(
        period_hours=summary.period_hours,
        total_calls=summary.total_calls,
        successful_calls=summary.successful_calls,
        failed_calls=summary.failed_calls,
        cached_calls=summary.cached_calls,
        total_cost_usd=summary.total_cost_usd,
        avg_latency_ms=summary.avg_latency_ms,
        cache_hit_rate=summary.cache_hit_rate,
        success_rate=summary.success_rate,
        calls_by_capability=summary.calls_by_capability,
        errors_by_type=summary.errors_by_type,
    )


@router.post(
    "/feedback",
    status_code=201,
    summary="Submit feedback",
    description="Submit accuracy feedback on LLM suggestions.",
)
async def submit_feedback(
    request: FeedbackRequest,
    event_store = Depends(get_event_store),
):
    """
    Submit accuracy feedback.
    
    Records whether user accepted, rejected, or modified an LLM suggestion.
    Used for confidence calibration and prompt improvement.
    """
    from src.domain.events import (
        LLMSuggestionAccepted,
        LLMSuggestionRejected,
    )
    
    if request.action == "accepted":
        event = LLMSuggestionAccepted(
            coin_id=request.coin_id,
            capability=request.capability,
            field_name=request.field,
            suggested_value=request.suggested_value,
            confidence=request.confidence,
            model_used=request.model_used,
        )
    elif request.action in ("rejected", "modified"):
        event = LLMSuggestionRejected(
            coin_id=request.coin_id,
            capability=request.capability,
            field_name=request.field,
            suggested_value=request.suggested_value,
            user_correction=request.user_value,
            rejection_reason=request.reason,
            confidence=request.confidence,
            model_used=request.model_used,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
    
    event_store.append(event)
    
    return {"status": "recorded", "event_id": event.event_id}


# =============================================================================
# LLM REVIEW QUEUE ENDPOINTS
# =============================================================================

class CatalogReferenceValidation(BaseModel):
    """Validation result for a suggested catalog reference."""
    reference_text: str
    parsed_catalog: Optional[str] = None  # "RIC", "RSC", "Cohen", etc.
    parsed_number: Optional[str] = None
    parsed_volume: Optional[str] = None
    validation_status: str  # "matches", "partial_match", "mismatch", "unknown"
    confidence: float = 0.0  # 0.0 to 1.0
    match_reason: Optional[str] = None  # Why it matches/doesn't match
    existing_reference: Optional[str] = None  # If already in DB
    numismatic_warning: Optional[str] = None  # Category/catalog consistency warning from catalog_validation


class LlmSuggestedDesign(BaseModel):
    """LLM-suggested design fields (legends, exergue, descriptions)."""
    obverse_legend: Optional[str] = None
    reverse_legend: Optional[str] = None
    exergue: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_description: Optional[str] = None
    obverse_legend_expanded: Optional[str] = None
    reverse_legend_expanded: Optional[str] = None


class LlmSuggestedAttribution(BaseModel):
    """LLM-suggested attribution (issuer, mint, denomination, dates)."""
    issuer: Optional[str] = None
    mint: Optional[str] = None
    denomination: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None


class LLMSuggestionItem(BaseModel):
    """Item in the LLM suggestions review queue."""
    coin_id: int
    # Core coin identification
    issuer: Optional[str] = None
    denomination: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    category: Optional[str] = None
    # Legends for context
    obverse_legend: Optional[str] = None
    reverse_legend: Optional[str] = None
    # Existing catalog references (for comparison)
    existing_references: List[str] = Field(default_factory=list)
    # LLM suggestions
    suggested_references: List[str] = Field(default_factory=list)
    validated_references: List[CatalogReferenceValidation] = Field(default_factory=list)
    rarity_info: Optional[RarityInfoResponse] = None
    suggested_design: Optional[LlmSuggestedDesign] = None
    suggested_attribution: Optional[LlmSuggestedAttribution] = None
    enriched_at: Optional[str] = None


class LLMReviewQueueResponse(BaseModel):
    """Response for LLM review queue."""
    items: List[LLMSuggestionItem]
    total: int


def _parse_catalog_reference(ref_text: str) -> Dict[str, Optional[str]]:
    """
    Parse a catalog reference string using the central parser.
    Delegates to src.infrastructure.services.catalogs.parser.parse_catalog_reference.
    """
    from src.infrastructure.services.catalogs.parser import parse_catalog_reference as _central_parse
    return _central_parse(ref_text)


def _validate_catalog_reference(
    ref_text: str,
    coin_issuer: Optional[str],
    coin_mint: Optional[str],
    coin_year_start: Optional[int],
    coin_year_end: Optional[int],
    coin_category: Optional[str],
    existing_refs: List[str],
) -> CatalogReferenceValidation:
    """
    Validate a suggested catalog reference against coin attributes.
    Includes numismatic consistency (category vs catalog) via catalog_validation service.
    """
    parsed = _parse_catalog_reference(ref_text)

    # Numismatic validation: category vs catalog alignment
    from src.application.services.catalog_validation import validate_reference_for_coin
    numismatic_result = validate_reference_for_coin(
        catalog=parsed.get("catalog"),
        number=parsed.get("number"),
        volume=parsed.get("volume"),
        coin_category=coin_category,
        year_start=coin_year_start,
        year_end=coin_year_end,
        issuer=coin_issuer,
    )
    numismatic_warning = numismatic_result.message if numismatic_result.status == "warning" else None

    # Check if reference already exists in DB
    normalized_refs = [r.upper().replace(".", " ").replace(",", " ") for r in existing_refs]

    existing_match = None
    for existing in normalized_refs:
        if parsed["catalog"] and parsed["catalog"].upper() in existing:
            if parsed["number"] and parsed["number"] in existing:
                existing_match = existing
                break

    validation_status = "unknown"
    confidence = 0.5
    match_reason = None

    if existing_match:
        validation_status = "matches"
        confidence = 1.0
        match_reason = f"Already exists in database: {existing_match}"
    elif parsed["catalog"]:
        validation_status = "partial_match"
        confidence = 0.6
        match_reason = f"Parsed as {parsed['catalog']} {parsed['number'] or ''}"

    return CatalogReferenceValidation(
        reference_text=ref_text,
        parsed_catalog=parsed["catalog"],
        parsed_number=parsed["number"],
        parsed_volume=parsed["volume"],
        validation_status=validation_status,
        confidence=confidence,
        match_reason=match_reason,
        existing_reference=existing_match,
        numismatic_warning=numismatic_warning,
    )


@router.get(
    "/review",
    response_model=LLMReviewQueueResponse,
    summary="Get LLM suggestions for review",
    description="Get all coins with pending LLM suggestions (references, rarity) for review.",
)
async def get_llm_review_queue(
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    db: Session = Depends(get_db),
):
    """
    Get LLM suggestions pending review.
    
    Returns coins that have LLM-suggested references, rarity, design, or attribution
    that haven't been applied yet. Includes full coin details for context
    and validates suggested catalog references against coin attributes.
    """
    from sqlalchemy import text
    from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

    result = db.execute(text("""
        SELECT 
            id, issuer, denomination, mint, category,
            year_start, year_end,
            obverse_legend, reverse_legend,
            llm_suggested_references, llm_suggested_rarity,
            llm_suggested_design, llm_suggested_attribution,
            llm_enriched_at
        FROM coins_v2 
        WHERE llm_suggested_references IS NOT NULL 
           OR llm_suggested_rarity IS NOT NULL
           OR llm_suggested_design IS NOT NULL
           OR llm_suggested_attribution IS NOT NULL
        ORDER BY llm_enriched_at DESC
        LIMIT :limit
    """), {"limit": limit})

    rows = result.fetchall()
    items = []
    repo = SqlAlchemyCoinRepository(db)

    for row in rows:
        (coin_id, issuer, denomination, mint, category,
         year_start, year_end, obverse_legend, reverse_legend,
         refs_json, rarity_json, design_json, attribution_json, enriched_at) = row

        coin = repo.get_by_id(coin_id)
        existing_refs = []
        if coin and coin.references:
            existing_refs = [
                f"{ref.catalog} {ref.volume or ''} {ref.number}".strip()
                for ref in coin.references
            ]

        suggested_refs = []
        if refs_json:
            try:
                suggested_refs = json.loads(refs_json)
            except json.JSONDecodeError:
                pass

        validated_refs = []
        for ref_text in suggested_refs:
            validation = _validate_catalog_reference(
                ref_text=ref_text,
                coin_issuer=issuer,
                coin_mint=mint,
                coin_year_start=year_start,
                coin_year_end=year_end,
                coin_category=category,
                existing_refs=existing_refs,
            )
            validated_refs.append(validation)

        rarity_info = None
        if rarity_json:
            try:
                rarity_data = json.loads(rarity_json)
                rarity_info = RarityInfoResponse(
                    rarity_code=rarity_data.get("rarity_code"),
                    rarity_description=rarity_data.get("rarity_description"),
                    specimens_known=rarity_data.get("specimens_known"),
                    source=rarity_data.get("source"),
                )
            except json.JSONDecodeError:
                pass

        suggested_design = None
        if design_json:
            try:
                design_data = json.loads(design_json)
                if isinstance(design_data, dict) and any(
                    design_data.get(k) for k in (
                        "obverse_legend", "reverse_legend", "exergue",
                        "obverse_description", "reverse_description",
                        "obverse_legend_expanded", "reverse_legend_expanded",
                    )
                ):
                    suggested_design = LlmSuggestedDesign(
                        obverse_legend=design_data.get("obverse_legend"),
                        reverse_legend=design_data.get("reverse_legend"),
                        exergue=design_data.get("exergue"),
                        obverse_description=design_data.get("obverse_description"),
                        reverse_description=design_data.get("reverse_description"),
                        obverse_legend_expanded=design_data.get("obverse_legend_expanded"),
                        reverse_legend_expanded=design_data.get("reverse_legend_expanded"),
                    )
            except (json.JSONDecodeError, TypeError):
                pass

        suggested_attribution = None
        if attribution_json:
            try:
                attr_data = json.loads(attribution_json)
                if isinstance(attr_data, dict) and any(
                    attr_data.get(k) is not None for k in ("issuer", "mint", "denomination", "year_start", "year_end")
                ):
                    suggested_attribution = LlmSuggestedAttribution(
                        issuer=attr_data.get("issuer"),
                        mint=attr_data.get("mint"),
                        denomination=attr_data.get("denomination"),
                        year_start=attr_data.get("year_start"),
                        year_end=attr_data.get("year_end"),
                    )
            except (json.JSONDecodeError, TypeError):
                pass

        if suggested_refs or rarity_info or suggested_design or suggested_attribution:
            enriched_at_str = str(enriched_at) if enriched_at else None
            items.append(LLMSuggestionItem(
                coin_id=coin_id,
                issuer=issuer,
                denomination=denomination,
                mint=mint,
                year_start=year_start,
                year_end=year_end,
                category=category,
                obverse_legend=obverse_legend,
                reverse_legend=reverse_legend,
                existing_references=existing_refs,
                suggested_references=suggested_refs,
                validated_references=validated_refs,
                rarity_info=rarity_info,
                suggested_design=suggested_design,
                suggested_attribution=suggested_attribution,
                enriched_at=enriched_at_str,
            ))

    return LLMReviewQueueResponse(
        items=items,
        total=len(items),
    )


@router.post(
    "/review/{coin_id}/dismiss",
    summary="Dismiss LLM suggestions",
    description="Clear LLM suggestions for a coin (reject all or by type).",
)
async def dismiss_llm_suggestions(
    coin_id: int,
    dismiss_references: bool = Query(True, description="Dismiss reference suggestions"),
    dismiss_rarity: bool = Query(True, description="Dismiss rarity suggestions"),
    dismiss_design: bool = Query(True, description="Dismiss design/legend suggestions"),
    dismiss_attribution: bool = Query(True, description="Dismiss attribution suggestions"),
    db: Session = Depends(get_db),
):
    """
    Dismiss (reject) LLM suggestions for a coin.
    
    Clears the stored suggestions without applying them.
    """
    from sqlalchemy import text

    updates = []
    if dismiss_references:
        updates.append("llm_suggested_references = NULL")
    if dismiss_rarity:
        updates.append("llm_suggested_rarity = NULL")
    if dismiss_design:
        updates.append("llm_suggested_design = NULL")
    if dismiss_attribution:
        updates.append("llm_suggested_attribution = NULL")

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to dismiss")

    try:
        db.execute(
            text(f"UPDATE coins_v2 SET {', '.join(updates)} WHERE id = :coin_id"),
            {"coin_id": coin_id}
        )
        db.commit()
        return {"status": "dismissed", "coin_id": coin_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/review/{coin_id}/approve",
    summary="Approve and apply LLM suggestions",
    description="Apply suggested rarity and catalog references to the coin, then clear suggestions.",
)
async def approve_llm_suggestions(
    coin_id: int,
    db: Session = Depends(get_db),
):
    """
    Apply LLM-suggested rarity, references, design, and attribution to the coin, then clear llm_suggested_*.
    - Rarity: copy rarity_code or rarity_description into coin.rarity; source into rarity_notes.
    - References: create reference_types + coin_references for each suggested ref string.
    - Design: copy obverse_legend, reverse_legend, exergue, descriptions, *_expanded into coin.
    - Attribution: copy issuer, mint, denomination, year_start, year_end into coin.
    """
    from sqlalchemy.orm import selectinload
    from src.infrastructure.persistence.orm import CoinModel, ReferenceTypeModel, CoinReferenceModel

    try:
        coin = (
            db.query(CoinModel)
            .options(selectinload(CoinModel.references).selectinload(CoinReferenceModel.reference_type))
            .filter(CoinModel.id == coin_id)
            .first()
        )
        if not coin:
            raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
        has_any = (
            coin.llm_suggested_rarity or coin.llm_suggested_references
            or coin.llm_suggested_design or coin.llm_suggested_attribution
        )
        if not has_any:
            raise HTTPException(status_code=400, detail="No pending suggestions to apply")

        applied_rarity = False
        applied_refs = 0
        applied_design = False
        applied_attribution = False

        if coin.llm_suggested_rarity:
            try:
                rarity_data = json.loads(coin.llm_suggested_rarity)
                code = rarity_data.get("rarity_code")
                desc = rarity_data.get("rarity_description")
                source = rarity_data.get("source")
                if code or desc:
                    raw = (code or desc) if code else desc
                    coin.rarity = normalize_rarity_for_api(raw)
                    coin.rarity_notes = source or rarity_data.get("rarity_description")
                    applied_rarity = True
                coin.llm_suggested_rarity = None
            except (json.JSONDecodeError, TypeError):
                coin.llm_suggested_rarity = None

        if coin.llm_suggested_references:
            try:
                ref_strings = json.loads(coin.llm_suggested_references)
                if isinstance(ref_strings, list):
                    ref_strings = [str(r).strip() for r in ref_strings if r and str(r).strip()]
                    if ref_strings:
                        from src.application.services.reference_sync import sync_coin_references
                        sync_coin_references(db, coin_id, ref_strings, "llm_approved", merge=True)
                        applied_refs = len(ref_strings)
                coin.llm_suggested_references = None
            except (json.JSONDecodeError, TypeError):
                coin.llm_suggested_references = None

        if coin.llm_suggested_design:
            try:
                design_data = json.loads(coin.llm_suggested_design)
                if isinstance(design_data, dict):
                    if design_data.get("obverse_legend") is not None:
                        coin.obverse_legend = design_data["obverse_legend"]
                    if design_data.get("reverse_legend") is not None:
                        coin.reverse_legend = design_data["reverse_legend"]
                    if design_data.get("exergue") is not None:
                        coin.exergue = design_data["exergue"]
                    if design_data.get("obverse_description") is not None:
                        coin.obverse_description = design_data["obverse_description"]
                    if design_data.get("reverse_description") is not None:
                        coin.reverse_description = design_data["reverse_description"]
                    if design_data.get("obverse_legend_expanded") is not None:
                        coin.obverse_legend_expanded = design_data["obverse_legend_expanded"]
                    if design_data.get("reverse_legend_expanded") is not None:
                        coin.reverse_legend_expanded = design_data["reverse_legend_expanded"]
                    applied_design = True
                coin.llm_suggested_design = None
            except (json.JSONDecodeError, TypeError):
                coin.llm_suggested_design = None

        if coin.llm_suggested_attribution:
            try:
                attr_data = json.loads(coin.llm_suggested_attribution)
                if isinstance(attr_data, dict):
                    if attr_data.get("issuer") is not None:
                        coin.issuer = attr_data["issuer"]
                    if attr_data.get("mint") is not None:
                        coin.mint = attr_data["mint"]
                    if attr_data.get("year_start") is not None:
                        coin.year_start = attr_data["year_start"]
                    if attr_data.get("year_end") is not None:
                        coin.year_end = attr_data["year_end"]
                    if attr_data.get("denomination") is not None:
                        coin.denomination = attr_data["denomination"]
                    applied_attribution = True
                coin.llm_suggested_attribution = None
            except (json.JSONDecodeError, TypeError):
                coin.llm_suggested_attribution = None

        db.commit()
        logger.info(
            "Applied LLM suggestions for coin %s: rarity=%s, refs=%s, design=%s, attribution=%s",
            coin_id, applied_rarity, applied_refs, applied_design, applied_attribution,
        )
        return {
            "status": "approved",
            "coin_id": coin_id,
            "applied_rarity": applied_rarity,
            "applied_references": applied_refs,
            "applied_design": applied_design,
            "applied_attribution": applied_attribution,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Approve LLM suggestions failed for coin %s: %s", coin_id, e)
        raise HTTPException(status_code=500, detail=str(e))