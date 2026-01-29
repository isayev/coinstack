"""
RIC (Roman Imperial Coinage) reference parser.

Outputs volume in Roman form (I, IV.1, VII.2) for canonical/local_ref consistency.
"""
import re
from typing import Optional

from .base import ParsedRef, arabic_to_roman, roman_to_arabic, volume_hyphen_slash_to_dot


def _normalize_mint(mint: str) -> str:
    """Normalize mint name for canonical form (title case, known mints)."""
    if not mint or not mint.strip():
        return mint or ""
    key = mint.strip().lower()
    return _RIC_MINT_NORMALIZE.get(key) or mint.strip().title()


def _part_to_canonical(part: str) -> str:
    """Normalize volume part: Roman (II, III) -> Arabic (2, 3) for canonical form."""
    if not part or not part.strip():
        return part or ""
    p = part.strip().upper()
    if p.isdigit():
        return p
    try:
        return str(roman_to_arabic(p))
    except Exception:
        return part


# Optional: normalize common mint names for canonical form (e.g. "Ticinum" consistent)
_RIC_MINT_NORMALIZE = {
    "ticinum": "Ticinum",
    "antioch": "Antioch",
    "rome": "Rome",
    "lugdunum": "Lugdunum",
    "alexandria": "Alexandria",
}

# Part can be Arabic (1, 2) or Roman (I, II, III) e.g. RIC V.II 325
_PART_GROUP = r"(\d+|[IVX]+)"
# RIC volume patterns: roman_volume, roman_volume_dot, arabic_volume, roman_volume_hyphen; with optional mint
_PATTERNS = [
    # RIC VII Ticinum 123, RIC II Antioch 756 (volume + optional mint + number)
    (r"RIC\s+([IVX]+)([²³]|[23])?\s+([A-Za-z]+)\s+(\d+)([a-z])?", "roman_volume_mint"),
    # RIC IV.1 Antioch 351b, RIC V.II Antioch 325 (volume with part Arabic or Roman + optional mint + number)
    (r"RIC\s+([IVX]+)[.\-/]" + _PART_GROUP + r"\s+([A-Za-z]+)\s+(\d+)([a-z])?", "roman_volume_part_mint"),
    # RIC I (2) 207, RIC I(2) 207 (parenthesized edition - common in OCRE citations)
    (r"RIC\s+([IVX]+)\s*\(\s*([23])\s*\)\s+(\d+)([a-z])?", "roman_volume_edition_paren"),
    # RIC I 207, RIC II³ 430, RIC I² 207a
    (r"RIC\s+([IVX]+)([²³]|[23])?\s+(\d+)([a-z])?", "roman_volume"),
    # RIC IV.1 351b, RIC V.II 325, RIC IV-1 351, RIC IV/1 351 (volume with part Arabic or Roman)
    (r"RIC\s+([IVX]+)[.\-/]" + _PART_GROUP + r"\s+(\d+)([a-z])?", "roman_volume_part"),
    # RIC 1 207, RIC 2.3 430
    (r"RIC\s+(\d+)(?:\.(\d))?\s+(\d+)([a-z])?", "arabic_volume"),
    # RIC hyphenated: RIC II-123 (number immediately after hyphen)
    (r"RIC\s+([IVX]+)-(\d+)([a-z])?", "roman_volume_hyphen"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse RIC reference. Returns ParsedRef with volume in Roman, or None if no match."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for pattern, kind in _PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if kind == "roman_volume_mint":
            roman_vol = m.group(1).upper()
            edition = m.group(2)  # ², ³, 2, 3
            mint_raw = m.group(3)
            number = m.group(4)
            variant = m.group(5) if m.lastindex >= 5 else None
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            if edition:
                ed_num = "2" if edition in ("²", "2") else "3"
                vol_canon = f"{vol_canon}.{ed_num}"
            num_str = f"{number}{variant}" if variant else number
            mint = _normalize_mint(mint_raw) if mint_raw else None
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                mint=mint,
                normalized=norm.lower(),
            )
        if kind == "roman_volume_part_mint":
            roman_vol = m.group(1).upper()
            part = m.group(2)
            part_canon = _part_to_canonical(part)
            mint_raw = m.group(3)
            number = m.group(4)
            variant = m.group(5) if m.lastindex >= 5 else None
            vol_canon = f"{roman_vol}.{part_canon}"
            num_str = f"{number}{variant}" if variant else number
            mint = _normalize_mint(mint_raw) if mint_raw else None
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{part_canon}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                mint=mint,
                normalized=norm.lower(),
            )
        if kind == "roman_volume_edition_paren":
            roman_vol = m.group(1).upper()
            edition = m.group(2)  # 2 or 3
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            vol_canon = f"{roman_vol}.{edition}"
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "roman_volume":
            roman_vol = m.group(1).upper()
            edition = m.group(2)  # ², ³, 2, 3
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            if edition:
                ed_num = "2" if edition in ("²", "2") else "3"
                vol_canon = f"{vol_canon}.{ed_num}"
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "roman_volume_part":
            roman_vol = m.group(1).upper()
            part = m.group(2)
            part_canon = _part_to_canonical(part)
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            vol_canon = f"{roman_vol}.{part_canon}"
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{part_canon}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "arabic_volume":
            arabic_vol = m.group(1)
            sub = m.group(2)  # e.g. .3 for part
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            try:
                vol_int = int(arabic_vol)
                roman_vol = arabic_to_roman(vol_int)
            except (ValueError, TypeError):
                return None
            vol_canon = roman_vol
            if sub:
                vol_canon = f"{vol_canon}.{sub}"
            num_str = f"{number}{variant}" if variant else number
            norm = f"ric.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "roman_volume_hyphen":
            roman_vol = m.group(1).upper()
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"ric.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="ric",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
    return None
