from typing import List, Optional
import logging
from src.domain.services.scraper_service import IScraper, ScrapeResult, ScrapeStatus

logger = logging.getLogger(__name__)

class ScraperOrchestrator:
    """Selects the correct scraper for a URL."""
    
    def __init__(self, scrapers: List[IScraper]):
        self.scrapers = scrapers

    def get_scraper(self, url: str) -> Optional[IScraper]:
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return scraper
        return None

    async def scrape(self, url: str) -> ScrapeResult:
        """
        Orchestrate the scraping of a URL.
        Returns a structured ScrapeResult.
        """
        logger.info(f"Orchestrating scrape for: {url}")
        
        scraper = self.get_scraper(url)
        if not scraper:
            return ScrapeResult(
                status=ScrapeStatus.ERROR,
                error_message=f"No scraper found for URL: {url}"
            )
        
        try:
            return await scraper.scrape(url)
        except Exception as e:
            logger.exception(f"Unhandled error in scraper {type(scraper).__name__}: {e}")
            return ScrapeResult(
                status=ScrapeStatus.ERROR,
                error_message=str(e)
            )