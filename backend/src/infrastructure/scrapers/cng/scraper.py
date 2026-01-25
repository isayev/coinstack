"""
CNG Scraper Service
"""

import asyncio
import logging
import random
import re
from typing import Optional

from src.domain.services.scraper_service import IScraper
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import CNGParser
from .models import CNGCoinData

logger = logging.getLogger(__name__)

class CNGScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for Classical Numismatic Group (CNG).
    Includes automatic retry logic and rate limiting (3.0s between requests).
    """

    BASE_URL = "https://auctions.cngcoins.com"

    def __init__(self, headless: bool = True):
        super().__init__(headless=headless, source="cng")
        self.parser = CNGParser()
    
    def can_handle(self, url: str) -> bool:
        return "cngcoins.com" in url or "cng" in url.lower()
    
    async def scrape(self, url: str) -> Optional[AuctionLot]:
        """Scrape a CNG lot URL with automatic rate limiting and retry."""
        if not await self.ensure_browser():
            return None

        # Enforce rate limiting (handled by base class: 3.0s for CNG)
        await self._enforce_rate_limit()

        page = await self.context.new_page()
        try:
            logger.info(f"Fetching CNG URL: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if not response or response.status >= 400:
                logger.error(f"CNG returned status {response.status if response else 'None'}")
                return None
            
            # Wait for Angular content
            try:
                await page.wait_for_selector('[class*="lot"]', timeout=10000)
            except TimeoutError:
                logger.warning(f"Timeout waiting for lot selector on {url}")
            except Exception as e:
                logger.error(f"Error waiting for lot selector on {url}: {type(e).__name__}: {str(e)}")
            
            html = await page.content()
            
            # Parse
            data: CNGCoinData = self.parser.parse(html, url)
            
            return self._map_to_domain(data)
            
        except Exception as e:
            logger.exception(f"Error scraping CNG URL {url}: {e}")
            return None
        finally:
            await page.close()

    def _map_to_domain(self, data: CNGCoinData) -> AuctionLot:
        """Map CNG-specific model to generic Domain AuctionLot."""
        
        # Primary Image
        primary_img = None
        if data.images:
            primary_img = data.images[0].url_full_res or data.images[0].url
        
        return AuctionLot(
            source="CNG",
            lot_id=data.cng_lot_id,
            url=data.url,
            sale_name=data.auction.auction_name if data.auction else "CNG Auction",
            lot_number=str(data.auction.lot_number) if data.auction else "0",
            
            # Pricing
            hammer_price=data.auction.sold_price_usd if data.auction else None,
            estimate_low=data.auction.estimate_usd if data.auction else None,
            estimate_high=data.auction.estimate_usd if data.auction else None,
            currency="USD",
            
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
            additional_images=[img.url_full_res or img.url for img in data.images[1:]]
        )
