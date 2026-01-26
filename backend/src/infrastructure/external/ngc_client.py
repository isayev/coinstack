"""NGC Ancients certificate lookup client with caching and rate limiting."""
import re
import asyncio
import logging
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal
from bs4 import BeautifulSoup
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


# ============================================================================
# EXCEPTIONS
# ============================================================================

class NGCError(Exception):
    """Base exception for NGC connector errors."""
    pass


class InvalidCertificateError(NGCError):
    """Invalid certificate number format."""
    pass


class CertificateNotFoundError(NGCError):
    """Certificate not found in NGC database."""
    pass


class NGCTimeoutError(NGCError):
    """NGC lookup timed out."""
    pass


class NGCRateLimitError(NGCError):
    """Rate limited by NGC."""
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


# ============================================================================
# DATA MODELS
# ============================================================================

class ImagePreview(BaseModel):
    """Preview data for a coin image."""
    url: str
    source: str = "ngc_photovision"
    image_type: str = "combined"
    is_primary: bool = False


class NGCCertificateData(BaseModel):
    """Data extracted from NGC certificate page."""
    cert_number: str
    grade: Optional[str] = None
    strike_score: Optional[str] = None
    surface_score: Optional[str] = None
    numeric_grade: Optional[int] = None
    designation: Optional[str] = None
    description: Optional[str] = None
    coin_type: Optional[str] = None
    images: list[ImagePreview] = []
    verified: bool = True
    verification_url: str = ""


# ============================================================================
# RATE LIMITER
# ============================================================================

class AsyncRateLimiter:
    """Simple async rate limiter using token bucket."""
    
    def __init__(self, rate: int, per: int = 60):
        """
        Args:
            rate: Number of requests allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a rate limit token, waiting if necessary."""
        async with self._lock:
            now = datetime.utcnow()
            time_passed = (now - self.last_update).total_seconds()
            
            # Replenish tokens
            self.tokens = min(self.rate, self.tokens + time_passed * (self.rate / self.per))
            self.last_update = now
            
            if self.tokens < 1:
                # Calculate wait time
                wait_time = (1 - self.tokens) * (self.per / self.rate)
                logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# ============================================================================
# CACHE
# ============================================================================

class SimpleCache:
    """Simple in-memory cache with TTL."""
    
    def __init__(self):
        self._cache: dict[str, tuple[str, datetime]] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expires_at = self._cache[key]
            if datetime.utcnow() < expires_at:
                logger.debug(f"Cache hit for {key}")
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: str, ttl: int):
        """Set value in cache with TTL in seconds."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._cache[key] = (value, expires_at)
        logger.debug(f"Cached {key} for {ttl}s")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries."""
        now = datetime.utcnow()
        expired = [k for k, (_, exp) in self._cache.items() if now >= exp]
        for key in expired:
            del self._cache[key]


# ============================================================================
# NGC CLIENT
# ============================================================================

class NGCClient:
    """
    NGC Ancients certificate lookup client.
    
    Features:
    - Rate limiting (5 requests/minute by default)
    - 30-day caching of successful lookups
    - Certificate format validation
    - Robust error handling with specific exception types
    - Image extraction (PhotoVision)
    """
    
    # Rate limit: 5 requests per minute
    RATE_LIMIT = 5
    RATE_PERIOD = 60  # seconds
    
    # Cache TTL: 30 days (NGC data doesn't change)
    CACHE_TTL = 86400 * 30
    
    # Certificate validation pattern (7-10 digits, optionally with dash: XXXXXXX-XXX)
    CERT_PATTERN = re.compile(r'^\d{7,10}(?:-\d{1,3})?$')
    
    # NGC URLs - try both formats
    BASE_URL = "https://www.ngccoin.com/certlookup/{cert}/NGCAncients"
    BASE_URL_ALT = "https://www.ngccoin.com/certlookup/{cert}/"
    VERIFY_URL = "https://www.ngccoin.com/certlookup/{cert}/"
    
    # Request timeout
    TIMEOUT = 30.0
    
    # User agent - more recent to avoid blocking
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    
    def __init__(
        self,
        cache: Optional[SimpleCache] = None,
        rate_limit: int = RATE_LIMIT,
        timeout: float = TIMEOUT,
    ):
        """
        Initialize NGC client.
        
        Args:
            cache: Cache instance (uses global cache if None)
            rate_limit: Max requests per minute
            timeout: Request timeout in seconds
        """
        self.cache = cache or SimpleCache()
        self.rate_limiter = AsyncRateLimiter(rate_limit, self.RATE_PERIOD)
        self.timeout = timeout
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
    
    async def _ensure_browser(self) -> bool:
        """Ensure browser is started."""
        if self._browser is None or not self._browser.is_connected():
            try:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--no-first-run',
                        '--no-sandbox',
                        '--disable-infobars',
                    ]
                )
                self._context = await self._browser.new_context(
                    user_agent=self.USER_AGENT,
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                )
                # Add comprehensive stealth scripts to avoid detection
                await self._context.add_init_script("""
                    // Remove webdriver property
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Override plugins
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Override languages
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Chrome runtime
                    window.chrome = {
                        runtime: {}
                    };
                    
                    // Permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                """)
                return True
            except Exception as e:
                logger.error(f"Failed to start browser: {e}")
                return False
        return True
    
    async def close(self):
        """Close browser."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
    
    async def lookup_certificate(self, cert_number: str) -> NGCCertificateData:
        """
        Lookup NGC certificate and extract coin data.
        
        Args:
            cert_number: NGC certification number
            
        Returns:
            NGCCertificateData with grade, scores, and images
            
        Raises:
            InvalidCertificateError: Invalid certificate format
            CertificateNotFoundError: Certificate not found
            NGCTimeoutError: Request timed out
            NGCRateLimitError: Rate limited (includes retry_after)
        """
        # 1. Validate certificate format
        cert_number = cert_number.strip()
        # Keep dashes in URL - NGC uses format like "2167888-014"
        # Remove dashes only for validation
        cert_clean = cert_number.replace('-', '')
        if not re.match(r'^\d{7,10}$', cert_clean):
            raise InvalidCertificateError(
                f"Invalid NGC cert format: {cert_number}. Must be 7-10 digits (with optional dash)."
            )
        # Keep original format with dash for URL (NGC expects it)
        cert_number_for_url = cert_number  # Keep dashes
        
        # 2. Check cache (use cleaned version for cache key)
        cache_key = f"ngc:{cert_clean}"
        cached = await self.cache.get(cache_key)
        if cached:
            logger.info(f"NGC cache hit for cert {cert_number}")
            return NGCCertificateData.model_validate_json(cached)
        
        # 3. Rate limit
        await self.rate_limiter.acquire()
        
        # 4. Ensure browser is ready
        if not await self._ensure_browser():
            raise NGCError("Failed to start browser for NGC lookup")
        
        # 5. Fetch certificate page using Playwright
        # Use original format with dash for URL
        urls_to_try = [
            self.BASE_URL.format(cert=cert_number_for_url),
            self.BASE_URL_ALT.format(cert=cert_number_for_url),
        ]
        
        # First, visit main NGC site to establish session (helps bypass some protections)
        try:
            page = await self._context.new_page()
            try:
                await page.goto("https://www.ngccoin.com", wait_until='domcontentloaded', timeout=10000)
                await asyncio.sleep(1)  # Brief pause
            except Exception:
                pass  # Continue even if main site visit fails
            finally:
                await page.close()
        except Exception:
            pass  # Continue with certificate lookup
        
        html_content = None
        for url in urls_to_try:
            try:
                page = await self._context.new_page()
                try:
                    async with asyncio.timeout(self.timeout):
                        response = await page.goto(url, wait_until='domcontentloaded', timeout=int(self.timeout * 1000))
                        
                        if not response:
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise CertificateNotFoundError(f"NGC cert {cert_number} not found")
                            continue
                        
                        # Check status
                        if response.status == 404:
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise CertificateNotFoundError(f"NGC cert {cert_number_for_url} not found")
                            continue
                        
                        if response.status == 429:
                            retry_after = int(response.headers.get("retry-after", 60))
                            await page.close()
                            raise NGCRateLimitError(
                                f"Rate limited by NGC",
                                retry_after=retry_after
                            )
                        
                        if response.status == 403:
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise NGCError(
                                    f"NGC returned 403 Forbidden. This may indicate anti-bot protection. "
                                    f"Please try accessing the certificate manually at: {self.VERIFY_URL.format(cert=cert_number_for_url)}"
                                )
                            logger.warning(f"403 on {url}, trying alternative...")
                            continue
                        
                        if response.status != 200:
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise NGCError(f"NGC returned status {response.status}")
                            continue
                        
                        # Wait for page to fully load and any anti-bot checks to complete
                        try:
                            # Wait for main content to appear
                            await page.wait_for_selector('body', timeout=5000)
                            # Additional wait for dynamic content
                            await asyncio.sleep(3)
                            # Scroll a bit to simulate human behavior
                            await page.evaluate('window.scrollTo(0, 100)')
                            await asyncio.sleep(1)
                        except Exception:
                            pass  # Continue even if selectors don't appear
                        
                        # Get page content
                        html_content = await page.content()
                        
                        # Check if we got blocked (common indicators)
                        if 'cloudflare' in html_content.lower() or 'checking your browser' in html_content.lower():
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise NGCError(
                                    f"NGC is showing anti-bot protection (Cloudflare). "
                                    f"Please try accessing manually: {self.VERIFY_URL.format(cert=cert_number_for_url)}"
                                )
                            logger.warning("Cloudflare protection detected, trying alternative URL...")
                            continue
                        
                        # Check if certificate was found (NGC returns 200 even for not found)
                        if "not found" in html_content.lower() or "no results" in html_content.lower():
                            await page.close()
                            if url == urls_to_try[-1]:
                                raise CertificateNotFoundError(f"NGC cert {cert_number_for_url} not found")
                            continue
                        
                        await page.close()
                        break  # Success!
                        
                except PlaywrightTimeoutError:
                    await page.close()
                    if url == urls_to_try[-1]:
                        raise NGCTimeoutError(f"NGC lookup timed out for cert {cert_number_for_url}")
                    continue
                except Exception as e:
                    await page.close()
                    if url == urls_to_try[-1]:
                        logger.error(f"Error fetching NGC cert {cert_number_for_url}: {e}")
                        raise NGCError(f"Error fetching certificate: {e}")
                    continue
                    
            except asyncio.TimeoutError:
                if url == urls_to_try[-1]:
                    raise NGCTimeoutError(f"NGC lookup timed out for cert {cert_number_for_url}")
                continue
        
        if not html_content:
            raise CertificateNotFoundError(f"NGC cert {cert_number_for_url} not found")
        
        # 6. Parse response (use cleaned version for cert_number in data)
        data = self._parse_certificate_page(html_content, cert_clean)
        
        # 7. Cache successful lookup
        await self.cache.set(cache_key, data.model_dump_json(), self.CACHE_TTL)
        logger.info(f"NGC lookup successful for cert {cert_number}, cached for 30 days")
        
        return data
    
    def _parse_certificate_page(self, html: str, cert_number: str) -> NGCCertificateData:
        """
        Parse NGC certificate page HTML.
        
        Extracts:
        - Grade (MS, AU, XF, VF, etc.)
        - Strike/Surface scores (4/5, 5/5)
        - Designation (Choice, Fine Style)
        - Description
        - PhotoVision images
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # Initialize data
        grade = None
        strike_score = None
        surface_score = None
        numeric_grade = None
        designation = None
        description = None
        coin_type = None
        images: list[ImagePreview] = []
        
        # --- Parse Grade ---
        # Try to find grade section
        grade_elem = soup.select_one('.cert-grade, .grade, [class*="grade"]')
        if grade_elem:
            grade_text = grade_elem.get_text(strip=True)
            match = re.search(r'(MS|AU|XF|VF|Fine|VG|Good|AG|Fair|Poor)\s*(\d+)?', grade_text, re.I)
            if match:
                grade = match.group(1).upper()
                if match.group(2):
                    numeric_grade = int(match.group(2))
        
        # Look for strike/surface scores
        score_elem = soup.select_one('.cert-scores, [class*="strike"], [class*="surface"]')
        if score_elem:
            score_text = score_elem.get_text(strip=True)
            
            strike_match = re.search(r'Strike[:\s]*(\d/\d)', score_text, re.I)
            if strike_match:
                strike_score = strike_match.group(1)
            
            surface_match = re.search(r'Surface[:\s]*(\d/\d)', score_text, re.I)
            if surface_match:
                surface_score = surface_match.group(1)
        
        # Alternative: Look for scores in any text
        if not strike_score or not surface_score:
            full_text = soup.get_text()
            if not strike_score:
                match = re.search(r'Strike[:\s]*(\d/\d)', full_text, re.I)
                if match:
                    strike_score = match.group(1)
            if not surface_score:
                match = re.search(r'Surface[:\s]*(\d/\d)', full_text, re.I)
                if match:
                    surface_score = match.group(1)
        
        # Look for designation
        designation_elem = soup.select_one('.cert-designation, [class*="designation"]')
        if designation_elem:
            designation = designation_elem.get_text(strip=True)
        else:
            # Check for common designations in text
            full_text = soup.get_text()
            for des in ['Fine Style', 'Choice', 'Gem', 'Superb Gem', 'NGC Ancients']:
                if des.lower() in full_text.lower():
                    designation = des
                    break
        
        # Parse description/coin type
        desc_elem = soup.select_one('.cert-description, .coin-description, [class*="description"]')
        if desc_elem:
            description = desc_elem.get_text(strip=True)
        
        type_elem = soup.select_one('.cert-type, .coin-type, [class*="cointype"]')
        if type_elem:
            coin_type = type_elem.get_text(strip=True)
        
        # --- Parse Images ---
        # Look for PhotoVision images
        img_patterns = [
            'img[src*="photovision"]',
            'img[src*="ngc"]',
            '.cert-images img',
            '.coin-images img',
            '[class*="photo"] img',
        ]
        
        for pattern in img_patterns:
            for img in soup.select(pattern):
                src = img.get('src') or img.get('data-src')
                if src and 'placeholder' not in src.lower():
                    # Determine image type from context
                    img_type = "combined"
                    parent_text = img.parent.get_text().lower() if img.parent else ""
                    alt_text = (img.get('alt') or '').lower()
                    
                    if 'obverse' in parent_text or 'obverse' in alt_text:
                        img_type = "obverse"
                    elif 'reverse' in parent_text or 'reverse' in alt_text:
                        img_type = "reverse"
                    elif 'slab' in parent_text or 'holder' in parent_text:
                        img_type = "slab_front"
                    
                    # Make URL absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.ngccoin.com' + src
                    
                    images.append(ImagePreview(
                        url=src,
                        source="ngc_photovision",
                        image_type=img_type,
                    ))
        
        # Deduplicate images by URL
        seen_urls = set()
        unique_images = []
        for img in images:
            if img.url not in seen_urls:
                seen_urls.add(img.url)
                unique_images.append(img)
        
        return NGCCertificateData(
            cert_number=cert_number,
            grade=grade,
            strike_score=strike_score,
            surface_score=surface_score,
            numeric_grade=numeric_grade,
            designation=designation,
            description=description or coin_type,
            coin_type=coin_type,
            images=unique_images,
            verified=True,
            verification_url=self.VERIFY_URL.format(cert=cert_number),
        )


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Global cache instance
_ngc_cache = SimpleCache()

# Global client instance (reuses rate limiter and cache)
_ngc_client: Optional[NGCClient] = None


def get_ngc_client() -> NGCClient:
    """Get NGC client instance (singleton for rate limiting)."""
    global _ngc_client
    if _ngc_client is None:
        _ngc_client = NGCClient(cache=_ngc_cache)
    return _ngc_client


async def cleanup_ngc_client():
    """Cleanup NGC client (call on shutdown)."""
    global _ngc_client
    if _ngc_client:
        await _ngc_client.close()
        _ngc_client = None
