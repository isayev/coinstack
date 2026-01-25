import pytest
from decimal import Decimal
from src.domain.coin import Coin, Dimensions, Category, Metal, Attribution, GradingDetails, GradingState

class TestCoinEntity:
    def test_create_valid_coin(self):
        dims = Dimensions(weight_g=Decimal("3.5"), diameter_mm=Decimal("18.0"))
        attr = Attribution(issuer="Augustus")
        grading = GradingDetails(grading_state=GradingState.RAW, grade="VF")
        
        coin = Coin(
            id=None,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=dims,
            attribution=attr,
            grading=grading
        )
        assert coin.dimensions.weight_g == Decimal("3.5")
    
    def test_dimensions_validation(self):
        """Domain entity should prevent invalid state."""
        with pytest.raises(ValueError, match="Weight must be positive"):
            Dimensions(weight_g=Decimal("-1.0"), diameter_mm=Decimal("10.0"))

    def test_die_axis_validation(self):
        with pytest.raises(ValueError, match="Die axis"):
            Dimensions(weight_g=Decimal("1"), diameter_mm=Decimal("1"), die_axis=13)
