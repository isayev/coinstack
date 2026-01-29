"""
Sear (Roman Coins and Their Values) reference parser.

Requires "Sear" or "SCV" prefix (not bare "S") to avoid confusion with RPC supplement "S".
"""
import re
from typing import Optional

from .base import ParsedRef, make_simple_ref


_PATTERN = re.compile(
    r"(?:Sear|SCV)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse Sear reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    return make_simple_ref("sear", m.group(1), m.group(2))
