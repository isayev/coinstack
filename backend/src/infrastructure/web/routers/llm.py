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

import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field

from src.domain.llm import (
    LLMCapability,
    LLMError,
    LLMParseError,
    LLMProviderUnavailable,
    LLMRateLimitExceeded,
    LLMBudgetExceeded,
    LLMCapabilityNotAvailable,
)

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


class StatusResponse(BaseModel):
    """LLM service status."""
    status: str
    profile: str
    monthly_cost_usd: float
    monthly_budget_usd: float
    budget_remaining_usd: float
    capabilities_available: List[str]
    ollama_available: bool


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


def get_db():
    """Get database session."""
    from src.infrastructure.persistence.database import get_db as _get_db
    return next(_get_db())


@router.post(
    "/context/generate",
    response_model=ContextGenerateResponse,
    summary="Generate historical context",
    description="Generate historical context narrative for a coin.",
)
async def generate_context(
    request: ContextGenerateRequest,
    llm_service = Depends(get_llm_service),
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
    from src.infrastructure.persistence.database import SessionLocal
    
    try:
        # Fetch full coin data from database
        db = SessionLocal()
        try:
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
                "weight_g": coin.weight_g,
                "diameter_mm": coin.diameter_mm,
                "die_axis": coin.die_axis,
                
                # Existing catalog references (passed to LLM for context)
                "references": existing_references,
                
                # Grading context
                "grade": coin.grade,
            }
            
            # Remove None/empty values for cleaner prompt (keep references even if empty)
            coin_data = {k: v for k, v in coin_data.items() 
                        if v is not None and v != "" and (k == "references" or v != [])}
            
        finally:
            db.close()
        
        result = await llm_service.generate_context(coin_data)
        
        # Extract citation and enrichment data from result
        llm_found_refs = result.get("llm_citations", [])
        suggested_refs = result.get("suggested_references", [])
        matched_refs = result.get("matched_references", [])
        
        # Save to database (raw content for backward compat, sections as JSON)
        db = SessionLocal()
        try:
            coin = db.query(CoinModel).filter(CoinModel.id == request.coin_id).first()
            if coin:
                # Store raw content for backward compatibility
                coin.historical_significance = result["raw_content"]
                # Store sections as JSON string
                coin.llm_analysis_sections = json.dumps(result["sections"])
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
                    logger.info(f"Coin {request.coin_id}: LLM suggested {len(suggested_refs)} new reference(s): {suggested_refs}")
                
                # Store rarity info if found
                rarity_info = result.get("rarity_info", {})
                if rarity_info and (rarity_info.get("rarity_code") or rarity_info.get("rarity_description")):
                    coin.llm_suggested_rarity = json.dumps(rarity_info)
                    logger.info(f"Coin {request.coin_id}: LLM identified rarity: {rarity_info.get('rarity_code')} ({rarity_info.get('rarity_description')})")
                
                db.commit()
                logger.info(f"Saved historical context ({len(result['sections'])} sections) for coin {request.coin_id}")
        except Exception as db_err:
            logger.error(f"Failed to save historical context: {db_err}")
            db.rollback()
        finally:
            db.close()
        
        # Build response with section objects
        sections_list = [
            ContextSectionResponse(
                key=key,
                title=SECTION_TITLES.get(key, key.replace("_", " ").title()),
                content=content
            )
            for key, content in result["sections"].items()
        ]
        
        # Build rarity response if found
        rarity_info = result.get("rarity_info", {})
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
            raw_content=result["raw_content"],
            confidence=result["confidence"],
            cost_usd=result["cost_usd"],
            model_used=result["model_used"],
            existing_references=existing_references,
            all_llm_citations=llm_found_refs,
            suggested_references=suggested_refs,
            matched_references=matched_refs,
            rarity_info=rarity_response,
        )
    except LLMError as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        resp = httpx.get(f"{llm_service.config.settings.get('ollama_host', 'http://localhost:11434')}/api/version", timeout=2)
        ollama_available = resp.status_code == 200
    except Exception:
        pass
    
    return StatusResponse(
        status="operational",
        profile=llm_service.get_active_profile(),
        monthly_cost_usd=monthly_cost,
        monthly_budget_usd=budget,
        budget_remaining_usd=max(0, budget - monthly_cost),
        capabilities_available=available,
        ollama_available=ollama_available,
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
    enriched_at: Optional[str] = None


class LLMReviewQueueResponse(BaseModel):
    """Response for LLM review queue."""
    items: List[LLMSuggestionItem]
    total: int


def _parse_catalog_reference(ref_text: str) -> Dict[str, Optional[str]]:
    """
    Parse a catalog reference string into structured components.
    
    Examples:
        "RIC IV.1 289c" -> {catalog: "RIC", volume: "IV.1", number: "289c"}
        "Cohen 382" -> {catalog: "Cohen", volume: None, number: "382"}
        "RSC 382" -> {catalog: "RSC", volume: None, number: "382"}
    """
    import re
    
    # Catalog patterns with capture groups
    patterns = [
        (r'\b(RIC)\s+([IVX]+(?:\.\d+|i)?)\s*,?\s*(\d+[a-z]?)\b', 'RIC'),
        (r'\b(RSC)\s+(\d+[a-z]?)\b', 'RSC'),
        (r'\b(Cohen)\s+(\d+[a-z]?)\b', 'Cohen'),
        (r'\b(Sear)\s+(\d+)\b', 'Sear'),
        (r'\b(RRC|Crawford)\s+(\d+(?:/\d+)?[a-z]?)\b', 'RRC'),
        (r'\b(BMC(?:RE)?)\s+([IVXLC]+|\d+)?\s*,?\s*(\d+)\b', 'BMC'),
        (r'\b(RPC)\s+([IVXLC]+)\s*,?\s*(\d+\??)\b', 'RPC'),
    ]
    
    for pattern, catalog_name in patterns:
        match = re.search(pattern, ref_text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if catalog_name == 'RIC' and len(groups) >= 3:
                return {
                    "catalog": "RIC",
                    "volume": groups[1],
                    "number": groups[2],
                }
            elif catalog_name in ['RSC', 'Cohen', 'Sear'] and len(groups) >= 2:
                return {
                    "catalog": catalog_name,
                    "volume": None,
                    "number": groups[1],
                }
            elif catalog_name == 'RRC' and len(groups) >= 2:
                return {
                    "catalog": "RRC",
                    "volume": None,
                    "number": groups[1],
                }
            elif catalog_name == 'BMC' and len(groups) >= 2:
                return {
                    "catalog": groups[0],
                    "volume": groups[1] if len(groups) > 2 else None,
                    "number": groups[-1],
                }
            elif catalog_name == 'RPC' and len(groups) >= 3:
                return {
                    "catalog": "RPC",
                    "volume": groups[1],
                    "number": groups[2],
                }
    
    # Fallback: extract first word as catalog
    parts = ref_text.split()
    if parts:
        return {
            "catalog": parts[0].upper(),
            "volume": None,
            "number": parts[-1] if len(parts) > 1 else None,
        }
    
    return {"catalog": None, "volume": None, "number": None}


def _validate_catalog_reference(
    ref_text: str,
    coin_issuer: Optional[str],
    coin_mint: Optional[str],
    coin_year_start: Optional[int],
    coin_year_end: Optional[int],
    existing_refs: List[str],
) -> CatalogReferenceValidation:
    """
    Validate a suggested catalog reference against coin attributes.
    
    Returns validation status and confidence score.
    """
    parsed = _parse_catalog_reference(ref_text)
    
    # Check if reference already exists in DB
    normalized_refs = [r.upper().replace(".", " ").replace(",", " ") for r in existing_refs]
    ref_normalized = ref_text.upper().replace(".", " ").replace(",", " ")
    
    existing_match = None
    for existing in normalized_refs:
        if parsed["catalog"] and parsed["catalog"].upper() in existing:
            if parsed["number"] and parsed["number"] in existing:
                existing_match = existing
                break
    
    # Validation logic based on catalog type
    validation_status = "unknown"
    confidence = 0.5
    match_reason = None
    
    if existing_match:
        validation_status = "matches"
        confidence = 1.0
        match_reason = f"Already exists in database: {existing_match}"
    elif parsed["catalog"]:
        # Basic validation: if we can parse it, it's at least a valid format
        validation_status = "partial_match"
        confidence = 0.6
        match_reason = f"Parsed as {parsed['catalog']} {parsed['number'] or ''}"
        
        # For RIC references, we could check issuer/mint/date ranges
        # This would require external catalog data or heuristics
        # For now, we mark as partial_match if parsed successfully
    
    return CatalogReferenceValidation(
        reference_text=ref_text,
        parsed_catalog=parsed["catalog"],
        parsed_number=parsed["number"],
        parsed_volume=parsed["volume"],
        validation_status=validation_status,
        confidence=confidence,
        match_reason=match_reason,
        existing_reference=existing_match,
    )


@router.get(
    "/review",
    response_model=LLMReviewQueueResponse,
    summary="Get LLM suggestions for review",
    description="Get all coins with pending LLM suggestions (references, rarity) for review.",
)
async def get_llm_review_queue(
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
):
    """
    Get LLM suggestions pending review.
    
    Returns coins that have LLM-suggested references or rarity info
    that haven't been applied yet. Includes full coin details for context
    and validates suggested catalog references against coin attributes.
    """
    from sqlalchemy import text
    from src.infrastructure.persistence.database import SessionLocal
    from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
    
    db = SessionLocal()
    try:
        # Query coins with LLM suggestions - fetch more fields for context
        result = db.execute(text("""
            SELECT 
                id, issuer, denomination, mint, category,
                year_start, year_end,
                obverse_legend, reverse_legend,
                llm_suggested_references, llm_suggested_rarity,
                llm_enriched_at
            FROM coins_v2 
            WHERE llm_suggested_references IS NOT NULL 
               OR llm_suggested_rarity IS NOT NULL
            ORDER BY llm_enriched_at DESC
            LIMIT :limit
        """), {"limit": limit})
        
        rows = result.fetchall()
        items = []
        
        # Get repository for fetching existing references
        repo = SqlAlchemyCoinRepository(db)
        
        for row in rows:
            (coin_id, issuer, denomination, mint, category,
             year_start, year_end, obverse_legend, reverse_legend,
             refs_json, rarity_json, enriched_at) = row
            
            # Get existing references from coin
            coin = repo.get_by_id(coin_id)
            existing_refs = []
            if coin and coin.references:
                existing_refs = [
                    f"{ref.catalog} {ref.volume or ''} {ref.number}".strip()
                    for ref in coin.references
                ]
            
            # Parse references JSON
            suggested_refs = []
            if refs_json:
                try:
                    suggested_refs = json.loads(refs_json)
                except json.JSONDecodeError:
                    pass
            
            # Validate each suggested reference
            validated_refs = []
            for ref_text in suggested_refs:
                validation = _validate_catalog_reference(
                    ref_text=ref_text,
                    coin_issuer=issuer,
                    coin_mint=mint,
                    coin_year_start=year_start,
                    coin_year_end=year_end,
                    existing_refs=existing_refs,
                )
                validated_refs.append(validation)
            
            # Parse rarity JSON
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
            
            # Only include if there are actual suggestions
            if suggested_refs or rarity_info:
                # enriched_at is already a string from the database
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
                    enriched_at=enriched_at_str,
                ))
        
        return LLMReviewQueueResponse(
            items=items,
            total=len(items),
        )
    finally:
        db.close()


@router.post(
    "/review/{coin_id}/dismiss",
    summary="Dismiss LLM suggestions",
    description="Clear LLM suggestions for a coin (reject all).",
)
async def dismiss_llm_suggestions(
    coin_id: int,
    dismiss_references: bool = Query(True, description="Dismiss reference suggestions"),
    dismiss_rarity: bool = Query(True, description="Dismiss rarity suggestions"),
):
    """
    Dismiss (reject) LLM suggestions for a coin.
    
    Clears the stored suggestions without applying them.
    """
    from sqlalchemy import text
    from src.infrastructure.persistence.database import SessionLocal
    
    db = SessionLocal()
    try:
        updates = []
        if dismiss_references:
            updates.append("llm_suggested_references = NULL")
        if dismiss_rarity:
            updates.append("llm_suggested_rarity = NULL")
        
        if not updates:
            raise HTTPException(status_code=400, detail="Nothing to dismiss")
        
        db.execute(
            text(f"UPDATE coins_v2 SET {', '.join(updates)} WHERE id = :coin_id"),
            {"coin_id": coin_id}
        )
        db.commit()
        
        return {"status": "dismissed", "coin_id": coin_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
