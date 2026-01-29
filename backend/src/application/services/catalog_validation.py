"""
Numismatic validation for catalog references vs coin attributes.

Checks category/catalog alignment (e.g. RIC for imperial, RRC for republic)
and optionally date/issuer consistency. Used by LLM review and bulk enrich.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class CatalogValidationResult:
    """Result of validating a reference against coin context."""
    status: str  # "ok" | "warning" | "error"
    message: Optional[str] = None


# Catalog -> typical coin categories (lowercase). Mismatch = warning.
_CATALOG_CATEGORIES: dict[str, set[str]] = {
    "RIC": {"roman_imperial", "roman_provincial", "byzantine", "gallic_empire", "palmyrene_empire", "romano_british"},
    "RRC": {"roman_republic"},
    "crawford": {"roman_republic"},
    "RPC": {"roman_provincial", "roman_imperial"},
    "RSC": {"roman_imperial", "roman_provincial"},
    "Cohen": {"roman_imperial", "roman_provincial"},
    "Sear": {"roman_imperial", "roman_republic", "roman_provincial", "byzantine", "greek"},
    "BMCRE": {"roman_imperial", "roman_provincial"},
    "BMC": {"roman_imperial", "roman_provincial", "greek"},
    "Sydenham": {"roman_republic"},
}


def validate_reference_for_coin(
    catalog: Optional[str],
    number: Optional[str],
    volume: Optional[str],
    coin_category: Optional[str],
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    issuer: Optional[str] = None,
) -> CatalogValidationResult:
    """
    Validate that a catalog reference is consistent with coin category (and optionally dates/issuer).

    - Category vs catalog: e.g. RIC for imperial, RRC for republic; mismatch returns warning.
    - Date/issuer checks are optional (not implemented in first version).
    """
    catalog_str = (catalog or "").strip()
    if not catalog_str:
        return CatalogValidationResult(status="ok", message=None)

    cat_upper = catalog_str.upper()
    if cat_upper == "RRC":
        cat_key = "RRC"
    elif cat_upper == "CRAWFORD":
        cat_key = "crawford"
    else:
        cat_key = cat_upper
    allowed = _CATALOG_CATEGORIES.get(cat_key)
    if not allowed:
        # Unknown catalog - no category check
        return CatalogValidationResult(status="ok", message=None)

    coin_cat = (coin_category or "").strip().lower()
    if not coin_cat:
        return CatalogValidationResult(status="ok", message=None)

    if coin_cat in allowed:
        return CatalogValidationResult(status="ok", message=None)

    return CatalogValidationResult(
        status="warning",
        message=f"Catalog {catalog_str} is typically used for {', '.join(sorted(allowed))}; this coin is {coin_cat}. Verify the reference.",
    )
