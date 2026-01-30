"""
Biddr Scraper Service
"""

import asyncio
import logging
import random
from typing import Optional

from src.domain.services.scraper_service import IScraper, ScrapeResult, ScrapeStatus
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import BiddrParser
from .models import BiddrCoinData

logger = logging.getLogger(__name__)

class BiddrScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for Biddr.com.
    Includes automatic retry logic and rate limiting (2.0s between requests).
    """

    BASE_URL = "https://www.biddr.com"

    def __init__(self, headless: bool = True):
        super().__init__(headless=headless, source="biddr")
        self.parser = BiddrParser()
    
    def can_handle(self, url: str) -> bool:
        return "biddr.com" in url or "biddr" in url.lower()
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape a Biddr lot URL with automatic rate limiting and retry."""
        try:
            logger.info(f"Fetching Biddr URL: {url}")
            
            # Use fetch_page with selector
            html = await self.fetch_page(
                url, 
                wait_selector='h1, h2, .lot-info, [class*="lot"], [class*="description"]'
            )
            
            # Parse
            data: BiddrCoinData = self.parser.parse(html, url)
            lot = self._map_to_domain(data)
            return ScrapeResult(status=ScrapeStatus.SUCCESS, data=lot)
            
        except Exception as e:
            logger.exception(f"Error scraping Biddr URL {url}: {e}")
            if "blocked" in str(e).lower() or "403" in str(e):
                return ScrapeResult(status=ScrapeStatus.BLOCKED, error_message=str(e))
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message=str(e))

    def _map_to_domain(self, data: BiddrCoinData) -> AuctionLot:
        """Map Biddr-specific model to generic Domain AuctionLot."""
        
        # Primary Image
        primary_img = None
        if data.images:
            primary_img = data.images[0].url_large or data.images[0].url
        
        return AuctionLot(
            source=data.auction_house, # "Biddr/Savoca" etc
            lot_id=data.biddr_lot_id,
            url=data.url,
            sale_name=data.auction.auction_name or "Biddr Auction",
            lot_number=str(data.auction.lot_number) if data.auction.lot_number else "0",
            
            # Pricing
            hammer_price=data.auction.hammer_price,
            estimate_low=data.auction.estimate_low,
            estimate_high=data.auction.estimate_high,
            currency=data.auction.currency,
            
            # Attribution
            issuer=data.ruler,
            mint=data.mint,
            year_start=None,
            year_end=None,
            
            # Physical
            weight_g=data.physical.weight_g,
            diameter_mm=data.physical.diameter_mm,
            die_axis=data.physical.die_axis_hours,
            
            # Grading
            grade=data.grade,
            
            # Description
            description=data.raw_description,
            
            # Images
            primary_image_url=primary_img,
            additional_images=[img.url_large or img.url for img in data.images[1:]]
        )