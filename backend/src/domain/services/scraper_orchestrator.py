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
        scraper = self.get_scraper(url)
        if not scraper:
            raise ValueError(f"No scraper found for URL: {url}")
        return await scraper.scrape(url)
