"""
eBay Scraper Service
"""

import asyncio
import logging
import random
import hashlib
from typing import Optional

from src.domain.services.scraper_service import IScraper
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import EbayParser
from .models import EbayCoinData

logger = logging.getLogger(__name__)

# Realistic user agents
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
]

class EbayScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for eBay listings with enhanced stealth.
    """
    
    BASE_URL = "https://www.ebay.com"
    MIN_DELAY = 5.0
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.parser = EbayParser()
    
    def can_handle(self, url: str) -> bool:
        return "ebay.com" in url or "ebay" in url.lower()
    
    async def scrape(self, url: str) -> Optional[AuctionLot]:
        """Scrape an eBay listing URL."""
        if not await self.ensure_browser():
            return None
        
        # Enhanced rate limiting for eBay
        delay = self.MIN_DELAY + random.uniform(2.0, 5.0)
        await asyncio.sleep(delay)
        
        # Use a new context for better isolation/stealth per request if possible, 
        # but PlaywrightScraperBase reuses context. We'll stick to base for now.
        
        page = await self.context.new_page()
        try:
            logger.info(f"Fetching eBay URL: {url}")
            
            # Navigate with longer timeout
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if not response or response.status >= 400:
                logger.error(f"eBay returned status {response.status if response else 'None'}")
                return None
            
            # Human-like wait
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            # Scroll to trigger lazy loading
            await self._human_scroll(page)
            
            html = await page.content()
            
            # Parse
            data: EbayCoinData = self.parser.parse(html, url)
            
            return self._map_to_domain(data)
            
        except Exception as e:
            logger.exception(f"Error scraping eBay URL {url}: {e}")
            return None
        finally:
            await page.close()

    async def _human_scroll(self, page):
        """Simulate human scrolling."""
        try:
            for _ in range(3):
                await page.evaluate(f'window.scrollBy(0, {random.randint(300, 700)})')
                await asyncio.sleep(random.uniform(0.5, 1.5))
        except:
            pass

    def _map_to_domain(self, data: EbayCoinData) -> AuctionLot:
        """Map eBay model to generic Domain AuctionLot."""
        
        # Primary Image
        primary_img = None
        if data.images:
            primary_img = data.images[0].url_large or data.images[0].url
        
        # Determine sale status
        ended = data.listing.is_ended or data.listing.is_sold
        
        return AuctionLot(
            source="eBay",
            lot_id=data.ebay_item_id,
            url=data.url,
            sale_name=f"eBay Listing {data.ebay_item_id}",
            lot_number=data.ebay_item_id,
            
            # Pricing
            hammer_price=data.final_price, # Use final price (including shipping logic if applied)
            estimate_low=data.listing.current_price, # Rough mapping
            estimate_high=data.listing.buy_it_now_price,
            currency=data.listing.currency,
            
            # Attribution
            issuer=data.ruler,
            mint=data.mint,
            year_start=None,
            year_end=None,
            
            # Physical
            weight_g=data.physical.weight_g,
            diameter_mm=data.physical.diameter_mm,
            die_axis=None,
            
            # Grading
            grade=data.grading.grade or data.grading.raw_grade,
            
            # Description
            description=data.description or data.title,
            
            # Images
            primary_image_url=primary_img,
            additional_images=[img.url_large or img.url for img in data.images[1:]]
        )
