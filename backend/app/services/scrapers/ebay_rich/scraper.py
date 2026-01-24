"""
eBay Scraper Service

Main service for scraping eBay listings using Playwright.
Handles eBay's JavaScript-rendered pages and anti-bot measures.
Enhanced with stealth features and respectful rate limiting.
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

from .parser import EbayParser
from .models import EbayCoinData, EbayImage

logger = logging.getLogger(__name__)


# Realistic user agents (recent Chrome versions on Windows)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# Realistic viewport sizes (common monitor resolutions)
VIEWPORTS = [
    {'width': 1920, 'height': 1080},
    {'width': 1536, 'height': 864},
    {'width': 1440, 'height': 900},
    {'width': 1366, 'height': 768},
    {'width': 1280, 'height': 720},
    {'width': 2560, 'height': 1440},
]


class EbayScraper:
    """
    Scraper for eBay listings.
    
    Uses Playwright for JavaScript rendering with enhanced stealth.
    """
    
    # Rate limiting - respectful delays to avoid detection
    MIN_DELAY_SECONDS = 8.0
    MAX_DELAY_SECONDS = 15.0
    
    # Additional random micro-delays for human-like behavior
    MIN_ACTION_DELAY = 0.3
    MAX_ACTION_DELAY = 1.5
    
    def __init__(
        self,
        image_dir: str = "data/ebay_images",
        headless: bool = True,
    ):
        self.image_dir = Path(image_dir)
        self.headless = headless
        
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = EbayParser()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._request_count = 0
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        await self.stop()
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent string."""
        return random.choice(USER_AGENTS)
    
    def _get_random_viewport(self) -> dict:
        """Get a random viewport size."""
        return random.choice(VIEWPORTS)
    
    async def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """Add a random delay for human-like behavior."""
        min_sec = min_sec or self.MIN_ACTION_DELAY
        max_sec = max_sec or self.MAX_ACTION_DELAY
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    async def start(self):
        """Start browser with enhanced stealth settings"""
        self._playwright = await async_playwright().start()
        
        # Enhanced browser args for stealth
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--disable-gpu',
            '--window-size=1920,1080',
            '--start-maximized',
            '--disable-extensions',
            '--disable-plugins-discovery',
            '--disable-infobars',
            '--ignore-certificate-errors',
            '--no-first-run',
            '--no-default-browser-check',
            '--disable-background-networking',
            '--disable-sync',
            '--disable-translate',
            '--metrics-recording-only',
            '--safebrowsing-disable-auto-update',
        ]
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=browser_args,
        )
        
        # Random viewport and user agent for this session
        viewport = self._get_random_viewport()
        user_agent = self._get_random_user_agent()
        
        self._context = await self._browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation'],
            color_scheme='light',
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            # Additional headers to appear more legitimate
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
        )
        
        # Note: Don't block images as we need their URLs for extraction
        # Block only fonts and unnecessary resources
        await self._context.route('**/*.{woff,woff2,ttf,otf}', lambda route: route.abort())
        
        logger.info(f"eBay scraper browser started (viewport: {viewport['width']}x{viewport['height']})")
    
    async def stop(self):
        """Stop browser"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("eBay scraper browser stopped")
    
    async def scrape_url(
        self,
        url: str,
        download_images: bool = False,
    ) -> EbayCoinData:
        """
        Scrape an eBay listing by URL with human-like behavior.
        """
        if not self._context:
            raise RuntimeError("Scraper not started. Use 'async with' context.")
        
        self._request_count += 1
        
        # Rate limiting with progressive delays (longer delays after many requests)
        base_delay = random.uniform(self.MIN_DELAY_SECONDS, self.MAX_DELAY_SECONDS)
        
        # Add extra delay every 5 requests to simulate breaks
        if self._request_count % 5 == 0:
            extra_delay = random.uniform(5.0, 15.0)
            logger.info(f"Taking a longer break ({extra_delay:.1f}s) after {self._request_count} requests")
            base_delay += extra_delay
        
        # Occasional very long pause (like a human getting distracted)
        if random.random() < 0.1:  # 10% chance
            extra_delay = random.uniform(10.0, 30.0)
            logger.info(f"Random long pause ({extra_delay:.1f}s)")
            base_delay += extra_delay
        
        await asyncio.sleep(base_delay)
        
        page = await self._context.new_page()
        
        try:
            # Apply stealth
            stealth = Stealth()
            await stealth.apply_stealth_async(page)
            
            # Additional JavaScript to mask automation
            await page.add_init_script("""
                // Override navigator properties
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override chrome property
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add realistic plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin' }
                    ]
                });
                
                // Add realistic languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            logger.info(f"Fetching eBay ({self._request_count}): {url}")
            
            # Small delay before navigation (human reaction time)
            await self._random_delay(0.5, 1.5)
            
            # Navigate with longer timeout for eBay
            await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Human-like wait for page to render
            await self._random_delay(2.0, 4.0)
            
            try:
                await page.wait_for_selector(
                    'h1, .x-item-title, #itemTitle, .vi-title',
                    timeout=20000
                )
            except:
                logger.warning("Timeout waiting for eBay page title")
            
            # Human-like scrolling behavior
            await self._human_like_scroll(page)
            
            # Small delay after scrolling
            await self._random_delay(1.0, 2.0)
            
            html = await page.content()
            
            # Parse
            coin_data = self.parser.parse(html, url)
            
            # Download images if requested
            if download_images and coin_data.images:
                coin_data.images = await self._download_images(coin_data)
            
            return coin_data
            
        finally:
            # Small delay before closing (humans don't instantly close tabs)
            await self._random_delay(0.3, 0.8)
            await page.close()
    
    async def _human_like_scroll(self, page):
        """Simulate human-like scrolling behavior."""
        try:
            # Get page height
            page_height = await page.evaluate('document.body.scrollHeight')
            viewport_height = await page.evaluate('window.innerHeight')
            
            if page_height <= viewport_height:
                return
            
            # Scroll down in chunks like a human would
            current_position = 0
            scroll_distance = random.randint(200, 400)
            
            while current_position < page_height * 0.6:  # Scroll to ~60% of page
                # Random scroll amount
                scroll_distance = random.randint(150, 350)
                current_position += scroll_distance
                
                await page.evaluate(f'window.scrollTo(0, {current_position})')
                await self._random_delay(0.2, 0.6)
            
            # Sometimes scroll back up a bit (like reviewing something)
            if random.random() < 0.3:  # 30% chance
                scroll_back = random.randint(100, 300)
                await page.evaluate(f'window.scrollTo(0, {current_position - scroll_back})')
                await self._random_delay(0.5, 1.0)
                
        except Exception as e:
            logger.debug(f"Scroll failed (non-critical): {e}")
    
    async def scrape_item(
        self,
        item_id: str,
        download_images: bool = False,
    ) -> EbayCoinData:
        """
        Scrape by eBay item ID.
        """
        url = f"https://www.ebay.com/itm/{item_id}"
        return await self.scrape_url(url, download_images)
    
    async def _download_images(self, coin_data: EbayCoinData) -> list[EbayImage]:
        """Download images locally with stealth headers."""
        import httpx
        
        updated_images = []
        
        # Use random user agent for image downloads
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://www.ebay.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
        }
        
        async with httpx.AsyncClient(headers=headers) as client:
            for img in coin_data.images:
                try:
                    url = img.url_large or img.url
                    
                    # Generate filename
                    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    filename = f"ebay_{coin_data.ebay_item_id}_{img.index}_{url_hash}.jpg"
                    local_path = self.image_dir / filename
                    
                    if not local_path.exists():
                        # Random delay between image downloads (1-3 seconds)
                        await asyncio.sleep(random.uniform(1.0, 3.0))
                        response = await client.get(url, follow_redirects=True, timeout=30.0)
                        response.raise_for_status()
                        local_path.write_bytes(response.content)
                    
                    img.local_path = str(local_path)
                    updated_images.append(img)
                    
                except Exception as e:
                    logger.warning(f"Failed to download image {img.url}: {e}")
                    updated_images.append(img)
        
        return updated_images


async def scrape_ebay_listing(url: str, download_images: bool = False) -> EbayCoinData:
    """
    Convenience function to scrape a single eBay listing.
    """
    async with EbayScraper() as scraper:
        return await scraper.scrape_url(url, download_images)


def ebay_data_to_dict(data: EbayCoinData) -> dict:
    """
    Convert EbayCoinData to dict format for API response/database storage.
    """
    return {
        'url': data.url,
        'auction_house': 'eBay',
        'lot_id': data.ebay_item_id,
        'title': data.title,
        'scraped_at': data.scraped_at.isoformat(),
        
        # Coin details (LOW TRUST)
        'ruler': data.ruler,
        'reign_dates': data.reign_dates,
        'era': data.era,
        'denomination': data.denomination,
        'metal': data.metal,
        'mint': data.mint,
        'mint_date': data.mint_date,
        
        # Physical
        'diameter_mm': data.physical.diameter_mm,
        'weight_g': data.physical.weight_g,
        
        # Description
        'description': data.description,
        'item_specifics': data.item_specifics,
        
        # References (LOW TRUST)
        'references': [ref.normalized for ref in data.references],
        'references_raw': [ref.raw_text for ref in data.references],
        
        # Grading
        'is_slabbed': data.grading.is_slabbed,
        'grade_service': data.grading.grading_service,
        'grade': data.grading.grade or data.grading.raw_grade,
        'cert_number': data.grading.cert_number,
        
        # Condition
        'condition': data.condition.value if data.condition else None,
        
        # Listing info (HIGH TRUST)
        'listing_type': data.listing.listing_type.value if data.listing.listing_type else None,
        'current_price': data.listing.current_price,
        'hammer_price': data.listing.sold_price or data.listing.current_price,
        'buy_it_now_price': data.listing.buy_it_now_price,
        'shipping_cost': data.listing.shipping_cost,
        'currency': data.listing.currency,
        'bids': data.listing.bid_count,
        'is_sold': data.listing.is_sold,
        'is_ended': data.listing.is_ended,
        'total_price': data.final_price,
        
        # Seller info (HIGH TRUST)
        'seller_username': data.seller.username,
        'seller_feedback_score': data.seller.feedback_score,
        'seller_feedback_percent': data.seller.feedback_percent,
        'seller_is_top_rated': data.seller.is_top_rated,
        'seller_location': data.seller.location,
        'is_trusted_seller': data.is_trusted_seller,
        
        # Images (HIGH TRUST)
        'photos': [img.url for img in data.images],
        'primary_photo_url': data.images[0].url if data.images else None,
        
        # Trust metadata
        '_trust_note': 'eBay data is user-generated. Trust only: prices, dates, images, seller info.',
    }
