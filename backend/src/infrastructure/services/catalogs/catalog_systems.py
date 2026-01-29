"""
Single source of truth for catalog display names and reference_types.system keys.

Used by: parser (for dict output), reference_sync (catalog_to_system), coin_repository
(catalog_to_system, display name in _reference_to_domain).
"""
from typing import Dict

# System key (storage) -> display name (API/UI)
SYSTEM_TO_DISPLAY: Dict[str, str] = {
    "ric": "RIC",
    "crawford": "RRC",
    "rpc": "RPC",
    "rsc": "RSC",
    "bmcre": "BMCRE",
    "sear": "Sear",
    "sydenham": "Sydenham",
}

# Display name (lowercased) -> system key. Built from SYSTEM_TO_DISPLAY plus aliases.
def _build_display_to_system() -> Dict[str, str]:
    out: Dict[str, str] = {}
    for system, display in SYSTEM_TO_DISPLAY.items():
        out[display.lower()] = system
    # Aliases: RRC and Crawford both -> crawford
    out["rrc"] = "crawford"
    out["crawford"] = "crawford"
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
