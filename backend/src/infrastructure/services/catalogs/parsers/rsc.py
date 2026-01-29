"""
RSC (Roman Silver Coins) reference parser.

Optional volume in Roman form.
"""
import re
from typing import Optional

from .base import ParsedRef, roman_to_arabic


_PATTERN = re.compile(
    r"RSC\s+(?:([IVX]+)\s+)?(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse RSC reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    volume_roman = m.group(1)
    number = m.group(2)
    variant = m.group(3)
    num_str = f"{number}{variant}" if variant else number
    if volume_roman:
        arabic_vol = roman_to_arabic(volume_roman.upper())
        norm = f"rsc.{arabic_vol}.{number}"
    else:
        norm = f"rsc.{number}"
    if variant:
        norm += variant
    return ParsedRef(
        system="rsc",
        volume=volume_roman.upper() if volume_roman else None,
        number=num_str,
        variant=variant,
        normalized=norm.lower(),
        warnings=[] if volume_roman else ["RSC reference without volume"],
    )
