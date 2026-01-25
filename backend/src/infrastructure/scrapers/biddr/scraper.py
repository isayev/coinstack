"""
Biddr Scraper Service
"""

import asyncio
import logging
import random
from typing import Optional

from src.domain.services.scraper_service import IScraper
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import BiddrParser
from .models import BiddrCoinData

logger = logging.getLogger(__name__)

class BiddrScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for Biddr.com.
    """
    
    BASE_URL = "https://www.biddr.com"
    MIN_DELAY = 2.0
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.parser = BiddrParser()
    
    def can_handle(self, url: str) -> bool:
        return "biddr.com" in url or "biddr" in url.lower()
    
    async def scrape(self, url: str) -> Optional[AuctionLot]:
        """Scrape a Biddr lot URL."""
        if not await self.ensure_browser():
            return None
        
        # Rate limit
        await asyncio.sleep(self.MIN_DELAY + random.uniform(0, 2))
        
        page = await self.context.new_page()
        try:
            logger.info(f"Fetching Biddr URL: {url}")
            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            
            if not response or response.status >= 400:
                logger.error(f"Biddr returned status {response.status if response else 'None'}")
                return None
            
            # Wait for content
            try:
                await page.wait_for_selector(
                    'h1, h2, .lot-info, [class*="lot"], [class*="description"]',
                    timeout=10000
                )
            except:
                pass
            
            html = await page.content()
            
            # Parse
            data: BiddrCoinData = self.parser.parse(html, url)
            
            return self._map_to_domain(data)
            
        except Exception as e:
            logger.exception(f"Error scraping Biddr URL {url}: {e}")
            return None
        finally:
            await page.close()

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
