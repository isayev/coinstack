"""
Biddr Scraper Service

Main service for scraping Biddr auction data using Playwright.
Handles JavaScript-rendered pages and rate limiting.
"""

import asyncio
import logging
import random
import re
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext
from playwright_stealth.stealth import Stealth

from .parser import BiddrParser
from .models import BiddrCoinData, BiddrImage

logger = logging.getLogger(__name__)


class BiddrScraper:
    """
    Scraper for Biddr auction platform.
    
    Uses Playwright for JavaScript rendering and handles
    multiple sub-houses (Savoca, Roma, Leu, etc.).
    """
    
    BASE_URL = "https://www.biddr.com"
    
    # Rate limiting
    MIN_DELAY_SECONDS = 2.0
    MAX_DELAY_SECONDS = 4.0
    
    def __init__(
        self, 
        image_dir: str = "data/biddr_images",
        headless: bool = True,
    ):
        self.image_dir = Path(image_dir)
        self.headless = headless
        
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = BiddrParser()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.stop()
    
    async def start(self):
        """Start browser"""
        self._playwright = await async_playwright().start()
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )
        
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
        )
        
        logger.info("Biddr scraper browser started")
    
    async def stop(self):
        """Stop browser"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Biddr scraper browser stopped")
    
    async def scrape_url(
        self,
        url: str,
        download_images: bool = False,
    ) -> BiddrCoinData:
        """
        Scrape a Biddr lot by URL.
        """
        if not self._context:
            raise RuntimeError("Scraper not started. Use 'async with' context.")
        
        # Rate limiting
        await asyncio.sleep(random.uniform(self.MIN_DELAY_SECONDS, self.MAX_DELAY_SECONDS))
        
        page = await self._context.new_page()
        
        try:
            # Apply stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            logger.info(f"Fetching Biddr: {url}")
            
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content
            await asyncio.sleep(3)
            
            try:
                await page.wait_for_selector(
                    'h1, h2, .lot-info, [class*="lot"], [class*="description"]',
                    timeout=10000
                )
            except:
                pass
            
            html = await page.content()
            
            # Parse
            coin_data = self.parser.parse(html, url)
            
            # Download images if requested
            if download_images and coin_data.images:
                coin_data.images = await self._download_images(coin_data)
            
            return coin_data
            
        finally:
            await page.close()
    
    async def scrape_lot(
        self,
        auction_id: int,
        lot_id: int,
        download_images: bool = False,
    ) -> BiddrCoinData:
        """
        Scrape by auction and lot IDs.
        """
        url = f"{self.BASE_URL}/auctions/browse?a={auction_id}&l={lot_id}"
        return await self.scrape_url(url, download_images)
    
    async def _download_images(self, coin_data: BiddrCoinData) -> list[BiddrImage]:
        """Download images locally"""
        import httpx
        
        updated_images = []
        
        async with httpx.AsyncClient() as client:
            for img in coin_data.images:
                try:
                    url = img.url_large or img.url
                    
                    # Generate filename
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"biddr_{coin_data.biddr_lot_id}_{img.index}_{url_hash}.jpg"
                    local_path = self.image_dir / filename
                    
                    if not local_path.exists():
                        await asyncio.sleep(0.5)
                        response = await client.get(url, follow_redirects=True, timeout=30.0)
                        response.raise_for_status()
                        local_path.write_bytes(response.content)
                    
                    img.local_path = str(local_path)
                    updated_images.append(img)
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {img.url}: {e}")
                    updated_images.append(img)
        
        return updated_images


async def scrape_biddr_lot(url: str, download_images: bool = False) -> BiddrCoinData:
    """
    Convenience function to scrape a single Biddr lot.
    """
    async with BiddrScraper() as scraper:
        return await scraper.scrape_url(url, download_images)


def biddr_data_to_dict(data: BiddrCoinData) -> dict:
    """
    Convert BiddrCoinData to dict format for API response/database storage.
    """
    return {
        'url': data.url,
        'auction_house': 'Biddr',
        'sub_house': data.sub_house.value if data.sub_house else None,
        'lot_id': data.biddr_lot_id,
        'title': data.title,
        'scraped_at': data.scraped_at.isoformat(),
        
        # Ruler and classification
        'ruler': data.ruler,
        'ruler_title': data.ruler_title,
        'reign_dates': data.reign_dates,
        'era': data.era,
        'denomination': data.denomination,
        'metal': data.metal.value if data.metal else None,
        'mint': data.mint,
        'mint_date': data.mint_date,
        'struck_under': data.struck_under,
        
        # Physical measurements
        'diameter_mm': data.physical.diameter_mm,
        'weight_g': data.physical.weight_g,
        'die_axis': data.physical.die_axis_hours,
        
        # Descriptions
        'obverse_description': data.obverse_description,
        'reverse_description': data.reverse_description,
        'exergue': data.exergue,
        'description': data.raw_description,
        
        # Condition
        'grade': data.grade,
        'grade_german': data.grade_german,
        'condition_notes': data.condition_notes,
        
        # References
        'references': [ref.normalized for ref in data.references],
        'references_raw': [ref.raw_text for ref in data.references],
        
        # Provenance
        'provenance': data.provenance.raw_text if data.provenance else None,
        'pedigree_year': data.provenance.pedigree_year if data.provenance else None,
        'has_provenance': data.has_provenance,
        
        # Auction info
        'auction_name': data.auction.auction_name if data.auction else None,
        'lot_number': data.auction.lot_number if data.auction else None,
        'hammer_price': data.auction.hammer_price if data.auction else None,
        'estimate_low': data.auction.estimate_low if data.auction else None,
        'estimate_high': data.auction.estimate_high if data.auction else None,
        'starting_price': data.auction.starting_price if data.auction else None,
        'total_price_usd': data.total_price,
        'currency': data.auction.currency if data.auction else 'EUR',
        'bids': data.auction.bids if data.auction else None,
        'is_sold': data.auction.is_sold if data.auction else False,
        'is_closed': data.auction.is_closed if data.auction else False,
        
        # Images
        'photos': [img.url for img in data.images],
        'primary_photo_url': data.images[0].url if data.images else None,
    }
