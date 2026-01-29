"""
Sear (Roman Coins and Their Values) reference parser.
"""
import re
from typing import Optional

from .base import ParsedRef


_PATTERN = re.compile(
    r"(?:Sear|SCV|S)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse Sear reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    number = m.group(1)
    variant = m.group(2)
    num_str = f"{number}{variant}" if variant else number
    norm = f"sear.{number}"
    if variant:
        norm += variant
    return ParsedRef(
        system="sear",
        number=num_str,
        variant=variant,
        normalized=norm.lower(),
    )
