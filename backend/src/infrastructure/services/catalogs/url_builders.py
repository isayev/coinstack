"""
Build external catalog URLs from a reference (dict or ParsedRef-like).

Used by OCRE/CRRO/RPC services and frontend link builders. Ref shape:
  catalog/system, volume (Roman for RIC/RPC), number, variant, mint, supplement.
"""
from typing import Any, Dict, Optional

from .catalog_systems import catalog_to_system
from .parsers import roman_to_arabic

OCRE_BASE = "http://numismatics.org/ocre"
CRRO_BASE = "http://numismatics.org/crro"
RPC_BASE = "http://numismatics.org/rpc"


def _ref_volume_arabic(ref: Dict[str, Any]) -> Optional[int]:
    """Volume as integer for URL (Roman -> arabic). Handles IV.1 by using Roman part only."""
    vol = ref.get("volume")
    if not vol:
        return None
    s = str(vol).strip().upper()
    if s.isdigit():
        return int(s)
    # Use only the Roman numeral part (e.g. IV from IV.1)
    roman_part = s.split(".")[0].split("/")[0].strip()
    if not roman_part:
        return None
    try:
        return roman_to_arabic(roman_part)
    except Exception:
        return None


def build_ocre_url(ref: Dict[str, Any], emperor: Optional[str] = None) -> Optional[str]:
    """Build OCRE (RIC) type URL. ref: catalog, volume, number, variant?, mint?."""
    system = catalog_to_system(ref.get("catalog") or ref.get("system") or "")
    if system != "ric":
        return None
    vol_arabic = _ref_volume_arabic(ref)
    number = ref.get("number") or ""
    if not number:
        return None
    # OCRE id format: ric.1.207, ric.1(2).aug.207
    parts = ["ric"]
    if vol_arabic is not None:
        parts.append(str(vol_arabic))
    parts.append(str(number).split("/")[0])
    external_id = ".".join(parts)
    return f"{OCRE_BASE}/id/{external_id}"


def build_ocre_search_url(query: str) -> str:
    """Build OCRE search URL."""
    return f"{OCRE_BASE}/results?q={query}"


def build_crro_url(ref: Dict[str, Any]) -> Optional[str]:
    """Build CRRO (Crawford/RRC) type URL."""
    system = catalog_to_system(ref.get("catalog") or ref.get("system") or "")
    if system != "crawford":
        return None
    number = ref.get("number") or ""
    if not number:
        return None
    # CRRO id: crawford.335.1c
    n = number.replace("/", ".")
    external_id = f"crawford.{n}"
    return f"{CRRO_BASE}/id/{external_id}"


def build_crro_search_url(query: str) -> str:
    """Build CRRO search URL."""
    return f"{CRRO_BASE}/results?q={query}"


def build_rpc_type_url(ref: Dict[str, Any]) -> Optional[str]:
    """Build RPC Online type URL. Volume in path as arabic."""
    system = catalog_to_system(ref.get("catalog") or ref.get("system") or "")
    if system != "rpc":
        return None
    vol_arabic = _ref_volume_arabic(ref)
    number = ref.get("number") or ""
    if not number:
        return None
    if vol_arabic is None:
        return f"{RPC_BASE}/search?q={number}"
    num_clean = str(number).split("/")[0]
    return f"{RPC_BASE}/coins/{vol_arabic}/{num_clean}"


def build_rpc_search_url(ref: Dict[str, Any]) -> str:
    """Build RPC search URL from ref number."""
    number = ref.get("number") or ""
    return f"{RPC_BASE}/search?q={number}"
