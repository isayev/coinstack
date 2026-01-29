"""Import API router for V2 - URL scraping, NGC lookup, and import confirmation."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from decimal import Decimal
from src.infrastructure.external.ngc_client import (
    get_ngc_client,
    NGCClient,
    InvalidCertificateError,
    CertificateNotFoundError,
    NGCTimeoutError,
    NGCRateLimitError,
)
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.web.dependencies import get_db
from sqlalchemy.orm import Session
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.heritage.scraper import HeritageScraper
from src.infrastructure.scrapers.cng.scraper import CNGScraper
from src.infrastructure.scrapers.biddr.scraper import BiddrScraper
from src.infrastructure.scrapers.ebay.scraper import EbayScraper
from src.infrastructure.scrapers.agora.scraper import AgoraScraper

router = APIRouter(prefix="/api/v2/import", tags=["import"])

# ============================================================================
# IMPORT CONFIRMATION SCHEMAS
# ============================================================================

class ImportConfirmRequest(BaseModel):
    """Request to confirm and save imported coin."""
    coin_data: Dict[str, Any] = Field(..., description="Coin data to import")
    source_type: str = Field(..., description="Source type (ngc, ebay, heritage, etc.)")
    source_id: Optional[str] = Field(None, description="Source identifier")
    source_url: Optional[str] = Field(None, description="Source URL")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw scraped data")
    track_price_history: bool = Field(default=False, description="Track price history")
    sold_price_usd: Optional[float] = Field(None, description="Sold price in USD")
    auction_date: Optional[str] = Field(None, description="Auction date")
    auction_house: Optional[str] = Field(None, description="Auction house")
    lot_number: Optional[str] = Field(None, description="Lot number")
    merge_with_coin_id: Optional[int] = Field(None, description="Merge with existing coin ID")

class ImportConfirmResponse(BaseModel):
    """Response after confirming import."""
    success: bool
    coin_id: Optional[int] = None
    error: Optional[str] = None
    merged: bool = False

# ============================================================================
# DEPENDENCIES
# ============================================================================

def get_scraper_orchestrator():
    """Get scraper orchestrator with all scrapers."""
    return ScraperOrchestrator([
        HeritageScraper(headless=True),
        CNGScraper(headless=True),
        BiddrScraper(headless=True),
        EbayScraper(headless=True),
        AgoraScraper(headless=True),
    ])

# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class UrlImportRequest(BaseModel):
    """Request to import from URL."""
    url: str = Field(..., description="Auction or listing URL to scrape")

class NGCImportRequest(BaseModel):
    """Request to import from NGC certificate."""
    cert_number: str = Field(..., description="NGC certification number (7-10 digits)")
    
    @field_validator('cert_number')
    @classmethod
    def validate_cert_format(cls, v: str) -> str:
        v = v.strip()
        # Remove dashes for validation (NGC accepts both formats like "2167888-014")
        v_clean = v.replace('-', '')
        if not v_clean.isdigit():
            raise ValueError("Certificate number must contain only digits (with optional dash)")
        if not (7 <= len(v_clean) <= 10):
            raise ValueError("Certificate number must be 7-10 digits")
        return v  # Return original format, client will clean it


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ImagePreview(BaseModel):
    """Preview data for a coin image."""
    url: str
    source: str = "ngc_photovision"
    image_type: str = "combined"
    is_primary: bool = False
    thumbnail_url: Optional[str] = None
    local_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class CoinSummary(BaseModel):
    """Summary of a coin for duplicate detection display."""
    id: int
    title: str
    thumbnail: Optional[str] = None
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    match_reason: str  # "exact_source" | "ngc_cert" | "physical_match"
    match_confidence: Optional[float] = None
    issuing_authority: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    weight_g: Optional[Decimal] = None
    grade: Optional[str] = None


class CoinPreviewData(BaseModel):
    """All coin fields for preview/edit before import."""
    # Grading (NGC authoritative)
    grade_service: Optional[str] = None
    grade: Optional[str] = None
    strike_quality: Optional[int] = None
    surface_quality: Optional[int] = None
    certification_number: Optional[str] = None
    
    # Description
    description: Optional[str] = None
    title: Optional[str] = None
    
    # Images
    images: List[ImagePreview] = []
    
    # Holder type
    holder_type: Optional[str] = None
    
    # All other fields optional for partial data
    category: Optional[str] = None
    metal: Optional[str] = None
    denomination: Optional[str] = None
    issuing_authority: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    
    # Acquisition/Auction fields
    acquisition_price: Optional[Decimal] = None
    acquisition_source: Optional[str] = None
    acquisition_url: Optional[str] = None
    acquisition_date: Optional[str] = None
    acquisition_currency: Optional[str] = None
    
    # Auction-specific fields
    auction_house: Optional[str] = None
    auction_date: Optional[str] = None
    lot_number: Optional[str] = None
    hammer_price: Optional[Decimal] = None
    total_price: Optional[Decimal] = None
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    currency: Optional[str] = None
    sale_name: Optional[str] = None
    references: List[str] = []


class ImportPreviewResponse(BaseModel):
    """Response for import preview (NGC, URL, etc.)."""
    success: bool
    error: Optional[str] = None
    error_code: Optional[str] = None
    retry_after: Optional[int] = None
    manual_entry_suggested: bool = False
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    coin_data: Optional[CoinPreviewData] = None
    field_confidence: Dict[str, str] = {}  # "high" | "medium" | "low"
    similar_coins: List[CoinSummary] = []
    detected_references: List[str] = []
    enrichment_available: bool = False
    raw_data: Optional[Dict[str, Any]] = None


# --- Enrich preview (Phase 1 stub; Phase 6 will implement real catalog lookup) ---

class EnrichPreviewRequest(BaseModel):
    """Request for catalog enrichment preview. Matches frontend useEnrichPreview."""
    references: List[str] = Field(default_factory=list, description="Reference strings to look up (e.g. RIC I 207)")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (ruler, mint, denomination)")


class EnrichPreviewResponse(BaseModel):
    """Response for enrich-preview. Matches frontend ImportPreviewResponse subset (suggestions, lookup_results)."""
    success: bool = True
    suggestions: Dict[str, Any] = Field(default_factory=dict, description="Field -> {field, value, source, confidence}")
    lookup_results: List[Any] = Field(default_factory=list, description="Per-reference lookup status")


# ============================================================================
# ENRICH PREVIEW (Phase 6: real catalog lookup)
# ============================================================================

def _payload_to_suggestions(payload: Dict[str, Any], source: str = "catalog", confidence: float = 0.9) -> Dict[str, Any]:
    """Map CatalogPayload to EnrichmentPanel suggestion keys. Each value is { value, source, confidence }."""
    out: Dict[str, Any] = {}
    if payload.get("authority"):
        out["issuing_authority"] = {"value": payload["authority"], "source": source, "confidence": confidence}
    if payload.get("mint"):
        out["mint_name"] = {"value": payload["mint"], "source": source, "confidence": confidence}
    if payload.get("date_from") is not None:
        out["mint_year_start"] = {"value": payload["date_from"], "source": source, "confidence": confidence}
    if payload.get("date_to") is not None:
        out["mint_year_end"] = {"value": payload["date_to"], "source": source, "confidence": confidence}
    if payload.get("denomination"):
        out["denomination"] = {"value": payload["denomination"], "source": source, "confidence": confidence}
    if payload.get("obverse_legend"):
        out["obverse_legend"] = {"value": payload["obverse_legend"], "source": source, "confidence": confidence}
    if payload.get("reverse_legend"):
        out["reverse_legend"] = {"value": payload["reverse_legend"], "source": source, "confidence": confidence}
    if payload.get("obverse_description"):
        out["obverse_description"] = {"value": payload["obverse_description"], "source": source, "confidence": confidence}
    if payload.get("reverse_description"):
        out["reverse_description"] = {"value": payload["reverse_description"], "source": source, "confidence": confidence}
    return out


@router.post("/enrich-preview", response_model=EnrichPreviewResponse)
async def enrich_preview(request: EnrichPreviewRequest):
    """
    Look up catalog data for given references and return suggestions for import.
    Uses CatalogRegistry (OCRE/CRRO/RPC) per reference; merges payload into suggestions.
    """
    from src.infrastructure.services.catalogs.registry import CatalogRegistry

    suggestions: Dict[str, Any] = {}
    lookup_results: List[Any] = []

    for ref in (request.references or []):
        ref = (ref or "").strip()
        if not ref:
            continue
        system = CatalogRegistry.detect_system(ref) or "ric"
        try:
            result = await CatalogRegistry.lookup(system, ref, request.context)
        except Exception as e:
            lookup_results.append({
                "reference": ref,
                "status": "error",
                "system": system,
                "confidence": 0.0,
                "error": str(e),
                "external_url": None,
            })
            continue
        lookup_results.append({
            "reference": ref,
            "status": result.status,
            "system": system,
            "confidence": result.confidence or 0.0,
            "error": result.error_message,
            "external_url": result.external_url,
        })
        if result.status == "success" and result.payload:
            for k, v in _payload_to_suggestions(
                result.payload, source=system.upper(), confidence=result.confidence or 0.9
            ).items():
                if k not in suggestions or (suggestions[k].get("confidence") or 0) < (v.get("confidence") or 0):
                    suggestions[k] = v

    return EnrichPreviewResponse(success=True, suggestions=suggestions, lookup_results=lookup_results)


# ============================================================================
# NGC IMPORT ENDPOINT
# ============================================================================

@router.post("/from-ngc", response_model=ImportPreviewResponse)
async def import_from_ngc(
    request: NGCImportRequest,
    db: Session = Depends(get_db),
    ngc_client: NGCClient = Depends(get_ngc_client),
):
    """
    Fetch NGC certificate and return preview data.
    
    Extracts grade, strike/surface scores, designation, and PhotoVision images.
    """
    try:
        cert_data = await ngc_client.lookup_certificate(request.cert_number)
    except InvalidCertificateError as e:
        return ImportPreviewResponse(
            success=False,
            error=str(e),
            error_code="invalid_cert",
            manual_entry_suggested=True,
        )
    except CertificateNotFoundError as e:
        return ImportPreviewResponse(
            success=False,
            error=str(e),
            error_code="not_found",
            manual_entry_suggested=True,
        )
    except NGCTimeoutError:
        return ImportPreviewResponse(
            success=False,
            error="NGC lookup timed out. Please try again.",
            error_code="timeout",
            retry_after=30,
        )
    except NGCRateLimitError as e:
        return ImportPreviewResponse(
            success=False,
            error="Rate limited by NGC. Please wait before trying again.",
            error_code="rate_limit",
            retry_after=e.retry_after,
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error looking up NGC cert {request.cert_number}")
        
        # Check if it's an anti-bot protection error
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg or "anti-bot" in error_msg.lower():
            return ImportPreviewResponse(
                success=False,
                error=(
                    "NGC is blocking automated access (anti-bot protection). "
                    f"You can manually enter the coin data, or try accessing the certificate at: "
                    f"https://www.ngccoin.com/certlookup/{request.cert_number}/"
                ),
                error_code="anti_bot_blocked",
                manual_entry_suggested=True,
            )
        
        return ImportPreviewResponse(
            success=False,
            error=f"NGC lookup failed: {error_msg}",
            error_code="ngc_error",
            manual_entry_suggested=True,
        )
    
    # Map NGC data to preview format
    coin_data = _map_ngc_to_preview(cert_data)
    
    # Check for duplicates by certification number
    coin_repo = SqlAlchemyCoinRepository(db)
    similar_coins = []
    
    # Search for coins with same NGC cert
    try:
        # Query coins with matching certification number
        # Use filters to find coins with matching NGC cert
        from src.domain.coin import GradeService
        matching_coins = coin_repo.get_all(
            limit=100,
            filters={
                "grade_service": "ngc",
            }
        )
        for coin in matching_coins:
            if (coin.grading and 
                coin.grading.service == GradeService.NGC and
                coin.grading.certification_number == request.cert_number):
                similar_coins.append(CoinSummary(
                    id=coin.id or 0,
                    title=f"{coin.attribution.issuer} {coin.denomination or ''}".strip(),
                    match_reason="ngc_cert",
                    match_confidence=1.0,
                    issuing_authority=coin.attribution.issuer,
                    denomination=coin.denomination,
                    metal=coin.metal.value if coin.metal else None,
                    weight_g=coin.dimensions.weight_g,
                    grade=coin.grading.grade,
                ))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error checking duplicates: {e}")
    
    return ImportPreviewResponse(
        success=True,
        source_type="ngc",
        source_id=request.cert_number,
        source_url=cert_data.verification_url,
        coin_data=coin_data,
        field_confidence={
            "grade": "high",
            "strike_quality": "high",
            "surface_quality": "high",
            "certification_number": "high",
            "grade_service": "high",
        },
        similar_coins=similar_coins,
        raw_data=cert_data.model_dump(),
    )


# ============================================================================
# URL IMPORT ENDPOINT
# ============================================================================

@router.post("/from-url", response_model=ImportPreviewResponse)
async def import_from_url(
    request: UrlImportRequest,
    db: Session = Depends(get_db),
    orchestrator: ScraperOrchestrator = Depends(get_scraper_orchestrator),
):
    """
    Scrape auction/listing URL and return preview data.
    
    Supports: Heritage, CNG, eBay, Biddr, Agora
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Normalize URL - trim whitespace
    url = request.url.strip() if request.url else ""
    
    # DEBUG: Write to file
    with open("c:/vibecode/coinstack/backend/import_debug.log", "a") as f:
        import datetime
        f.write(f"\n=== {datetime.datetime.now()} ===\n")
        f.write(f"URL: {url}\n")
        f.write(f"Orchestrator type: {type(orchestrator)}\n")
        f.write(f"Orchestrator scrapers: {[type(s).__name__ for s in orchestrator.scrapers]}\n")
    
    print(f"=== IMPORT API CALLED ===")
    print(f"Received URL import request: '{url}' (length: {len(url)})")
    logger.info(f"Received URL import request: '{url}' (length: {len(url)})")
    
    if not url:
        return ImportPreviewResponse(
            success=False,
            error="URL is required",
            error_code="invalid_url",
            manual_entry_suggested=False,
        )
    
    try:
        print(f"Starting scrape for URL: {url}")
        logger.info(f"Starting scrape for URL: {url}")
        # Scrape the URL
        try:
            with open("c:/vibecode/coinstack/backend/import_debug.log", "a") as f:
                f.write(f"Calling orchestrator.scrape()...\n")
            
            print(f"Calling orchestrator.scrape()...")
            auction_lot = await orchestrator.scrape(url)
            
            with open("c:/vibecode/coinstack/backend/import_debug.log", "a") as f:
                f.write(f"Scrape completed, result: {auction_lot is not None}\n")
                if auction_lot:
                    f.write(f"Auction lot: source={auction_lot.source}, lot_id={auction_lot.lot_id}, issuer={auction_lot.issuer}\n")
            
            print(f"Scrape completed, result: {auction_lot is not None}")
            logger.info(f"Scrape completed, result: {auction_lot is not None}")
            if auction_lot:
                print(f"Auction lot details: source={auction_lot.source}, lot_id={auction_lot.lot_id}, issuer={auction_lot.issuer}")
                logger.info(f"Auction lot details: source={auction_lot.source}, lot_id={auction_lot.lot_id}, issuer={auction_lot.issuer}")
        except Exception as scrape_error:
            logger.exception(f"Error during scrape: {scrape_error}")
            return ImportPreviewResponse(
                success=False,
                error=f"Scraping failed: {str(scrape_error)}",
                error_code="scrape_error",
                manual_entry_suggested=True,
            )
        
        if not auction_lot:
            logger.warning(f"Scraper returned None for URL: {url}")
            # Check which scraper was selected
            selected_scraper = orchestrator.get_scraper(url)
            if selected_scraper:
                scraper_name = type(selected_scraper).__name__
                logger.warning(f"Scraper selected: {scraper_name}, but returned None")
                
                # Provide site-specific error messages
                if "ebay" in url.lower():
                    error_msg = (
                        "eBay is blocking automated access. "
                        "Please manually enter the coin data from the listing, "
                        "or open the URL in your browser to copy the information."
                    )
                else:
                    error_msg = "Failed to scrape URL. The site may be blocking automated access or the URL format is unsupported."
            else:
                logger.error(f"No scraper found for URL: {url}")
                error_msg = "No scraper available for this URL. Supported sites: Heritage, CNG, eBay, Biddr, Agora."
            
            return ImportPreviewResponse(
                success=False,
                error=error_msg,
                error_code="scrape_failed",
                manual_entry_suggested=True,
            )
        
        logger.info(f"Scrape successful, lot_id: {auction_lot.lot_id}, issuer: {auction_lot.issuer}")
        
        # Map AuctionLot to preview format
        coin_data = _map_auction_to_preview(auction_lot)
        
        # Check for duplicates
        coin_repo = SqlAlchemyCoinRepository(db)
        similar_coins = []
        
        try:
            # Simple duplicate check by issuer and weight/diameter if available
            if coin_data.issuing_authority:
                matching_coins = coin_repo.get_all(
                    limit=50,
                    filters={
                        "issuer": coin_data.issuing_authority,
                    }
                )
                for coin in matching_coins:
                    # Check if weight/diameter are similar (within 5%)
                    weight_match = False
                    if coin_data.weight_g and coin.dimensions.weight_g:
                        diff = abs(float(coin_data.weight_g) - float(coin.dimensions.weight_g))
                        if diff / float(coin.dimensions.weight_g) < 0.05:
                            weight_match = True
                    
                    diameter_match = False
                    if coin_data.diameter_mm and coin.dimensions.diameter_mm:
                        diff = abs(float(coin_data.diameter_mm) - float(coin.dimensions.diameter_mm))
                        if diff / float(coin.dimensions.diameter_mm) < 0.05:
                            diameter_match = True
                    
                    if weight_match or diameter_match:
                        similar_coins.append(CoinSummary(
                            id=coin.id or 0,
                            title=f"{coin.attribution.issuer} {coin.denomination or ''}".strip(),
                            match_reason="physical_match",
                            match_confidence=0.8 if (weight_match and diameter_match) else 0.6,
                            issuing_authority=coin.attribution.issuer,
                            denomination=coin.denomination,
                            metal=coin.metal.value if coin.metal else None,
                            weight_g=coin.dimensions.weight_g,
                            grade=coin.grading.grade if coin.grading else None,
                        ))
        except Exception as e:
            logger.warning(f"Error checking duplicates: {e}")
        
        # Determine source type from URL
        source_type = "unknown"
        if "ebay.com" in url.lower():
            source_type = "ebay"
        elif "heritage" in url.lower() or "ha.com" in url.lower():
            source_type = "heritage"
        elif "cng" in url.lower():
            source_type = "cng"
        elif "biddr" in url.lower():
            source_type = "biddr"
        elif "agora" in url.lower():
            source_type = "agora"
        
        return ImportPreviewResponse(
            success=True,
            source_type=source_type,
            source_id=auction_lot.lot_id,
            source_url=url,
            coin_data=coin_data,
            field_confidence={
                "issuing_authority": "high" if coin_data.issuing_authority else "low",
                "weight_g": "high" if coin_data.weight_g else "low",
                "diameter_mm": "high" if coin_data.diameter_mm else "low",
                "grade": "medium" if coin_data.grade else "low",
            },
            similar_coins=similar_coins,
            raw_data={
                "source": auction_lot.source,
                "lot_id": auction_lot.lot_id,
                "url": auction_lot.url,
                "sale_name": auction_lot.sale_name,
                "lot_number": auction_lot.lot_number,
                "issuer": auction_lot.issuer,
                "mint": auction_lot.mint,
                "weight_g": float(auction_lot.weight_g) if auction_lot.weight_g else None,
                "diameter_mm": float(auction_lot.diameter_mm) if auction_lot.diameter_mm else None,
                "grade": auction_lot.grade,
                "hammer_price": float(auction_lot.hammer_price) if auction_lot.hammer_price else None,
            },
        )
        
    except ValueError as e:
        error_msg = str(e)
        logger.warning(f"ValueError scraping URL {url}: {error_msg}")
        return ImportPreviewResponse(
            success=False,
            error=error_msg if error_msg else "Invalid URL or no scraper available for this URL.",
            error_code="invalid_url",
            manual_entry_suggested=True,
        )
    except Exception as e:
        logger.exception(f"Error scraping URL {url}")
        error_msg = str(e)
        
        # Check for anti-bot protection
        if "403" in error_msg or "Forbidden" in error_msg or "blocking" in error_msg.lower():
            return ImportPreviewResponse(
                success=False,
                error=(
                    "The website is blocking automated access (anti-bot protection). "
                    "You can manually enter the coin data from the listing."
                ),
                error_code="anti_bot_blocked",
                manual_entry_suggested=True,
            )
        
        return ImportPreviewResponse(
            success=False,
            error=f"Failed to scrape URL: {error_msg}",
            error_code="scrape_error",
            manual_entry_suggested=True,
        )


def _map_auction_to_preview(auction_lot) -> CoinPreviewData:
    """
    Map AuctionLot to CoinPreviewData for preview/edit.
    """
    # Map images
    images = []
    if auction_lot.primary_image_url:
        images.append(ImagePreview(
            url=auction_lot.primary_image_url,
            source=_get_source_from_url(auction_lot.url),
            image_type="combined",
            is_primary=True,
        ))
    for img_url in (auction_lot.additional_images or []):
        images.append(ImagePreview(
            url=img_url,
            source=_get_source_from_url(auction_lot.url),
            image_type="combined",
            is_primary=False,
        ))
    
    from datetime import date as date_type
    
    # Format auction date if available
    auction_date_str = None
    if auction_lot.auction_date:
        if isinstance(auction_lot.auction_date, date_type):
            auction_date_str = auction_lot.auction_date.isoformat()
        else:
            auction_date_str = str(auction_lot.auction_date)
    
    return CoinPreviewData(
        # Attribution
        issuing_authority=auction_lot.issuer,
        mint=auction_lot.mint,
        year_start=auction_lot.year_start,
        year_end=auction_lot.year_end,
        
        # Physical
        weight_g=auction_lot.weight_g,
        diameter_mm=auction_lot.diameter_mm,
        die_axis=auction_lot.die_axis,
        
        # Grading
        grade=auction_lot.grade,
        grade_service=auction_lot.service,
        
        # Description
        description=auction_lot.description,
        title=auction_lot.sale_name or auction_lot.description,
        
        # Acquisition (from auction)
        acquisition_price=auction_lot.hammer_price,
        acquisition_source=auction_lot.source,
        acquisition_url=auction_lot.url,
        acquisition_date=auction_date_str,
        acquisition_currency=auction_lot.currency,
        
        # Auction-specific fields
        auction_house=auction_lot.source,
        auction_date=auction_date_str,
        lot_number=auction_lot.lot_number or auction_lot.lot_id,
        hammer_price=auction_lot.hammer_price,
        total_price=auction_lot.hammer_price,  # Same as hammer_price for now
        estimate_low=auction_lot.estimate_low,
        estimate_high=auction_lot.estimate_high,
        currency=auction_lot.currency,
        sale_name=auction_lot.sale_name,
        references=[],  # Can be populated from scraped data if available
        
        # Images
        images=images,
    )


def _get_source_from_url(url: str) -> str:
    """Determine image source from URL."""
    url_lower = url.lower()
    if "ebay.com" in url_lower:
        return "ebay"
    elif "heritage" in url_lower or "ha.com" in url_lower:
        return "heritage"
    elif "cng" in url_lower:
        return "cng"
    elif "biddr" in url_lower:
        return "biddr"
    elif "agora" in url_lower:
        return "agora"
    return "uploaded"


def _map_ngc_to_preview(cert_data) -> CoinPreviewData:
    """
    Map NGC certificate data to CoinPreviewData for preview/edit.
    
    Note: NGC data is limited - mainly grading info and images.
    Other fields need to be filled from auction data or manually.
    """
    import re
    
    # Parse strike/surface scores to integers
    strike_quality = None
    surface_quality = None
    
    if cert_data.strike_score:
        match = re.match(r'(\d)/\d', cert_data.strike_score)
        if match:
            strike_quality = int(match.group(1))
    
    if cert_data.surface_score:
        match = re.match(r'(\d)/\d', cert_data.surface_score)
        if match:
            surface_quality = int(match.group(1))
    
    # Build grade string
    grade_parts = []
    if cert_data.designation:
        grade_parts.append(cert_data.designation)
    if cert_data.grade:
        grade_parts.append(cert_data.grade)
        if cert_data.numeric_grade:
            grade_parts[-1] = f"{cert_data.grade} {cert_data.numeric_grade}"
    if cert_data.strike_score and cert_data.surface_score:
        grade_parts.append(f"{cert_data.strike_score}, {cert_data.surface_score}")
    
    grade = " ".join(grade_parts) if grade_parts else None
    
    # Map images
    images = [
        ImagePreview(
            url=img.url,
            source=img.source,
            image_type=img.image_type,
            is_primary=idx == 0,  # First image is primary
        )
        for idx, img in enumerate(cert_data.images)
    ]
    
    return CoinPreviewData(
        # Grading (NGC authoritative)
        grade_service="ngc",
        grade=grade,
        strike_quality=strike_quality,
        surface_quality=surface_quality,
        certification_number=cert_data.cert_number,
        
        # Description (may contain coin details)
        description=cert_data.description,
        title=cert_data.coin_type or cert_data.description,
        
        # Images
        images=images,
        
        # Holder type
        holder_type="ngc_slab",
    )


# ============================================================================
# IMPORT CONFIRMATION ENDPOINT
# ============================================================================

@router.post("/confirm", response_model=ImportConfirmResponse)
async def confirm_import(
    request: ImportConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm and save imported coin to database.
    
    Takes the edited coin data from the preview and creates/updates a coin record.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
        from decimal import Decimal
        from datetime import datetime
        
        coin_repo = SqlAlchemyCoinRepository(db)
        
        # Extract coin data
        data = request.coin_data
        
        # If merging with existing coin, load it first
        if request.merge_with_coin_id:
            logger.info(f"Merging with existing coin ID: {request.merge_with_coin_id}")
            # TODO: Implement proper merge logic
            return ImportConfirmResponse(
                success=False,
                error="Merge functionality not yet implemented",
            )
        
        # Create new coin
        logger.info(f"Creating new coin from {request.source_type}")
        
        # ============================================================================
        # FIELD NORMALIZATION - Convert frontend values to backend enum values
        # ============================================================================
        
        # Normalize category (frontend may send short forms)
        category = data.get("category", "roman_imperial")
        category_map = {
            "imperial": "roman_imperial",
            "republic": "roman_republic", 
            "provincial": "roman_provincial",
        }
        category = category_map.get(category, category)
        
        # Normalize metal (handle common abbreviations)
        metal = data.get("metal", "silver")
        if metal:
            metal = metal.lower().strip()
            metal_map = {
                "ar": "silver",
                "au": "gold",
                "ae": "bronze",
                "bi": "billon",
                "el": "electrum",
                "cu": "copper",
                "pb": "lead",
            }
            metal = metal_map.get(metal, metal)
        
        # Normalize grading_state
        grading_state = data.get("grading_state", "raw")
        if grading_state:
            grading_state = grading_state.lower().strip()
        
        # Normalize grade_service
        grade_service = data.get("grade_service")
        if grade_service:
            grade_service = grade_service.lower().strip()
            if grade_service in ["none", "n/a", "na", ""]:
                grade_service = None
        
        logger.info(f"Normalized values - category: {category}, metal: {metal}, grading_state: {grading_state}, grade_service: {grade_service}")
        
        # ============================================================================
        # BUILD COMPLETE COIN ENTITY - Handle ALL fields from frontend
        # ============================================================================
        from src.application.services.grade_normalizer import normalize_grade_for_storage
        from src.domain.coin import (
            Coin, Dimensions, Attribution, Category, Metal, 
            GradingDetails, GradingState, GradeService, AcquisitionDetails,
            Design, CatalogReference, CoinImage
        )
        
        # Parse enums
        try:
            category_enum = Category(category)
            metal_enum = Metal(metal)
            grading_state_enum = GradingState(grading_state)
            grade_service_enum = GradeService(grade_service) if grade_service else None
        except ValueError as e:
            raise ValueError(f"Invalid enum value: {e}")
        
        # Build value objects
        dimensions = Dimensions(
            weight_g=Decimal(str(data.get("weight_g", 0))) if data.get("weight_g") else Decimal("0"),
            diameter_mm=Decimal(str(data.get("diameter_mm", 0))) if data.get("diameter_mm") else Decimal("0"),
            die_axis=data.get("die_axis")
        )
        
        attribution = Attribution(
            issuer=data.get("issuing_authority") or data.get("issuer") or "Unknown",
            mint=data.get("mint_name"),
            year_start=data.get("mint_year_start") or data.get("year_start"),
            year_end=data.get("mint_year_end") or data.get("year_end")
        )
        
        grading = GradingDetails(
            grading_state=grading_state_enum,
            grade=normalize_grade_for_storage(data.get("grade")) or "Unknown",
            service=grade_service_enum,
            certification_number=data.get("certification_number")
        )
        
        acquisition = None
        if data.get("acquisition_price") or data.get("hammer_price"):
            acquisition = AcquisitionDetails(
                price=Decimal(str(data.get("acquisition_price") or data.get("hammer_price", 0))),
                currency=data.get("acquisition_currency") or data.get("currency") or "USD",
                source=data.get("acquisition_source") or data.get("auction_house") or "Unknown",
                date=None  # TODO: Parse date string
            )
        
        # Build Design object (legends and descriptions)
        design = None
        if any([
            data.get("obverse_legend"),
            data.get("obverse_description"),
            data.get("reverse_legend"),
            data.get("reverse_description"),
            data.get("exergue")
        ]):
            design = Design(
                obverse_legend=data.get("obverse_legend"),
                obverse_description=data.get("obverse_description"),
                reverse_legend=data.get("reverse_legend"),
                reverse_description=data.get("reverse_description"),
                exergue=data.get("exergue")
            )
        
        # Parse references using central parser (catalog, number, volume)
        ref_strings = [str(r).strip() for r in data.get("references", []) if r and str(r).strip()]
        
        # Create complete Coin entity
        new_coin = Coin(
            id=None,
            category=category_enum,
            metal=metal_enum,
            dimensions=dimensions,
            attribution=attribution,
            grading=grading,
            acquisition=acquisition,
            denomination=data.get("denomination"),
            portrait_subject=data.get("portrait_subject"),
            design=design,
            references=[],  # Persisted via ReferenceSyncService after save
            description=data.get("description"),
            personal_notes=data.get("personal_notes"),
            historical_significance=data.get("historical_significance"),
            storage_location=data.get("storage_location"),
            images=[]  # Will add images separately below
        )
        
        # Save to database
        saved_coin = coin_repo.save(new_coin)

        if ref_strings and saved_coin.id:
            from src.application.services.reference_sync import sync_coin_references
            from src.infrastructure.services.catalogs.registry import CatalogRegistry
            external_ids: Dict[str, tuple] = {}
            issuer = (saved_coin.attribution.issuer if saved_coin.attribution else None) or data.get("issuing_authority") or data.get("issuer")
            for ref_str in ref_strings:
                try:
                    system = CatalogRegistry.detect_system(ref_str) or "ric"
                    result = await CatalogRegistry.lookup(system, ref_str, {"ruler": issuer})
                    if result.status == "success" and (getattr(result, "external_id", None) or getattr(result, "external_url", None)):
                        external_ids[ref_str] = (getattr(result, "external_id", None), getattr(result, "external_url", None))
                except Exception as lookup_err:
                    logger.debug("Catalog lookup for import ref %s: %s", ref_str, lookup_err)
            sync_coin_references(db, saved_coin.id, ref_strings, "import", external_ids=external_ids if external_ids else None)
            saved_coin = coin_repo.get_by_id(saved_coin.id) or saved_coin
        
        logger.info(f"Coin created successfully with ID: {saved_coin.id}")
        
        # Add images to the coin if provided
        images = data.get("images", [])
        logger.info(f"Image data received: {images}")
        
        if images and saved_coin.id:
            logger.info(f"Adding {len(images)} images to coin {saved_coin.id}")
            from src.domain.coin import CoinImage
            
            for idx, img_data in enumerate(images):
                logger.info(f"Processing image {idx}: {img_data}")
                # img_data can be a dict with 'url', 'image_type', 'is_primary'
                # or from the frontend ImagePreview format
                if isinstance(img_data, dict):
                    url = img_data.get("url")
                    image_type = img_data.get("image_type") or img_data.get("source") or "unknown"
                    is_primary = img_data.get("is_primary", idx == 0)
                    
                    logger.info(f"  URL: {url}, Type: {image_type}, Primary: {is_primary}")
                    
                    if url:
                        saved_coin.add_image(url, image_type, is_primary)
                        logger.info(f"  Added image to coin. Total images now: {len(saved_coin.images)}")
            
            # Save coin again with images
            logger.info(f"Saving coin with {len(saved_coin.images)} images")
            saved_coin = coin_repo.save(saved_coin)
            logger.info(f"Images saved successfully for coin {saved_coin.id}. Final image count: {len(saved_coin.images)}")
        else:
            logger.warning(f"No images to add. images={bool(images)}, coin_id={saved_coin.id}")
        
        return ImportConfirmResponse(
            success=True,
            coin_id=saved_coin.id,
            merged=False,
        )
        
    except Exception as e:
        logger.exception(f"Error confirming import: {e}")
        return ImportConfirmResponse(
            success=False,
            error=str(e),
        )
