"""
Shared types and helpers for catalog reference parsers.

ParsedRef is the common output of per-catalog parsers. Volume is stored in
canonical form: Roman numerals (I, IV.1, VII.2) for RIC, RPC, DOC.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParsedRef:
    """Structured result from a single-catalog parser."""

    system: str  # "ric", "crawford", "rpc", etc.
    volume: Optional[str] = None  # Roman for RIC/RPC/DOC, e.g. "IV.1", "I"
    number: Optional[str] = None  # Main number; may include variant e.g. "351b", "335/1c"
    variant: Optional[str] = None  # Separate variant letter if needed for URL/display
    mint: Optional[str] = None  # RIC VI+ mint code, BMCRR/BMC Greek
    supplement: Optional[str] = None  # RPC "S", "S2"
    collection: Optional[str] = None  # SNG collection
    normalized: Optional[str] = None  # Internal normalized form e.g. "ric.4.1.351b"
    warnings: List[str] = field(default_factory=list)


# --- Roman / Arabic conversion (shared) ---

_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}


def roman_to_arabic(roman: str) -> int:
    """Convert Roman numeral to integer. Handles IV, IX, etc."""
    if not roman or not roman.strip():
        return 0
    s = roman.strip().upper()
    result = 0
    prev = 0
    for char in reversed(s):
        curr = _ROMAN_VALUES.get(char, 0)
        if curr < prev:
            result -= curr
        else:
            result += curr
        prev = curr
    return result


def arabic_to_roman(num: int) -> str:
    """Convert integer to Roman numeral (1-3999)."""
    if num <= 0:
        return ""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    result = []
    for i, v in enumerate(val):
        while num >= v:
            result.append(syms[i])
            num -= v
    return "".join(result)


def normalize_whitespace(s: str) -> str:
    """Collapse internal whitespace and strip."""
    if not s:
        return ""
    return " ".join(s.split()).strip()


def volume_hyphen_slash_to_dot(vol: str) -> str:
    """Normalize volume: IV-1, IV/1 -> IV.1."""
    if not vol:
        return vol
    return re.sub(r"[-/]", ".", vol.strip())


def make_simple_ref(system: str, number: str, variant: Optional[str] = None) -> ParsedRef:
    """Build ParsedRef for single-pattern catalogs (number + optional variant)."""
    num_str = f"{number}{variant}" if variant else number
    norm = f"{system}.{number}"
    if variant:
        norm += variant
    return ParsedRef(
        system=system,
        number=num_str,
        variant=variant,
        normalized=norm.lower(),
    )
