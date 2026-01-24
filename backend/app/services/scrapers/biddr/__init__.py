"""
Biddr Scraper Package

Production-ready scraper for Biddr auction platform (biddr.com).
Biddr hosts multiple auction houses including Savoca, Roma, Leu, Nomos, etc.
"""

from .models import (
    BiddrCoinData,
    BiddrPhysicalData,
    BiddrCatalogReference,
    BiddrProvenance,
    BiddrAuctionInfo,
    BiddrImage,
    BiddrMetal,
    BiddrSubHouse,
)
from .parser import BiddrParser
from .scraper import BiddrScraper, scrape_biddr_lot

__all__ = [
    # Models
    "BiddrCoinData",
    "BiddrPhysicalData",
    "BiddrCatalogReference",
    "BiddrProvenance",
    "BiddrAuctionInfo",
    "BiddrImage",
    "BiddrMetal",
    "BiddrSubHouse",
    # Parser
    "BiddrParser",
    # Scraper
    "BiddrScraper",
    "scrape_biddr_lot",
]
