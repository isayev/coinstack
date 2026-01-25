import pytest
from decimal import Decimal
from src.domain.coin import Coin, Attribution, Dimensions, Category, Metal, GradingDetails, GradingState
from src.domain.audit import ExternalAuctionData
from src.domain.strategies.attribution_strategy import AttributionStrategy

class TestAttributionStrategy:
    def test_issuer_mismatch(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(Decimal("3.0"), Decimal("18.0")),
            attribution=Attribution(issuer="Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            issuer="Claudius" # Mismatch
        )
        
        strategy = AttributionStrategy()
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 1
        assert results[0].field == "issuer"
        assert results[0].current_value == "Nero"
        assert results[0].auction_value == "Claudius"

    def test_mint_match(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(Decimal("3.0"), Decimal("18.0")),
            attribution=Attribution(issuer="Nero", mint="Rome"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            issuer="Nero",
            mint="Rome"
        )
        
        strategy = AttributionStrategy()
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 0