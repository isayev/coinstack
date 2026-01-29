"""Unit tests for central catalog reference parser (parse_catalog_reference)."""
import pytest
from src.infrastructure.services.catalogs.parser import (
    parse_catalog_reference,
    parse_catalog_reference_full,
    parser,
    ParseResult,
    canonical,
)


def test_parse_ric():
    out = parse_catalog_reference("RIC II 756")
    assert out["catalog"] == "RIC"
    assert out["number"] == "756"
    assert out["volume"] is not None


def test_parse_crawford():
    out = parse_catalog_reference("Crawford 335/1c")
    assert out["catalog"] == "RRC"
    assert out["number"]
    assert "335" in (out["number"] or "") or "1" in (out["number"] or "")


def test_parse_rpc():
    out = parse_catalog_reference("RPC I 4122")
    assert out["catalog"] == "RPC"
    assert out["volume"] is not None
    assert out["number"] == "4122"


def test_parse_rsc():
    out = parse_catalog_reference("RSC 162")
    assert out["catalog"] == "RSC"
    assert out["number"] == "162"


def test_parse_fallback():
    out = parse_catalog_reference("UnknownCatalog 99")
    assert out["catalog"] == "UNKNOWNCATALOG"
    assert out["number"] == "99"


def test_parse_empty():
    out = parse_catalog_reference("")
    assert out["catalog"] is None
    assert out["number"] is None
    assert out["volume"] is None


def test_parser_singleton_parse_result():
    result = parser.parse("RIC IV 289c")
    assert isinstance(result, ParseResult)
    assert result.system == "ric"
    assert result.number == "289"
    assert result.subtype == "c"


# --- Golden: dict shape unchanged for existing callers ---


def test_parse_catalog_reference_dict_shape():
    """parse_catalog_reference returns dict with catalog, volume, number (no extra keys required)."""
    out = parse_catalog_reference("RIC II 756")
    assert set(out.keys()) >= {"catalog", "volume", "number"}
    assert out["catalog"] == "RIC"
    assert out["volume"] == "II"  # Roman
    assert out["number"] == "756"


def test_parse_catalog_reference_ric_volume_roman():
    """RIC volume in API dict is Roman (I, II, IV.1) for consistency."""
    assert parse_catalog_reference("RIC 1 207")["volume"] == "I"
    assert parse_catalog_reference("RIC 2 756")["volume"] == "II"
    assert parse_catalog_reference("RIC IV.1 351b")["volume"] == "IV.1"


# --- Canonical: equivalent refs produce same string ---


def test_canonical_from_dict():
    """canonical(dict) produces display + volume + number."""
    c = canonical({"catalog": "RIC", "volume": "IV.1", "number": "351b"})
    assert c == "RIC IV.1 351b"


def test_canonical_equivalent_refs_same_string():
    """Equivalent refs in different forms produce the same canonical string (for dedupe)."""
    parsed1 = parse_catalog_reference("RIC IV-1 351 b")
    parsed2 = parse_catalog_reference("RIC IV.1 351b")
    c1 = canonical(parsed1)
    c2 = canonical(parsed2)
    assert c1 == c2, f"Expected same canonical: {c1!r} vs {c2!r}"


def test_canonical_dict_and_parsed_match():
    """canonical(dict from API) matches canonical(parse_catalog_reference(string))."""
    raw = "Crawford 335/1c"
    parsed = parse_catalog_reference(raw)
    c_parsed = canonical(parsed)
    c_dict = canonical({"catalog": "RRC", "volume": None, "number": "335/1c"})
    assert c_parsed == c_dict


# --- parse_catalog_reference_full ---


def test_parse_catalog_reference_full_returns_parse_result():
    """parse_catalog_reference_full returns ParseResult with confidence and warnings."""
    result = parse_catalog_reference_full("RIC I 207")
    assert isinstance(result, ParseResult)
    assert result.system == "ric"
    assert result.confidence >= 0.0
    assert hasattr(result, "warnings")
