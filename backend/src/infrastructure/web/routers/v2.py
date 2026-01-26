from fastapi import APIRouter, Depends, status, Query, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional, List
from datetime import date
from src.domain.repositories import ICoinRepository
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.coin import Coin, Dimensions, Attribution, GradingDetails, AcquisitionDetails, Category, Metal, GradingState, GradeService
from src.infrastructure.web.dependencies import get_coin_repo

router = APIRouter(prefix="/api/v2/coins", tags=["coins"])

# --- Request/Response Models ---
class ImageRequest(BaseModel):
    url: str
    image_type: str
    is_primary: bool = False

class CreateCoinRequest(BaseModel):
    category: str
    metal: str
    weight_g: Decimal
    diameter_mm: Decimal
    issuer: str
    grading_state: str
    grade: str
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    die_axis: Optional[int] = None
    grade_service: Optional[str] = None
    certification: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None
    acquisition_price: Optional[Decimal] = None
    acquisition_source: Optional[str] = None
    acquisition_date: Optional[date] = None
    acquisition_url: Optional[str] = None
    images: List[ImageRequest] = []
    # Collection management
    storage_location: Optional[str] = None
    personal_notes: Optional[str] = None

class DimensionsResponse(BaseModel):
    weight_g: Decimal
    diameter_mm: Decimal
    die_axis: Optional[int] = None

class AttributionResponse(BaseModel):
    issuer: str
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None

class GradingResponse(BaseModel):
    grading_state: str
    grade: str
    service: Optional[str] = None
    certification_number: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None

class AcquisitionResponse(BaseModel):
    price: Decimal
    currency: str
    source: str
    date: Optional[date] = None
    url: Optional[str] = None

class ImageResponse(BaseModel):
    url: str
    image_type: str
    is_primary: bool

class DesignResponse(BaseModel):
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None

class CatalogReferenceResponse(BaseModel):
    catalog: str
    number: str
    volume: Optional[str] = None
    suffix: Optional[str] = None
    raw_text: str = ""

class ProvenanceEntryResponse(BaseModel):
    source_type: str
    source_name: str
    event_date: Optional[date] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None
    raw_text: str = ""

class CoinResponse(BaseModel):
    id: Optional[int]
    category: str
    metal: str
    dimensions: DimensionsResponse
    attribution: AttributionResponse
    grading: GradingResponse
    acquisition: Optional[AcquisitionResponse] = None
    images: List[ImageResponse] = []
    # New fields
    description: Optional[str] = None
    denomination: Optional[str] = None
    portrait_subject: Optional[str] = None
    design: Optional[DesignResponse] = None
    references: List[CatalogReferenceResponse] = []
    provenance: List[ProvenanceEntryResponse] = []
    # Collection management
    storage_location: Optional[str] = None
    personal_notes: Optional[str] = None
    # LLM enrichment
    historical_significance: Optional[str] = None
    llm_enriched_at: Optional[str] = None
    llm_analysis_sections: Optional[str] = None      # JSON-encoded sections
    llm_suggested_references: Optional[List[str]] = None  # Citations found by LLM for audit
    llm_suggested_rarity: Optional[dict] = None      # Rarity info from LLM for audit
    # Navigation helpers
    prev_id: Optional[int] = None
    next_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def from_domain(coin: Coin) -> "CoinResponse":
        return CoinResponse(
            id=coin.id,
            category=coin.category.value,
            metal=coin.metal.value,
            dimensions=DimensionsResponse(
                weight_g=coin.dimensions.weight_g,
                diameter_mm=coin.dimensions.diameter_mm,
                die_axis=coin.dimensions.die_axis
            ),
            attribution=AttributionResponse(
                issuer=coin.attribution.issuer,
                mint=coin.attribution.mint,
                year_start=coin.attribution.year_start,
                year_end=coin.attribution.year_end
            ),
            grading=GradingResponse(
                grading_state=coin.grading.grading_state.value,
                grade=coin.grading.grade,
                service=coin.grading.service.value if coin.grading.service else None,
                certification_number=coin.grading.certification_number,
                strike=coin.grading.strike,
                surface=coin.grading.surface
            ),
            acquisition=AcquisitionResponse(
                price=coin.acquisition.price,
                currency=coin.acquisition.currency,
                source=coin.acquisition.source,
                date=coin.acquisition.date,
                url=coin.acquisition.url
            ) if coin.acquisition else None,
            images=[
                ImageResponse(
                    url=img.url,
                    image_type=img.image_type,
                    is_primary=img.is_primary
                ) for img in coin.images
            ],
            description=coin.description,
            denomination=coin.denomination,
            portrait_subject=coin.portrait_subject,
            design=DesignResponse(
                obverse_legend=coin.design.obverse_legend,
                obverse_description=coin.design.obverse_description,
                reverse_legend=coin.design.reverse_legend,
                reverse_description=coin.design.reverse_description,
                exergue=coin.design.exergue
            ) if coin.design else None,
            references=[
                CatalogReferenceResponse(
                    catalog=ref.catalog,
                    number=ref.number,
                    volume=ref.volume,
                    suffix=ref.suffix,
                    raw_text=ref.raw_text
                ) for ref in coin.references
            ],
            provenance=[
                ProvenanceEntryResponse(
                    source_type=p.source_type,
                    source_name=p.source_name,
                    event_date=p.event_date,
                    lot_number=p.lot_number,
                    notes=p.notes,
                    raw_text=p.raw_text
                ) for p in coin.provenance
            ],
            storage_location=coin.storage_location,
            personal_notes=coin.personal_notes,
            historical_significance=coin.historical_significance,
            llm_enriched_at=coin.llm_enriched_at,
            llm_analysis_sections=coin.llm_analysis_sections,
            llm_suggested_references=coin.llm_suggested_references,
            llm_suggested_rarity=coin.llm_suggested_rarity
        )

@router.post("", status_code=status.HTTP_201_CREATED)
def create_coin(
    request: CreateCoinRequest,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    use_case = CreateCoinUseCase(repo)
    
    # Map images via DTO? The UseCase/DTO needs updating too if we want to pass images.
    # For now, let's create the coin then add images? Or update DTO.
    # Updating DTO is better.
    # But since DTO is simple, we might need to extend it.
    
    # Simplified flow: Create Use Case handles DTO which we haven't updated yet.
    # Let's temporarily just pass basic data, and images support requires DTO update.
    # Or, we update DTO now.
    
    dto = CreateCoinDTO(
        category=request.category,
        metal=request.metal,
        weight_g=request.weight_g,
        diameter_mm=request.diameter_mm,
        issuer=request.issuer,
        grading_state=request.grading_state,
        grade=request.grade,
        mint=request.mint,
        year_start=request.year_start,
        year_end=request.year_end,
        die_axis=request.die_axis,
        grade_service=request.grade_service,
        certification=request.certification,
        acquisition_price=request.acquisition_price,
        acquisition_source=request.acquisition_source,
        acquisition_date=request.acquisition_date,
        # TODO: Add images to DTO
    )
    
    domain_coin = use_case.execute(dto)
    
    return CoinResponse.from_domain(domain_coin)

class PaginatedResponse(BaseModel):
    items: List[CoinResponse]
    total: int
    page: int
    per_page: int
    pages: int

@router.get("", response_model=PaginatedResponse)
def get_coins(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
    ids: Optional[str] = Query(None, description="Comma-separated list of coin IDs to fetch"),
    # Filter parameters
    category: Optional[str] = Query(None, description="Filter by category (e.g., roman_imperial, greek)"),
    metal: Optional[str] = Query(None, description="Filter by metal (e.g., gold, silver, bronze)"),
    denomination: Optional[str] = Query(None, description="Filter by denomination (e.g., denarius, aureus)"),
    grading_state: Optional[str] = Query(None, description="Filter by grading state (raw, slabbed)"),
    grade_service: Optional[str] = Query(None, description="Filter by grading service (ngc, pcgs)"),
    issuer: Optional[str] = Query(None, description="Filter by issuer name (partial match)"),
    year_start: Optional[int] = Query(None, description="Filter by minimum year (negative for BC)"),
    year_end: Optional[int] = Query(None, description="Filter by maximum year (negative for BC)"),
    weight_min: Optional[float] = Query(None, description="Filter by minimum weight in grams"),
    weight_max: Optional[float] = Query(None, description="Filter by maximum weight in grams"),
    repo: ICoinRepository = Depends(get_coin_repo)
):
    """
    Get paginated list of coins with optional filtering.
    
    Filters can be combined. All filters use AND logic.
    If `ids` parameter is provided, returns only those coins (ignores pagination).
    """
    # Handle ids parameter - fetch specific coins
    if ids:
        try:
            coin_ids = [int(id_str.strip()) for id_str in ids.split(",") if id_str.strip()]
            if coin_ids:
                coins = []
                for coin_id in coin_ids:
                    coin = repo.get_by_id(coin_id)
                    if coin:
                        coins.append(coin)
                return PaginatedResponse(
                    items=[CoinResponse.from_domain(c) for c in coins],
                    total=len(coins),
                    page=1,
                    per_page=len(coins),
                    pages=1
                )
        except ValueError:
            # Invalid ids format, fall through to normal query
            pass
    
    skip = (page - 1) * per_page
    
    # Build filters dict
    filters = {}
    if category:
        filters["category"] = category
    if metal:
        filters["metal"] = metal
    if denomination:
        filters["denomination"] = denomination
    if grading_state:
        filters["grading_state"] = grading_state
    if grade_service:
        filters["grade_service"] = grade_service
    if issuer:
        filters["issuer"] = issuer
    if year_start is not None:
        filters["year_start"] = year_start
    if year_end is not None:
        filters["year_end"] = year_end
    if weight_min is not None:
        filters["weight_min"] = weight_min
    if weight_max is not None:
        filters["weight_max"] = weight_max
    
    # Pass filters to repository
    coins = repo.get_all(
        skip=skip, 
        limit=per_page, 
        sort_by=sort_by, 
        sort_dir=sort_dir,
        filters=filters if filters else None
    )
    total = repo.count(filters=filters if filters else None)
    pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        items=[CoinResponse.from_domain(c) for c in coins],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

def _get_neighbor_ids(repo: ICoinRepository, coin_id: int) -> tuple[Optional[int], Optional[int]]:
    """
    Get previous and next coin IDs for navigation.
    
    Uses efficient SQL queries to find neighbors without loading all coins.
    Returns (prev_id, next_id) tuple.
    """
    # Get the coin's position in the collection (sorted by ID)
    # This is a simple but effective approach for navigation
    from src.infrastructure.persistence.database import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # Get previous ID (largest ID less than current)
        prev_result = db.execute(
            text("SELECT id FROM coins_v2 WHERE id < :coin_id ORDER BY id DESC LIMIT 1"),
            {"coin_id": coin_id}
        ).fetchone()
        prev_id = prev_result[0] if prev_result else None
        
        # Get next ID (smallest ID greater than current)
        next_result = db.execute(
            text("SELECT id FROM coins_v2 WHERE id > :coin_id ORDER BY id ASC LIMIT 1"),
            {"coin_id": coin_id}
        ).fetchone()
        next_id = next_result[0] if next_result else None
        
        return prev_id, next_id
    finally:
        db.close()


@router.get("/{coin_id}", response_model=CoinResponse)
def get_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    
    # Calculate neighbor IDs for navigation (efficient query)
    prev_id, next_id = _get_neighbor_ids(repo, coin_id)
    
    response = CoinResponse.from_domain(coin)
    response.prev_id = prev_id
    response.next_id = next_id
    return response

@router.put("/{coin_id}", response_model=CoinResponse)
def update_coin(
    coin_id: int,
    request: CreateCoinRequest,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    existing_coin = repo.get_by_id(coin_id)
    if not existing_coin:
        raise HTTPException(status_code=404, detail="Coin not found")
        
    try:
        updated_coin = Coin(
            id=coin_id,
            category=Category(request.category),
            metal=Metal(request.metal),
            dimensions=Dimensions(
                weight_g=request.weight_g,
                diameter_mm=request.diameter_mm,
                die_axis=request.die_axis
            ),
            attribution=Attribution(
                issuer=request.issuer,
                mint=request.mint,
                year_start=request.year_start,
                year_end=request.year_end
            ),
            grading=GradingDetails(
                grading_state=GradingState(request.grading_state),
                grade=request.grade,
                service=GradeService(request.grade_service) if request.grade_service else None,
                certification_number=request.certification,
                strike=request.strike,
                surface=request.surface
            ),
            acquisition=AcquisitionDetails(
                price=request.acquisition_price,
                currency="USD",
                source=request.acquisition_source or "Unknown",
                date=request.acquisition_date,
                url=request.acquisition_url
            ) if request.acquisition_price is not None else None,
            storage_location=request.storage_location,
            personal_notes=request.personal_notes
        )
        
        # Add images manually here since DTO/UseCase flow is pending update
        from src.domain.coin import CoinImage
        for img in request.images:
            updated_coin.add_image(img.url, img.image_type, img.is_primary)
        
        saved = repo.save(updated_coin)
        return CoinResponse.from_domain(saved)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{coin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    # First check if coin exists
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail=f"Coin {coin_id} not found")
    
    # Perform deletion
    deleted = repo.delete(coin_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete coin")


# --- Reference Search Endpoint ---

class ReferenceSearchResponse(BaseModel):
    """Response for reference search endpoint."""
    coins: List[CoinResponse]
    total: int
    catalog: str
    number: str
    volume: Optional[str] = None


@router.get("/by-reference", response_model=ReferenceSearchResponse)
def get_coins_by_reference(
    catalog: str = Query(..., description="Catalog system (e.g., RIC, Crawford, Sear, RSC, RPC, BMC)"),
    number: str = Query(..., description="Reference number (e.g., 756, 44/5, 1234a)"),
    volume: Optional[str] = Query(None, description="Volume (e.g., II, V.1) - optional"),
    repo: ICoinRepository = Depends(get_coin_repo)
):
    """
    Search for coins by catalog reference.
    
    Examples:
    - /api/v2/coins/by-reference?catalog=RIC&number=756
    - /api/v2/coins/by-reference?catalog=RIC&volume=II&number=756
    - /api/v2/coins/by-reference?catalog=Crawford&number=44/5
    
    Note: This endpoint requires the coin_references table to be populated.
    Currently returns coins where the reference matches in the coin_references table.
    """
    # Use repository method to find coins by reference
    # This will be implemented in the repository update (Phase 6)
    coins = repo.get_by_reference(catalog=catalog, number=number, volume=volume)
    
    return ReferenceSearchResponse(
        coins=[CoinResponse.from_domain(c) for c in coins],
        total=len(coins),
        catalog=catalog,
        number=number,
        volume=volume
    )