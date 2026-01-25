import pytest
from decimal import Decimal
from src.domain.coin import Coin, Dimensions, Attribution, Category, Metal, GradingDetails, GradingState
from src.domain.audit import ExternalAuctionData
from src.domain.strategies.physics_strategy import PhysicsStrategy

class TestPhysicsStrategy:
    def test_weight_discrepancy(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(weight_g=Decimal("3.50"), diameter_mm=Decimal("18.0")),
            attribution=Attribution("Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        # Weight difference > 0.05
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            weight_g=Decimal("3.60")
        )
        
        strategy = PhysicsStrategy(weight_tolerance=Decimal("0.05"))
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 1
        assert results[0].field == "weight_g"

    def test_weight_within_tolerance(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(weight_g=Decimal("3.50"), diameter_mm=Decimal("18.0")),
            attribution=Attribution("Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        # Weight difference <= 0.05
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            weight_g=Decimal("3.54")
        )
        
        strategy = PhysicsStrategy(weight_tolerance=Decimal("0.05"))
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 0

    def test_die_axis_mismatch(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(weight_g=Decimal("3.50"), diameter_mm=Decimal("18.0"), die_axis=6),
            attribution=Attribution("Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="1",
            die_axis=12
        )
        
        strategy = PhysicsStrategy()
        results = strategy.audit(coin, auction_data)
        
        assert len(results) == 1
        assert results[0].field == "die_axis"
