"""
Per-catalog reference parsers.

Each module exports parse(raw: str) -> Optional[ParsedRef].
Volume is in Roman form (I, IV.1) for RIC, RPC, DOC where applicable.
"""
from typing import Callable, Dict, Optional

from .base import (
    ParsedRef,
    arabic_to_roman,
    make_simple_ref,
    normalize_whitespace,
    roman_to_arabic,
    volume_hyphen_slash_to_dot,
)
from .ric import parse as parse_ric
from .crawford import parse as parse_crawford
from .rpc import parse as parse_rpc
from .rsc import parse as parse_rsc
from .doc import parse as parse_doc
from .bmcrr import parse as parse_bmcrr
from .bmcre import parse as parse_bmcre
from .sng import parse as parse_sng
from .cohen import parse as parse_cohen
from .calico import parse as parse_calico
from .sear import parse as parse_sear
from .sydenham import parse as parse_sydenham

# Registry: system key -> parse function. Order matters for detection precedence.
# BMCRR before BMCRE so "BMCRR 123" is not parsed as BMC.
SYSTEM_PARSERS: Dict[str, Callable[[str], Optional[ParsedRef]]] = {
    "ric": parse_ric,
    "crawford": parse_crawford,
    "rpc": parse_rpc,
    "rsc": parse_rsc,
    "doc": parse_doc,
    "bmcrr": parse_bmcrr,
    "bmcre": parse_bmcre,
    "sng": parse_sng,
    "cohen": parse_cohen,
    "calico": parse_calico,
    "sear": parse_sear,
    "sydenham": parse_sydenham,
}

__all__ = [
    "ParsedRef",
    "SYSTEM_PARSERS",
    "make_simple_ref",
    "parse_ric",
    "parse_crawford",
    "parse_rpc",
    "parse_rsc",
    "parse_doc",
    "parse_bmcrr",
    "parse_bmcre",
    "parse_sng",
    "parse_cohen",
    "parse_calico",
    "parse_sear",
    "parse_sydenham",
    "roman_to_arabic",
    "arabic_to_roman",
    "normalize_whitespace",
    "volume_hyphen_slash_to_dot",
]
