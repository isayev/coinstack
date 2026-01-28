"""
Domain types for enrichment application.

Used by ApplyEnrichmentService to apply suggested field values to a coin.
No database or framework dependencies.
"""
from dataclasses import dataclass
from typing import Any, Literal, Optional

# API-level field names that can be set by enrichment (catalog or audit)
ALLOWED_FIELDS = frozenset({
    "issuer",
    "mint",
    "year_start",
    "year_end",
    "grade",
    "obverse_legend",
    "reverse_legend",
    "obverse_description",
    "reverse_description",
})


@dataclass(frozen=True)
class EnrichmentApplication:
    """Request to apply one suggested value to a coin field."""
    coin_id: int
    field_name: str
    new_value: Any
    source_type: Literal["catalog", "audit", "manual"]
    source_id: Optional[str] = None  # e.g. external_id or auction_data id


@dataclass
class ApplicationResult:
    """Result of applying one enrichment."""
    success: bool
    field_name: str
    old_value: Any
    new_value: Any
    error: Optional[str] = None
