"""Rule-based reference parser for coin catalog references.

Orchestration layer: normalizes input, routes to per-catalog parsers (parsers/),
builds ParseResult and dict output. Single entry points: parse_catalog_reference(raw)
and parse_catalog_reference_full(raw).
"""
import re
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel

from src.infrastructure.services.catalogs.catalog_systems import (
    SYSTEM_TO_DISPLAY,
    reference_detection_pattern,
)
from src.infrastructure.services.catalogs.parsers import (
    SYSTEM_PARSERS,
    ParsedRef,
    normalize_whitespace,
)

# Compiled once at import for _looks_like_reference
_REF_DETECTION_PATTERN = reference_detection_pattern()


class ParseResult(BaseModel):
    """Result of parsing a reference string."""

    # Core fields
    system: Optional[str] = None       # "ric", "crawford", "rpc", etc.
    volume: Optional[str] = None       # Volume (Roman for RIC/RPC)
    number: Optional[str] = None      # Main reference number
    subtype: Optional[str] = None     # Variant/subtype like "a", "b"
    mint: Optional[str] = None        # RIC mint code, BMCRR/BMC Greek
    supplement: Optional[str] = None  # RPC S, S2
    collection: Optional[str] = None  # SNG collection

    # Parsing metadata
    raw: str = ""                     # Original input string
    normalized: Optional[str] = None  # Normalized form like "ric.1.207"
    confidence: float = 0.0            # 0-1, how confident we are in the parse
    needs_llm: bool = False          # True if LLM disambiguation needed
    warnings: List[str] = []          # Numismatic/validation warnings


def canonical(ref: Union[ParsedRef, Dict[str, Any]]) -> str:
    """
    Produce a single normalized string for local_ref and dedupe.
    Same logical reference in different forms (e.g. "RIC IV-1 351 b" vs dict
    catalog=RIC, volume=IV.1, number=351b) must yield the same string.
    """
    if isinstance(ref, ParsedRef):
        display = SYSTEM_TO_DISPLAY.get(ref.system) or ref.system
        parts = [display, ref.volume, ref.supplement, ref.mint, ref.collection, ref.number]
    else:
        d = ref
        catalog = d.get("catalog") or ""
        system = d.get("system") or ""
        display = (catalog.strip() and catalog) or (SYSTEM_TO_DISPLAY.get(system) if system else system) or system
        if isinstance(display, str):
            display = display.strip()
        parts = [
            display,
            d.get("volume"),
            d.get("supplement"),
            d.get("mint"),
            d.get("collection"),
            d.get("number"),
        ]
    joined = " ".join(str(p).strip() for p in parts if p is not None and str(p).strip())
    return normalize_whitespace(joined)


def _parsed_ref_to_result(parsed: ParsedRef, raw: str) -> ParseResult:
    """Convert ParsedRef to ParseResult."""
    confidence = 0.7 if parsed.warnings else 1.0
    needs_llm = parsed.needs_llm or any(
        "confirm" in w.lower() or "without volume" in w.lower()
        for w in parsed.warnings
    )
    # number without variant, subtype separate (e.g. 289 + c) for dict/API
    number = parsed.number
    subtype = parsed.variant
    if subtype and number and number.endswith(subtype):
        number = number[: -len(subtype)]
    return ParseResult(
        system=parsed.system,
        volume=parsed.volume,
        number=number,
        subtype=subtype,
        mint=parsed.mint,
        supplement=parsed.supplement,
        collection=parsed.collection,
        raw=raw,
        normalized=parsed.normalized,
        confidence=confidence,
        needs_llm=needs_llm,
        warnings=parsed.warnings.copy(),
    )


def _looks_like_reference(raw: str) -> bool:
    """Check if string looks like it could be a catalog reference."""
    has_numbers = bool(re.search(r"\d", raw))
    has_ref_words = _REF_DETECTION_PATTERN.search(raw) is not None
    return has_numbers and (has_ref_words or "/" in raw)


class ReferenceParser:
    """
    Orchestration layer: normalizes input, runs per-catalog parsers (parsers/),
    returns ParseResult. Supports RIC, Crawford, RPC, RSC, BMCRE, Sear, Sydenham.
    """

    def parse(self, raw: str) -> ParseResult:
        """
        Parse a reference string into structured components.
        Uses SYSTEM_PARSERS; volume is Roman for RIC/RPC.
        """
        if not raw or not raw.strip():
            return ParseResult(
                raw=raw or "",
                needs_llm=False,
            )
        text = normalize_whitespace(raw)
        # Attach trailing single-letter variant to number (e.g. "351 b" -> "351b") for canonical consistency
        text = re.sub(r"\s+([a-z])\s*$", r"\1", text)
        for _system, parse_fn in SYSTEM_PARSERS.items():
            parsed = parse_fn(text)
            if parsed is not None:
                return _parsed_ref_to_result(parsed, raw)
        if _looks_like_reference(text):
            return ParseResult(
                raw=raw,
                confidence=0.2,
                needs_llm=True,
            )
        return ParseResult(
            raw=raw,
            confidence=0.0,
            needs_llm=False,
        )

    def parse_multiple(self, raw: str) -> List[ParseResult]:
        """
        Parse a string that may contain multiple references.
        
        Handles separators like "; ", ", ", " / ", newlines
        """
        if not raw:
            return []
        
        # Split by common separators
        parts = re.split(r"[;,\n]|\s+/\s+", raw)
        results = []
        
        for part in parts:
            part = part.strip()
            if part:
                result = self.parse(part)
                results.append(result)
        
        return results


# Singleton instance for convenience
parser = ReferenceParser()

# Backward compat: repository and others may import SYSTEM_TO_DISPLAY_CATALOG from here
SYSTEM_TO_DISPLAY_CATALOG = SYSTEM_TO_DISPLAY


def _parse_result_to_dict(result: ParseResult) -> Dict[str, Any]:
    """
    Build dict from ParseResult for canonical() and sync.
    Returns catalog (display), volume, number, variant, mint, supplement, collection.
    """
    if result.system and result.system in SYSTEM_TO_DISPLAY:
        catalog = SYSTEM_TO_DISPLAY[result.system]
        number = (result.number or "") + (result.subtype or "")
        return {
            "catalog": catalog,
            "volume": result.volume,
            "number": number.strip() or None,
            "variant": result.subtype,
            "mint": result.mint,
            "supplement": result.supplement,
            "collection": result.collection,
        }
    return {
        "catalog": None,
        "volume": None,
        "number": None,
        "variant": None,
        "mint": None,
        "supplement": None,
        "collection": None,
    }


def parse_catalog_reference(raw: str) -> Dict[str, Optional[str]]:
    """
    Single entry point for parsing a catalog reference string.
    Returns dict with catalog (display), volume, number; may include optional
    variant, mint, supplement, collection. Volume is Roman for RIC/RPC.
    Use from routers, ReferenceSyncService, and scrapers. One parse path:
    delegates to parse_catalog_reference_full then _parse_result_to_dict.
    """
    if not raw or not str(raw).strip():
        return {
            "catalog": None,
            "volume": None,
            "number": None,
            "variant": None,
            "mint": None,
            "supplement": None,
            "collection": None,
        }
    result = parse_catalog_reference_full(str(raw).strip())
    return _parse_result_to_dict(result)


def parse_catalog_reference_full(raw: str) -> ParseResult:
    """
    Full parse with confidence and warnings.
    Use for UI preview or when confidence/warnings are needed without persisting.
    """
    if not raw or not str(raw).strip():
        return ParseResult(raw=raw or "", needs_llm=False)
    return parser.parse(str(raw).strip())


def parse_references(text: str) -> List[ParseResult]:
    """
    Convenience function to parse multiple references from a text string.
    
    Uses the singleton parser instance.
    
    Args:
        text: Text containing one or more reference strings (comma/semicolon separated)
        
    Returns:
        List of ParseResult objects for each reference found
    """
    return parser.parse_multiple(text)
