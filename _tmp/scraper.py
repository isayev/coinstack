"""
Heritage Auctions Scraper Service

Main service for scraping Heritage Auctions coin data:
- Fetches lot pages with rate limiting
- Parses HTML into structured data
- Downloads images locally
- Handles search and pagination
- Supports authenticated sessions for price data
"""

import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, AsyncIterator
from datetime import datetime
from urllib.parse import urljoin, urlencode, quote_plus
import aiofiles
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .parser import HeritageParser
from .models import (
    HeritageCoinData, HeritageImage, HeritageSearchResult, 
    HeritageSearchResults, GradingService
)

logger = logging.getLogger(__name__)


class HeritageScraper:
    """
    Scraper for Heritage Auctions (HA.com).
    
    Features:
    - Rate limiting (be respectful - Heritage is aggressive about blocking)
    - Automatic retry with backoff
    - Image downloading with deduplication
    - Search functionality
    - Optional authenticated session for price data
    - NGC verification link extraction
    """
    
    BASE_URL = "https://coins.ha.com"
    
    # Rate limiting - Heritage is more sensitive than CNG
    REQUESTS_PER_MINUTE = 20
    MIN_DELAY_SECONDS = 3.0
    
    # Image CDN
    IMAGE_CDN = "https://dyn1.heritagestatic.com"
    
    def __init__(
        self,
        image_dir: str = "data/heritage_images",
        cache_dir: Optional[str] = "data/heritage_cache",
        session_cookie: Optional[str] = None,
    ):
        """
        Initialize scraper.
        
        Args:
            image_dir: Directory for downloaded images
            cache_dir: Directory for HTML cache (speeds up re-scraping)
            session_cookie: Optional HA.com session cookie for price access
        """
        self.image_dir = Path(image_dir)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.session_cookie = session_cookie
        
        self.image_dir.mkdir(parents=True, exist_ok=True)
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.parser = HeritageParser()
        self._last_request_time = 0.0
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        cookies = {}
        if self.session_cookie:
            cookies["HASESSIONID"] = self.session_cookie
        
        self._client = httpx.AsyncClient(
            timeout=30.0,
            headers=headers,
            cookies=cookies,
            follow_redirects=True,
        )
        return self
    
    async def __aexit__(self, *args):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MAIN SCRAPING METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def scrape_lot(
        self,
        auction_id: int,
        lot_number: int,
        download_images: bool = True,
    ) -> HeritageCoinData:
        """
        Scrape a single Heritage lot by auction ID and lot number.
        
        Args:
            auction_id: Heritage auction ID (e.g., 61519)
            lot_number: Lot number within auction (e.g., 25289)
            download_images: Whether to download images locally
            
        Returns:
            HeritageCoinData with all extracted fields
        """
        lot_id = f"{auction_id}-{lot_number}"
        
        # Construct URL
        url = f"{self.BASE_URL}/c/item.zx?saleNo={auction_id}&lotIdNo={lot_number}"
        
        # Check cache first
        html = await self._get_cached(lot_id)
        if not html:
            html = await self._fetch(url)
            await self._save_cache(lot_id, html)
        
        # Parse HTML
        coin_data = self.parser.parse(html, url)
        
        # Download images if requested
        if download_images and coin_data.images:
            coin_data.images = await self._download_images(coin_data)
        
        return coin_data
    
    async def scrape_url(
        self,
        url: str,
        download_images: bool = True,
    ) -> HeritageCoinData:
        """
        Scrape a Heritage lot by full URL.
        
        Args:
            url: Full Heritage lot URL
            download_images: Whether to download images locally
            
        Returns:
            HeritageCoinData with all extracted fields
        """
        # Extract IDs from URL
        # Pattern: /a/{auction_id}-{lot_number}.s
        match = re.search(r'/a/(\d+)-(\d+)\.s', url)
        if not match:
            raise ValueError(f"Invalid Heritage URL format: {url}")
        
        auction_id = int(match.group(1))
        lot_number = int(match.group(2))
        lot_id = f"{auction_id}-{lot_number}"
        
        # Check cache first
        html = await self._get_cached(lot_id)
        if not html:
            html = await self._fetch(url)
            await self._save_cache(lot_id, html)
        
        # Parse HTML
        coin_data = self.parser.parse(html, url)
        
        # Download images if requested
        if download_images and coin_data.images:
            coin_data.images = await self._download_images(coin_data)
        
        return coin_data
    
    async def search(
        self,
        query: str,
        category: str = "ancients",
        page: int = 1,
        include_sold: bool = True,
    ) -> HeritageSearchResults:
        """
        Search Heritage auctions.
        
        Args:
            query: Search terms
            category: Category filter ("ancients", "us-coins", "world-coins")
            page: Page number (1-indexed)
            include_sold: Include past/sold lots
            
        Returns:
            HeritageSearchResults with lot summaries
        """
        params = {
            "N": "790+231",  # Category codes for ancients
            "Ntt": query,
            "Nty": "1",
            "No": (page - 1) * 60,  # Offset
        }
        
        if include_sold:
            params["type"] = "archive"
        
        url = f"{self.BASE_URL}/c/search.zx?{urlencode(params)}"
        html = await self._fetch(url)
        
        return self._parse_search_results(html, query, page)
    
    async def search_archives(
        self,
        query: str,
        max_results: int = 100,
    ) -> AsyncIterator[HeritageSearchResult]:
        """
        Search Heritage auction archives and iterate through results.
        
        Args:
            query: Search terms
            max_results: Maximum results to return
            
        Yields:
            HeritageSearchResult for each lot
        """
        page = 1
        count = 0
        
        while count < max_results:
            results = await self.search(query, page=page, include_sold=True)
            
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
        max_results: int = 50,
        download_images: bool = True,
    ) -> AsyncIterator[HeritageCoinData]:
        """
        Search and scrape full data for each result.
        
        Args:
            query: Search terms
            max_results: Maximum lots to scrape
            download_images: Whether to download images
            
        Yields:
            HeritageCoinData for each lot
        """
        async for result in self.search_archives(query, max_results):
            try:
                coin_data = await self.scrape_lot(
                    result.auction_id,
                    result.lot_number,
                    download_images
                )
                yield coin_data
            except Exception as e:
                logger.error(f"Failed to scrape lot {result.lot_id}: {e}")
                continue
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # NGC VERIFICATION
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def verify_ngc_cert(self, cert_number: str) -> Optional[dict]:
        """
        Verify NGC certification and get additional data.
        
        Args:
            cert_number: NGC certification number
            
        Returns:
            NGC verification data or None
        """
        url = f"https://www.ngccoin.com/certlookup/{cert_number}/NGCAncients"
        
        try:
            await self._rate_limit()
            response = await self._client.get(url)
            if response.status_code == 200:
                return {
                    'verified': True,
                    'cert_number': cert_number,
                    'url': url,
                }
        except Exception as e:
            logger.warning(f"NGC verification failed for {cert_number}: {e}")
        
        return None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HTTP FETCHING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
    )
    async def _fetch(self, url: str) -> str:
        """Fetch URL with rate limiting and retry"""
        await self._rate_limit()
        
        if not self._client:
            raise RuntimeError("Scraper not initialized. Use 'async with' context.")
        
        logger.info(f"Fetching: {url}")
        
        response = await self._client.get(url)
        
        # Check for rate limiting or blocking
        if response.status_code == 429:
            logger.warning("Rate limited by Heritage - backing off")
            await asyncio.sleep(60)
            raise Exception("Rate limited")
        
        if response.status_code == 403:
            logger.error("Blocked by Heritage - may need to rotate IP or wait")
            raise Exception("Blocked")
        
        response.raise_for_status()
        return response.text
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        
        if elapsed < self.MIN_DELAY_SECONDS:
            await asyncio.sleep(self.MIN_DELAY_SECONDS - elapsed)
        
        self._last_request_time = asyncio.get_event_loop().time()
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CACHING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def _get_cached(self, lot_id: str) -> Optional[str]:
        """Get cached HTML if available"""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{lot_id}.html"
        if cache_file.exists():
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                return await f.read()
        
        return None
    
    async def _save_cache(self, lot_id: str, html: str):
        """Save HTML to cache"""
        if not self.cache_dir:
            return
        
        cache_file = self.cache_dir / f"{lot_id}.html"
        async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
            await f.write(html)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # IMAGE DOWNLOADING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    async def _download_images(self, coin_data: HeritageCoinData) -> list[HeritageImage]:
        """Download all images for a coin"""
        updated_images = []
        
        for img in coin_data.images:
            try:
                local_path = await self._download_image(
                    coin_data.heritage_lot_id,
                    img.url,
                    img.index
                )
                img.local_path = str(local_path)
                updated_images.append(img)
            except Exception as e:
                logger.warning(f"Failed to download image {img.url}: {e}")
                updated_images.append(img)
        
        return updated_images
    
    async def _download_image(
        self,
        lot_id: str,
        url: str,
        index: int
    ) -> Path:
        """Download a single image"""
        # Generate filename
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        ext = 'jpg' if '.jpg' in url.lower() else 'png'
        filename = f"{lot_id}_{index}_{url_hash}.{ext}"
        local_path = self.image_dir / filename
        
        # Skip if already downloaded
        if local_path.exists():
            return local_path
        
        # Download
        await self._rate_limit()
        
        logger.info(f"Downloading image: {url}")
        response = await self._client.get(url)
        response.raise_for_status()
        
        # Save
        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(response.content)
        
        return local_path
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SEARCH RESULTS PARSING
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    def _parse_search_results(
        self,
        html: str,
        query: str,
        page: int
    ) -> HeritageSearchResults:
        """Parse search results page"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        results = []
        
        # Look for lot links
        for link in soup.find_all('a', href=re.compile(r'/a/\d+-\d+\.s')):
            href = link.get('href', '')
            match = re.search(r'/a/(\d+)-(\d+)\.s', href)
            if not match:
                continue
            
            auction_id = int(match.group(1))
            lot_number = int(match.group(2))
            lot_id = f"{auction_id}-{lot_number}"
            
            # Get title
            title = link.get_text(strip=True)
            if not title or len(title) < 10:
                parent = link.find_parent(['div', 'td', 'li'])
                if parent:
                    title_elem = parent.find(['h3', 'h4', 'span'])
                    if title_elem:
                        title = title_elem.get_text(strip=True)
            
            # Skip duplicates
            if any(r.lot_id == lot_id for r in results):
                continue
            
            # Check for sold status
            is_sold = False
            parent = link.find_parent(['div', 'tr'])
            if parent:
                if re.search(r'Sold|Closed|Archive', parent.get_text(), re.I):
                    is_sold = True
            
            # Check for grading service
            grading_service = None
            grade = None
            if 'NGC' in title:
                grading_service = GradingService.NGC
                ngc_match = re.search(r'NGC\s+(\w+\s*\d*/\d*\s*-\s*\d*/\d*)', title)
                if ngc_match:
                    grade = ngc_match.group(1)
            elif 'PCGS' in title:
                grading_service = GradingService.PCGS
            
            # Find thumbnail
            thumbnail = None
            if parent:
                img = parent.find('img', src=re.compile(r'heritagestatic'))
                if img:
                    thumbnail = img.get('src')
            
            results.append(HeritageSearchResult(
                lot_id=lot_id,
                auction_id=auction_id,
                lot_number=lot_number,
                title=title,
                url=urljoin(self.BASE_URL, href),
                thumbnail_url=thumbnail,
                is_sold=is_sold,
                grading_service=grading_service,
                grade=grade,
            ))
        
        # Get total count
        total = len(results)
        total_match = re.search(r'([\d,]+)\s+results?', soup.get_text(), re.I)
        if total_match:
            total = int(total_match.group(1).replace(',', ''))
        
        has_more = bool(soup.find('a', string=re.compile('Next', re.I)))
        
        return HeritageSearchResults(
            query=query,
            total_results=total,
            page=page,
            results=results,
            has_more=has_more,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONVENIENCE FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def scrape_heritage_lot(url: str, download_images: bool = True) -> HeritageCoinData:
    """
    Convenience function to scrape a single Heritage lot.
    """
    async with HeritageScraper() as scraper:
        return await scraper.scrape_url(url, download_images)


async def search_heritage(query: str, max_results: int = 50) -> list[HeritageSearchResult]:
    """
    Convenience function to search Heritage archives.
    """
    async with HeritageScraper() as scraper:
        results = []
        async for result in scraper.search_archives(query, max_results):
            results.append(result)
        return results
