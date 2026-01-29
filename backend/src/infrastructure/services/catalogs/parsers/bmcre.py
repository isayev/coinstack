"""
BMCRE (British Museum Catalogue of Roman Empire) reference parser.
"""
import re
from typing import Optional

from .base import ParsedRef, make_simple_ref


_PATTERN = re.compile(
    r"(?:BMCRE|BMC)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse BMCRE reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    return make_simple_ref("bmcre", m.group(1), m.group(2))
