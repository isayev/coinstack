"""
CNG Scraper Service

Main service for scraping CNG auction data:
- Fetches lot pages using Playwright (for JS-rendered content)
- Parses HTML into structured data using JSON-LD
- Downloads images locally
- Handles search and pagination
"""

import asyncio
import hashlib
import logging
import re
import random
from pathlib import Path
from typing import Optional, AsyncIterator
from datetime import datetime
from urllib.parse import urljoin, urlencode

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth.stealth import Stealth

from .parser import CNGParser
from .models import CNGCoinData, CNGImage, CNGSearchResult, CNGSearchResults

logger = logging.getLogger(__name__)


class CNGScraper:
    """
    Scraper for Classical Numismatic Group (CNG) auction site.
    
    Uses Playwright for JavaScript-rendered pages and extracts
    JSON-LD structured data for clean metadata extraction.
    """
    
    BASE_URL = "https://auctions.cngcoins.com"
    
    # Rate limiting
    MIN_DELAY_SECONDS = 2.0
    MAX_DELAY_SECONDS = 4.0
    
    def __init__(
        self, 
        image_dir: str = "data/cng_images",
        headless: bool = True,
    ):
        """
        Initialize scraper.
        
        Args:
            image_dir: Directory for downloaded images
            headless: Run browser in headless mode
        """
        self.image_dir = Path(image_dir)
        self.headless = headless
        
        self.image_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = CNGParser()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit"""
        await self.stop()
    
    async def start(self):
        """Start browser"""
        self._playwright = await async_playwright().start()
        
        # Launch with anti-detection options
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )
        
        # Create context with realistic settings
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        
        logger.info("CNG scraper browser started")
    
    async def stop(self):
        """Stop browser"""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("CNG scraper browser stopped")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MAIN SCRAPING METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def scrape_lot(
        self, 
        lot_id: str,
        download_images: bool = True,
    ) -> CNGCoinData:
        """
        Scrape a single CNG lot by ID.
        
        Args:
            lot_id: CNG lot ID (e.g., "4-DJ6RZM")
            download_images: Whether to download images locally
            
        Returns:
            CNGCoinData with all extracted fields
        """
        url = f"{self.BASE_URL}/lots/view/{lot_id}"
        return await self.scrape_url(url, download_images)
    
    async def scrape_url(
        self,
        url: str,
        download_images: bool = True,
    ) -> CNGCoinData:
        """
        Scrape a CNG lot by full URL.
        
        Args:
            url: Full CNG lot URL
            download_images: Whether to download images locally
            
        Returns:
            CNGCoinData with all extracted fields
        """
        # Fetch page with Playwright
        html = await self._fetch_page(url)
        
        # Parse HTML
        coin_data = self.parser.parse(html, url)
        
        # Download images if requested
        if download_images and coin_data.images:
            coin_data.images = await self._download_images(coin_data)
        
        return coin_data
    
    async def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 48,
    ) -> CNGSearchResults:
        """
        Search CNG auctions.
        
        Args:
            query: Search terms
            page: Page number (1-indexed)
            per_page: Results per page
            
        Returns:
            CNGSearchResults with lot summaries
        """
        params = {
            "search": query,
            "page": page,
            "per_page": per_page,
        }
        
        url = f"{self.BASE_URL}/lots?{urlencode(params)}"
        html = await self._fetch_page(url)
        
        return self._parse_search_results(html, query, page, per_page)
    
    async def search_all(
        self,
        query: str,
        max_results: int = 500,
    ) -> AsyncIterator[CNGSearchResult]:
        """
        Search and iterate through all results.
        
        Args:
            query: Search terms
            max_results: Maximum results to return
            
        Yields:
            CNGSearchResult for each lot
        """
        page = 1
        count = 0
        
        while count < max_results:
            results = await self.search(query, page=page)
            
            for result in results.results:
                yield result
                count += 1
                if count >= max_results:
                    return
            
            if not results.has_more:
                break
            
            page += 1
    
    async def scrape_search_results(
        self,
        query: str,
        max_results: int = 100,
        download_images: bool = True,
    ) -> AsyncIterator[CNGCoinData]:
        """
        Search and scrape full data for each result.
        
        Args:
            query: Search terms
            max_results: Maximum lots to scrape
            download_images: Whether to download images
            
        Yields:
            CNGCoinData for each lot
        """
        async for result in self.search_all(query, max_results):
            try:
                coin_data = await self.scrape_lot(result.lot_id, download_images)
                yield coin_data
            except Exception as e:
                logger.error(f"Failed to scrape lot {result.lot_id}: {e}")
                continue
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # PAGE FETCHING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def _fetch_page(self, url: str, retries: int = 3) -> str:
        """
        Fetch page using Playwright with retry logic.
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
            
            logger.info(f"Fetching CNG: {url}")
            
            # Navigate
            response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for Angular to render
            try:
                await page.wait_for_selector('[class*="lot"]', timeout=5000)
            except:
                pass  # May not have lot elements on all pages
            
            # Additional wait for dynamic content
            await asyncio.sleep(1)
            
            if response and response.status >= 400:
                if retries > 0:
                    logger.warning(f"Got {response.status}, retrying...")
                    await page.close()
                    return await self._fetch_page(url, retries - 1)
                raise Exception(f"HTTP {response.status} for {url}")
            
            html = await page.content()
            return html
            
        finally:
            await page.close()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # IMAGE DOWNLOADING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def _download_images(self, coin_data: CNGCoinData) -> list[CNGImage]:
        """
        Download all images for a coin.
        
        Returns updated image list with local_path set.
        """
        import httpx
        
        updated_images = []
        
        async with httpx.AsyncClient() as client:
            for img in coin_data.images:
                try:
                    local_path = await self._download_image(
                        client,
                        coin_data.cng_lot_id, 
                        img.url_full_res or img.url, 
                        img.index
                    )
                    img.local_path = str(local_path)
                    updated_images.append(img)
                except Exception as e:
                    logger.warning(f"Failed to download image {img.url}: {e}")
                    updated_images.append(img)  # Keep without local_path
        
        return updated_images
    
    async def _download_image(
        self, 
        client,
        lot_id: str, 
        url: str, 
        index: int
    ) -> Path:
        """
        Download a single image.
        
        Returns local path.
        """
        # Generate filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"cng_{lot_id}_{index}_{url_hash}.jpg"
        local_path = self.image_dir / filename
        
        # Skip if already downloaded
        if local_path.exists():
            logger.debug(f"Image already exists: {local_path}")
            return local_path
        
        # Rate limit
        await asyncio.sleep(0.5)
        
        logger.info(f"Downloading image: {url}")
        response = await client.get(url, follow_redirects=True, timeout=30.0)
        response.raise_for_status()
        
        # Save
        local_path.write_bytes(response.content)
        
        return local_path
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SEARCH RESULTS PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_search_results(
        self, 
        html: str, 
        query: str, 
        page: int, 
        per_page: int
    ) -> CNGSearchResults:
        """Parse search results page"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # Find lot links
        lot_links = soup.find_all('a', href=re.compile(r'/lots/view/([^/]+)'))
        seen_ids = set()
        
        for link in lot_links:
            href = link.get('href', '')
            lot_id_match = re.search(r'/lots/view/([^/]+)', href)
            if not lot_id_match:
                continue
            
            lot_id = lot_id_match.group(1)
            if lot_id in seen_ids:
                continue
            seen_ids.add(lot_id)
            
            # Get title from link or parent
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                parent = link.find_parent(['div', 'article', 'li'])
                if parent:
                    title_elem = parent.find(['h2', 'h3', 'h4', 'span'], class_=re.compile(r'title|name'))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
            
            # Extract lot number
            lot_num = 0
            parent = link.find_parent(['div', 'article', 'li'])
            if parent:
                lot_num_match = re.search(r'Lot\s*#?\s*(\d+)', parent.get_text())
                if lot_num_match:
                    lot_num = int(lot_num_match.group(1))
            
            # Check for pedigree badge
            pedigree_year = None
            if parent:
                pedigree_match = re.search(r'Pedigreed to (\d{4})', parent.get_text())
                if pedigree_match:
                    pedigree_year = int(pedigree_match.group(1))
            
            # Check for sold price
            sold_price = None
            is_sold = False
            if parent:
                sold_match = re.search(r'SOLD\s*\$?([\d,]+)', parent.get_text())
                if sold_match:
                    sold_price = int(sold_match.group(1).replace(',', ''))
                    is_sold = True
            
            # Find thumbnail
            thumbnail = None
            if parent:
                img = parent.find('img')
                if img:
                    thumbnail = img.get('src', '')
            
            results.append(CNGSearchResult(
                lot_id=lot_id,
                lot_number=lot_num,
                title=title,
                url=urljoin(self.BASE_URL, href),
                thumbnail_url=thumbnail,
                sold_price_usd=sold_price,
                is_sold=is_sold,
                pedigree_year=pedigree_year,
            ))
        
        # Get total count
        total = len(results)
        total_match = re.search(r'(\d+)\s+LOT', soup.get_text(), re.I)
        if total_match:
            total = int(total_match.group(1))
        
        # Determine if more pages
        has_more = len(results) >= per_page
        
        return CNGSearchResults(
            query=query,
            total_results=total,
            page=page,
            per_page=per_page,
            results=results,
            has_more=has_more,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVENIENCE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def scrape_cng_lot(url_or_id: str, download_images: bool = True) -> CNGCoinData:
    """
    Convenience function to scrape a single CNG lot.
    
    Args:
        url_or_id: Either full URL or lot ID (e.g., "4-DJ6RZM")
        download_images: Whether to download images locally
        
    Returns:
        CNGCoinData with all extracted fields
    """
    async with CNGScraper() as scraper:
        if url_or_id.startswith('http'):
            return await scraper.scrape_url(url_or_id, download_images)
        else:
            return await scraper.scrape_lot(url_or_id, download_images)


async def search_cng(query: str, max_results: int = 100) -> list[CNGSearchResult]:
    """
    Convenience function to search CNG.
    
    Args:
        query: Search terms
        max_results: Maximum results to return
        
    Returns:
        List of search results
    """
    async with CNGScraper() as scraper:
        results = []
        async for result in scraper.search_all(query, max_results):
            results.append(result)
        return results
