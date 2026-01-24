"""
Heritage Auctions Scraper Package

Scraper for Heritage Auctions (HA.com) coin data.
Extracts structured coin data, NGC/PCGS grades, provenance, and images.

Usage:
    from heritage_scraper import scrape_heritage_lot, search_heritage, HeritageScraper
    
    # Single lot
    coin = await scrape_heritage_lot("https://coins.ha.com/itm/.../a/61519-25316.s")
    
    # Search archives
    results = await search_heritage("hadrian denarius", max_results=50)
    
    # Full scraper with context
    async with HeritageScraper() as scraper:
        async for coin in scraper.scrape_search_results("titus denarius"):
            print(coin.title)
"""

from .models import (
    HeritageCoinData,
    HeritageImage,
    HeritageSearchResult,
    HeritageSearchResults,
    PhysicalData,
    CatalogReference,
    Provenance,
    ProvenanceEntry,
    AuctionInfo,
    HeritageAuctionType,
    HeritageMetal,
    SlabGrade,
    RawGrade,
    GradingService,
)

from .parser import HeritageParser

from .scraper import (
    HeritageScraper,
    scrape_heritage_lot,
    search_heritage,
)

from .integration import (
    HeritageIntegration,
    batch_import_heritage,
)

__all__ = [
    # Models
    'HeritageCoinData',
    'HeritageImage',
    'HeritageSearchResult',
    'HeritageSearchResults',
    'PhysicalData',
    'CatalogReference',
    'Provenance',
    'ProvenanceEntry',
    'AuctionInfo',
    'HeritageAuctionType',
    'HeritageMetal',
    'SlabGrade',
    'RawGrade',
    'GradingService',
    
    # Parser
    'HeritageParser',
    
    # Scraper
    'HeritageScraper',
    'scrape_heritage_lot',
    'search_heritage',
    
    # Integration
    'HeritageIntegration',
    'batch_import_heritage',
]

__version__ = '1.0.0'
