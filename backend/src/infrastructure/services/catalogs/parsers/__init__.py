"""
Per-catalog reference parsers.

Each module exports parse(raw: str) -> Optional[ParsedRef].
Volume is in Roman form (I, IV.1) for RIC, RPC, DOC where applicable.
"""
from typing import Callable, Dict, Optional

from .base import (
    ParsedRef,
    arabic_to_roman,
    normalize_whitespace,
    roman_to_arabic,
    volume_hyphen_slash_to_dot,
)
from .ric import parse as parse_ric
from .crawford import parse as parse_crawford
from .rpc import parse as parse_rpc
from .rsc import parse as parse_rsc
from .bmcre import parse as parse_bmcre
from .sear import parse as parse_sear
from .sydenham import parse as parse_sydenham

# Registry: system key -> parse function. Order matters for detection precedence.
SYSTEM_PARSERS: Dict[str, Callable[[str], Optional[ParsedRef]]] = {
    "ric": parse_ric,
    "crawford": parse_crawford,
    "rpc": parse_rpc,
    "rsc": parse_rsc,
    "bmcre": parse_bmcre,
    "sear": parse_sear,
    "sydenham": parse_sydenham,
}

__all__ = [
    "ParsedRef",
    "SYSTEM_PARSERS",
    "parse_ric",
    "parse_crawford",
    "parse_rpc",
    "parse_rsc",
    "parse_bmcre",
    "parse_sear",
    "parse_sydenham",
    "roman_to_arabic",
    "arabic_to_roman",
    "normalize_whitespace",
    "volume_hyphen_slash_to_dot",
]
