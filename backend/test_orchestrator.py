"""Test the scraper orchestrator."""
import asyncio
import sys
sys.path.insert(0, '.')

from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.heritage.scraper import HeritageScraper
from src.infrastructure.scrapers.cng.scraper import CNGScraper
from src.infrastructure.scrapers.biddr.scraper import BiddrScraper
from src.infrastructure.scrapers.ebay.scraper import EbayScraper
from src.infrastructure.scrapers.agora.scraper import AgoraScraper

async def test_orchestrator():
    url = "https://www.ebay.com/itm/197805685775"
    
    print(f"Testing orchestrator with URL: {url}")
    
    # Create orchestrator exactly like the API does
    orchestrator = ScraperOrchestrator([
        HeritageScraper(headless=True),
        CNGScraper(headless=True),
        BiddrScraper(headless=True),
        EbayScraper(headless=True),
        AgoraScraper(headless=True),
    ])
    
    # Check which scraper is selected
    scraper = orchestrator.get_scraper(url)
    print(f"Selected scraper: {type(scraper).__name__ if scraper else 'None'}")
    
    if not scraper:
        print("ERROR: No scraper found!")
        return None
    
    # Test scrape
    print("Calling orchestrator.scrape()...")
    result = await orchestrator.scrape(url)
    
    print(f"\n=== RESULT ===")
    print(f"Success: {result is not None}")
    
    if result:
        print(f"Source: {result.source}")
        print(f"Lot ID: {result.lot_id}")
        print(f"Issuer: {result.issuer}")
        print(f"Description: {result.description[:100] if result.description else 'None'}...")
    else:
        print("Orchestrator returned None")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(test_orchestrator())
    sys.exit(0 if result else 1)
