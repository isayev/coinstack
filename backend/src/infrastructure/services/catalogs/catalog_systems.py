"""
Single source of truth for catalog display names and reference_types.system keys.

Used by: parser (for dict output and reference detection), reference_sync (catalog_to_system),
coin_repository (catalog_to_system, display name in _reference_to_domain).
"""
import re
from typing import Dict, List

# System key (storage) -> display name (API/UI)
SYSTEM_TO_DISPLAY: Dict[str, str] = {
    "ric": "RIC",
    "crawford": "RRC",
    "rpc": "RPC",
    "rsc": "RSC",
    "doc": "DOC",
    "bmcrr": "BMCRR",
    "bmcre": "BMCRE",
    "sng": "SNG",
    "cohen": "Cohen",
    "calico": "Calicó",
    "sear": "Sear",
    "sydenham": "Sydenham",
}

# Words that indicate a catalog reference (for _looks_like_reference). Display names plus short aliases.
REFERENCE_DETECTION_WORDS: List[str] = [
    "RIC", "RPC", "Crawford", "Cr", "RRC", "RSC", "DOC", "BMCRR", "BMC", "BMCRE",
    "SNG", "Cohen", "Calicó", "Cal", "Sear", "SCV", "Sydenham", "Syd",
]


def reference_detection_pattern() -> re.Pattern:
    """Regex to detect catalog keywords in raw text (case-insensitive)."""
    alternation = "|".join(re.escape(w) for w in REFERENCE_DETECTION_WORDS)
    return re.compile(r"\b(" + alternation + r")\b", re.IGNORECASE)


# Display name (lowercased) -> system key. Built from SYSTEM_TO_DISPLAY plus aliases.
def _build_display_to_system() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for system, display in SYSTEM_TO_DISPLAY.items():
        out[display.lower()] = system
    # Aliases: RRC and Crawford both -> crawford
    out["rrc"] = "crawford"
    out["crawford"] = "crawford"
    out["calicó"] = "calico"
    out["calico"] = "calico"
    return out


DISPLAY_TO_SYSTEM: Dict[str, str] = _build_display_to_system()


def catalog_to_system(catalog: str) -> str:
    """
    Map display catalog (RIC, RRC, Crawford, etc.) to reference_types.system (lowercase).
    Used by reference_sync and coin_repository for lookups and persistence.
    """
    if not catalog:
        return ""
    key = (catalog or "").strip().lower()
    return DISPLAY_TO_SYSTEM.get(key) or key or "unknown"
