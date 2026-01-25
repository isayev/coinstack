"""
Shared Scraper Components

This module provides common models, parsers, and utilities used across
all auction house scrapers (Heritage, CNG, Biddr, eBay, Agora).

Usage:
    from src.infrastructure.scrapers.shared import (
        PhysicalData,
        CatalogReference,
        ProvenanceEntry,
        Image,
        Metal,
        extract_references,
        parse_physical,
    )
"""

from src.infrastructure.scrapers.shared.models import (
    Metal,
    GradingService,
    PhysicalData,
    CatalogReference,
    ProvenanceEntry,
    Provenance,
    Image,
    SlabGrade,
    RawGrade,
)

from src.infrastructure.scrapers.shared.reference_patterns import (
    extract_references,
    extract_primary_reference,
    normalize_reference,
    is_valid_reference,
    REFERENCE_PATTERNS,
)

from src.infrastructure.scrapers.shared.physical_parser import (
    parse_physical,
    parse_weight_with_unit,
    validate_physical_data,
)

__all__ = [
    # Models
    "Metal",
    "GradingService",
    "PhysicalData",
    "CatalogReference",
    "ProvenanceEntry",
    "Provenance",
    "Image",
    "SlabGrade",
    "RawGrade",
    # Reference extraction
    "extract_references",
    "extract_primary_reference",
    "normalize_reference",
    "is_valid_reference",
    "REFERENCE_PATTERNS",
    # Physical parsing
    "parse_physical",
    "parse_weight_with_unit",
    "validate_physical_data",
]
