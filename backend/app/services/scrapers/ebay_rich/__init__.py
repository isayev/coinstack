"""
eBay Scraper Package

Scraper for eBay coin listings. 
Note: eBay data is user-generated and less reliable than auction house data.
Trust primarily: dates, prices, and images.
"""

from .models import (
    EbayCoinData,
    EbayPhysicalData,
    EbayCatalogReference,
    EbayImage,
    EbayListingInfo,
    EbaySellerInfo,
    EbayListingType,
    EbayCondition,
)
from .parser import EbayParser
from .scraper import EbayScraper, scrape_ebay_listing

# Re-export old class name for backwards compatibility with orchestrator
# The orchestrator expects EBayScraper (capital B)
EBayScraper = EbayScraper

__all__ = [
    # Models
    "EbayCoinData",
    "EbayPhysicalData",
    "EbayCatalogReference",
    "EbayImage",
    "EbayListingInfo",
    "EbaySellerInfo",
    "EbayListingType",
    "EbayCondition",
    # Parser
    "EbayParser",
    # Scraper
    "EbayScraper",
    "EBayScraper",  # Backwards compatible alias
    "scrape_ebay_listing",
]
