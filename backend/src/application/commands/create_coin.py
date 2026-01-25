from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import date
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal, 
    GradingDetails, GradingState, GradeService, AcquisitionDetails
)
from src.domain.repositories import ICoinRepository

@dataclass
class CreateCoinDTO:
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
    acquisition_price: Optional[Decimal] = None
    acquisition_source: Optional[str] = None
    acquisition_date: Optional[date] = None

class CreateCoinUseCase:
    def __init__(self, repository: ICoinRepository):
        self.repository = repository

    def execute(self, dto: CreateCoinDTO) -> Coin:
        try:
            category = Category(dto.category)
            metal = Metal(dto.metal)
            grading_state = GradingState(dto.grading_state)
            grade_service = GradeService(dto.grade_service) if dto.grade_service else None
        except ValueError as e:
            raise ValueError(f"Invalid enum value: {e}")

        grading = GradingDetails(
            grading_state=grading_state,
            grade=dto.grade,
            service=grade_service,
            certification_number=dto.certification
        )

        acquisition = None
        if dto.acquisition_price is not None:
            acquisition = AcquisitionDetails(
                price=dto.acquisition_price,
                currency="USD", # Default for now
                source=dto.acquisition_source or "Unknown",
                date=dto.acquisition_date
            )

        new_coin = Coin(
            id=None,
            category=category,
            metal=metal,
            dimensions=Dimensions(
                weight_g=dto.weight_g,
                diameter_mm=dto.diameter_mm,
                die_axis=dto.die_axis
            ),
            attribution=Attribution(
                issuer=dto.issuer,
                mint=dto.mint,
                year_start=dto.year_start,
                year_end=dto.year_end
            ),
            grading=grading,
            acquisition=acquisition
        )

        return self.repository.save(new_coin)