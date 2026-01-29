"""
DOC (Die Orientierung der Kaiserporträts) reference parser.

Volumes 1–5 (Roman imperial portrait orientation catalog).
Outputs volume in Roman form (I–V) for canonical/local_ref consistency.
"""
import re
from typing import Optional

from .base import ParsedRef, arabic_to_roman, roman_to_arabic


# DOC volume patterns: arabic 1-5, roman I-V
_PATTERNS = [
    # DOC 1 234, DOC 2 567a, DOC 5 12
    (r"DOC\s+([1-5])\s+(\d+)([a-z])?", "arabic_volume"),
    # DOC I 234, DOC III 567a, DOC V 12
    (r"DOC\s+([IVX]+)\s+(\d+)([a-z])?", "roman_volume"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse DOC reference. Returns ParsedRef with volume in Roman, or None."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for pattern, kind in _PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if kind == "arabic_volume":
            arabic_vol = m.group(1)
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            try:
                vol_int = int(arabic_vol)
                if vol_int < 1 or vol_int > 5:
                    continue
                roman_vol = arabic_to_roman(vol_int)
            except (ValueError, TypeError):
                continue
            num_str = f"{number}{variant}" if variant else number
            norm = f"doc.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="doc",
                volume=roman_vol,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "roman_volume":
            roman_vol = m.group(1).upper()
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            arabic_vol = roman_to_arabic(roman_vol)
            if arabic_vol < 1 or arabic_vol > 5:
                continue
            num_str = f"{number}{variant}" if variant else number
            norm = f"doc.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="doc",
                volume=roman_vol,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
    return None
