import pytest
from decimal import Decimal
from src.domain.coin import Coin, Dimensions, Attribution, Category, Metal, GradingDetails, GradingState
from src.domain.audit import ExternalAuctionData
from src.domain.strategies.date_strategy import DateStrategy

class TestDateStrategy:
    def test_year_start_mismatch(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(weight_g=Decimal("3.50"), diameter_mm=Decimal("18.0")),
            attribution=Attribution("Nero", year_start=54),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            year_start=55
        )
        
        strategy = DateStrategy()
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 1
        assert results[0].field == "year_start"
        assert results[0].current_value == "54"
        assert results[0].auction_value == "55"
