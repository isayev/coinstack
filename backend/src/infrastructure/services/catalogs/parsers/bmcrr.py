"""
BMCRR (British Museum Catalogue of Roman Republic) reference parser.

Format: BMCRR 123, BMC RR 123, or BMC RR 123a.
Distinct from BMCRE (Roman Empire); register BMCRR before BMCRE so "BMCRR" is not parsed as BMC.
"""
import re
from typing import Optional

from .base import ParsedRef, make_simple_ref


_PATTERN = re.compile(
    r"(?:BMCRR|BMC\s+RR)\s+(\d+)([a-z])?",
    re.IGNORECASE,
)


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse BMCRR reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    m = _PATTERN.match(raw.strip())
    if not m:
        return None
    return make_simple_ref("bmcrr", m.group(1), m.group(2))
