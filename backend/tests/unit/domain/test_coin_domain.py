import pytest
from decimal import Decimal
from src.domain.coin import Coin, Dimensions, Category, Metal, Attribution, GradingDetails, GradingState, GradeService, CoinImage

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


class TestCoinImageManagement:
    """Test suite for Coin.add_image() and primary_image property."""

    @pytest.fixture
    def sample_coin(self):
        """Create a sample coin for testing."""
        dims = Dimensions(weight_g=Decimal("3.5"), diameter_mm=Decimal("18.0"))
        attr = Attribution(issuer="Augustus")
        grading = GradingDetails(
            grading_state=GradingState.RAW,
            grade="VF",
            service=GradeService.NONE
        )

        return Coin(
            id=None,
            category=Category.ROMAN_IMPERIAL,
            metal=Metal.SILVER,
            dimensions=dims,
            attribution=attr,
            grading=grading
        )

    def test_add_non_primary_image(self, sample_coin):
        """Adding a non-primary image should append it to the list."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=False)

        assert len(sample_coin.images) == 1
        assert sample_coin.images[0].url == "http://example.com/img1.jpg"
        assert sample_coin.images[0].image_type == "obverse"
        assert sample_coin.images[0].is_primary is False

    def test_add_primary_image_to_empty_list(self, sample_coin):
        """Adding a primary image to empty list should work."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=True)

        assert len(sample_coin.images) == 1
        assert sample_coin.images[0].is_primary is True

    def test_add_primary_image_demotes_existing_primary(self, sample_coin):
        """Adding a new primary image should demote the existing primary."""
        # Add first primary image
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=True)
        assert sample_coin.images[0].is_primary is True

        # Add second primary image
        sample_coin.add_image("http://example.com/img2.jpg", "reverse", is_primary=True)

        # Should have 2 images
        assert len(sample_coin.images) == 2

        # First image should be demoted
        assert sample_coin.images[0].is_primary is False
        assert sample_coin.images[0].url == "http://example.com/img1.jpg"

        # Second image should be primary
        assert sample_coin.images[1].is_primary is True
        assert sample_coin.images[1].url == "http://example.com/img2.jpg"

    def test_only_one_primary_image_allowed(self, sample_coin):
        """Only one image can be primary at any time."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=False)
        sample_coin.add_image("http://example.com/img2.jpg", "reverse", is_primary=True)
        sample_coin.add_image("http://example.com/img3.jpg", "slab", is_primary=True)

        # Count primary images
        primary_count = sum(1 for img in sample_coin.images if img.is_primary)
        assert primary_count == 1

        # Last added image should be primary
        assert sample_coin.images[2].is_primary is True

    def test_primary_image_property_returns_primary(self, sample_coin):
        """primary_image property should return the primary image."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=False)
        sample_coin.add_image("http://example.com/img2.jpg", "reverse", is_primary=True)
        sample_coin.add_image("http://example.com/img3.jpg", "slab", is_primary=False)

        primary = sample_coin.primary_image
        assert primary is not None
        assert primary.url == "http://example.com/img2.jpg"
        assert primary.is_primary is True

    def test_primary_image_property_falls_back_to_first(self, sample_coin):
        """If no primary exists, primary_image should return first image."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=False)
        sample_coin.add_image("http://example.com/img2.jpg", "reverse", is_primary=False)

        primary = sample_coin.primary_image
        assert primary is not None
        assert primary.url == "http://example.com/img1.jpg"

    def test_primary_image_property_returns_none_when_empty(self, sample_coin):
        """If no images exist, primary_image should return None."""
        assert len(sample_coin.images) == 0
        assert sample_coin.primary_image is None

    def test_coin_image_is_frozen(self):
        """CoinImage should be a frozen dataclass."""
        img = CoinImage("http://example.com/img.jpg", "obverse", is_primary=True)

        with pytest.raises(Exception):  # FrozenInstanceError in Python 3.10+
            img.is_primary = False

    def test_multiple_non_primary_images(self, sample_coin):
        """Should be able to add multiple non-primary images."""
        sample_coin.add_image("http://example.com/img1.jpg", "obverse", is_primary=False)
        sample_coin.add_image("http://example.com/img2.jpg", "reverse", is_primary=False)
        sample_coin.add_image("http://example.com/img3.jpg", "edge", is_primary=False)

        assert len(sample_coin.images) == 3
        assert all(not img.is_primary for img in sample_coin.images)
