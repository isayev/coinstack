import pytest
from decimal import Decimal
from src.domain.coin import Coin, GradingDetails, GradingState, Dimensions, Attribution, Category, Metal
from src.domain.audit import AuditEngine, ExternalAuctionData
from src.domain.strategies.grade_strategy import GradeStrategy

class TestAuditEngine:
    def test_grade_discrepancy_found(self):
        # Arrange
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(Decimal("3.0"), Decimal("18.0")),
            attribution=Attribution("Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="123",
            grade="XF"
        )
        
        strategy = GradeStrategy()
        engine = AuditEngine([strategy])

        # Act
        results = engine.run(coin, auction_data)

        # Assert
        assert len(results) == 1
        assert results[0].field == "grade"
        assert results[0].current_value == "VF"
        assert results[0].auction_value == "XF"
        assert results[0].source == "Heritage"

    def test_no_discrepancy_when_match(self):
        coin = Coin(
            id=1,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=Dimensions(Decimal("3.0"), Decimal("18.0")),
            attribution=Attribution("Nero"),
            grading=GradingDetails(GradingState.RAW, "VF")
        )
        
        auction_data = ExternalAuctionData(
            source="Heritage",
            lot_number="123",
            grade="VF"
        )
        
        engine = AuditEngine([GradeStrategy()])
        results = engine.run(coin, auction_data)
        assert len(results) == 0
