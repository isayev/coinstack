"""
eBay Scraper Service
"""

import asyncio
import logging
import random
import hashlib
from typing import Optional

from src.domain.services.scraper_service import IScraper, ScrapeResult, ScrapeStatus
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import EbayParser
from .models import EbayCoinData

logger = logging.getLogger(__name__)

class EbayScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for eBay listings with enhanced stealth.
    Includes automatic retry logic and rate limiting (5.0s between requests).
    """

    BASE_URL = "https://www.ebay.com"

    def __init__(self, headless: bool = True):
        super().__init__(headless=headless, source="ebay")
        self.parser = EbayParser()
    
    def can_handle(self, url: str) -> bool:
        return "ebay.com" in url or "ebay" in url.lower()
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape an eBay listing URL with automatic rate limiting and retry."""
        if not await self.ensure_browser():
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message="Failed to start browser")

        # Enforce rate limiting (handled by base class: 5.0s for eBay)
        await self._enforce_rate_limit()

        # First, visit main eBay site to establish session (helps bypass anti-bot)
        try:
            session_page = await self.context.new_page()
            try:
                logger.debug("Establishing eBay session...")
                await session_page.goto("https://www.ebay.com", wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(random.uniform(1.5, 3.0))  # Human-like pause
            except Exception as e:
                logger.warning(f"Failed to visit eBay main site (continuing anyway): {e}")
            finally:
                await session_page.close()
        except Exception as e:
            logger.warning(f"Error establishing eBay session: {e}")

        page = await self.context.new_page()
        try:
            logger.info(f"Fetching eBay URL: {url}")
            
            # Navigate with longer timeout
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            if not response:
                return ScrapeResult(status=ScrapeStatus.ERROR, error_message="No response received")
            
            if response.status >= 400:
                html = await page.content()
                if "Checking your browser" in html or "Pardon Our Interruption" in html:
                    logger.error("eBay anti-bot protection detected - blocking automated access")
                    return ScrapeResult(status=ScrapeStatus.BLOCKED, error_message="Anti-bot detection triggered")
                return ScrapeResult(status=ScrapeStatus.ERROR, error_message=f"HTTP Error {response.status}")
            
            # Human-like wait
            await asyncio.sleep(random.uniform(2.0, 4.0))
            
            # Scroll to trigger lazy loading
            await self._human_scroll(page)
            
            html = await page.content()
            
            # Check again for anti-bot page after waiting
            if "Checking your browser" in html or "Pardon Our Interruption" in html:
                logger.error("eBay anti-bot protection detected after page load")
                return ScrapeResult(status=ScrapeStatus.BLOCKED, error_message="Anti-bot detection triggered (post-load)")
            
            # Parse
            data: EbayCoinData = self.parser.parse(html, url)
            
            if not data:
                 return ScrapeResult(status=ScrapeStatus.ERROR, error_message="Parser returned no data")

            lot = self._map_to_domain(data)
            return ScrapeResult(status=ScrapeStatus.SUCCESS, data=lot)
            
        except Exception as e:
            logger.exception(f"Error scraping eBay URL {url}: {e}")
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message=str(e))
        finally:
            await page.close()

    async def _human_scroll(self, page):
        """Simulate human scrolling."""
        try:
            for _ in range(3):
                await page.evaluate(f'window.scrollBy(0, {random.randint(300, 700)})')
                await asyncio.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.warning(f"Human scroll simulation failed: {type(e).__name__}: {str(e)}")
            # Continue anyway - scrolling is nice-to-have for stealth

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