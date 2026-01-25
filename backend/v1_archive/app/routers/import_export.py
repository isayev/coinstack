"""Import/Export API router with URL scraping, NGC lookup, and preview support."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
import logging
from typing import List, Optional, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel

from app.database import get_db
from app.services.excel_import import import_collection_file
from app.services.duplicate_detector import DuplicateDetector, get_duplicate_detector
from app.services.ngc_connector import (
    NGCConnector, 
    get_ngc_connector,
    InvalidCertificateError,
    CertificateNotFoundError,
    NGCTimeoutError,
    NGCRateLimitError,
)
from app.services.scrapers.orchestrator import AuctionOrchestrator
from app.services.reference_parser import parse_references
from app.models import Coin, ImportRecord
from app.models.mint import Mint
from app.models.image import CoinImage, ImageType
from app.models.price_history import PriceHistory
from app.data.rulers import get_reign_dates
from app.schemas.import_preview import (
    URLImportRequest,
    NGCImportRequest,
    DuplicateCheckRequest,
    CoinImportConfirm,
    ImportPreviewResponse,
    DuplicateCheckResponse,
    ImportConfirmResponse,
    CoinPreviewData,
    ImagePreview,
    ImageSource,
    ImageType as PreviewImageType,
    FieldConfidence,
    CoinSummary,
)
from app.services.catalogs.registry import CatalogRegistry
from app.services.catalogs.base import CatalogPayload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/import", tags=["import"])


class BackfillResult(BaseModel):
    """Result of backfill operation."""
    updated: int
    skipped: int
    not_found: List[str]


@router.post("/backfill-reign-dates", response_model=BackfillResult)
async def backfill_reign_dates(
    dry_run: bool = False,
    db: Session = Depends(get_db),
):
    """Backfill reign dates for coins based on issuing_authority.
    
    Uses the built-in ruler database to lookup reign dates.
    Only updates coins that don't already have reign dates set.
    """
    # Get coins without reign dates
    coins = db.query(Coin).filter(
        (Coin.reign_start.is_(None)) | (Coin.reign_end.is_(None))
    ).all()
    
    updated = 0
    skipped = 0
    not_found = set()
    
    for coin in coins:
        if not coin.issuing_authority:
            skipped += 1
            continue
        
        reign_start, reign_end = get_reign_dates(coin.issuing_authority)
        
        if reign_start is not None and reign_end is not None:
            if not dry_run:
                coin.reign_start = reign_start
                coin.reign_end = reign_end
            updated += 1
        else:
            not_found.add(coin.issuing_authority)
            skipped += 1
    
    if not dry_run:
        db.commit()
    
    return BackfillResult(
        updated=updated,
        skipped=skipped,
        not_found=sorted(list(not_found)),
    )


@router.post("/collection")
async def import_collection(
    file: UploadFile = File(...),
    dry_run: bool = False,
    db: Session = Depends(get_db),
):
    """Import collection from CSV or Excel file."""
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload CSV or Excel file.",
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    try:
        result = await import_collection_file(db, tmp_path, dry_run=dry_run)
        return result.to_dict()
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()


# ============================================================================
# URL IMPORT
# ============================================================================

def get_orchestrator() -> AuctionOrchestrator:
    """Get configured orchestrator instance."""
    return AuctionOrchestrator(timeout=30.0)


def map_lot_data_to_preview(lot_data, source: str) -> CoinPreviewData:
    """Map scraped lot data to CoinPreviewData."""
    images = []
    
    # Map photos to ImagePreview
    if lot_data.photos:
        source_enum = ImageSource.HERITAGE
        if source.lower() == "cng":
            source_enum = ImageSource.CNG
        elif source.lower() == "ebay":
            source_enum = ImageSource.EBAY
        elif source.lower() == "biddr":
            source_enum = ImageSource.BIDDR
        elif source.lower() == "roma":
            source_enum = ImageSource.ROMA
        elif source.lower() == "agora":
            source_enum = ImageSource.AGORA
        
        for i, url in enumerate(lot_data.photos):
            img_type = PreviewImageType.COMBINED
            # Try to determine if obverse or reverse
            url_lower = url.lower()
            if 'obv' in url_lower or 'front' in url_lower:
                img_type = PreviewImageType.OBVERSE
            elif 'rev' in url_lower or 'back' in url_lower:
                img_type = PreviewImageType.REVERSE
            
            images.append(ImagePreview(
                url=url,
                source=source_enum,
                image_type=img_type,
            ))
    
    # Parse references from description
    references = []
    if lot_data.description:
        try:
            parsed_refs = parse_references(lot_data.description)
            references = [ref.local_ref for ref in parsed_refs]
        except Exception:
            pass
    
    return CoinPreviewData(
        # Classification - need to extract from description/title
        title=lot_data.title,
        description=lot_data.description,
        
        # Physical
        weight_g=Decimal(str(lot_data.weight_g)) if lot_data.weight_g else None,
        diameter_mm=Decimal(str(lot_data.diameter_mm)) if lot_data.diameter_mm else None,
        
        # Grading
        grade_service=lot_data.grade_service.lower() if lot_data.grade_service else None,
        grade=lot_data.grade,
        certification_number=lot_data.certification_number,
        
        # Auction data
        auction_house=lot_data.house,
        sale_name=lot_data.sale_name,
        lot_number=lot_data.lot_number,
        auction_date=lot_data.auction_date,
        hammer_price=Decimal(str(lot_data.hammer_price)) if lot_data.hammer_price else None,
        total_price=Decimal(str(lot_data.total_price)) if lot_data.total_price else None,
        estimate_low=Decimal(str(lot_data.estimate_low)) if lot_data.estimate_low else None,
        estimate_high=Decimal(str(lot_data.estimate_high)) if lot_data.estimate_high else None,
        currency=lot_data.currency or "USD",
        sold=lot_data.sold,
        
        # Acquisition
        acquisition_source=lot_data.house,
        acquisition_url=lot_data.url,
        acquisition_date=lot_data.auction_date,
        acquisition_price=Decimal(str(lot_data.total_price or lot_data.hammer_price)) if (lot_data.total_price or lot_data.hammer_price) else None,
        
        # Images
        images=images,
        
        # References
        references=references,
    )


def calculate_field_confidence(lot_data, source: str) -> dict[str, FieldConfidence]:
    """Calculate confidence levels for parsed fields."""
    confidence = {}
    
    # Physical measurements are usually reliable
    if lot_data.weight_g:
        confidence["weight_g"] = FieldConfidence.HIGH
    if lot_data.diameter_mm:
        confidence["diameter_mm"] = FieldConfidence.HIGH
    
    # Auction data is reliable
    confidence["hammer_price"] = FieldConfidence.HIGH
    confidence["auction_house"] = FieldConfidence.HIGH
    confidence["lot_number"] = FieldConfidence.HIGH
    confidence["auction_date"] = FieldConfidence.HIGH
    
    # Grade from slab is high confidence
    if lot_data.grade_service:
        confidence["grade"] = FieldConfidence.HIGH
        confidence["certification_number"] = FieldConfidence.HIGH
    else:
        # Dealer grade is medium confidence
        confidence["grade"] = FieldConfidence.MEDIUM
    
    # Title/description need verification
    confidence["title"] = FieldConfidence.MEDIUM
    confidence["description"] = FieldConfidence.MEDIUM
    
    # Fields that need manual verification
    confidence["issuing_authority"] = FieldConfidence.LOW
    confidence["denomination"] = FieldConfidence.LOW
    confidence["metal"] = FieldConfidence.LOW
    confidence["category"] = FieldConfidence.LOW
    
    return confidence


@router.post("/from-url", response_model=ImportPreviewResponse)
async def import_from_url(
    request: URLImportRequest,
    db: Session = Depends(get_db),
):
    """
    Parse auction URL and return structured preview data.
    
    Supported sources: Heritage, CNG, eBay, Biddr, Roma, Agora
    """
    url = request.url
    orchestrator = get_orchestrator()
    
    # 1. Detect source
    source = orchestrator.detect_house(url)
    if source is None:
        return ImportPreviewResponse(
            success=False,
            error="Unsupported URL. Supported: Heritage, CNG, eBay, Biddr, Roma, Agora",
            error_code="unsupported_url",
            manual_entry_suggested=True,
        )
    
    # 2. Scrape with error handling
    try:
        result = await orchestrator.scrape_url(url)
    except Exception as e:
        logger.exception(f"Error scraping {url}")
        return ImportPreviewResponse(
            success=False,
            error=f"Could not parse {source} page: {str(e)}",
            error_code="scrape_error",
            manual_entry_suggested=True,
        )
    
    if result.status == "error":
        return ImportPreviewResponse(
            success=False,
            error=result.error_message,
            error_code="scrape_error",
            source_type=source.lower(),
        )
    
    if not result.lot_data:
        return ImportPreviewResponse(
            success=False,
            error="No data extracted from page",
            error_code="no_data",
            source_type=source.lower(),
            manual_entry_suggested=True,
        )
    
    # 3. Map to preview schema
    coin_data = map_lot_data_to_preview(result.lot_data, source)
    
    # 4. Calculate field confidence
    field_confidence = calculate_field_confidence(result.lot_data, source)
    
    # 5. Check for duplicates
    detector = get_duplicate_detector(db)
    similar_coins = detector.check_duplicate(
        source_type=source.lower(),
        source_id=result.lot_data.lot_id,
        weight_g=coin_data.weight_g,
        issuing_authority=coin_data.issuing_authority,
    )
    
    # 6. Detect catalog references
    detected_refs = coin_data.references if coin_data.references else []
    
    return ImportPreviewResponse(
        success=True,
        source_type=source.lower(),
        source_id=result.lot_data.lot_id,
        source_url=url,
        coin_data=coin_data,
        field_confidence=field_confidence,
        similar_coins=similar_coins,
        detected_references=detected_refs,
        enrichment_available=len(detected_refs) > 0,
        raw_data=result.lot_data.model_dump() if result.lot_data else None,
    )


# ============================================================================
# NGC IMPORT
# ============================================================================

@router.post("/from-ngc", response_model=ImportPreviewResponse)
async def import_from_ngc(
    request: NGCImportRequest,
    db: Session = Depends(get_db),
):
    """
    Fetch NGC certificate and return preview data.
    
    Extracts grade, strike/surface scores, designation, and PhotoVision images.
    """
    ngc = get_ngc_connector()
    
    try:
        cert_data = await ngc.lookup_certificate(request.cert_number)
    except InvalidCertificateError as e:
        return ImportPreviewResponse(
            success=False,
            error=str(e),
            error_code="invalid_cert",
        )
    except CertificateNotFoundError as e:
        return ImportPreviewResponse(
            success=False,
            error=str(e),
            error_code="not_found",
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
        logger.exception(f"Error looking up NGC cert {request.cert_number}")
        return ImportPreviewResponse(
            success=False,
            error=f"NGC lookup failed: {str(e)}",
            error_code="ngc_error",
        )
    
    # Map to preview data
    coin_data = ngc.map_to_preview(cert_data)
    
    # Check for duplicates
    detector = get_duplicate_detector(db)
    similar_coins = detector.check_duplicate(
        source_type="ngc",
        source_id=request.cert_number,
        ngc_cert=request.cert_number,
    )
    
    return ImportPreviewResponse(
        success=True,
        source_type="ngc",
        source_id=request.cert_number,
        source_url=cert_data.verification_url,
        coin_data=coin_data,
        field_confidence={
            "grade": FieldConfidence.HIGH,
            "strike_quality": FieldConfidence.HIGH,
            "surface_quality": FieldConfidence.HIGH,
            "certification_number": FieldConfidence.HIGH,
            "grade_service": FieldConfidence.HIGH,
        },
        similar_coins=similar_coins,
        raw_data=cert_data.model_dump(),
    )


# ============================================================================
# DUPLICATE CHECK
# ============================================================================

@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(
    request: DuplicateCheckRequest,
    db: Session = Depends(get_db),
):
    """Check for potential duplicate coins before import."""
    detector = get_duplicate_detector(db)
    similar_coins = detector.check_duplicate(
        source_type=request.source_type,
        source_id=request.source_id,
        ngc_cert=request.ngc_cert,
        weight_g=request.weight_g,
        diameter_mm=request.diameter_mm,
        issuing_authority=request.issuing_authority,
        denomination=request.denomination,
    )
    
    return DuplicateCheckResponse(
        has_duplicates=len(similar_coins) > 0,
        similar_coins=similar_coins,
    )


# ============================================================================
# IMPORT CONFIRMATION
# ============================================================================

@router.post("/confirm", response_model=ImportConfirmResponse)
async def confirm_import(
    data: CoinImportConfirm,
    db: Session = Depends(get_db),
):
    """
    Create coin from previewed/edited data.
    
    Handles:
    - Creating new coin or merging with existing
    - Storing import provenance
    - Adding to price history if auction data available
    - Downloading and storing images
    """
    try:
        merged = False
        
        if data.merge_with_coin_id:
            # Merge with existing coin
            coin = db.query(Coin).get(data.merge_with_coin_id)
            if not coin:
                return ImportConfirmResponse(
                    success=False,
                    error="Coin to merge with not found",
                )
            coin = update_coin_from_preview(coin, data.coin_data)
            merged = True
        else:
            # Create new coin
            coin = create_coin_from_preview(db, data.coin_data)
            db.add(coin)
            db.flush()  # Get coin ID
        
        # Store import provenance
        import_record = ImportRecord(
            coin_id=coin.id,
            source_type=data.source_type,
            source_id=data.source_id,
            source_url=data.source_url,
            raw_data=data.raw_data,
            import_method="url_scrape" if data.source_type != "ngc" else "ngc_lookup",
        )
        db.add(import_record)
        
        # Add to price history if tracking enabled and price available
        if data.track_price_history and data.sold_price_usd and data.auction_date:
            price_record = PriceHistory(
                coin_id=coin.id,
                price_usd=data.sold_price_usd,
                price_date=data.auction_date,
                source="auction",
                source_name=data.auction_house,
                lot_number=data.lot_number,
                url=data.source_url,
            )
            db.add(price_record)
        
        # Store images (URLs for now, download can be done async)
        for i, img in enumerate(data.coin_data.images):
            # Determine image type
            img_type = ImageType.OBVERSE if img.image_type.value == "obverse" else (
                ImageType.REVERSE if img.image_type.value == "reverse" else ImageType.OTHER
            )
            
            coin_image = CoinImage(
                coin_id=coin.id,
                image_type=img_type,
                file_path=img.url,  # Store URL, download later
                is_primary=(i == 0),
                source_url=img.url,
                source_house=img.source.value,
            )
            db.add(coin_image)
        
        db.commit()
        
        return ImportConfirmResponse(
            success=True,
            coin_id=coin.id,
            merged=merged,
        )
        
    except Exception as e:
        logger.exception("Error confirming import")
        db.rollback()
        return ImportConfirmResponse(
            success=False,
            error=str(e),
        )


def create_coin_from_preview(db: Session, data: CoinPreviewData) -> Coin:
    """Create a new Coin from preview data."""
    from app.models.coin import Category, Metal, GradeService, HolderType, Rarity
    
    # Map category
    category = None
    if data.category:
        try:
            category = Category(data.category.lower())
        except ValueError:
            category = Category.OTHER
    else:
        category = Category.OTHER
    
    # Map metal
    metal = None
    if data.metal:
        try:
            metal = Metal(data.metal.lower())
        except ValueError:
            metal = Metal.UNCERTAIN
    else:
        metal = Metal.UNCERTAIN
    
    # Map grade service
    grade_service = None
    if data.grade_service:
        try:
            grade_service = GradeService(data.grade_service.lower())
        except ValueError:
            pass
    
    # Map holder type
    holder_type = None
    if data.holder_type:
        try:
            holder_type = HolderType(data.holder_type.lower())
        except ValueError:
            pass
    
    # Map rarity
    rarity = None
    if data.rarity:
        try:
            rarity = Rarity(data.rarity.lower())
        except ValueError:
            pass
    
    # Handle mint
    mint_id = data.mint_id
    if not mint_id and data.mint_name:
        # Try to find existing mint or create new one
        mint = db.query(Mint).filter(Mint.name == data.mint_name).first()
        if not mint:
            mint = Mint(name=data.mint_name)
            db.add(mint)
            db.flush()
        mint_id = mint.id
    
    coin = Coin(
        # Classification
        category=category,
        sub_category=data.sub_category,
        denomination=data.denomination or "Unknown",
        metal=metal,
        series=data.series,
        
        # People
        issuing_authority=data.issuing_authority or "Unknown",
        portrait_subject=data.portrait_subject,
        status=data.status,
        
        # Chronology
        reign_start=data.reign_start,
        reign_end=data.reign_end,
        mint_year_start=data.mint_year_start,
        mint_year_end=data.mint_year_end,
        is_circa=data.is_circa,
        dating_notes=data.dating_notes,
        
        # Physical
        weight_g=data.weight_g,
        diameter_mm=data.diameter_mm,
        diameter_min_mm=data.diameter_min_mm,
        thickness_mm=data.thickness_mm,
        die_axis=data.die_axis,
        is_test_cut=data.is_test_cut,
        
        # Design
        obverse_legend=data.obverse_legend,
        obverse_legend_expanded=data.obverse_legend_expanded,
        obverse_description=data.obverse_description,
        obverse_symbols=data.obverse_symbols,
        reverse_legend=data.reverse_legend,
        reverse_legend_expanded=data.reverse_legend_expanded,
        reverse_description=data.reverse_description,
        reverse_symbols=data.reverse_symbols,
        exergue=data.exergue,
        
        # Mint
        mint_id=mint_id,
        officina=data.officina,
        
        # Grading
        grade_service=grade_service,
        grade=data.grade,
        strike_quality=data.strike_quality,
        surface_quality=data.surface_quality,
        certification_number=data.certification_number,
        eye_appeal=data.eye_appeal,
        toning_description=data.toning_description,
        style_notes=data.style_notes,
        
        # Acquisition
        acquisition_date=data.acquisition_date,
        acquisition_price=data.acquisition_price,
        acquisition_currency=data.acquisition_currency,
        acquisition_source=data.acquisition_source,
        acquisition_url=data.acquisition_url,
        
        # Valuation
        estimate_low=data.estimate_low,
        estimate_high=data.estimate_high,
        estimated_value_usd=data.estimated_value_usd,
        
        # Storage
        holder_type=holder_type,
        storage_location=data.storage_location,
        for_sale=data.for_sale or False,
        
        # Research
        rarity=rarity,
        rarity_notes=data.rarity_notes,
        historical_significance=data.historical_significance,
        personal_notes=data.personal_notes,
        provenance_notes=data.provenance_notes,
    )
    
    return coin


def update_coin_from_preview(coin: Coin, data: CoinPreviewData) -> Coin:
    """Update existing coin with preview data (for merge)."""
    # Only update fields that have values in the preview data
    fields_to_update = [
        "denomination", "metal", "series", "issuing_authority", "portrait_subject",
        "status", "reign_start", "reign_end", "mint_year_start", "mint_year_end",
        "weight_g", "diameter_mm", "die_axis", "obverse_legend", "obverse_description",
        "reverse_legend", "reverse_description", "exergue", "grade", "grade_service",
        "strike_quality", "surface_quality", "certification_number",
        "acquisition_date", "acquisition_price", "acquisition_source", "acquisition_url",
    ]
    
    for field in fields_to_update:
        value = getattr(data, field, None)
        if value is not None:
            setattr(coin, field, value)
    
    coin.updated_at = datetime.utcnow()
    return coin


# ============================================================================
# ENRICHMENT FOR IMPORT PREVIEW
# ============================================================================

class EnrichPreviewRequest(BaseModel):
    """Request to enrich import preview data from catalog references."""
    references: List[str]  # List of reference strings like ["RIC II 756", "BMC 123"]
    context: Optional[dict] = None  # Optional context for better matching


class EnrichmentField(BaseModel):
    """A single enrichment field suggestion."""
    field: str
    value: Any
    source: str  # Which reference provided this
    confidence: float = 1.0


class EnrichPreviewResponse(BaseModel):
    """Response with enrichment suggestions for import preview."""
    success: bool
    error: Optional[str] = None
    
    # Fields that can fill empty values
    suggestions: dict[str, EnrichmentField] = {}
    
    # All lookup results for debugging
    lookup_results: List[dict] = []


@router.post("/enrich-preview", response_model=EnrichPreviewResponse)
async def enrich_preview(
    request: EnrichPreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Look up catalog references and return enrichment suggestions for import preview.
    
    Unlike /catalog/enrich/{coin_id}, this works before a coin is created.
    It takes reference strings and returns suggested field values.
    """
    if not request.references:
        return EnrichPreviewResponse(
            success=False,
            error="No references provided"
        )
    
    suggestions: dict[str, EnrichmentField] = {}
    lookup_results: List[dict] = []
    
    # Rate limiting
    import asyncio
    
    for ref_str in request.references[:5]:  # Limit to 5 references
        try:
            # Parse reference
            parsed = parse_references(ref_str)
            if not parsed:
                lookup_results.append({
                    "reference": ref_str,
                    "status": "parse_error",
                    "error": "Could not parse reference"
                })
                continue
            
            parsed_ref = parsed[0]  # Take first parsed reference
            system = parsed_ref.system
            
            if not system:
                lookup_results.append({
                    "reference": ref_str,
                    "status": "unknown_system",
                    "error": "Unknown reference system"
                })
                continue
            
            # Rate limit between lookups
            await asyncio.sleep(1.0)
            
            # Look up in catalog
            result = await CatalogRegistry.lookup(
                system=system,
                reference=ref_str,
                context=request.context
            )
            
            lookup_results.append({
                "reference": ref_str,
                "system": system,
                "status": result.status,
                "external_id": result.external_id,
                "external_url": result.external_url,
                "confidence": result.confidence,
            })
            
            # Extract payload if successful
            if result.status == "success" and result.payload:
                payload = CatalogPayload(**result.payload)
                
                # Map payload fields to coin fields
                field_mapping = [
                    ("issuing_authority", payload.authority, "authority"),
                    ("denomination", payload.denomination, "denomination"),
                    ("mint_name", payload.mint, "mint"),
                    ("mint_year_start", payload.date_from, "date_from"),
                    ("mint_year_end", payload.date_to, "date_to"),
                    ("obverse_description", payload.obverse_description, "obverse_description"),
                    ("obverse_legend", payload.obverse_legend, "obverse_legend"),
                    ("reverse_description", payload.reverse_description, "reverse_description"),
                    ("reverse_legend", payload.reverse_legend, "reverse_legend"),
                    ("metal", payload.material, "material"),
                ]
                
                for coin_field, catalog_value, source_field in field_mapping:
                    if catalog_value and coin_field not in suggestions:
                        suggestions[coin_field] = EnrichmentField(
                            field=coin_field,
                            value=catalog_value,
                            source=f"{system.upper()}: {ref_str}",
                            confidence=result.confidence,
                        )
            
            # If ambiguous, still try to get data from best candidate
            elif result.status == "ambiguous" and result.candidates:
                best = result.candidates[0]
                if best.external_id:
                    service = CatalogRegistry.get_service(system)
                    if service:
                        try:
                            await asyncio.sleep(1.0)  # Rate limit
                            jsonld = await service.fetch_type_data(best.external_id)
                            if jsonld:
                                payload = service.parse_payload(jsonld)
                                
                                # Add with lower confidence
                                field_mapping = [
                                    ("issuing_authority", payload.authority),
                                    ("denomination", payload.denomination),
                                    ("mint_name", payload.mint),
                                    ("obverse_description", payload.obverse_description),
                                    ("reverse_description", payload.reverse_description),
                                ]
                                
                                for coin_field, catalog_value in field_mapping:
                                    if catalog_value and coin_field not in suggestions:
                                        suggestions[coin_field] = EnrichmentField(
                                            field=coin_field,
                                            value=catalog_value,
                                            source=f"{system.upper()}: {ref_str} (best match)",
                                            confidence=best.confidence * 0.8,
                                        )
                        except Exception as e:
                            logger.warning(f"Failed to fetch candidate data: {e}")
                            
        except Exception as e:
            logger.exception(f"Error looking up reference {ref_str}")
            lookup_results.append({
                "reference": ref_str,
                "status": "error",
                "error": str(e)
            })
    
    return EnrichPreviewResponse(
        success=True,
        suggestions=suggestions,
        lookup_results=lookup_results,
    )


# Need to import these
from pydantic import BaseModel
from typing import Any


# ============================================================================
# BATCH IMPORT
# ============================================================================

class BatchURLImportRequest(BaseModel):
    """Request to batch import from multiple URLs."""
    urls: List[str]  # List of auction URLs


class BatchPreviewItem(BaseModel):
    """Single item in batch preview results."""
    url: str
    success: bool
    error: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    title: Optional[str] = None
    thumbnail: Optional[str] = None
    preview: Optional[ImportPreviewResponse] = None


class BatchURLImportResponse(BaseModel):
    """Response from batch URL import."""
    total: int
    successful: int
    failed: int
    items: List[BatchPreviewItem]


@router.post("/batch-urls", response_model=BatchURLImportResponse)
async def batch_import_urls(
    request: BatchURLImportRequest,
    db: Session = Depends(get_db),
):
    """
    Batch parse multiple auction URLs and return preview data for each.
    
    Rate limited to prevent overwhelming auction sites.
    Maximum 10 URLs per request.
    """
    import asyncio
    
    urls = request.urls[:10]  # Limit to 10 URLs
    orchestrator = get_orchestrator()
    detector = get_duplicate_detector(db)
    
    items: List[BatchPreviewItem] = []
    successful = 0
    failed = 0
    
    for url in urls:
        # Rate limit between requests
        await asyncio.sleep(2.0)
        
        # Detect source
        source = orchestrator.detect_house(url)
        if source is None:
            items.append(BatchPreviewItem(
                url=url,
                success=False,
                error="Unsupported URL",
            ))
            failed += 1
            continue
        
        try:
            # Scrape
            result = await orchestrator.scrape_url(url)
            
            if result.status == "error" or not result.lot_data:
                items.append(BatchPreviewItem(
                    url=url,
                    success=False,
                    error=result.error_message or "Failed to parse",
                    source_type=source.lower(),
                ))
                failed += 1
                continue
            
            # Map to preview
            coin_data = map_lot_data_to_preview(result.lot_data, source)
            field_confidence = calculate_field_confidence(result.lot_data, source)
            
            # Check duplicates
            similar_coins = detector.check_duplicate(
                source_type=source.lower(),
                source_id=result.lot_data.lot_id,
                weight_g=coin_data.weight_g,
                issuing_authority=coin_data.issuing_authority,
            )
            
            # Detect references
            detected_refs = coin_data.references if coin_data.references else []
            
            # Build full preview response
            preview = ImportPreviewResponse(
                success=True,
                source_type=source.lower(),
                source_id=result.lot_data.lot_id,
                source_url=url,
                coin_data=coin_data,
                field_confidence=field_confidence,
                similar_coins=similar_coins,
                detected_references=detected_refs,
                enrichment_available=len(detected_refs) > 0,
                raw_data=result.lot_data.model_dump() if result.lot_data else None,
            )
            
            # Get thumbnail
            thumbnail = None
            if coin_data.images:
                thumbnail = coin_data.images[0].url
            
            items.append(BatchPreviewItem(
                url=url,
                success=True,
                source_type=source.lower(),
                source_id=result.lot_data.lot_id,
                title=coin_data.title or f"{coin_data.issuing_authority} {coin_data.denomination}".strip(),
                thumbnail=thumbnail,
                preview=preview,
            ))
            successful += 1
            
        except Exception as e:
            logger.exception(f"Error processing batch URL {url}")
            items.append(BatchPreviewItem(
                url=url,
                success=False,
                error=str(e),
                source_type=source.lower() if source else None,
            ))
            failed += 1
    
    return BatchURLImportResponse(
        total=len(urls),
        successful=successful,
        failed=failed,
        items=items,
    )
