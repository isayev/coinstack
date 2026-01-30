"""
Agora Scraper Service
"""

import asyncio
import logging
import random
from typing import Optional

from src.domain.services.scraper_service import IScraper, ScrapeResult, ScrapeStatus
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import AgoraParser
from .models import AgoraCoinData

logger = logging.getLogger(__name__)

class AgoraScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for Agora Auctions.
    Includes automatic retry logic and rate limiting (2.0s between requests).
    """

    BASE_URL = "https://agoraauctions.com"

    def __init__(self, headless: bool = True):
        super().__init__(headless=headless, source="agora")
        self.parser = AgoraParser()
    
    def can_handle(self, url: str) -> bool:
        return "agoraauctions.com" in url or "agora-auctions" in url
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape an Agora lot URL with automatic rate limiting and retry."""
        try:
            logger.info(f"Fetching Agora URL: {url}")
            
            # Use fetch_page (no special wait logic needed usually for Agora, but wait_until=domcontentloaded is default)
            html = await self.fetch_page(url)
            
            data = self.parser.parse(html, url)
            lot = self._map_to_domain(data)
            return ScrapeResult(status=ScrapeStatus.SUCCESS, data=lot)
            
        except Exception as e:
            logger.exception(f"Error scraping Agora URL {url}: {e}")
            if "blocked" in str(e).lower() or "403" in str(e):
                return ScrapeResult(status=ScrapeStatus.BLOCKED, error_message=str(e))
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message=str(e))

    def _map_to_domain(self, data: AgoraCoinData) -> AuctionLot:
        """Map Agora model to generic Domain AuctionLot."""
        
        return AuctionLot(
            source="Agora Auctions",
            lot_id=data.agora_lot_id,
            url=data.url,
            sale_name="Agora Auction", 
            lot_number=data.lot_number or "0",
            
            # Pricing
            hammer_price=data.hammer_price,
            estimate_low=data.estimate_low,
            estimate_high=data.estimate_high,
            currency=data.currency,
            
            # Attribution (simple parsing for now)
            issuer=None, # Parser doesn't extract ruler reliably yet
            mint=None,
            year_start=None,
            year_end=None,
            
            # Physical
            weight_g=data.physical.weight_g,
            diameter_mm=data.physical.diameter_mm,
            die_axis=data.physical.die_axis,
            
            # Grading
            grade=data.grade,
            
            # Description
            description=data.description or data.title,
            
            # Images
            primary_image_url=data.primary_photo_url,
            additional_images=data.photos[1:] if len(data.photos) > 1 else []
        )