"""
Calicó (Catálogo de monedas españolas / Spanish coin catalog) reference parser.

Format: Calicó 123, Cal. 123, Calicó 456a.
Used for Iberian and Spanish coins.
"""
import re
from typing import Optional

from .base import ParsedRef, make_simple_ref


_PATTERN = re.compile(
    r"(?:Calicó|Cal\.?)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse Calicó reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    return make_simple_ref("calico", m.group(1), m.group(2))
