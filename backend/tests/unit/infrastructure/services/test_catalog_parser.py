"""Unit tests for central catalog reference parser (parse_catalog_reference)."""
import pytest
from src.infrastructure.services.catalogs.parser import (
    _parse_result_to_dict,
    canonical,
    parse_catalog_reference,
    parse_catalog_reference_full,
    parser,
    ParseResult,
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
    """Unrecognized strings return 7-key dict with None catalog/number (no heuristic fallback)."""
    out = parse_catalog_reference("UnknownCatalog 99")
    assert out["catalog"] is None
    assert out["number"] is None
    assert out["volume"] is None


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


def test_canonical_includes_supplement():
    """canonical() includes supplement so RPC I S 123 and RPC I 123 get distinct local_ref."""
    c_no_supp = canonical({"catalog": "RPC", "volume": "I", "number": "123"})
    c_with_supp = canonical({"catalog": "RPC", "volume": "I", "supplement": "S", "number": "123"})
    assert c_no_supp == "RPC I 123"
    assert c_with_supp == "RPC I S 123"
    assert c_no_supp != c_with_supp


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


def test_parse_catalog_reference_full_returns_subtype():
    """parse_catalog_reference_full returns ParseResult with subtype (variant) when present."""
    result = parse_catalog_reference_full("RIC IV.1 351b")
    assert isinstance(result, ParseResult)
    assert result.system == "ric"
    assert result.subtype == "b"
    assert result.number == "351"


def test_parse_catalog_reference_matches_parse_result_to_dict():
    """parse_catalog_reference(raw) returns same catalog/volume/number as _parse_result_to_dict(full)."""
    raw = "RIC II 756"
    full = parse_catalog_reference_full(raw)
    expected = _parse_result_to_dict(full)
    out = parse_catalog_reference(raw)
    assert out.get("catalog") == expected.get("catalog")
    assert out.get("volume") == expected.get("volume")
    assert out.get("number") == expected.get("number")


# --- Phase A: RIC mint, RPC supplement, Crawford hyphen/no-space/range ---


def test_ric_with_mint():
    """RIC with optional mint: VII Ticinum 123, IV.1 Antioch 351b."""
    result = parse_catalog_reference_full("RIC VII Ticinum 123")
    assert result.system == "ric"
    assert result.volume == "VII"
    assert result.number == "123"
    assert result.mint == "Ticinum"
    result2 = parse_catalog_reference_full("RIC IV.1 Antioch 351b")
    assert result2.system == "ric"
    assert result2.volume == "IV.1"
    assert result2.number == "351"
    assert result2.subtype == "b"
    assert result2.mint == "Antioch"
    out = parse_catalog_reference("RIC VII Ticinum 123")
    assert out.get("mint") == "Ticinum"
    assert out.get("catalog") == "RIC"
    assert out.get("number") == "123"


def test_rpc_with_supplement():
    """RPC with supplement S, S2, S3."""
    result = parse_catalog_reference_full("RPC I S 123")
    assert result.system == "rpc"
    assert result.volume == "I"
    assert result.number == "123"
    assert result.supplement == "S"
    result2 = parse_catalog_reference_full("RPC I S2 456")
    assert result2.supplement == "S2"
    assert result2.number == "456"
    out = parse_catalog_reference("RPC I S 123")
    assert out.get("supplement") == "S"
    assert canonical(out) == "RPC I S 123"


def test_crawford_hyphen_and_range():
    """Crawford: 335-1c normalized to 335/1; variant in subtype; 235/1a-c stores first variant + warning."""
    result = parse_catalog_reference_full("Crawford 335-1c")
    assert result.system == "crawford"
    assert result.number == "335/1"
    assert result.subtype == "c"
    assert (result.number or "") + (result.subtype or "") == "335/1c"
    assert "Hyphen" in (result.warnings or [""])[0]
    result2 = parse_catalog_reference_full("Crawford 235/1a-c")
    assert result2.system == "crawford"
    assert result2.number == "235/1"
    assert result2.subtype == "a"
    assert any("Range" in w for w in (result2.warnings or []))
    out = parse_catalog_reference("Crawford 335-1c")
    assert out.get("number") == "335/1c"
    assert out.get("catalog") == "RRC"


# --- Phase B: DOC parser ---


def test_parse_doc():
    """DOC (Die Orientierung der Kaiserporträts): volume 1-5 + number + optional variant."""
    out = parse_catalog_reference("DOC 1 234")
    assert out["catalog"] == "DOC"
    assert out["volume"] == "I"
    assert out["number"] == "234"
    out2 = parse_catalog_reference("DOC 3 567a")
    assert out2["catalog"] == "DOC"
    assert out2["volume"] == "III"
    assert out2["number"] == "567a"
    result = parse_catalog_reference_full("DOC II 100")
    assert result.system == "doc"
    assert result.volume == "II"
    assert result.number == "100"
    assert canonical(out) == "DOC I 234"
    assert canonical(out2) == "DOC III 567a"


# --- Parser review: edge cases and functionality ---


@pytest.mark.parametrize(
    "raw,expected_catalog,expected_number",
    [
        ("RIC I 207", "RIC", "207"),
        ("ric ii 756", "RIC", "756"),
        ("RIC IV.1 351b", "RIC", "351b"),
        ("RIC V.II 325", "RIC", "325"),
        ("RIC IV-1 351", "RIC", "351"),
        ("RIC IV/1 351", "RIC", "351"),
        ("RIC 1 207", "RIC", "207"),
        ("RIC 2.3 430", "RIC", "430"),
        ("RIC II-123", "RIC", "123"),
        ("RPC I 4122", "RPC", "4122"),
        ("RPC I/5678", "RPC", "5678"),
        ("RPC 1 5678", "RPC", "5678"),
        ("RPC I S 123", "RPC", "123"),
        ("RPC I S2 456", "RPC", "456"),
        ("Crawford 335/1c", "RRC", "335/1c"),
        ("Cr. 335/1", "RRC", "335/1"),
        ("RRC 335/1c", "RRC", "335/1c"),
        ("RSC 162", "RSC", "162"),
        ("RSC II 240", "RSC", "240"),
        ("DOC 1 234", "DOC", "234"),
        ("DOC III 567a", "DOC", "567a"),
        ("BMCRE 123", "BMCRE", "123"),
        ("BMC 456a", "BMCRE", "456a"),
        ("Sear 6846", "Sear", "6846"),
        ("SCV 6846", "Sear", "6846"),
        ("Sydenham 123", "Sydenham", "123"),
        ("Syd. 456", "Sydenham", "456"),
        ("SNG Cop 123", "SNG", "123"),
        ("SNG ANS 336", "SNG", "336"),
        ("BMCRR 100", "BMCRR", "100"),
        ("BMC RR 200a", "BMCRR", "200a"),
        ("Cohen 382", "Cohen", "382"),
        ("Cohen I 123a", "Cohen", "123a"),
        ("Calicó 123", "Calicó", "123"),
        ("Cal. 456", "Calicó", "456"),
    ],
)
def test_parser_happy_path_variants(raw, expected_catalog, expected_number):
    """All parsers accept common real-world variants (case, punctuation, aliases)."""
    out = parse_catalog_reference(raw)
    assert out.get("catalog") == expected_catalog
    assert out.get("number") == expected_number or expected_number in (out.get("number") or "")


def test_sear_requires_sear_or_scv_not_bare_s():
    """Sear parser does not match bare 'S 123' to avoid confusion with RPC supplement."""
    out = parse_catalog_reference("S 123")
    # Should not be parsed as Sear (no longer matches); fallback or unknown
    assert out.get("catalog") != "Sear"
    out_sear = parse_catalog_reference("Sear 123")
    assert out_sear.get("catalog") == "Sear"
    assert out_sear.get("number") == "123"
    out_scv = parse_catalog_reference("SCV 123")
    assert out_scv.get("catalog") == "Sear"
    assert out_scv.get("number") == "123"


def test_ric_volume_alternatives_same_canonical():
    """RIC IV.1, IV-1, IV/1 produce same canonical string."""
    c1 = canonical(parse_catalog_reference("RIC IV.1 351b"))
    c2 = canonical(parse_catalog_reference("RIC IV-1 351b"))
    c3 = canonical(parse_catalog_reference("RIC IV/1 351b"))
    assert c1 == c2 == c3 == "RIC IV.1 351b"


def test_ric_volume_edition_parenthesized():
    """RIC I (2) 207 and RIC I(2) 207 parse (parenthesized edition, common in OCRE citations)."""
    for raw in ("RIC I (2) 207", "RIC I(2) 207"):
        result = parse_catalog_reference_full(raw)
        assert result.system == "ric"
        assert result.volume == "I.2"
        assert result.number == "207"
    out = parse_catalog_reference("RIC I (2) 207")
    assert out.get("catalog") == "RIC"
    assert out.get("volume") == "I.2"
    assert out.get("number") == "207"


def test_ric_volume_part_roman_numeral():
    """RIC V.II 325 (Roman part) parses and normalizes to V.2 for canonical/OCRE lookup."""
    result = parse_catalog_reference_full("RIC V.II 325")
    assert result.system == "ric"
    assert result.volume == "V.2"
    assert result.number == "325"
    out = parse_catalog_reference("RIC V.II 325")
    assert out.get("catalog") == "RIC"
    assert out.get("volume") == "V.2"
    assert out.get("number") == "325"
    c = canonical(out)
    assert c == "RIC V.2 325"


def test_ric_edition_superscript():
    """RIC with edition ² or ³ produces volume with .2 or .3."""
    out = parse_catalog_reference_full("RIC I² 207a")
    assert out.system == "ric"
    assert out.volume == "I.2"
    assert out.number == "207"
    assert out.subtype == "a"
    out3 = parse_catalog_reference_full("RIC II³ 430")
    assert out3.volume == "II.3"
    assert out3.number == "430"


def test_ric_unknown_mint_title_case():
    """RIC with unknown mint name gets title case from parser."""
    result = parse_catalog_reference_full("RIC VII SomeMint 123")
    assert result.mint == "Somemint"
    result2 = parse_catalog_reference_full("RIC II rome 756")
    assert result2.mint == "Rome"


def test_crawford_bare_format_warning():
    """Bare 335/1 or 335-1 without prefix gets Crawford with warning."""
    r1 = parse_catalog_reference_full("335/1c")
    assert r1.system == "crawford"
    assert r1.number == "335/1"
    assert r1.subtype == "c"
    assert any("confirm" in (w or "").lower() or "Bare" in (w or "") for w in (r1.warnings or []))
    r2 = parse_catalog_reference_full("335-1c")
    assert r2.system == "crawford"
    assert any("hyphen" in (w or "").lower() or "Bare" in (w or "") for w in (r2.warnings or []))


def test_crawford_no_subnumber():
    """Crawford Cr 123 (no subnumber) parses as single number."""
    out = parse_catalog_reference("Cr 123")
    assert out.get("catalog") == "RRC"
    assert out.get("number") == "123"


def test_rpc_no_volume_warning():
    """RPC 5678 (no volume) parses with warning."""
    result = parse_catalog_reference_full("RPC 5678")
    assert result.system == "rpc"
    assert result.volume is None
    assert result.number == "5678"
    assert any("without volume" in (w or "").lower() for w in (result.warnings or []))


def test_rsc_with_and_without_volume():
    """RSC with volume has volume; RSC 162 without volume has warning."""
    out_vol = parse_catalog_reference("RSC II 240")
    assert out_vol.get("volume") == "II"
    assert out_vol.get("number") == "240"
    r_novol = parse_catalog_reference_full("RSC 162")
    assert r_novol.system == "rsc"
    assert r_novol.volume is None
    assert r_novol.number == "162"
    assert any("without volume" in (w or "").lower() for w in (r_novol.warnings or []))


def test_doc_volume_bounds():
    """DOC only accepts volumes 1-5; DOC 6 or DOC VI returns None from DOC parser."""
    assert parse_catalog_reference("DOC 1 1").get("catalog") == "DOC"
    assert parse_catalog_reference("DOC 5 999").get("catalog") == "DOC"
    # DOC 6 or DOC VI should not match DOC (volume out of range)
    from src.infrastructure.services.catalogs.parsers.doc import parse as parse_doc
    assert parse_doc("DOC 6 1") is None
    assert parse_doc("DOC VI 1") is None
    assert parse_doc("DOC IX 1") is None


def test_doc_roman_volume_i_v():
    """DOC I through V (roman) parse correctly."""
    assert parse_catalog_reference("DOC I 1")["volume"] == "I"
    assert parse_catalog_reference("DOC V 1")["volume"] == "V"
    assert parse_catalog_reference("DOC III 100")["volume"] == "III"


def test_bmcre_bmc_alias():
    """BMCRE and BMC both map to BMCRE system."""
    assert parse_catalog_reference("BMCRE 100")["catalog"] == "BMCRE"
    assert parse_catalog_reference("BMC 100")["catalog"] == "BMCRE"
    assert parse_catalog_reference("BMC 100a")["number"] == "100a"


def test_sydenham_syd_alias():
    """Sydenham and Syd. parse to Sydenham."""
    assert parse_catalog_reference("Sydenham 100")["catalog"] == "Sydenham"
    assert parse_catalog_reference("Syd. 100")["catalog"] == "Sydenham"
    assert parse_catalog_reference("Syd 100")["catalog"] == "Sydenham"


def test_parser_precedence_ric_before_doc():
    """RIC and DOC have distinct prefixes; correct parser wins."""
    assert parse_catalog_reference("RIC II 756")["catalog"] == "RIC"
    assert parse_catalog_reference("DOC 2 756")["catalog"] == "DOC"


def test_rpc_supplement_precedence():
    """RPC I S 123 is RPC with supplement, not RPC I number 123."""
    out = parse_catalog_reference("RPC I S 123")
    assert out.get("catalog") == "RPC"
    assert out.get("supplement") == "S"
    assert out.get("number") == "123"
    assert canonical(out) == "RPC I S 123"


def test_parse_result_dict_has_seven_keys():
    """parse_catalog_reference returns dict with catalog, volume, number, variant, mint, supplement, collection."""
    out = parse_catalog_reference("RIC II 756")
    assert set(out.keys()) == {
        "catalog", "volume", "number", "variant", "mint", "supplement", "collection",
    }
    out2 = parse_catalog_reference("RPC I S 123")
    assert out2.get("supplement") == "S"
    out3 = parse_catalog_reference("RIC VII Ticinum 123")
    assert out3.get("mint") == "Ticinum"


def test_empty_and_whitespace():
    """Empty and whitespace-only input returns null catalog."""
    assert parse_catalog_reference("").get("catalog") is None
    assert parse_catalog_reference("   ").get("catalog") is None
    result = parse_catalog_reference_full("")
    assert result.raw == ""
    assert result.system is None


def test_canonical_with_mint():
    """canonical() includes mint when present (RIC VII Ticinum 123)."""
    out = parse_catalog_reference("RIC VII Ticinum 123")
    c = canonical(out)
    assert "Ticinum" in c
    assert c == "RIC VII Ticinum 123"


def test_crawford_no_space_prefix():
    """Crawford335/1c (no space after Crawford) parses as Crawford."""
    out = parse_catalog_reference("Crawford335/1c")
    assert out.get("catalog") == "RRC"
    assert "335" in (out.get("number") or "") and "1" in (out.get("number") or "")


# --- New catalogs: SNG, BMCRR, Cohen, Calicó ---


def test_parse_sng_with_collection():
    """SNG (Sylloge Nummorum Graecorum): SNG [collection] number; collection in ref."""
    out = parse_catalog_reference("SNG Cop 123")
    assert out["catalog"] == "SNG"
    assert out["collection"] == "Cop"
    assert out["number"] == "123"
    out2 = parse_catalog_reference("SNG ANS 336")
    assert out2["catalog"] == "SNG"
    assert out2["collection"] == "ANS"
    assert out2["number"] == "336"
    out3 = parse_catalog_reference("SNG Fitzwilliam 789a")
    assert out3["collection"] == "Fitzwilliam"
    assert out3["number"] == "789a"
    assert canonical(out) == "SNG Cop 123"
    assert canonical(out2) == "SNG ANS 336"


def test_parse_bmcrr():
    """BMCRR (British Museum Roman Republic): BMCRR 123 or BMC RR 123."""
    out = parse_catalog_reference("BMCRR 123")
    assert out["catalog"] == "BMCRR"
    assert out["number"] == "123"
    out2 = parse_catalog_reference("BMC RR 456a")
    assert out2["catalog"] == "BMCRR"
    assert out2["number"] == "456a"
    assert parse_catalog_reference("BMCRE 100")["catalog"] == "BMCRE"
    assert parse_catalog_reference("BMCRR 100")["catalog"] == "BMCRR"


def test_parse_cohen():
    """Cohen (Roman Imperial): Cohen 382, Cohen 382a, Cohen I 123."""
    out = parse_catalog_reference("Cohen 382")
    assert out["catalog"] == "Cohen"
    assert out["number"] == "382"
    out2 = parse_catalog_reference("Cohen 382a")
    assert out2["number"] == "382a"
    out3 = parse_catalog_reference("Cohen I 123")
    assert out3["volume"] == "I"
    assert out3["number"] == "123"
    r = parse_catalog_reference_full("Cohen 400")
    assert any("without volume" in (w or "").lower() for w in (r.warnings or []))


def test_parse_calico():
    """Calicó (Spanish catalog): Calicó 123, Cal. 123."""
    out = parse_catalog_reference("Calicó 123")
    assert out["catalog"] == "Calicó"
    assert out["number"] == "123"
    out2 = parse_catalog_reference("Cal. 456a")
    assert out2["catalog"] == "Calicó"
    assert out2["number"] == "456a"
    assert canonical(out) == "Calicó 123"
