from typing import List, Optional
from src.domain.services.scraper_service import IScraper
from src.domain.auction import AuctionLot

class ScraperOrchestrator:
    """Selects the correct scraper for a URL."""
    
    def __init__(self, scrapers: List[IScraper]):
        self.scrapers = scrapers

    def get_scraper(self, url: str) -> Optional[IScraper]:
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return scraper
        return None

    async def scrape(self, url: str) -> Optional[AuctionLot]:
        with open("c:/vibecode/coinstack/backend/orchestrator_debug.log", "a") as f:
            f.write(f"\n=== Orchestrator.scrape() called ===\n")
            f.write(f"URL: {url}\n")
            f.write(f"Available scrapers: {[type(s).__name__ for s in self.scrapers]}\n")
        
        scraper = self.get_scraper(url)
        
        with open("c:/vibecode/coinstack/backend/orchestrator_debug.log", "a") as f:
            f.write(f"Selected scraper: {type(scraper).__name__ if scraper else 'None'}\n")
        
        if not scraper:
            with open("c:/vibecode/coinstack/backend/orchestrator_debug.log", "a") as f:
                f.write("ERROR: No scraper found!\n")
            raise ValueError(f"No scraper found for URL: {url}")
        
        with open("c:/vibecode/coinstack/backend/orchestrator_debug.log", "a") as f:
            f.write("Calling scraper.scrape()...\n")
        
        result = await scraper.scrape(url)
        
        with open("c:/vibecode/coinstack/backend/orchestrator_debug.log", "a") as f:
            f.write(f"Scraper returned: {result is not None}\n")
        
        return result
