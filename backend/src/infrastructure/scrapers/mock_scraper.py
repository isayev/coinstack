import asyncio
from typing import Optional
from decimal import Decimal
from src.domain.auction import AuctionLot
from src.domain.services.scraper_service import IScraper

class MockScraper(IScraper):
    """Mock scraper for testing."""
    
    def can_handle(self, url: str) -> bool:
        return "mock-auction.com" in url

    async def scrape(self, url: str) -> Optional[AuctionLot]:
        # Simulate network delay
        await asyncio.sleep(0.01)
        
        if "not-found" in url:
            return None
            
        return AuctionLot(
            source="MockAuction",
            lot_id="12345",
            url=url,
            sale_name="Mock Sale 1",
            lot_number="100",
            hammer_price=Decimal("500.00"),
            issuer="Augustus",
            grade="VF",
            weight_g=Decimal("3.50")
        )
