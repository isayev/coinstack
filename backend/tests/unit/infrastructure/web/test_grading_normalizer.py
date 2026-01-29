"""Unit tests for strike/surface grading normalizer."""
import pytest

from src.infrastructure.web.grading_normalizer import normalize_strike_surface


@pytest.mark.unit
class TestNormalizeStrikeSurface:
    def test_fraction_form(self):
        assert normalize_strike_surface("4/5") == "4"
        assert normalize_strike_surface("5/5") == "5"
        assert normalize_strike_surface("1/5") == "1"
        assert normalize_strike_surface(" 3/5 ") == "3"

    def test_single_digit(self):
        assert normalize_strike_surface("1") == "1"
        assert normalize_strike_surface("5") == "5"
        assert normalize_strike_surface("4") == "4"

    def test_integer(self):
        assert normalize_strike_surface(4) == "4"
        assert normalize_strike_surface(5) == "5"
        assert normalize_strike_surface(1) == "1"

    def test_empty_or_none(self):
        assert normalize_strike_surface(None) is None
        assert normalize_strike_surface("") is None
        assert normalize_strike_surface("   ") is None

    def test_invalid_returns_none(self):
        assert normalize_strike_surface("6") is None
        assert normalize_strike_surface("0") is None
        assert normalize_strike_surface("10") is None
        assert normalize_strike_surface("abc") is None
        assert normalize_strike_surface("4/10") == "4"  # first part is 4, valid
        assert normalize_strike_surface("6/5") is None  # 6 out of range
