from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import date
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, GradingState, GradeService, AcquisitionDetails,
    IssueStatus, DieInfo, FindData, Design, CoinImage
)
from src.domain.repositories import ICoinRepository

@dataclass
class ImageDTO:
    url: str
    image_type: str
    is_primary: bool = False

@dataclass
class DesignDTO:
    obverse_legend: Optional[str] = None
    obverse_description: Optional[str] = None
    reverse_legend: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None

@dataclass
class CreateCoinDTO:
    category: str
    metal: str
    diameter_mm: Decimal
    issuer: str
    grading_state: str
    grade: str
    weight_g: Optional[Decimal] = None
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
    
    # Extensions & New Fields
    denomination: Optional[str] = None
    portrait_subject: Optional[str] = None
    design: Optional[DesignDTO] = None
    
    # Research Grade Extensions
    specific_gravity: Optional[Decimal] = None
    issue_status: str = "official"
    obverse_die_id: Optional[str] = None
    reverse_die_id: Optional[str] = None
    find_spot: Optional[str] = None
    find_date: Optional[date] = None
    
    # Lists
    images: List[ImageDTO] = field(default_factory=list)

class CreateCoinUseCase:
    def __init__(self, repository: ICoinRepository):
        self.repository = repository

    def execute(self, dto: CreateCoinDTO) -> Coin:
        try:
            category = Category(dto.category)
            metal = Metal(dto.metal)
            grading_state = GradingState(dto.grading_state)
            grade_service = GradeService(dto.grade_service) if dto.grade_service else None
            issue_status = IssueStatus(dto.issue_status) if dto.issue_status else IssueStatus.OFFICIAL
        except ValueError as e:
            raise ValueError(f"Invalid enum value: {e}")

        grading = GradingDetails(
            grading_state=grading_state,
            grade=dto.grade,
            service=grade_service,
            certification_number=dto.certification,
            strike=dto.strike,
            surface=dto.surface,
        )

        acquisition = None
        if dto.acquisition_price is not None:
            acquisition = AcquisitionDetails(
                price=dto.acquisition_price,
                currency="USD", # Default for now
                source=dto.acquisition_source or "Unknown",
                date=dto.acquisition_date,
                url=dto.acquisition_url
            )

        # Build Design value object
        design = None
        if dto.design:
            design = Design(
                obverse_legend=dto.design.obverse_legend,
                obverse_description=dto.design.obverse_description,
                reverse_legend=dto.design.reverse_legend,
                reverse_description=dto.design.reverse_description,
                exergue=dto.design.exergue
            )

        # Map Images
        images = [
            CoinImage(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
            for img in dto.images
        ]

        new_coin = Coin(
            id=None,
            category=category,
            metal=metal,
            dimensions=Dimensions(
                weight_g=dto.weight_g,
                diameter_mm=dto.diameter_mm,
                die_axis=dto.die_axis,
                specific_gravity=dto.specific_gravity
            ),
            attribution=Attribution(
                issuer=dto.issuer,
                mint=dto.mint,
                year_start=dto.year_start,
                year_end=dto.year_end
            ),
            grading=grading,
            acquisition=acquisition,
            
            # New Fields
            denomination=dto.denomination,
            portrait_subject=dto.portrait_subject,
            design=design,
            images=images,
            
            # Extensions
            issue_status=issue_status,
            die_info=DieInfo(
                obverse_die_id=dto.obverse_die_id,
                reverse_die_id=dto.reverse_die_id
            ) if (dto.obverse_die_id or dto.reverse_die_id) else None,
            find_data=FindData(
                find_spot=dto.find_spot,
                find_date=dto.find_date
            ) if (dto.find_spot or dto.find_date) else None
        )

        return self.repository.save(new_coin)