"""
RPC (Roman Provincial Coins) reference parser.

Outputs volume in Roman form (I, II, IV.1) for canonical/local_ref consistency.
"""
import re
from typing import Optional

from .base import ParsedRef, arabic_to_roman, roman_to_arabic, volume_hyphen_slash_to_dot


_PATTERNS = [
    # RPC I S 123, RPC I S2 456, RPC IV S3 789 (volume + supplement + number)
    (r"RPC\s+([IVX]+)[/\s]+(S\d?)\s+(\d+)\s*([a-zA-Z])?$", "roman_volume_supplement"),
    # RPC 1 S 5678 (arabic volume + supplement)
    (r"RPC\s+(\d+)[/\s]+(S\d?)\s+(\d+)\s*([a-zA-Z])?$", "arabic_volume_supplement"),
    # RPC I 1234, RPC I/5678, RPC IV 123a, RPC IV.1 1234, RPC IV.1 1234 (temp)
    # Supports IV.1 (dot) or IV/1
    (r"RPC\s+([IVX]+(?:\.[\d]+)?)[/\s]+(\d+)\s*([a-zA-Z])?$", "roman_volume"),
    # RPC 1 5678, RPC 2 123, RPC 4.1 1234
    (r"RPC\s+(\d+(?:\.\d+)?)[/\s]+(\d+)\s*([a-zA-Z])?$", "arabic_volume"),
    # RPC 5678 (no volume)
    (r"RPC\s+(\d+)\s*([a-zA-Z])?$", "no_volume"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse RPC reference. Volume in Roman. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    text = raw.strip()
    # Normalize "RPC online 1234" -> "RPC 1234" (treat online as no-volume or ignore it)
    text = re.sub(r"^RPC\s+online\s+", "RPC ", text, flags=re.IGNORECASE)
    
    for pattern, kind in _PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if kind == "roman_volume_supplement":
            roman_vol = m.group(1).upper()
            supp = (m.group(2) or "").strip().upper()  # S, S2, S3
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            num_str = f"{number}{variant}" if variant else number
            supplement = supp if supp else "S"
            arabic_vol = roman_to_arabic(roman_vol)
            norm = f"rpc.{arabic_vol}.{supplement}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="rpc",
                volume=vol_canon,
                number=num_str,
                variant=variant,
                supplement=supplement,
                normalized=norm.lower(),
            )
        if kind == "arabic_volume_supplement":
            arabic_vol = m.group(1)
            supp = (m.group(2) or "").strip().upper()
            number = m.group(3)
            variant = m.group(4) if m.lastindex >= 4 else None
            try:
                vol_int = int(arabic_vol)
                roman_vol = arabic_to_roman(vol_int)
            except (ValueError, TypeError):
                return None
            num_str = f"{number}{variant}" if variant else number
            supplement = supp if supp else "S"
            norm = f"rpc.{arabic_vol}.{supplement}.{number}"
            if variant:
                norm += variant
            return ParsedRef(
                system="rpc",
                volume=roman_vol,
                number=num_str,
                variant=variant,
                supplement=supplement,
                normalized=norm.lower(),
            )
        if kind == "roman_volume":
            roman_vol = m.group(1).upper()
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            
            # Handle IV.1 style
            vol_canon = volume_hyphen_slash_to_dot(roman_vol)
            
            num_str = f"{number}{variant}" if variant else number
            
            # Normalize for searching
            try:
                # If volume has part (IV.1), use float/decimal logic for Arabic if needed
                # But roman_to_arabic usually handles integers.
                # Simplification: just use the string volume for normalization if complex
                if "." in roman_vol:
                    main_vol = roman_vol.split(".")[0]
                    main_arabic = roman_to_arabic(main_vol)
                    suffix = roman_vol.split(".")[1]
                    arabic_vol = f"{main_arabic}.{suffix}"
                else:
                    arabic_vol = str(roman_to_arabic(roman_vol))
            except Exception:
                arabic_vol = roman_vol

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
            arabic_vol_raw = m.group(1)
            number = m.group(2)
            variant = m.group(3) if m.lastindex >= 3 else None
            
            try:
                if "." in arabic_vol_raw:
                    main, sub = arabic_vol_raw.split(".")
                    roman_main = arabic_to_roman(int(main))
                    roman_vol = f"{roman_main}.{sub}"
                else:
                    roman_vol = arabic_to_roman(int(arabic_vol_raw))
            except (ValueError, TypeError):
                roman_vol = arabic_vol_raw

            num_str = f"{number}{variant}" if variant else number
            norm = f"rpc.{arabic_vol_raw}.{number}"
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
