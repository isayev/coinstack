import pytest
from decimal import Decimal
from datetime import date
from src.domain.coin import (
    Coin, Dimensions, Attribution, Category, Metal,
    GradingDetails, GradingState, GradeService, AcquisitionDetails
)
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

def test_repository_full_persistence(db_session):
    repo = SqlAlchemyCoinRepository(db_session)
    
    # Create Full Domain Entity
    new_coin = Coin(
        id=None,
        category=Category.ROMAN_IMPERIAL,
        metal=Metal.SILVER,
        dimensions=Dimensions(weight_g=Decimal("3.52"), diameter_mm=Decimal("18.5")),
        attribution=Attribution(issuer="Trajan", year_start=98, year_end=117),
        grading=GradingDetails(
            grading_state=GradingState.SLABBED,
            service=GradeService.NGC,
            grade="Ch XF",
            strike="5/5",
            surface="4/5",
            certification_number="123456-001"
        ),
        acquisition=AcquisitionDetails(
            price=Decimal("250.00"),
            currency="USD",
            source="Heritage Auctions",
            date=date(2023, 5, 15)
        )
    )
    
    # Save
    saved_coin = repo.save(new_coin)
    
    assert saved_coin.id is not None
    assert saved_coin.grading.service == GradeService.NGC
    assert saved_coin.acquisition.price == Decimal("250.00")
    
    # Retrieve
    fetched_coin = repo.get_by_id(saved_coin.id)
    assert fetched_coin is not None
    assert fetched_coin.grading.grade == "Ch XF"
    assert fetched_coin.grading.strike == "5/5"
    assert fetched_coin.acquisition.source == "Heritage Auctions"
