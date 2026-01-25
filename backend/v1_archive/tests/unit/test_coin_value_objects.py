import pytest
from decimal import Decimal
from datetime import date
from src.domain.coin import GradingDetails, AcquisitionDetails, GradeService, GradingState

class TestValueObjects:
    def test_grading_details_valid(self):
        grading = GradingDetails(
            grading_state=GradingState.SLABBED,
            service=GradeService.NGC,
            grade="XF",
            certification_number="12345-001"
        )
        assert grading.service == GradeService.NGC

    def test_grading_validation_slabbed_needs_service(self):
        """If a coin is slabbed, it must have a service."""
        # This is a domain rule we might want to enforce
        with pytest.raises(ValueError, match="Service required for slabbed coins"):
            GradingDetails(
                grading_state=GradingState.SLABBED,
                service=None, # Invalid
                grade="XF"
            )

    def test_acquisition_details_positive_price(self):
        with pytest.raises(ValueError, match="Price cannot be negative"):
            AcquisitionDetails(
                price=Decimal("-10.00"),
                currency="USD",
                source="eBay",
                date=date(2023, 1, 1)
            )

    def test_acquisition_future_date_warning(self):
        # Maybe not an error, but let's just ensure basic creation works
        acq = AcquisitionDetails(
            price=Decimal("100.00"),
            currency="USD",
            source="Heritage",
            date=date(2023, 1, 1)
        )
        assert acq.currency == "USD"
