"""
Crawford (RRC / Roman Republican Coinage) reference parser.
"""
import re
from typing import List, Optional

from .base import ParsedRef, normalize_whitespace


def _crawford_ref(
    main_num: str,
    sub_num: str,
    variant: Optional[str],
    warnings: Optional[List[str]] = None,
) -> ParsedRef:
    """Build ParsedRef for main/sub + optional variant."""
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
        warnings=warnings or [],
    )


_PATTERNS = [
    # Crawford 335-1c or 335/1c (hyphen normalized to slash)
    (r"(?:Crawford|Cr\.?|RRC)[:\s]*(\d+)-(\d+)([a-z])?", "hyphen"),
    # Range: 235/1a-c store first variant + warning
    (r"(?:Crawford|Cr\.?|RRC)[:\s]*(\d+)/(\d+)([a-z])-([a-z])", "range"),
    # Crawford 335/1c, Cr. 335/1, RRC 335/1c, Crawford:335/1, Crawford335/1c (no space)
    (r"(?:Crawford|Cr\.?|RRC)[:\s]*(\d+)/(\d+)([a-z])?", "standard"),
    # Just number: 335/1c or 335-1c (bare)
    (r"^(\d+)/(\d+)([a-z])?$", "bare"),
    (r"^(\d+)-(\d+)([a-z])?$", "bare_hyphen"),
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
        if kind == "hyphen":
            return _crawford_ref(
                m.group(1), m.group(2), m.group(3) if m.lastindex >= 3 else None,
                ["Hyphen normalized to slash"],
            )
        if kind == "range":
            main_num, sub_num, first_var = m.group(1), m.group(2), m.group(3)
            ref = _crawford_ref(main_num, sub_num, first_var, ["Range stored as first variant only"])
            return ref
        if kind == "bare_hyphen":
            return _crawford_ref(
                m.group(1), m.group(2), m.group(3) if m.lastindex >= 3 else None,
                ["Bare Crawford format - hyphen normalized to slash"],
            )
        main_num = m.group(1)
        sub_num = m.group(2)
        variant = m.group(3) if m.lastindex >= 3 else None
        warnings = ["Bare Crawford format - confirm catalog"] if kind == "bare" else []
        return _crawford_ref(main_num, sub_num, variant, warnings)
    return None
