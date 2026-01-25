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

class CoinResponse(BaseModel):
    id: Optional[int]
    category: str
    metal: str
    dimensions: DimensionsResponse
    attribution: AttributionResponse
    grading: GradingResponse
    acquisition: Optional[AcquisitionResponse] = None
    images: List[ImageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def from_domain(coin) -> "CoinResponse":
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
            ]
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
    sort_dir: str = Query("asc", regex="^(asc|desc)$"),
    repo: ICoinRepository = Depends(get_coin_repo)
):
    skip = (page - 1) * per_page
    coins = repo.get_all(skip=skip, limit=per_page, sort_by=sort_by, sort_dir=sort_dir)
    total = repo.count()
    pages = (total + per_page - 1) // per_page
    
    return PaginatedResponse(
        items=[CoinResponse.from_domain(c) for c in coins],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

@router.get("/{coin_id}", response_model=CoinResponse)
def get_coin(
    coin_id: int,
    repo: ICoinRepository = Depends(get_coin_repo)
):
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return CoinResponse.from_domain(coin)

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
            ) if request.acquisition_price is not None else None
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
    if hasattr(repo, 'delete'):
        repo.delete(coin_id)