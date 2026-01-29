"""Unit tests for central catalog reference parser (parse_catalog_reference)."""
import pytest
from src.infrastructure.services.catalogs.parser import parse_catalog_reference, parser, ParseResult


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
