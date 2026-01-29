"""
Cohen (Description historique des monnaies... Roman Empire) reference parser.

Format: Cohen 123, Cohen 382a, Cohen I 123, Cohen II 456a.
Optional volume (Roman I–VIII); variant letter common.
"""
import re
from typing import Optional

from .base import ParsedRef, arabic_to_roman, roman_to_arabic


_PATTERNS = [
    # Cohen I 123, Cohen II 456a, Cohen VIII 12
    (r"Cohen\s+([IVX]+)\s+(\d+)([a-z])?", "roman_volume"),
    # Cohen 123, Cohen 382a
    (r"Cohen\s+(\d+)([a-z])?", "no_volume"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse Cohen reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    for pattern, kind in _PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if kind == "roman_volume":
            roman_vol = m.group(1).upper()
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"cohen.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="cohen",
                volume=roman_vol,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "no_volume":
            number = m.group(1)
            variant = m.group(2) if m.lastindex >= 2 else None
            num_str = f"{number}{variant}" if variant else number
            norm = f"cohen.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="cohen",
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
                warnings=["Cohen reference without volume - 8 volumes (I–VIII)"],
            )
    return None
