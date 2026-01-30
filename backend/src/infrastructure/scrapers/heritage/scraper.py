"""
Heritage Auctions Scraper Service
"""

import asyncio
import logging
import random
import re
from typing import Optional
from pathlib import Path

from src.domain.services.scraper_service import IScraper, ScrapeResult, ScrapeStatus
from src.domain.auction import AuctionLot
from src.infrastructure.scrapers.base_playwright import PlaywrightScraperBase

from .parser import HeritageParser
from .models import HeritageCoinData

logger = logging.getLogger(__name__)

class HeritageScraper(PlaywrightScraperBase, IScraper):
    """
    Scraper for Heritage Auctions (coins.ha.com).
    Uses Playwright for content fetching and regex for detailed parsing.
    Includes automatic retry logic and rate limiting (2.0s between requests).
    """

    BASE_URL = "https://coins.ha.com"

    def __init__(self, headless: bool = True):
        super().__init__(headless=headless, source="heritage")
        self.parser = HeritageParser()
    
    def can_handle(self, url: str) -> bool:
        return "coins.ha.com" in url or "heritage" in url.lower()
    
    async def scrape(self, url: str) -> ScrapeResult:
        """Scrape a Heritage lot URL with automatic rate limiting and retry."""
        if not await self.ensure_browser():
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message="Failed to start browser")

        # Enforce rate limiting (handled by base class)
        await self._enforce_rate_limit()

        page = await self.context.new_page()
        try:
            # Set extra headers for Heritage
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://coins.ha.com/',
            })

            logger.info(f"Fetching Heritage URL: {url}")
            response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            if not response:
                return ScrapeResult(status=ScrapeStatus.ERROR, error_message="No response received")

            if response.status == 404:
                return ScrapeResult(status=ScrapeStatus.NOT_FOUND, error_message="Lot not found")
            
            if response.status in (403, 429):
                return ScrapeResult(status=ScrapeStatus.BLOCKED, error_message=f"Blocked (HTTP {response.status})")
            
            if response.status >= 400:
                return ScrapeResult(status=ScrapeStatus.ERROR, error_message=f"HTTP Error {response.status}")
            
            # Wait for key elements
            try:
                await page.wait_for_selector('.lot-title', timeout=10000)
            except Exception:
                pass # Try parsing anyway
            
            # Enhance data with JS (Prices aren't always in static HTML)
            js_data = await page.evaluate('''() => {
                const result = {};
                
                // Price
                const priceEl = document.querySelector('.price-sold, .bid-price, [class*="Price"]');
                if (priceEl) {
                    const match = priceEl.innerText.match(/\$([\d,]+)/);
                    if (match) result.sold_price = parseInt(match[1].replace(',', ''));
                }
                
                // Estimates
                const estEl = document.querySelector('.estimate, [class*="stimate"]');
                if (estEl) {
                    const match = estEl.innerText.match(/\$([\d,]+)\s*[-–]\s*\$([\d,]+)/);
                    if (match) {
                        result.estimate_low = parseInt(match[1].replace(',', ''));
                        result.estimate_high = parseInt(match[2].replace(',', ''));
                    }
                }
                
                return result;
            }''')
            
            html = await page.content()
            
            # Parse Structured Data
            data: HeritageCoinData = self.parser.parse(html, url)
            
            # Merge JS data
            if data.auction:
                if js_data.get('sold_price'):
                    data.auction.sold_price_usd = js_data['sold_price']
                    data.auction.is_sold = True
                if js_data.get('estimate_low'):
                    data.auction.estimate_low_usd = js_data['estimate_low']
                    data.auction.estimate_high_usd = js_data['estimate_high']
            
            lot = self._map_to_domain(data)
            return ScrapeResult(status=ScrapeStatus.SUCCESS, data=lot)
            
        except Exception as e:
            logger.exception(f"Error scraping Heritage URL {url}: {e}")
            return ScrapeResult(status=ScrapeStatus.ERROR, error_message=str(e))
        finally:
            await page.close()

    def _map_to_domain(self, data: HeritageCoinData) -> AuctionLot:
        """Map Heritage-specific model to generic Domain AuctionLot."""
        
        # Primary Image
        primary_img = None
        if data.images:
            primary_img = data.images[0].url_full_res or data.images[0].url
        
        return AuctionLot(
            source="Heritage Auctions",
            lot_id=data.heritage_lot_id,
            url=data.url,
            sale_name=data.auction.auction_name if data.auction else "Heritage Auction",
            lot_number=str(data.auction.lot_number) if data.auction else "0",
            
            # Pricing
            hammer_price=data.auction.sold_price_usd if data.auction else None,
            estimate_low=data.auction.estimate_low_usd if data.auction else None,
            estimate_high=data.auction.estimate_high_usd if data.auction else None,
            currency="USD",
            
            # Attribution
            issuer=data.ruler,
            mint=data.mint,
            year_start=None, # Parser could define logic to split reign_dates/mint_date
            year_end=None,
            
            # Physical
            weight_g=data.physical.weight_gm,
            diameter_mm=data.physical.diameter_mm,
            die_axis=data.physical.die_axis_hours,
            
            # Grading
            grade=data.grade_display,
            service=data.slab_grade.service.value if data.slab_grade else None,
            certification=data.certification_number,
            
            # Description
            description=data.raw_description,
            
            # Images
            primary_image_url=primary_img,
            additional_images=[img.url_full_res or img.url for img in data.images[1:]]
        )