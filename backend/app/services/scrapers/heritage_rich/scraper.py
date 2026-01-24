"""
Heritage Auctions Scraper Service

Main service for scraping Heritage Auctions coin data using Playwright.
Heritage is STRICT about rate limiting - respect their server.

RATE LIMITS:
- 3 second MINIMUM between requests
- 429 errors trigger 60 second backoff
- 403 = IP blocked (wait 24 hours)
"""

import asyncio
import hashlib
import logging
import re
import random
from pathlib import Path
from typing import Optional
from datetime import datetime

from playwright.async_api import async_playwright, Browser, BrowserContext, TimeoutError as PlaywrightTimeout
from playwright_stealth.stealth import Stealth

from .parser import HeritageParser
from .models import HeritageCoinData, HeritageImage

logger = logging.getLogger(__name__)


class HeritageRateLimitError(Exception):
    """Raised when Heritage rate limits (429)"""
    pass


class HeritageBlockedError(Exception):
    """Raised when Heritage blocks IP (403)"""
    pass


class HeritageScraper:
    """
    Scraper for Heritage Auctions (HA.com).
    
    STRICT RATE LIMITING:
    - 3 second minimum between requests
    - 429 errors → 60 second backoff  
    - 403 = IP blocked (wait 24 hours)
    
    Heritage is the largest numismatic auction house and aggressively
    protects against scraping. Be respectful.
    """
    
    BASE_URL = "https://coins.ha.com"
    
    # STRICT Rate limiting - Heritage is aggressive
    MIN_DELAY_SECONDS = 3.0      # 3 second minimum
    MAX_DELAY_SECONDS = 5.0      # Random jitter up to 5s
    BACKOFF_429_SECONDS = 60.0   # 60s backoff on 429
    
    def __init__(
        self,
        image_dir: str = "data/heritage_images",
        headless: bool = True,
    ):
        self.image_dir = Path(image_dir)
        self.headless = headless
        
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = HeritageParser()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._last_request_time = 0.0
        self._consecutive_429s = 0
    
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
        
        logger.info("Heritage scraper browser started")
    
    async def stop(self):
        """Stop browser"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Heritage scraper browser stopped")
    
    async def _enforce_rate_limit(self):
        """
        Enforce STRICT rate limiting.
        
        Heritage is aggressive about blocking scrapers.
        - Minimum 3 second delay between requests
        - Random jitter to avoid patterns
        """
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        # Calculate required delay with jitter
        min_delay = self.MIN_DELAY_SECONDS
        if self._consecutive_429s > 0:
            # Exponential backoff after 429s
            min_delay = min(self.BACKOFF_429_SECONDS * (2 ** (self._consecutive_429s - 1)), 300)
            logger.warning(f"Rate limit backoff: waiting {min_delay}s (429 count: {self._consecutive_429s})")
        
        required_delay = min_delay + random.uniform(0, self.MAX_DELAY_SECONDS - self.MIN_DELAY_SECONDS)
        
        if elapsed < required_delay:
            wait_time = required_delay - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def scrape_url(
        self,
        url: str,
        download_images: bool = False,
    ) -> HeritageCoinData:
        """
        Scrape a Heritage lot by URL.
        
        STRICT RATE LIMITING APPLIES.
        """
        if not self._context:
            raise RuntimeError("Scraper not started. Use 'async with' context.")
        
        # STRICT rate limiting
        await self._enforce_rate_limit()
        
        page = await self._context.new_page()
        
        try:
            # Apply stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            logger.info(f"Fetching Heritage: {url}")
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            # Check for rate limiting / blocking
            if response:
                status = response.status
                
                if status == 429:
                    self._consecutive_429s += 1
                    logger.error(f"Heritage 429 Rate Limited! Backing off {self.BACKOFF_429_SECONDS}s")
                    await asyncio.sleep(self.BACKOFF_429_SECONDS)
                    raise HeritageRateLimitError("429 Rate Limited - backing off")
                
                if status == 403:
                    logger.error("Heritage 403 BLOCKED! IP may be blocked for 24 hours.")
                    raise HeritageBlockedError("403 Blocked - IP may need 24 hour cooldown")
                
                if status >= 400:
                    logger.error(f"Heritage error status: {status}")
                    raise Exception(f"HTTP {status}")
                
                # Success - reset 429 counter
                self._consecutive_429s = 0
            
            # Wait for content
            await asyncio.sleep(2)
            
            try:
                await page.wait_for_selector('h1, .lot-title, #auction-description', timeout=15000)
            except PlaywrightTimeout:
                logger.warning("Timeout waiting for Heritage page content")
            
            html = await page.content()
            
            # Parse
            coin_data = self.parser.parse(html, url)
            
            # Try to extract additional data via JS
            js_data = await self._extract_via_js(page)
            coin_data = self._merge_js_data(coin_data, js_data)
            
            # Download images if requested
            if download_images and coin_data.images:
                coin_data.images = await self._download_images(coin_data)
            
            return coin_data
            
        finally:
            await page.close()
    
    async def _extract_via_js(self, page) -> dict:
        """Extract additional data via JavaScript evaluation"""
        try:
            return await page.evaluate('''() => {
                const result = {};
                
                // Price
                const priceEl = document.querySelector('.price-sold, .bid-price, [class*="Price"]');
                if (priceEl) {
                    const match = priceEl.innerText.match(/\\$([\\d,]+)/);
                    if (match) result.sold_price = parseInt(match[1].replace(',', ''));
                }
                
                // Estimates
                const estEl = document.querySelector('.estimate, [class*="stimate"]');
                if (estEl) {
                    const match = estEl.innerText.match(/\\$([\\d,]+)\\s*[-–]\\s*\\$([\\d,]+)/);
                    if (match) {
                        result.estimate_low = parseInt(match[1].replace(',', ''));
                        result.estimate_high = parseInt(match[2].replace(',', ''));
                    }
                }
                
                // Bids
                const bidsEl = document.querySelector('.bid-count, [class*="bids"]');
                if (bidsEl) {
                    const match = bidsEl.innerText.match(/(\\d+)\\s*bids?/i);
                    if (match) result.bids = parseInt(match[1]);
                }
                
                // Page views
                const viewsEl = document.querySelector('[class*="views"], [class*="Views"]');
                if (viewsEl) {
                    const match = viewsEl.innerText.match(/(\\d+)/);
                    if (match) result.page_views = parseInt(match[1]);
                }
                
                // Images - comprehensive search
                result.images = [];
                const imgSelectors = [
                    'img[src*="heritagestatic"]',
                    'img[src*="cloudfront"]',
                    '.lot-image img',
                    '.gallery img',
                    '[class*="lot"] img'
                ];
                
                for (const sel of imgSelectors) {
                    document.querySelectorAll(sel).forEach(img => {
                        let src = img.src || img.getAttribute('data-src') || img.getAttribute('data-zoom');
                        if (src && !src.includes('logo') && !src.includes('icon') && src.length > 30) {
                            // Try to get high-res version
                            src = src.replace('/thumb/', '/').replace('/sm/', '/lg/');
                            if (!result.images.includes(src)) {
                                result.images.push(src);
                            }
                        }
                    });
                }
                
                // NGC cert link
                const ngcLink = document.querySelector('a[href*="ngccoin.com/certlookup"]');
                if (ngcLink) {
                    result.ngc_cert_url = ngcLink.href;
                    const certMatch = ngcLink.href.match(/certlookup\\/(\\d+)/);
                    if (certMatch) result.ngc_cert_number = certMatch[1];
                }
                
                // Sold status
                result.is_sold = !!document.querySelector('.sold, [class*="sold"], [class*="Sold"]');
                
                return result;
            }''')
        except Exception as e:
            logger.warning(f"JS extraction failed: {e}")
            return {}
    
    def _merge_js_data(self, coin_data: HeritageCoinData, js_data: dict) -> HeritageCoinData:
        """Merge JS-extracted data into parsed coin data"""
        if not js_data:
            return coin_data
        
        # Update auction info
        if coin_data.auction:
            if js_data.get('sold_price') and not coin_data.auction.sold_price_usd:
                coin_data.auction.sold_price_usd = js_data['sold_price']
            if js_data.get('estimate_low') and not coin_data.auction.estimate_low_usd:
                coin_data.auction.estimate_low_usd = js_data['estimate_low']
            if js_data.get('estimate_high') and not coin_data.auction.estimate_high_usd:
                coin_data.auction.estimate_high_usd = js_data['estimate_high']
            if js_data.get('bids') and not coin_data.auction.bids:
                coin_data.auction.bids = js_data['bids']
            if js_data.get('is_sold'):
                coin_data.auction.is_sold = True
        
        # Update NGC cert if found
        if js_data.get('ngc_cert_number') and coin_data.slab_grade:
            if not coin_data.slab_grade.certification_number:
                coin_data.slab_grade.certification_number = js_data['ngc_cert_number']
            if js_data.get('ngc_cert_url') and not coin_data.slab_grade.verification_url:
                coin_data.slab_grade.verification_url = js_data['ngc_cert_url']
        
        # Add images if we got more
        if js_data.get('images'):
            existing_urls = {img.url for img in coin_data.images}
            for i, url in enumerate(js_data['images']):
                if url not in existing_urls:
                    from .models import HeritageImage
                    coin_data.images.append(HeritageImage(
                        url=url,
                        url_full_res=url,
                        index=len(coin_data.images),
                        image_type="coin",
                        source="heritage"
                    ))
        
        return coin_data
    
    async def _download_images(self, coin_data: HeritageCoinData) -> list[HeritageImage]:
        """Download all images for a coin"""
        import httpx
        
        updated_images = []
        
        async with httpx.AsyncClient() as client:
            for img in coin_data.images:
                try:
                    url = img.url_full_res or img.url
                    
                    # Generate filename
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"heritage_{coin_data.heritage_lot_id}_{img.index}_{url_hash}.jpg"
                    local_path = self.image_dir / filename
                    
                    if not local_path.exists():
                        # Rate limit image downloads too
                        await asyncio.sleep(1)
                        response = await client.get(url, follow_redirects=True, timeout=30.0)
                        response.raise_for_status()
                        local_path.write_bytes(response.content)
                    
                    img.local_path = str(local_path)
                    updated_images.append(img)
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {img.url}: {e}")
                    updated_images.append(img)
        
        return updated_images


async def scrape_heritage_lot(url: str, download_images: bool = False) -> HeritageCoinData:
    """
    Convenience function to scrape a single Heritage lot.
    
    STRICT RATE LIMITING APPLIES.
    """
    async with HeritageScraper() as scraper:
        return await scraper.scrape_url(url, download_images)


def heritage_data_to_dict(data: HeritageCoinData) -> dict:
    """
    Convert HeritageCoinData to dict format for API response/database storage.
    """
    grade = None
    grade_service = None
    cert_number = None
    
    if data.is_slabbed and data.slab_grade:
        grade = data.slab_grade.full_grade
        grade_service = data.slab_grade.service.value
        cert_number = data.slab_grade.certification_number
    elif data.raw_grade:
        grade = data.raw_grade.full_grade
    
    return {
        'url': data.url,
        'auction_house': 'Heritage Auctions',
        'lot_id': data.heritage_lot_id,
        'title': data.title,
        'scraped_at': data.scraped_at.isoformat(),
        
        # Category
        'category': data.category,
        'subcategory': data.subcategory,
        
        # Ruler and classification
        'ruler': data.ruler,
        'ruler_title': data.ruler_title,
        'reign_dates': data.reign_dates,
        'denomination': data.denomination,
        'metal': data.metal.value if data.metal else None,
        'mint': data.mint,
        'mint_date': data.mint_date,
        
        # Physical measurements
        'diameter_mm': data.physical.diameter_mm,
        'weight_g': data.physical.weight_gm,
        'die_axis': data.physical.die_axis_hours,
        
        # Descriptions
        'obverse_legend': data.obverse_legend,
        'obverse_description': data.obverse_description,
        'reverse_legend': data.reverse_legend,
        'reverse_description': data.reverse_description,
        'exergue': data.exergue,
        'description': data.raw_description,
        
        # Grading
        'is_slabbed': data.is_slabbed,
        'grade': grade,
        'grade_service': grade_service,
        'cert_number': cert_number,
        'condition_notes': data.condition_notes,
        'surface_issues': data.surface_issues,
        
        # References
        'references': [ref.normalized for ref in data.references],
        'references_raw': [ref.raw_text for ref in data.references],
        
        # Provenance
        'provenance': data.provenance.raw_text if data.provenance else None,
        'collection_name': data.provenance.collection_name if data.provenance else None,
        'has_provenance': data.has_provenance,
        
        # Historical
        'historical_notes': data.historical_notes,
        
        # Auction info
        'auction_id': data.auction.auction_id if data.auction else None,
        'auction_name': data.auction.auction_name if data.auction else None,
        'auction_type': data.auction.auction_type.value if data.auction and data.auction.auction_type else None,
        'lot_number': data.auction.lot_number if data.auction else None,
        'auction_date': data.auction.auction_date.isoformat() if data.auction and data.auction.auction_date else None,
        'hammer_price': data.auction.sold_price_usd if data.auction else None,
        'estimate_low': data.auction.estimate_low_usd if data.auction else None,
        'estimate_high': data.auction.estimate_high_usd if data.auction else None,
        'total_price_usd': data.auction.total_price_usd if data.auction else None,
        'bids': data.auction.bids if data.auction else None,
        'is_sold': data.auction.is_sold if data.auction else False,
        'currency': 'USD',
        
        # Images
        'photos': [img.url for img in data.images],
        'primary_photo_url': data.images[0].url if data.images else None,
    }
