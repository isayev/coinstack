"""
RPC (Roman Provincial Coins) reference parser.

Outputs volume in Roman form (I, II, IV.1) for canonical/local_ref consistency.
"""
import re
from typing import Optional

from .base import ParsedRef, arabic_to_roman, roman_to_arabic, volume_hyphen_slash_to_dot


_PATTERNS = [
    # RPC I 1234, RPC I/5678, RPC IV 123a
    (r"RPC\s+([IVX]+)[/\s]+(\d+)([a-z])?", "roman_volume"),
    # RPC 1 5678, RPC 2 123
    (r"RPC\s+(\d+)[/\s]+(\d+)([a-z])?", "arabic_volume"),
    # RPC 5678 (no volume)
    (r"RPC\s+(\d+)([a-z])?$", "no_volume"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse RPC reference. Volume in Roman. Returns ParsedRef or None."""
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
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            num_str = f"{number}{variant}" if variant else number
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"rpc.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="rpc",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "arabic_volume":
            arabic_vol = m.group(1)
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            try:
                vol_int = int(arabic_vol)
                roman_vol = arabic_to_roman(vol_int)
            except (ValueError, TypeError):
                return None
            num_str = f"{number}{variant}" if variant else number
            norm = f"rpc.{arabic_vol}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="rpc",
                volume=roman_vol,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
            )
        if kind == "no_volume":
            number = m.group(1)
            variant = m.group(2) if m.lastindex >= 2 else None
            num_str = f"{number}{variant}" if variant else number
            norm = f"rpc.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="rpc",
                volume=None,
                number=num_str,
                variant=variant,
                normalized=norm.lower(),
                warnings=["RPC reference without volume - may need volume identification"],
            )
    return None
