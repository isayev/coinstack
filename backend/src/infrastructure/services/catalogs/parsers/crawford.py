"""
Crawford (RRC / Roman Republican Coinage) reference parser.
"""
import re
from typing import Optional

from .base import ParsedRef, normalize_whitespace


_PATTERNS = [
    # Crawford 335/1c, Cr. 335/1, RRC 335/1c, Crawford:335/1
    (r"(?:Crawford|Cr\.?|RRC)[:\s]*(\d+)/(\d+)([a-z])?", "standard"),
    # Just number: 335/1c (bare)
    (r"^(\d+)/(\d+)([a-z])?$", "bare"),
    # Cr 123 (no subnumber)
    (r"(?:Crawford|Cr\.?|RRC)[:\s]*(\d+)$", "no_subnumber"),
]


def parse(raw: str) -> Optional[ParsedRef]:
    """Parse Crawford/RRC reference. Returns ParsedRef or None."""
    if not raw or not raw.strip():
        return None
    text = normalize_whitespace(raw)
    for pattern, kind in _PATTERNS:
        m = re.match(pattern, text, re.IGNORECASE)
        if not m:
            continue
        if kind == "no_subnumber":
            main_num = m.group(1)
            full_number = main_num
            norm = f"crawford.{main_num}"
            return ParsedRef(
                system="crawford",
                number=full_number,
                normalized=norm.lower(),
            )
        main_num = m.group(1)
        sub_num = m.group(2)
        variant = m.group(3) if m.lastindex >= 3 else None
        full_number = f"{main_num}/{sub_num}"
        if variant:
            full_number += variant
        norm = f"crawford.{main_num}.{sub_num}"
        if variant:
            norm += variant
        return ParsedRef(
            system="crawford",
            number=full_number,
            variant=variant,
            normalized=norm.lower(),
            warnings=["Bare Crawford format - confirm catalog"] if kind == "bare" else [],
        )
    return None
