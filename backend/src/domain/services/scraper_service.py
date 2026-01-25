from typing import Protocol, Optional
from src.domain.auction import AuctionLot

class IScraper(Protocol):
    """Interface for an auction scraper."""
    
    def can_handle(self, url: str) -> bool:
        """Checks if this scraper handles the given URL."""
        ...

    async def scrape(self, url: str) -> Optional[AuctionLot]:
        """Scrapes the URL and returns an AuctionLot."""
        ...
