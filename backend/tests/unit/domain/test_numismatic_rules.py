import pytest
from decimal import Decimal
from src.domain.coin import (
    Coin, Dimensions, GradingDetails, GradingState, GradeService, 
    AcquisitionDetails, EnrichmentData
)

class TestNumismaticRules:
    def test_dimensions_validation(self):
        """Test that invalid dimensions raise ValueError."""
        # Negative weight
        with pytest.raises(ValueError, match="Weight must be positive"):
            Dimensions(diameter_mm=Decimal("19.0"), weight_g=Decimal("-1.0"))
            
        # Negative diameter
        with pytest.raises(ValueError, match="Diameter must be positive"):
            Dimensions(diameter_mm=Decimal("-19.0"), weight_g=Decimal("3.5"))
            
        # Invalid die axis (must be 0-12)
        with pytest.raises(ValueError, match="Die axis must be between 0 and 12"):
            Dimensions(diameter_mm=Decimal("19.0"), die_axis=13)
            
        # Valid dimensions
        d = Dimensions(diameter_mm=Decimal("19.0"), weight_g=Decimal("3.5"), die_axis=6)
        assert d.diameter_mm == Decimal("19.0")

    def test_slabbed_coins_require_service(self):
        """Test that SLABBED grading state requires a service."""
        with pytest.raises(ValueError, match="Slabbed coins must have a grading service specified"):
            GradingDetails(
                grading_state=GradingState.SLABBED,
                grade="XF",
                service=None
            )
            
        # Valid slabbed
        g = GradingDetails(
            grading_state=GradingState.SLABBED,
            grade="XF",
            service=GradeService.NGC
        )
        assert g.service == GradeService.NGC

    def test_acquisition_negative_price(self):
        """Test that acquisition price cannot be negative."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            AcquisitionDetails(
                price=Decimal("-10.00"),
                currency="USD",
                source="eBay"
            )

    def test_enrichment_data_immutability(self):
        """Test that EnrichmentData is immutable (slots=True, frozen=True)."""
        enrichment = EnrichmentData(
            historical_significance="Rare coin",
            suggested_references=["RIC 123"]
        )
        
        # Verify attribute access
        assert enrichment.historical_significance == "Rare coin"
        
        # Verify immutability
        with pytest.raises(AttributeError):
            enrichment.historical_significance = "Changed"
