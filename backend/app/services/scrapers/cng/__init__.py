"""
CNG (Classical Numismatic Group) Scraper Package

Production-ready scraper for CNG auction data with full provenance extraction.
Leverages JSON-LD schema.org data embedded in pages for cleaner extraction.
"""

from .models import (
    CNGCoinData,
    PhysicalData,
    CatalogReference,
    Provenance,
    ProvenanceEntry,
    CNGImage,
    AuctionInfo,
    CNGAuctionType,
    CNGMetal,
    CNGSearchResult,
    CNGSearchResults,
)
from .parser import CNGParser
from .scraper import CNGScraper, scrape_cng_lot, search_cng

__all__ = [
    # Models
    "CNGCoinData",
    "PhysicalData",
    "CatalogReference",
    "Provenance",
    "ProvenanceEntry",
    "CNGImage",
    "AuctionInfo",
    "CNGAuctionType",
    "CNGMetal",
    "CNGSearchResult",
    "CNGSearchResults",
    # Parser
    "CNGParser",
    # Scraper
    "CNGScraper",
    "scrape_cng_lot",
    "search_cng",
]
