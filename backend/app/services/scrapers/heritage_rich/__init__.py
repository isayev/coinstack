"""
Heritage Auctions Scraper Package

Production-ready scraper for Heritage Auctions (HA.com).
Heritage is the largest numismatic auction house in the world.

RATE LIMITS (STRICT):
- 3 second minimum between requests
- 429 errors trigger 60s backoff
- 403 = IP blocked (wait 24 hours)
"""

from .models import (
    HeritageCoinData,
    PhysicalData,
    CatalogReference,
    Provenance,
    ProvenanceEntry,
    HeritageImage,
    AuctionInfo,
    SlabGrade,
    RawGrade,
    HeritageAuctionType,
    HeritageMetal,
    GradingService,
)
from .parser import HeritageParser
from .scraper import HeritageScraper, scrape_heritage_lot

__all__ = [
    # Models
    "HeritageCoinData",
    "PhysicalData",
    "CatalogReference",
    "Provenance",
    "ProvenanceEntry",
    "HeritageImage",
    "AuctionInfo",
    "SlabGrade",
    "RawGrade",
    "HeritageAuctionType",
    "HeritageMetal",
    "GradingService",
    # Parser
    "HeritageParser",
    # Scraper
    "HeritageScraper",
    "scrape_heritage_lot",
]
